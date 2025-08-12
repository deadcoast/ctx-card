# `ctxcard_gen.py` — CTX-CARD v2.1 (raises + lint PX)

1. **Collects `raise` info** per function/method and appends `!raises[...]` to both **`SG:`** and **`TY:`**.
2. **Expands `PX:`** with common AST lint rules:

   - bare `except:`
   - wildcard imports (`from x import *`)
   - `eval` / `exec` calls
   - mutable default args (list/dict/set)
   - `print()` in non-test modules
   - (kept) global assignment in `svc` modules

Just replace your current file with this.

---

```python
#!/usr/bin/env python3
# CTX-CARD generator — v2.1
# Adds:
#  - !raises[...] in SG: and TY: by scanning function/method bodies
#  - Expanded PX: lint rules (bare except, wildcard import, eval/exec, mutable defaults, print())
#
# Retains spec-complete CTX-CARD v1 emission and Python extras from v2.

from __future__ import annotations
import argparse, ast, sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

# ---------- utils ----------

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

# ---------- data models ----------

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
    raises: List[str] = field(default_factory=list)   # new: collected raise types

@dataclass
class ModuleInfo:
    id: int
    path: str
    dotted: str
    role_tags: Set[str] = field(default_factory=set)
    symbols: List[Symbol] = field(default_factory=list)
    imports_paths: Set[str] = field(default_factory=set)
    import_names: Dict[str, str] = field(default_factory=dict)
    fn_to_sid: Dict[str,int] = field(default_factory=dict)
    prop_to_sid: Dict[str,int] = field(default_factory=dict)
    dts: List[Tuple[str,Dict[str,str]]] = field(default_factory=list)
    errors: List[Tuple[str,str,str]] = field(default_factory=list)
    routes: List[Tuple[int,str,str,List[str]]] = field(default_factory=list)
    calls: List[Tuple[int,Tuple[int,int]]] = field(default_factory=list)
    tokens: List[Tuple[str,List[str]]] = field(default_factory=list)
    reexports: Dict[str,str] = field(default_factory=dict)
    px: List[Tuple[str,StringError]] = field(default_factory=list)  # type: ignore

StringError = str  # tiny hack to keep dataclass import order minimal

@dataclass
class ScanResult:
    modules: Dict[str, ModuleInfo]
    langs: List[str]

# ---------- heuristics ----------

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

# ---------- Python helpers ----------

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
        elif tail=="property" or tail=="cached_property": mods.add("property")
    return mods

def class_has_descriptor_dunders(node: ast.ClassDef) -> bool:
    names={stmt.name for stmt in node.body if isinstance(stmt,(ast.FunctionDef,ast.AsyncFunctionDef))}
    return bool({"__get__","__set__","__set_name__"} & names)

def is_enum_class(node: ast.ClassDef) -> bool:
    for b in node.bases:
        nm = ann_to_str(b) or dotted_from_ast(b)
        if nm.endswith(".Enum") or nm=="Enum": return True
    return False

# ----- raise analysis helpers -----

def walk_ignoring_nested(fn_node: ast.AST):
    """Yield nodes in fn_node, but do not descend into inner defs/classes/lambdas."""
    stack=[fn_node]
    while stack:
        n=stack.pop()
        yield n
        for ch in ast.iter_child_nodes(n):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            stack.append(ch)

def exception_name_from_raise(exc: Optional[ast.AST]) -> str:
    # raise SomeError(), raise pkg.Err, raise SomeError
    if exc is None:
        return "ReRaise"
    if isinstance(exc, ast.Call):
        return dotted_from_ast(exc.func) or "Exception"
    if isinstance(exc, (ast.Name, ast.Attribute)):
        return dotted_from_ast(exc) or "Exception"
    return "Exception"

def collect_raises_in_function(fn_node: ast.AST) -> List[str]:
    seen: List[str]=[]
    for n in walk_ignoring_nested(fn_node):
        if isinstance(n, ast.Raise):
            nm = exception_name_from_raise(n.exc)
            if nm not in seen: seen.append(nm)
    return seen

# ---------- repo index ----------

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

# ---------- scan pass A ----------

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

        # imports (alias map + edges) + lint PX: wildcard imports
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
                    if isinstance(n, ast.alias) and n.name=="*":
                        mi.px.append(("forbid wildcard import","namespace"))
                    alias=n.asname or n.name
                    dotted=(base_full+"."+n.name) if base_full and n.name!="*" else n.name
                    mi.import_names[alias]=dotted

        for tok in imports_raw:
            if not tok: continue
            if tok in dotted_to_path:
                mi.imports_paths.add(dotted_to_path[tok]); continue
            last=tok.split(".")[-1]
            for rp2 in stem_to_paths.get(last, []):
                mi.imports_paths.add(rp2)

        # symbols + DTO/ER/TK + lint PX: bare except, eval/exec, print(), mutable defaults
        sid=1
        # pre-scan for lint items across the file
        for n in ast.walk(tree):
            if isinstance(n, ast.ExceptHandler) and n.type is None:
                mi.px.append(("forbid bare except","error-handling"))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in {"eval","exec"}:
                mi.px.append(("forbid eval/exec","security"))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id=="print":
                if "test" not in rp.lower():
                    mi.px.append(("forbid print in production","logging"))

        def has_mutable_default(fn: ast.AST) -> bool:
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)): return False
            muts=(ast.List, ast.Dict, ast.Set)
            for d in fn.args.defaults:
                if isinstance(d, muts): return True
            for d in fn.args.kw_defaults:
                if d is not None and isinstance(d, muts): return True
            return False

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                # class symbol
                cls=node.name
                sym_cls=Symbol(mid=mi.id, sid=sid, kind="cls", name=cls)
                if class_has_descriptor_dunders(node): sym_cls.modifiers.add("descriptor")
                mi.symbols.append(sym_cls); sid+=1

                # DTOs & Errors & Enums
                if is_enum_class(node):
                    keys=[]
                    for b in node.body:
                        if isinstance(b, ast.Assign):
                            for t in b.targets:
                                if isinstance(t, ast.Name) and t.id.isupper():
                                    keys.append(t.id)
                    if keys: mi.tokens.append((node.name, keys))
                for b in node.bases:
                    bn=ann_to_str(b) or dotted_from_ast(b)
                    if bn.endswith("Exception") or bn=="Exception":
                        mi.errors.append((cls,"domain","custom exception"))
                decos=[dotted_from_ast(d if not isinstance(d, ast.Call) else d.func) for d in node.decorator_list]
                is_dataclass = any(n.endswith("dataclass") for n in decos)
                is_pyd=False
                for b in node.bases:
                    bn=ann_to_str(b) or dotted_from_ast(b)
                    if bn.endswith("BaseModel") or bn.endswith("pydantic.BaseModel"): is_pyd=True
                if is_dataclass or is_pyd:
                    fields={}
                    for stmt in node.body:
                        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                            t=ann_to_str(stmt.annotation) or "Any"; fields[stmt.target.id]=t
                    mi.dts.append((cls, fields))

                # class methods/properties
                for stmt in node.body:
                    if isinstance(stmt,(ast.FunctionDef, ast.AsyncFunctionDef)):
                        decos=[dotted_from_ast(d if not isinstance(d, ast.Call) else d.func) for d in stmt.decorator_list]
                        mods=method_modifiers(decos)
                        if "property" in mods:
                            sp=Symbol(mid=mi.id, sid=sid, kind="prop", name=f"{cls}.{stmt.name}",
                                      deco=decos, modifiers={"property"})
                            mi.symbols.append(sp); mi.prop_to_sid[sp.name]=sid; sid+=1
                            continue
                        sig=function_signature(stmt)
                        raises = collect_raises_in_function(stmt)
                        sm=Symbol(mid=mi.id, sid=sid, kind="fn", name=f"{cls}.{stmt.name}",
                                  signature=sig, deco=decos, modifiers=mods, raises=raises)
                        mi.symbols.append(sm); mi.fn_to_sid[sm.name]=sid; sid+=1

            elif isinstance(node,(ast.FunctionDef, ast.AsyncFunctionDef)):
                name=node.name
                sig=function_signature(node)
                raises = collect_raises_in_function(node)
                sym=Symbol(mid=mi.id, sid=sid, kind="fn", name=name, signature=sig, raises=raises)
                # lint: mutable defaults
                if has_mutable_default(node):
                    mi.px.append(("forbid mutable default arguments","bug-risk"))
                # IO routes (fastapi/flask) — unchanged from earlier
                for d in node.decorator_list:
                    if isinstance(d, ast.Call):
                        nm=dotted_from_ast(d.func)
                        if nm in ("app.get","app.post","app.put","app.delete",
                                  "router.get","router.post","router.put","router.delete"):
                            verb=nm.split(".")[-1].upper()
                            if d.args and isinstance(d.args[0], ast.Constant) and isinstance(d.args[0].value,str):
                                mi.routes.append((sid,verb,d.args[0].value,["200"]))
                        if nm and nm.endswith(".route"):
                            pathv=None; verb="GET"
                            if d.args and isinstance(d.args[0], ast.Constant) and isinstance(d.args[0].value,str):
                                pathv=d.args[0].value
                            for kw in d.keywords or []:
                                if kw.arg=="methods" and isinstance(kw.value,(ast.List,ast.Tuple)):
                                    for elt in kw.value.elts:
                                        if isinstance(elt, ast.Constant) and isinstance(elt.value,str):
                                            verb=elt.value.upper(); break
                            if pathv: mi.routes.append((sid,verb,pathv,["200"]))
                mi.symbols.append(sym); mi.fn_to_sid[name]=sid; sid+=1

        # PX: forbid global state in svc (simple heuristic: any Assign at module top)
        if "svc" in mi.role_tags:
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    mi.px.append(("forbid global state in svc","concurrency"))

    langs=detect_langs(root)
    return ScanResult(modules=modules, langs=langs)

# ---------- pass B: resolve calls (unchanged behavior) ----------

def build_reexports_global(mods: Dict[str, ModuleInfo]) -> Dict[str,str]:
    m={}
    for mi in mods.values(): m.update(mi.reexports)
    return m

def build_indices_again(mods: Dict[str, ModuleInfo]):
    dotted_to_path: Dict[str,str]={}
    for rp,mi in mods.items(): dotted_to_path[mi.dotted]=rp
    return dotted_to_path

def resolve_target(full_dotted: str, dotted_to_path: Dict[str,str], mods: Dict[str, ModuleInfo]) -> Tuple[Optional[int], Optional[int], str]:
    rp = longest_prefix_module(full_dotted, dotted_to_path)
    if not rp: return None, None, "mod"
    mt = mods[rp]
    prefix_len = len(mt.dotted.split(".")) if mt.dotted else 0
    parts = full_dotted.split(".")
    rest = parts[prefix_len:]
    if len(rest)>=2:
        cand=f"{rest[0]}.{rest[1]}"
        if cand in mt.prop_to_sid: return mt.id, mt.prop_to_sid[cand], "prop"
        if cand in mt.fn_to_sid:   return mt.id, mt.fn_to_sid[cand], "fn"
    if len(rest)>=1:
        nm=rest[0]
        if nm in mt.prop_to_sid: return mt.id, mt.prop_to_sid[nm], "prop"
        if nm in mt.fn_to_sid:   return mt.id, mt.fn_to_sid[nm], "fn"
    return mt.id, 0, "mod"

def extract_calls(root: Path, scan: ScanResult) -> None:
    mods=scan.modules
    dotted_to_path = build_indices_again(mods)
    for rp, mi in mods.items():
        full=root/rp
        if full.suffix.lower()!=".py": continue
        try:
            src=full.read_text(encoding="utf-8", errors="replace")
            tree=ast.parse(src, filename=str(full))
        except Exception:
            continue
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                setattr(child,"parent",parent)
        local = dict(mi.fn_to_sid)
        def caller_sid(node: ast.AST) -> Optional[int]:
            up=node
            while True:
                up=getattr(up,"parent",None)
                if up is None: return None
                if isinstance(up,(ast.FunctionDef, ast.AsyncFunctionDef)):
                    # try class.method resolution
                    owner=up; cls=None; p=owner
                    while True:
                        p=getattr(p,"parent",None)
                        if p is None: break
                        if isinstance(p, ast.ClassDef): cls=p.name; break
                    return local.get(f"{cls}.{owner.name}") if cls else local.get(owner.name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call): continue
            src_sid = caller_sid(node)
            if not src_sid: continue
            tgt=None
            if isinstance(node.func, ast.Name):
                sid = local.get(node.func.id)
                if sid: tgt=(mi.id, sid, "fn")
            elif isinstance(node.func, ast.Attribute):
                dotted = dotted_from_ast(node.func)
                if dotted:
                    head = dotted.split(".")[0]
                    mapped = mi.import_names.get(head)
                    full_dotted = ".".join([mapped]+dotted.split(".")[1:]) if mapped else dotted
                    tmid, tsid, kind = resolve_target(full_dotted, dotted_to_path, mods)
                    if tmid is not None: tgt=(tmid, tsid, kind)
            if tgt:
                if tgt[2]=="prop":  # don't create call edges to properties
                    continue
                mi.calls.append((src_sid,(tgt[0],tgt[1])))

# ---------- AL + NM + render ----------

DEFAULT_ALIASES = [
    ("cfg","Configuration"),("svc","Service"),("repo","Repository"),("dto","DataTransferObject"),
    ("uc","UseCase"),("http","HTTP"),("db","Database"),("jwt","JWT"),
]

def check_prefix_free(pairs: List[Tuple[str,str]]) -> Tuple[List[Tuple[str,str]], List[Tuple[str,str]]]:
    ks=[k for k,_ in pairs]; px=[]
    for i,k1 in enumerate(ks):
        for j,k2 in enumerate(ks):
            if i==j: continue
            if k2.startswith(k1):
                px.append((f"AL prefix-free violated: '{k1}' is prefix of '{k2}'","aliases"))
    # dedupe:
    out=[]; seen=set()
    for item in px:
        if item not in seen: out.append(item); seen.add(item)
    return pairs, out

def render_card(proj: str, langs: List[str], std: str, mods: Dict[str, ModuleInfo]) -> str:
    lines=[]
    # ID
    lines.append(f"ID: proj|{proj} lang|{','.join(langs)} std|{std} ts|{today_stamp()}")

    # AL
    al_ok, al_px = check_prefix_free(DEFAULT_ALIASES)
    for k,v in al_ok: lines.append(f"AL: {k}=>{v}")

    # NM
    for scope, regex, ex in [
        ("module", r"^[a-z_]+$", "auth_service"),
        ("class",  r"^[A-Z][A-Za-z0-9]+$", "AuthService"),
        ("func",   r"^[a-z_][a-z0-9_]*$", "issue_token"),
        ("var",    r"^[a-z_][a-z0-9_]*$", "user_repo"),
    ]:
        lines.append(f"NM: {scope} | {regex} | {ex}")

    # MO/SY/SG/IN/MD
    mlist=sorted(mods.values(), key=lambda m: m.id)
    for m in mlist:
        tags="{"+",".join(sorted(m.role_tags))+"}"
        lines.append(f"MO: #{m.id} | {m.path} | {tags}")
    for m in mlist:
        for s in m.symbols:
            lines.append(f"SY: #{s.mid}.#{s.sid} | {s.kind} | {s.name}")
            if s.kind=="fn" and s.signature:
                sig = s.signature
                if s.raises:
                    sig = f"{sig} !raises[{','.join(s.raises)}]"
                lines.append(f"SG: #{s.mid}.#{s.sid} | {sig}")
            if s.invariants:
                lines.append(f"IN: {s.name.split('.')[-1]} ⇒ {s.invariants}")
            if s.modifiers:
                lines.append(f"MD: #{s.mid}.#{s.sid} | "+"{"+",".join(sorted(s.modifiers))+"}")

    # DT
    for m in mlist:
        for nm, fields in m.dts:
            field_s=",".join(f"{k}:{v}" for k,v in fields.items())
            lines.append(f"DT: {nm} | {{{field_s}}}")

    # TK
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

    # CN
    lines.append("CN: async fn end with _async")
    lines.append("CN: repos never import svc")

    # PX (module + AL prefix-free violations)
    for m in mlist:
        # dedupe PX for each module
        seen=set()
        for rule, reason in m.px:
            key=(rule,reason)
            if key in seen: continue
            lines.append(f"PX: {rule} | {reason}")
            seen.add(key)
    for rule, reason in al_px:
        lines.append(f"PX: {rule} | {reason}")

    # EX / RV
    lines.append("EX: var(repo) => user_repo")
    lines.append("EX: class(Service) => AuthService")
    lines.append("EX: func(token) => issue_token")
    lines.append("RV: Public fns documented; No bare except")

    return "\n".join(ascii_only(ln) for ln in lines) + "\n"

# ---------- TY (optional full list) ----------

def append_ty(lines: List[str], mods: Dict[str, ModuleInfo]) -> None:
    for m in sorted(mods.values(), key=lambda x: x.id):
        for s in m.symbols:
            if s.kind=="fn" and s.signature:
                sig = s.signature
                if s.raises:
                    sig = f"{sig} !raises[{','.join(s.raises)}]"
                lines.append(f"TY: fn | {s.name} | {sig}")

# ---------- Δ ----------

def diff_lines(old_text: str, new_text: str) -> str:
    old=[ln for ln in old_text.splitlines() if ln.strip()]
    new=[ln for ln in new_text.splitlines() if ln.strip()]
    old_set, new_set = set(old), set(new)
    add=[ln for ln in new if ln not in old_set]
    rem=[ln for ln in old if ln not in new_set]
    delta=[f"Δ: + {ln}" for ln in add] + [f"Δ: - {ln}" for ln in rem]
    return ("\n".join(delta)+"\n") if delta else ""

# ---------- CLI ----------

def main():
    ap=argparse.ArgumentParser(description="Generate CTX-CARD v2.1 (raises + PX lints).")
    ap.add_argument("root", nargs="?", default=".", help="Repo root")
    ap.add_argument("--proj", default=None, help="Project slug (default: folder name)")
    ap.add_argument("--std", default="pep8", help="Style/standard hint")
    ap.add_argument("--include", default=None, help="Glob include (e.g., '**/*.py')")
    ap.add_argument("--exclude", default=None, help="Glob exclude (e.g., '**/tests/**')")
    ap.add_argument("--out", default="CTXCARD.md", help="Root card output path")
    ap.add_argument("--emit-ty", action="store_true", help="Also emit TY: lines")
    ap.add_argument("--delta-from", default=None, help="Existing CTXCARD to compute Δ and append")
    ap.add_argument("--stdout", action="store_true", help="Print to stdout")
    args=ap.parse_args()

    root=Path(args.root).resolve()
    proj=args.proj or root.name

    scan=scan_repo(root, args.include, args.exclude)
    extract_calls(root, scan)

    text = render_card(proj, scan.langs, args.std, scan.modules)
    if args.emit_ty:
        extra=[]; append_ty(extra, scan.modules)
        if extra: text = text + "\n".join(extra) + "\n"

    if args.delta_from:
        old_path=Path(args.delta_from)
        old_text = old_path.read_text(encoding="utf-8", errors="replace") if old_path.exists() else ""
        text = text + diff_lines(old_text, text)

    if args.stdout:
        sys.stdout.write(text)
    else:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote {args.out}")

if __name__=="__main__":
    main()
```

## What changed (quick)

- **Raise scanning**: walks each function’s body (ignoring nested defs/classes) to collect exception types and appends `!raises[...]` to `SG:` and `TY:`. Reraises appear as `ReRaise`.
- **PX rules added**:

  - `PX: forbid bare except | error-handling`
  - `PX: forbid wildcard import | namespace`
  - `PX: forbid eval/exec | security`
  - `PX: forbid mutable default arguments | bug-risk`
  - `PX: forbid print in production | logging`
  - `PX: forbid global state in svc | concurrency` (kept)

If you want more PX checks (e.g., `from … import *` in `__init__` only, or `no relative import ..`), say so and I’ll tack them on without bloating tokens.
