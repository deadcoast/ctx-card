# `ctxcard_gen.py` — CTX-CARD v2 (spec-complete, Python-extended)

- V2 emits the designed tagset, enforces prefix-free aliases, supports **per-package cards** (`CTXCARD.<pkg>.md`), and includes **Δ** diff output.

```python
#!/usr/bin/env python3
# CTX-CARD generator — v2 (spec-complete for your CTX-CARD v1)
# Implements: ID, AL (prefix-free), NM, TY, TK, MO, SY, SG, ED, IN, CN, ER, IO, DT, PX, EX, RV, Δ
# Extras (Python): call-graph with cross-module resolution, class methods, properties, descriptors,
# dataclasses/pydantic DTOs, FastAPI/Flask routes, Exception taxonomy, Enums -> TK.
#
# Zero third-party deps. Python 3.9+ (uses ast.unparse).

from __future__ import annotations
import argparse, ast, os, sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

# ============ utils ============

def today_stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d")

def relpath(p: Path, root: Path) -> str:
    try: return str(p.relative_to(root).as_posix())
    except Exception: return str(p.as_posix())

def is_probably_binary(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return b"\0" in f.read(2048)
    except Exception:
        return True

def ascii_only(s: str) -> str:
    return s.encode("ascii", "ignore").decode("ascii")

def file_to_dotted(rp: str) -> str:
    p = Path(rp)
    if p.name == "__init__.py":
        return str(p.parent).replace("/", ".")
    return rp[:-3].replace("/", ".") if rp.endswith(".py") else rp.replace("/", ".")

def ann_to_str(ann: Optional[ast.AST]) -> str:
    if ann is None: return ""
    try: return ast.unparse(ann)
    except Exception: return ""

# ============ data ============

@dataclass
class Symbol:
    mid: int
    sid: int
    kind: str     # "mod" | "cls" | "fn" | "prop"
    name: str     # "func" or "Class.method" or "Class.attr"
    signature: Optional[str] = None
    deco: List[str] = field(default_factory=list)
    modifiers: Set[str] = field(default_factory=set)  # staticmethod, classmethod, property, descriptor
    invariants: Optional[str] = None

@dataclass
class ModuleInfo:
    id: int
    path: str
    dotted: str
    role_tags: Set[str] = field(default_factory=set)
    symbols: List[Symbol] = field(default_factory=list)
    imports_paths: Set[str] = field(default_factory=set)       # resolved repo paths (module edges)
    import_names: Dict[str, str] = field(default_factory=dict) # alias -> dotted origin
    fn_to_sid: Dict[str,int] = field(default_factory=dict)     # "func" or "Class.method" -> sid
    prop_to_sid: Dict[str,int] = field(default_factory=dict)   # "Class.attr" -> sid
    dts: List[Tuple[str,Dict[str,str]]] = field(default_factory=list) # DT
    errors: List[Tuple[str,str,str]] = field(default_factory=list)    # ER
    routes: List[Tuple[int,str,str,List[str]]] = field(default_factory=list)  # IO
    calls: List[Tuple[int,Tuple[int,int]]] = field(default_factory=list)      # ED calls
    tokens: List[Tuple[str,List[str]]] = field(default_factory=list)          # TK name -> keys
    reexports: Dict[str,str] = field(default_factory=dict)      # pkg.attr -> dotted origin
    invariants_mod: List[str] = field(default_factory=list)     # IN at module level (rare)
    px: List[Tuple[str,str]] = field(default_factory=list)      # PX rules discovered

@dataclass
class ScanResult:
    modules: Dict[str, ModuleInfo]
    langs: List[str]

# ============ heuristics ============

CODE_EXTS = {".py",".ts",".tsx",".js",".jsx",".go",".rs",".java",".kt",".swift",".c",".h",".cpp",".hpp",".cs"}

def is_code_file(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in CODE_EXTS and not is_probably_binary(p)

def role_tags_for(path: str) -> Set[str]:
    low = path.lower()
    tags = set()
    for k,t in [("test","test"),("auth","auth"),("api","api"),
                ("repo","repo"),("repository","repo"),("service","svc"),("svc","svc")]:
        if k in low: tags.add(t)
    return tags or {"mod"}

def detect_langs(root: Path) -> List[str]:
    exts = {p.suffix.lower() for p in root.rglob("*") if p.is_file()}
    lang_map = {".py":"py",".ts":"ts",".tsx":"tsx",".js":"js",".jsx":"jsx",".go":"go",".rs":"rs",
                ".java":"java",".kt":"kt",".swift":"swift",".c":"c",".h":"c-h",".cpp":"cpp",
                ".hpp":"cpp-h",".cs":"cs"}
    out = sorted({lang_map[e] for e in exts if e in lang_map})
    return out or ["unknown"]

# ============ Python parsing helpers ============

def dotted_from_ast(expr: ast.AST) -> str:
    if isinstance(expr, ast.Name): return expr.id
    if isinstance(expr, ast.Attribute):
        base = dotted_from_ast(expr.value)
        return f"{base}.{expr.attr}" if base else expr.attr
    return ""

def function_signature(node: ast.AST) -> str:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)): return ""
    args=[]
    for a in node.args.args:
        t = ann_to_str(a.annotation); args.append(f"{a.arg}:{t}" if t else a.arg)
    if node.args.vararg: args.append(f"*{node.args.vararg.arg}")
    for a in node.args.kwonlyargs:
        t = ann_to_str(a.annotation); args.append(f"{a.arg}:{t}" if t else a.arg)
    if node.args.kwarg: args.append(f"**{node.args.kwarg.arg}")
    ret = ann_to_str(node.returns) or "Any"
    return f"({','.join(args)})->{ret}"

def extract_invariants(node: ast.AST) -> Optional[str]:
    doc = ast.get_docstring(node) or ""
    if not doc: return None
    req=ens=None
    for line in doc.splitlines():
        ls=line.strip()
        if ls.lower().startswith("requires:"): req = ls.split(":",1)[1].strip()
        elif ls.lower().startswith("ensures:"): ens = ls.split(":",1)[1].strip()
    if req or ens:
        if req and ens: return f"requires({req}) ∧ ensures({ens})"
        return f"requires({req})" if req else f"ensures({ens})"
    return None

def method_modifiers(decos: List[str]) -> Set[str]:
    mods=set()
    for nm in decos:
        tail = nm.split(".")[-1]
        if tail=="staticmethod": mods.add("staticmethod")
        elif tail=="classmethod": mods.add("classmethod")
        elif tail=="property": mods.add("property")
        elif tail=="cached_property": mods.add("property")
    return mods

def class_has_descriptor_dunders(node: ast.ClassDef) -> bool:
    names={stmt.name for stmt in node.body if isinstance(stmt,(ast.FunctionDef,ast.AsyncFunctionDef))}
    return bool({"__get__","__set__","__set_name__"} & names)

def is_enum_class(node: ast.ClassDef) -> Optional[str]:
    # enum.Enum or a subclass; return enum base name if found
    for b in node.bases:
        nm = ann_to_str(b) or dotted_from_ast(b)
        if nm.endswith(".Enum") or nm=="Enum": return nm
    return None

# ============ repository index helpers ============

def build_indices(mods: Dict[str, ModuleInfo]) -> Tuple[Dict[str,str], Dict[str,List[str]]]:
    dotted_to_path: Dict[str,str]={}
    stem_to_paths: Dict[str,List[str]]={}
    for rp, mi in mods.items():
        dotted_to_path[mi.dotted]=rp
        stem_to_paths.setdefault(Path(rp).stem, []).append(rp)
    return dotted_to_path, stem_to_paths

def longest_prefix_module(dotted: str, dotted_to_path: Dict[str,str]) -> Optional[str]:
    parts=dotted.split(".")
    for i in range(len(parts),0,-1):
        cand=".".join(parts[:i])
        rp=dotted_to_path.get(cand)
        if rp: return rp
    return None

# ============ scan pass A (build symbols, imports, DTOs, TK, ER, IO) ============

def scan_repo(root: Path, include_glob: Optional[str], exclude_glob: Optional[str]) -> ScanResult:
    files=[]
    it = root.rglob("**/*" if include_glob is None else include_glob)
    for p in it:
        if not p.is_file(): continue
        if exclude_glob and p.match(exclude_glob): continue
        if is_code_file(p): files.append(p)
    files=sorted(set(files), key=lambda x: relpath(x, root))

    modules: Dict[str, ModuleInfo]={}
    mid=1
    for path in files:
        rp=relpath(path, root)
        md=file_to_dotted(rp)
        mi=ModuleInfo(id=mid, path=rp, dotted=md, role_tags=role_tags_for(rp))
        mi.symbols.append(Symbol(mid=mid, sid=0, kind="mod", name=Path(rp).stem))
        modules[rp]=mi
        mid+=1

    dotted_to_path, stem_to_paths = build_indices(modules)

    for rp, mi in modules.items():
        full=root/rp
        if full.suffix.lower()!=".py": continue
        try:
            src=full.read_text(encoding="utf-8", errors="replace")
            tree=ast.parse(src, filename=str(full))
        except Exception:
            continue

        imported_symbols: Dict[str,str]={}

        # imports: alias map and module import edges
        imports_raw:set[str]=set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    mi.import_names[n.asname or n.name]=n.name
                    imports_raw.add(n.name)
            elif isinstance(node, ast.ImportFrom):
                base=node.module or ""
                dots="."*(node.level or 0)
                base_full=(dots+base) if base or dots else ""
                imports_raw.add(dots+base if base or dots else "")
                for n in node.names:
                    alias=n.asname or n.name
                    dotted=(base_full+"."+n.name) if base_full else n.name
                    mi.import_names[alias]=dotted
                    imported_symbols[alias]=dotted

        # resolve imports to repo paths (module edges)
        for tok in imports_raw:
            if not tok: continue
            if tok in dotted_to_path:
                mi.imports_paths.add(dotted_to_path[tok]); continue
            last=tok.split(".")[-1]
            for rp2 in stem_to_paths.get(last, []):
                mi.imports_paths.add(rp2)

        # symbols (classes, methods, properties, functions), DTOs, ER, TK(Enums)
        sid=1
        enum_buffers: List[Tuple[str,List[str]]] = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                # Enum -> TK
                enum_base = is_enum_class(node)
                if enum_base:
                    keys=[]
                    for b in node.body:
                        if isinstance(b, ast.Assign):
                            for t in b.targets:
                                if isinstance(t, ast.Name) and t.id.isupper():
                                    keys.append(t.id)
                    if keys:
                        mi.tokens.append((node.name, keys))

                # class symbol
                cls=node.name
                sym_cls=Symbol(mid=mi.id, sid=sid, kind="cls", name=cls)
                if class_has_descriptor_dunders(node): sym_cls.modifiers.add("descriptor")
                invc=extract_invariants(node)
                if invc: sym_cls.invariants=invc
                mi.symbols.append(sym_cls); sid+=1

                # DT: dataclass / pydantic
                is_dataclass=False; is_pyd=False
                decos=[]
                for d in node.decorator_list:
                    nm = dotted_from_ast(d.func) if isinstance(d, ast.Call) else dotted_from_ast(d)
                    decos.append(nm)
                if any(n.endswith("dataclass") for n in decos): is_dataclass=True
                for b in node.bases:
                    bn=ann_to_str(b) or dotted_from_ast(b)
                    if bn.endswith("BaseModel") or bn.endswith("pydantic.BaseModel"): is_pyd=True
                if is_dataclass or is_pyd:
                    fields={}
                    for stmt in node.body:
                        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                            t=ann_to_str(stmt.annotation) or "Any"
                            fields[stmt.target.id]=t
                    mi.dts.append((cls, fields))

                # methods/properties
                for stmt in node.body:
                    if isinstance(stmt,(ast.FunctionDef, ast.AsyncFunctionDef)):
                        decos=[dotted_from_ast(d if not isinstance(d, ast.Call) else d.func) for d in stmt.decorator_list]
                        mods=method_modifiers(decos)
                        if "property" in mods:
                            sp=Symbol(mid=mi.id, sid=sid, kind="prop", name=f"{cls}.{stmt.name}",
                                      deco=decos, modifiers={"property"})
                            inv=extract_invariants(stmt)
                            if inv: sp.invariants=inv
                            mi.symbols.append(sp)
                            mi.prop_to_sid[sp.name]=sid
                            sid+=1
                            continue
                        sig=function_signature(stmt)
                        sm=Symbol(mid=mi.id, sid=sid, kind="fn", name=f"{cls}.{stmt.name}",
                                  signature=sig, deco=decos, modifiers=mods)
                        inv=extract_invariants(stmt)
                        if inv: sm.invariants=inv
                        mi.symbols.append(sm)
                        mi.fn_to_sid[sm.name]=sid
                        sid+=1

                # ER: exceptions
                for b in node.bases:
                    bn=ann_to_str(b) or dotted_from_ast(b)
                    if bn.endswith("Exception") or bn=="Exception":
                        mi.errors.append((cls,"domain","custom exception"))

            elif isinstance(node,(ast.FunctionDef, ast.AsyncFunctionDef)):
                name=node.name
                decos=[dotted_from_ast(d if not isinstance(d, ast.Call) else d.func) for d in node.decorator_list]
                sig=function_signature(node)
                sym=Symbol(mid=mi.id, sid=sid, kind="fn", name=name, signature=sig, deco=decos)
                inv=extract_invariants(node)
                if inv: sym.invariants=inv
                mi.symbols.append(sym); mi.fn_to_sid[name]=sid

                # IO: FastAPI/Flask
                for d in node.decorator_list:
                    if isinstance(d, ast.Call):
                        nm=dotted_from_ast(d.func)
                        if nm in ("app.get","app.post","app.put","app.delete",
                                  "router.get","router.post","router.put","router.delete"):
                            verb=nm.split(".")[-1].upper()
                            if d.args and isinstance(d.args[0], ast.Constant) and isinstance(d.args[0].value,str):
                                mi.routes.append((sid,verb,d.args[0].value,["200"]))
                        if nm and nm.endswith(".route"): # Flask
                            pathv=None; verb="GET"
                            if d.args and isinstance(d.args[0], ast.Constant) and isinstance(d.args[0].value,str):
                                pathv=d.args[0].value
                            for kw in d.keywords or []:
                                if kw.arg=="methods" and isinstance(kw.value,(ast.List,ast.Tuple)):
                                    for elt in kw.value.elts:
                                        if isinstance(elt, ast.Constant) and isinstance(elt.value,str):
                                            verb=elt.value.upper(); break
                            if pathv: mi.routes.append((sid,verb,pathv,["200"]))
                sid+=1

        # re-exports: __init__.py + __all__
        if Path(rp).name=="__init__.py":
            pkg=mi.dotted
            for local, origin in imported_symbols.items():
                mi.reexports[f"{pkg}.{local}"]=origin
        exps=[]
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id=="__all__":
                        if isinstance(node.value,(ast.List,ast.Tuple)):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value,str):
                                    exps.append(elt.value)
        if exps:
            pkg=mi.dotted
            # prefer imported origin; else local symbol
            locals_defined = {s.name.split(".")[0] for s in mi.symbols if s.sid!=0}
            for nm in exps:
                origin = imported_symbols.get(nm)
                if not origin and nm in locals_defined:
                    origin = f"{pkg}.{nm}"
                if origin:
                    mi.reexports[f"{pkg}.{nm}"]=origin

        # PX rule: prefix-free AL will be validated later; cheap example PX we add:
        # forbid assignment to globals in svc modules (very conservative)
        if "svc" in mi.role_tags:
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    mi.px.append(("forbid global state in svc","concurrency"))

    langs=detect_langs(root)
    return ScanResult(modules=modules, langs=langs)

# ============ pass B: resolve calls ============

def build_reexports_global(mods: Dict[str, ModuleInfo]) -> Dict[str,str]:
    m={}
    for mi in mods.values(): m.update(mi.reexports)
    return m

def resolve_qualified(full_dotted: str, dotted_to_path: Dict[str,str], modules: Dict[str, ModuleInfo], rexp: Dict[str,str]) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """Return (mid, sid, kind_or_none) using longest-prefix and class.method/func lookup; try re-exports."""
    def try_direct(dotted: str):
        rp = longest_prefix_module(dotted, dotted_to_path)
        if not rp: return None, None, None
        mt = modules[rp]
        prefix_len = len(mt.dotted.split(".")) if mt.dotted else 0
        parts = dotted.split(".")
        rest = parts[prefix_len:]
        if len(rest)>=2:
            cand=f"{rest[0]}.{rest[1]}"
            sid = mt.fn_to_sid.get(cand) or mt.prop_to_sid.get(cand)
            if sid:
                kind = "prop" if cand in mt.prop_to_sid else "fn"
                return mt.id, sid, kind
        if len(rest)>=1:
            nm=rest[0]
            sid = mt.fn_to_sid.get(nm) or mt.prop_to_sid.get(nm)
            if sid:
                kind = "prop" if nm in mt.prop_to_sid else "fn"
                return mt.id, sid, kind
        return mt.id, 0, "mod"
    mid,sid,kind = try_direct(full_dotted)
    if mid is not None: return mid,sid,kind
    origin = rexp.get(full_dotted)
    if origin:
        return try_direct(origin)
    return None, None, None

def extract_calls(root: Path, scan: ScanResult) -> None:
    mods=scan.modules
    dotted_to_path,_=build_indices(mods)
    rexp=build_reexports_global(mods)

    for rp, mi in mods.items():
        full=root/rp
        if full.suffix.lower()!=".py": continue
        try:
            src=full.read_text(encoding="utf-8", errors="replace")
            tree=ast.parse(src, filename=str(full))
        except Exception:
            continue

        # parent links
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                setattr(child, "parent", parent)

        # local fn/method lookup
        local = dict(mi.fn_to_sid)

        def caller_sid_of(node: ast.AST) -> Optional[int]:
            up=node
            while True:
                up=getattr(up,"parent",None)
                if up is None: return None
                if isinstance(up,(ast.FunctionDef, ast.AsyncFunctionDef)):
                    # check if within a class
                    owner=up; cls=None; p2=owner
                    while True:
                        p2=getattr(p2,"parent",None)
                        if p2 is None: break
                        if isinstance(p2, ast.ClassDef): cls=p2.name; break
                    if cls:
                        return local.get(f"{cls}.{owner.name}") or local.get(owner.name)
                    return local.get(owner.name)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call): continue
            caller_sid = caller_sid_of(node)
            if not caller_sid: continue

            target=None
            if isinstance(node.func, ast.Name):
                sid = local.get(node.func.id)
                if sid: target=(mi.id, sid, "fn")
            elif isinstance(node.func, ast.Attribute):
                dotted = dotted_from_ast(node.func)
                if dotted:
                    head=dotted.split(".")[0]
                    mapped=mi.import_names.get(head)
                    full_dotted = ".".join([mapped]+dotted.split(".")[1:]) if mapped else dotted
                    tmid, tsid, kind = resolve_qualified(full_dotted, dotted_to_path, mods, rexp)
                    if tmid is not None:
                        target=(tmid, tsid, kind or "fn")

            if target:
                tmid, tsid, k = target
                # do not create calls to properties (attribute access)
                if k=="prop": continue
                mi.calls.append((caller_sid,(tmid,tsid)))

# ============ AL: prefix-free enforcement & defaults ============

DEFAULT_ALIASES = [
    ("cfg","Configuration"),
    ("svc","Service"),
    ("repo","Repository"),
    ("dto","DataTransferObject"),
    ("uc","UseCase"),
    ("http","HTTP"),
    ("db","Database"),
    ("jwt","JWT"),
]

def check_prefix_free(pairs: List[Tuple[str,str]]) -> Tuple[List[Tuple[str,str]], List[Tuple[str,str]]]:
    """Return (ok_aliases, px_violations as (rule,reason))."""
    ks=[k for k,_ in pairs]
    violations=[]
    for i,k1 in enumerate(ks):
        for j,k2 in enumerate(ks):
            if i==j: continue
            if k2.startswith(k1):
                violations.append((f"AL prefix-free violated: '{k1}' is prefix of '{k2}'","aliases"))
    # dedupe same violations
    seen=set(); px=[]
    for r,why in violations:
        if r not in seen:
            px.append((r,why)); seen.add(r)
    return pairs, px

# ============ Render ============

def render_card(proj: str, langs: List[str], std: str, mods: Dict[str, ModuleInfo]) -> str:
    lines=[]
    # ID
    lines.append(f"ID: proj|{proj} lang|{','.join(langs)} std|{std} ts|{today_stamp()}")

    # AL (prefix-free)
    al_ok, al_px = check_prefix_free(DEFAULT_ALIASES)
    for k,v in al_ok:
        lines.append(f"AL: {k}=>{v}")

    # NM defaults (compact, regex anchored)
    NM = [
        ("module", r"^[a-z_]+$", "auth_service"),
        ("class",  r"^[A-Z][A-Za-z0-9]+$", "AuthService"),
        ("func",   r"^[a-z_][a-z0-9_]*$", "issue_token"),
        ("var",    r"^[a-z_][a-z0-9_]*$", "user_repo"),
    ]
    for scope, regex, ex in NM:
        lines.append(f"NM: {scope} | {regex} | {ex}")

    # MO/SY/SG/IN/MD
    mlist = sorted(mods.values(), key=lambda m: m.id)
    for m in mlist:
        tags="{"+",".join(sorted(m.role_tags))+"}"
        lines.append(f"MO: #{m.id} | {m.path} | {tags}")
    for m in mlist:
        for s in m.symbols:
            lines.append(f"SY: #{s.mid}.#{s.sid} | {s.kind} | {s.name}")
            if s.kind=="fn" and s.signature:
                lines.append(f"SG: #{s.mid}.#{s.sid} | {s.signature}")
            if s.invariants:
                # IN line uses symbol name prefix for readability
                lines.append(f"IN: {s.name.split('.')[-1]} ⇒ {s.invariants}")
            if s.modifiers:
                lines.append(f"MD: #{s.mid}.#{s.sid} | "+"{"+",".join(sorted(s.modifiers))+"}")

    # DT
    for m in mlist:
        for nm, fields in m.dts:
            field_s=",".join(f"{k}:{v}" for k,v in fields.items())
            lines.append(f"DT: {nm} | {{{field_s}}}")

    # TK (Enums → names)
    for m in mlist:
        for nm, keys in m.tokens:
            lines.append(f"TK: {nm} | "+"{"+",".join(keys)+"}")

    # ER
    for m in mlist:
        for (nm, cat, meaning) in m.errors:
            lines.append(f"ER: {nm} | {cat} | {meaning}")

    # ED (imports)
    for m in mlist:
        for dep in sorted(m.imports_paths):
            mt=mods.get(dep)
            if mt:
                lines.append(f"ED: #{m.id}.#0 -> #{mt.id}.#0 | imports")

    # ED (calls)
    for m in mlist:
        for caller_sid,(tmid,tsid) in m.calls:
            lines.append(f"ED: #{m.id}.#{caller_sid} -> #{tmid}.#{tsid} | calls")

    # IO
    for m in mlist:
        for sid, verb, pathv, codes in m.routes:
            fn = next((s for s in m.symbols if s.sid==sid), None)
            sig = fn.signature if fn else "(…)->Any"
            in_sig = sig.split(")->")[0].lstrip("(") if ")->" in sig else ""
            out_sig = sig.split(")->")[-1] if ")->" in sig else "Any"
            lines.append(f"IO: {verb} {pathv} | {in_sig} | {out_sig} | {','.join(codes)}")

    # CN minimal policy rails
    lines.append("CN: async fn end with _async")
    lines.append("CN: repos never import svc")

    # PX
    for m in mlist:
        for rule, reason in m.px:
            lines.append(f"PX: {rule} | {reason}")
    # Include AL prefix-free violations (if any)
    for rule, reason in al_px:
        lines.append(f"PX: {rule} | {reason}")

    # EX (micro examples) — seed a few canonical spellings
    lines.append("EX: var(repo) => user_repo")
    lines.append("EX: class(Service) => AuthService")
    lines.append("EX: func(token) => issue_token")

    # RV
    lines.append("RV: Public fns documented; No bare except")

    # ASCII enforcement
    return "\n".join(ascii_only(ln) for ln in lines) + "\n"

# ============ TY schema supplement (optional) ============

def append_ty(lines: List[str], mods: Dict[str, ModuleInfo]) -> None:
    """Emit TY lines (kind|name|sig) for functions/methods we discovered."""
    for m in sorted(mods.values(), key=lambda x: x.id):
        for s in m.symbols:
            if s.kind=="fn" and s.signature:
                # Build fully-qualified logical name: Module or Class.method
                fq = s.name
                lines.append(f"TY: fn | {fq} | {s.signature}")

# ============ Δ computation ============

def diff_lines(old_text: str, new_text: str) -> str:
    old = [ln for ln in old_text.splitlines() if ln.strip()]
    new = [ln for ln in new_text.splitlines() if ln.strip()]
    old_set, new_set = set(old), set(new)
    add = [ln for ln in new if ln not in old_set]
    rem = [ln for ln in old if ln not in new_set]
    delta=[]
    for ln in add: delta.append(f"Δ: + {ln}")
    for ln in rem: delta.append(f"Δ: - {ln}")
    return ("\n".join(delta)+"\n") if delta else ""

# ============ per-package cards ============

def top_level_packages(mods: Dict[str, ModuleInfo]) -> Dict[str, List[ModuleInfo]]:
    bypkg: Dict[str,List[ModuleInfo]]={}
    for m in mods.values():
        parts = m.dotted.split(".")
        top = parts[0] if parts and parts[0] else None
        if top:
            bypkg.setdefault(top, []).append(m)
    return bypkg

def render_for_package(root_card: str, pkg: str, mods: Dict[str, ModuleInfo], langs: List[str], std: str, proj: str) -> str:
    # Filter module dict to those in pkg
    sub = {m.path:m for m in mods.values() if m.dotted.split(".")[0]==pkg}
    return render_card(proj, langs, std, sub)

# ============ CLI ============

def main():
    ap=argparse.ArgumentParser(description="Generate CTX-CARD v2 (spec-complete, Python-extended).")
    ap.add_argument("root", nargs="?", default=".", help="Repo root")
    ap.add_argument("--proj", default=None, help="Project slug (default: folder name)")
    ap.add_argument("--std", default="pep8", help="Style/standard hint")
    ap.add_argument("--include", default=None, help="Glob include (e.g., '**/*.py')")
    ap.add_argument("--exclude", default=None, help="Glob exclude (e.g., '**/tests/**')")
    ap.add_argument("--out", default="CTXCARD.md", help="Root card output path")
    ap.add_argument("--emit-ty", action="store_true", help="Also emit TY: lines")
    ap.add_argument("--per-package", action="store_true", help="Also emit CTXCARD.<pkg>.md for top-level packages")
    ap.add_argument("--delta-from", default=None, help="Existing CTXCARD to compute Δ and append")
    ap.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing files")
    args=ap.parse_args()

    root=Path(args.root).resolve()
    proj=args.proj or root.name

    scan=scan_repo(root, args.include, args.exclude)
    # second pass calls
    extract_calls(root, scan)

    text = render_card(proj, scan.langs, args.std, scan.modules)
    if args.emit_ty:
        extra=[]
        append_ty(extra, scan.modules)
        if extra:
            text = text + "\n".join(extra) + "\n"

    if args.delta_from:
        old_path=Path(args.delta_from)
        old_text = old_path.read_text(encoding="utf-8", errors="replace") if old_path.exists() else ""
        text = text + diff_lines(old_text, text)

    if args.stdout:
        sys.stdout.write(text)
    else:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote {args.out}")

    # per-package cards
    if args.per_package and not args.stdout:
        pkgs = top_level_packages(scan.modules)
        for pkg in sorted(pkgs.keys()):
            ptext = render_for_package(text, pkg, scan.modules, scan.langs, args.std, proj)
            outp = Path(f"CTXCARD.{pkg}.md")
            outp.write_text(ptext, encoding="utf-8")
            print(f"Wrote {outp}")

if __name__=="__main__":
    main()
```

---

## What this build covers (point-by-point vs your spec)

- **File naming**: writes `CTXCARD.md`; optional `--per-package` writes `CTXCARD.<pkg>.md` for each top-level package.
- **ASCII only**: enforced at render.
- **2–4 char tags**: outputs exactly the tags you defined.
- **Indexed identifiers**: `MO`/`SY` indices `#mid.#sid` everywhere; `ED` uses them.
- **Prefix-free `AL`**: included + violations emitted as `PX:` if any conflict.
- **Tags implemented**:

  - `ID, AL, NM, MO, SY, SG, ED (imports/calls), IN, CN, ER, IO, DT, TK, PX, EX, RV, Δ` ✔
  - `TY:` optional via `--emit-ty` (keeps default card smaller; you can turn it on).

## Usage

```bash
# Simple
python ctxcard_gen.py

# Include TY lines and per-package cards
python ctxcard_gen.py --emit-ty --per-package

# Python-only scan, exclude tests, append Δ vs existing card
python ctxcard_gen.py --include "**/*.py" --exclude "**/tests/**" --delta-from CTXCARD.md

# Print to stdout
python ctxcard_gen.py --stdout
```

---

If you want me to wire in **raise analysis** for `!raises[...]` in `TY`/`SG` (by scanning `raise X` inside functions) or expand **PX** with more AST lint rules (no bare `except`, no wildcard imports, etc.), say the word and I’ll add it cleanly without bloating tokens.
