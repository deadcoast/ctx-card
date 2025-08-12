#!/usr/bin/env python3
# CTX-CARD generator (v1.6 — Python: call-semantics tags + properties + descriptors)
# Adds:
# - MD: lines for symbol modifiers {staticmethod,classmethod,property,descriptor}
# - Detect @property / cached_property (functools or direct), index as kind "prop"
# - Tag classes as {descriptor} if they define __get__/__set__/__set_name__
# - Skip creating "calls" edges to properties
#
# Still includes:
# - Modules, symbols (classes, functions, methods, properties), signatures,
#   DTOs (dataclass/pydantic), Errors, IO (FastAPI/Flask), invariants,
#   module import edges, cross-module function/method call graph with re-exports.
#
# Zero third-party deps.

from __future__ import annotations
import argparse, ast
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

# ---------- utils ----------

def today_stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d")

def relpath(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root).as_posix())
    except Exception:
        return str(p.as_posix())

def is_probably_binary(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return b"\0" in f.read(2048)
    except Exception:
        return True

def ann_to_str(ann: Optional[ast.AST]) -> str:
    if ann is None: return ""
    try: return ast.unparse(ann)  # py3.9+
    except Exception: return ""

def file_to_dotted(rp: str) -> str:
    p = Path(rp)
    if p.name == "__init__.py":
        return str(p.parent).replace("/", ".")
    return rp[:-3].replace("/", ".") if rp.endswith(".py") else rp.replace("/", ".")

# ---------- datatypes ----------

@dataclass
class Symbol:
    mid: int
    sid: int
    kind: str            # "mod" | "cls" | "fn" | "prop"
    name: str            # fn: "func" or "Class.method"; prop: "Class.attr"
    signature: Optional[str] = None
    bases: List[str] = field(default_factory=list)
    deco: List[str] = field(default_factory=list)
    doc_invariants: Optional[str] = None
    modifiers: Set[str] = field(default_factory=set)  # {"staticmethod","classmethod","property","descriptor"}

@dataclass
class ModuleInfo:
    id: int
    path: str
    role_tags: Set[str] = field(default_factory=set)
    symbols: List[Symbol] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)
    import_names: Dict[str, str] = field(default_factory=dict)
    routes: List[Tuple[int,str,str,List[str]]] = field(default_factory=list)  # (sid, verb, path, codes)
    dts: List[Tuple[str,Dict[str,str]]] = field(default_factory=list)         # (DTOName, fields)
    errors: List[Tuple[str,str,str]] = field(default_factory=list)            # (Name, category, meaning)
    calls: List[Tuple[int,Tuple[int,int]]] = field(default_factory=list)      # (caller_sid, (mid,sid))

    dotted_name: str = ""
    fn_name_to_sid: Dict[str,int] = field(default_factory=dict)      # "func" and "Class.method" -> sid
    prop_name_to_sid: Dict[str,int] = field(default_factory=dict)    # "Class.attr" -> sid
    top_level_defs: Set[str] = field(default_factory=set)
    reexports: Dict[str, str] = field(default_factory=dict)          # pkg.attr -> dotted origin

# ---------- heuristics ----------

CODE_EXTS = {".py",".ts",".tsx",".js",".jsx",".go",".rs",".java",".kt",".swift",".c",".h",".cpp",".hpp",".cs"}

def is_code_file(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in CODE_EXTS and not is_probably_binary(p)

def default_role_tags(path: str) -> Set[str]:
    low = path.lower()
    tags = set()
    for k,t in [
        ("test","test"),("auth","auth"),("api","api"),
        ("repo","repo"),("repository","repo"),("service","svc"),("svc","svc")
    ]:
        if k in low: tags.add(t)
    return tags or {"mod"}

# ---------- py helpers ----------

def dotted_name_from_ast(expr: ast.AST) -> str:
    if isinstance(expr, ast.Name): return expr.id
    if isinstance(expr, ast.Attribute):
        base = dotted_name_from_ast(expr.value)
        return f"{base}.{expr.attr}" if base else expr.attr
    return ""

def function_signature(node: ast.AST) -> str:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)): return ""
    args = []
    for a in node.args.args:
        t = ann_to_str(a.annotation)
        args.append(f"{a.arg}:{t}" if t else a.arg)
    if node.args.vararg: args.append(f"*{node.args.vararg.arg}")
    for a in node.args.kwonlyargs:
        t = ann_to_str(a.annotation)
        args.append(f"{a.arg}:{t}" if t else a.arg)
    if node.args.kwarg: args.append(f"**{node.args.kwarg.arg}")
    ret = ann_to_str(node.returns) or "Any"
    return f"({','.join(args)})->{ret}"

def docstring_invariants(node: ast.AST) -> Optional[str]:
    doc = ast.get_docstring(node) or ""
    if not doc: return None
    req = ens = None
    for line in doc.splitlines():
        ls = line.strip()
        if ls.lower().startswith("requires:"): req = ls.split(":",1)[1].strip()
        elif ls.lower().startswith("ensures:"): ens = ls.split(":",1)[1].strip()
    if req or ens:
        if req and ens: return f"requires({req}) ∧ ensures({ens})"
        return f"requires({req})" if req else f"ensures({ens})"
    return None

def class_is_exception(node: ast.ClassDef) -> bool:
    for b in node.bases:
        nm = ann_to_str(b) or dotted_name_from_ast(b)
        if nm.endswith("Exception") or nm == "Exception": return True
    return False

def class_is_dataclass(node: ast.ClassDef) -> bool:
    decos = []
    for d in node.decorator_list:
        decos.append(dotted_name_from_ast(d.func) if isinstance(d, ast.Call) else dotted_name_from_ast(d))
    return any(n.endswith("dataclass") for n in decos)

def class_is_pydantic(node: ast.ClassDef) -> bool:
    for b in node.bases:
        nm = ann_to_str(b) or dotted_name_from_ast(b)
        if nm.endswith("BaseModel") or nm.endswith("pydantic.BaseModel"): return True
    return False

def class_fields_from_annotations(node: ast.ClassDef) -> Dict[str,str]:
    fields: Dict[str,str] = {}
    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            t = ann_to_str(stmt.annotation) or "Any"
            fields[stmt.target.id] = t
    return fields

def method_modifiers(decos: List[str]) -> Set[str]:
    mods = set()
    for nm in decos:
        tail = nm.split(".")[-1]
        if tail == "staticmethod": mods.add("staticmethod")
        elif tail == "classmethod": mods.add("classmethod")
        elif tail == "property": mods.add("property")
        elif tail == "cached_property": mods.add("property")
    return mods

def class_has_descriptor_dunders(node: ast.ClassDef) -> bool:
    names = {stmt.name for stmt in node.body if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return bool({"__get__","__set__","__set_name__"} & names)

# ---------- indices ----------

@dataclass
class ScanResult:
    modules: Dict[str, ModuleInfo]
    lang_set: List[str]

def detect_langs(root: Path) -> List[str]:
    exts = {p.suffix.lower() for p in root.rglob("*") if p.is_file()}
    lang_map = {".py":"py",".ts":"ts",".tsx":"tsx",".js":"js",".jsx":"jsx",".go":"go",".rs":"rs",
                ".java":"java",".kt":"kt",".swift":"swift",".c":"c",".h":"c-h",".cpp":"cpp",
                ".hpp":"cpp-h",".cs":"cs"}
    langs = sorted({lang_map[e] for e in exts if e in lang_map})
    return langs or ["unknown"]

def normalize_import_token(token: str, file_path: Path, root: Path) -> str:
    if not token: return ""
    if token.startswith("."):
        up = len(token) - len(token.lstrip("."))
        base_dir = file_path.parent
        for _ in range(up): base_dir = base_dir.parent
        remainder = token.lstrip(".").replace(".","/")
        cand = base_dir / (remainder + ".py") if remainder else base_dir
        return relpath(cand, root)
    return token

def build_repo_indices(modules: Dict[str, ModuleInfo]) -> Tuple[Dict[str,str], Dict[str,List[str]]]:
    dotted_to_path: Dict[str,str] = {}
    stem_to_paths: Dict[str,List[str]] = {}
    for rp in modules.keys():
        d = file_to_dotted(rp)
        if d: dotted_to_path[d] = rp
        stem_to_paths.setdefault(Path(rp).stem, []).append(rp)
    return dotted_to_path, stem_to_paths

def longest_prefix_module(dotted: str, dotted_to_path: Dict[str,str]) -> Optional[str]:
    parts = dotted.split(".")
    for i in range(len(parts), 0, -1):
        cand = ".".join(parts[:i])
        rp = dotted_to_path.get(cand)
        if rp: return rp
    return None

# ---------- scan pass A ----------

def scan_repo_pass_a(root: Path, include_glob: Optional[str], exclude_glob: Optional[str]) -> ScanResult:
    files: List[Path] = []
    it = root.rglob("**/*" if include_glob is None else include_glob)
    for p in it:
        if not p.is_file(): continue
        if exclude_glob and p.match(exclude_glob): continue
        if is_code_file(p): files.append(p)
    files = sorted(set(files), key=lambda x: relpath(x, root))

    modules: Dict[str, ModuleInfo] = {}
    mid = 1
    for path in files:
        rp = relpath(path, root)
        mi = ModuleInfo(id=mid, path=rp, role_tags=default_role_tags(rp))
        mi.symbols.append(Symbol(mid=mid, sid=0, kind="mod", name=Path(rp).stem))
        mi.dotted_name = file_to_dotted(rp)
        modules[rp] = mi
        mid += 1

    dotted_to_path, stem_to_paths = build_repo_indices(modules)

    for rp, mi in modules.items():
        full = root / rp
        if full.suffix.lower() != ".py": continue
        try:
            src = full.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(src, filename=str(full))
        except Exception:
            continue

        # imports + track imported symbols for re-exports
        imported_symbols: Dict[str,str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    mi.import_names[n.asname or n.name] = n.name
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                dots = "." * (node.level or 0)
                base_full = (dots + base) if base or dots else ""
                for n in node.names:
                    alias = n.asname or n.name
                    dotted = (base_full + "." + n.name) if base_full else n.name
                    mi.import_names[alias] = dotted
                    imported_symbols[alias] = dotted

        # symbols (classes, methods, properties, functions)
        sid = 1
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                cls = node.name
                sym_cls = Symbol(mid=mi.id, sid=sid, kind="cls", name=cls)
                sym_cls.bases = [ann_to_str(b) or dotted_name_from_ast(b) for b in node.bases]
                inv = docstring_invariants(node)
                if inv: sym_cls.doc_invariants = inv
                if class_has_descriptor_dunders(node): sym_cls.modifiers.add("descriptor")
                mi.symbols.append(sym_cls)
                mi.top_level_defs.add(cls)
                sid += 1

                # class contents
                for stmt in node.body:
                    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        decos = [dotted_name_from_ast(d if not isinstance(d, ast.Call) else d.func)
                                 for d in stmt.decorator_list]
                        mods = method_modifiers(decos)
                        name_fn = f"{cls}.{stmt.name}"
                        if "property" in mods and len(stmt.args.args) >= 1:
                            # Index as property (no call signature)
                            sp = Symbol(mid=mi.id, sid=sid, kind="prop", name=f"{cls}.{stmt.name}",
                                        deco=decos, modifiers={"property"})
                            invm = docstring_invariants(stmt)
                            if invm: sp.doc_invariants = invm
                            mi.symbols.append(sp)
                            mi.prop_name_to_sid[sp.name] = sid
                            sid += 1
                            continue
                        sig = function_signature(stmt)
                        sm = Symbol(mid=mi.id, sid=sid, kind="fn", name=name_fn,
                                    signature=sig, deco=decos, modifiers=mods)
                        invm = docstring_invariants(stmt)
                        if invm: sm.doc_invariants = invm
                        mi.symbols.append(sm)
                        mi.fn_name_to_sid[name_fn] = sid
                        sid += 1

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                decos = [dotted_name_from_ast(d if not isinstance(d, ast.Call) else d.func)
                         for d in node.decorator_list]
                mods = method_modifiers(decos)  # rarely relevant at module level; harmless
                sig = function_signature(node)
                sym = Symbol(mid=mi.id, sid=sid, kind="fn", name=name,
                             signature=sig, deco=decos, modifiers=mods)
                inv = docstring_invariants(node)
                if inv: sym.doc_invariants = inv
                mi.symbols.append(sym)
                mi.fn_name_to_sid[name] = sid
                mi.top_level_defs.add(name)
                # routes
                for d in node.decorator_list:
                    if isinstance(d, ast.Call):
                        nm = dotted_name_from_ast(d.func)
                        if nm in ("app.get","app.post","app.put","app.delete","router.get","router.post","router.put","router.delete"):
                            verb = nm.split(".")[-1].upper()
                            if d.args and isinstance(d.args[0], ast.Constant) and isinstance(d.args[0].value, str):
                                mi.routes.append((sid, verb, d.args[0].value, ["200"]))
                        if nm.endswith(".route"):
                            route_path = None; verb = "GET"
                            if d.args and isinstance(d.args[0], ast.Constant) and isinstance(d.args[0].value, str):
                                route_path = d.args[0].value
                            for kw in d.keywords or []:
                                if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                                    for elt in kw.value.elts:
                                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                            verb = elt.value.upper(); break
                            if route_path: mi.routes.append((sid, verb, route_path, ["200"]))
                sid += 1

        # DTOs & Errors
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                if class_is_dataclass(node) or class_is_pydantic(node):
                    mi.dts.append((node.name, class_fields_from_annotations(node)))
                if class_is_exception(node):
                    mi.errors.append((node.name, "domain", "custom exception"))

        # module-level imports → edges (resolved later)
        imports_raw: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names: imports_raw.add(n.name)
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                dots = "." * (node.level or 0)
                imports_raw.add(dots + base if base or dots else "")
        resolved: Set[str] = set()
        for tok in imports_raw:
            norm = normalize_import_token(tok, full, root)
            if norm.endswith(".py"):
                cand = norm if norm in modules else norm[:-3]
                if cand in modules: resolved.add(cand)
                continue
            # exact dotted module
            if tok in dict(build_repo_indices(modules))[0]:
                resolved.add(dict(build_repo_indices(modules))[0][tok]); continue
            # suffix fallback
            last = tok.split(".")[-1] if tok else ""
            for rp2 in stem_to_paths.get(last, []):
                resolved.add(rp2)
        mi.imports = resolved

        # re-exports
        if Path(rp).name == "__init__.py":
            pkg_dot = mi.dotted_name
            for local, origin in imported_symbols.items():
                mi.reexports[f"{pkg_dot}.{local}"] = origin
        export_names: List[str] = []
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    export_names.append(elt.value)
        if export_names:
            pkg_dot = mi.dotted_name
            for nm in export_names:
                origin = imported_symbols.get(nm)
                if not origin and nm in mi.top_level_defs:
                    origin = f"{pkg_dot}.{nm}"
                if origin:
                    mi.reexports[f"{pkg_dot}.{nm}"] = origin

    langs = detect_langs(root)
    return ScanResult(modules=modules, lang_set=langs)

# ---------- pass B: calls with methods + re-exports ----------

def build_global_reexports(mods: Dict[str, ModuleInfo]) -> Dict[str,str]:
    m: Dict[str,str] = {}
    for mi in mods.values():
        m.update(mi.reexports)
    return m

def resolve_qualified(full_dotted: str, dotted_to_path: Dict[str,str], modules: Dict[str, ModuleInfo], reexp: Dict[str,str]) -> Tuple[Optional[int], Optional[int]]:
    def try_direct(dotted: str) -> Tuple[Optional[int], Optional[int]]:
        rp_target = longest_prefix_module(dotted, dotted_to_path)
        if not rp_target: return None, None
        mt = modules[rp_target]
        mod_prefix_len = len(file_to_dotted(rp_target).split("."))
        parts = dotted.split(".")
        rest = parts[mod_prefix_len:]
        # try Class.method
        if len(rest) >= 2:
            cand = f"{rest[0]}.{rest[1]}"
            sid = mt.fn_name_to_sid.get(cand) or mt.prop_name_to_sid.get(cand)
            if sid: return mt.id, sid
        # then plain function
        if len(rest) >= 1:
            sid = mt.fn_name_to_sid.get(rest[0]) or mt.prop_name_to_sid.get(rest[0])
            if sid: return mt.id, sid
        return mt.id, 0
    mid, sid = try_direct(full_dotted)
    if mid is not None: return mid, sid
    origin = reexp.get(full_dotted)
    if origin:
        return try_direct(origin)
    return None, None

def extract_calls_pass_b(root: Path, scan: ScanResult) -> None:
    modules = scan.modules
    dotted_to_path, _ = build_repo_indices(modules)
    reexp = build_global_reexports(modules)

    for rp, mi in modules.items():
        full = root / rp
        if full.suffix.lower() != ".py": continue
        try:
            src = full.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(src, filename=str(full))
        except Exception:
            continue

        # parent links
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                setattr(child, "parent", parent)

        local_lookup = dict(mi.fn_name_to_sid)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call): continue
            # find caller sid
            caller_sid = None
            up = node
            while True:
                up = getattr(up, "parent", None)
                if up is None: break
                if isinstance(up, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    cls_owner = None; p2 = up
                    while True:
                        p2 = getattr(p2, "parent", None)
                        if p2 is None: break
                        if isinstance(p2, ast.ClassDef): cls_owner = p2.name; break
                    caller_sid = local_lookup.get(f"{cls_owner}.{up.name}") if cls_owner else local_lookup.get(up.name)
                    break
            if not caller_sid: continue

            target: Optional[Tuple[int,int]] = None

            if isinstance(node.func, ast.Name):
                fn = node.func.id
                sid = local_lookup.get(fn)
                if sid:
                    target = (mi.id, sid)

            elif isinstance(node.func, ast.Attribute):
                dotted = dotted_name_from_ast(node.func)
                if dotted:
                    head = dotted.split(".")[0]
                    mapped_head = mi.import_names.get(head)
                    full_dotted = ".".join([mapped_head] + dotted.split(".")[1:]) if mapped_head else dotted
                    t_mid, t_sid = resolve_qualified(full_dotted, dotted_to_path, modules, reexp)
                    if t_mid is not None:
                        target = (t_mid, t_sid)

            if target:
                # suppress edges to properties
                t_mid, t_sid = target
                if t_sid != 0:
                    mt = next((m for m in modules.values() if m.id == t_mid), None)
                    if mt:
                        sym = next((s for s in mt.symbols if s.sid == t_sid), None)
                        if sym and sym.kind == "prop":
                            continue
                mi.calls.append((caller_sid, target))

# ---------- render ----------

HEADER_ALIASES = [
    "cfg=>Configuration","svc=>Service","repo=>Repository","dto=>DataTransferObject",
    "uc=>UseCase","http=>HTTP","db=>Database","jwt=>JWT",
]

NAMING_GRAMMAR_DEFAULT = [
    ("module", r"^[a-z_]+$", "auth_service"),
    ("class",  r"^[A-Z][A-Za-z0-9]+$", "AuthService"),
    ("func",   r"^[a-z_]+$", "issue_token"),
    ("var",    r"^[a-z_]+$", "user_repo"),
]

@dataclass
class RenderResult:
    text: str

def render_ctxcard(proj: str, langs: List[str], std: str, scan: ScanResult) -> RenderResult:
    lines: List[str] = []
    lines.append(f"ID: proj|{proj} lang|{','.join(langs)} std|{std} ts|{today_stamp()}")

    for al in HEADER_ALIASES:
        lines.append(f"AL: {al}")
    for scope, regex, example in NAMING_GRAMMAR_DEFAULT:
        lines.append(f"NM: {scope} | {regex} | {example}")

    mlist = sorted(scan.modules.values(), key=lambda m: m.id)

    # MO
    for m in mlist:
        tags = "{" + ",".join(sorted(m.role_tags)) + "}"
        lines.append(f"MO: #{m.id} | {m.path} | {tags}")

    # SY / SG / IN / MD
    for m in mlist:
        for s in m.symbols:
            lines.append(f"SY: #{m.id}.#{s.sid} | {s.kind} | {s.name}")
            if s.kind == "fn" and s.signature:
                lines.append(f"SG: #{m.id}.#{s.sid} | {s.signature}")
            if s.doc_invariants:
                lines.append(f"IN: {s.name} ⇒ {s.doc_invariants}")
            if s.modifiers:
                lines.append(f"MD: #{s.mid}.#{s.sid} | "+"{"+",".join(sorted(s.modifiers))+"}")

    # DT
    for m in mlist:
        for name, fields in m.dts:
            field_s = ",".join(f"{k}:{v}" for k,v in fields.items())
            lines.append(f"DT: {name} | {{{field_s}}}")

    # ER
    for m in mlist:
        for (name, category, meaning) in m.errors:
            lines.append(f"ER: {name} | {category} | {meaning}")

    # ED imports
    for m in mlist:
        for dep_path in sorted(m.imports):
            dep = scan.modules.get(dep_path)
            if dep:
                lines.append(f"ED: #{m.id}.#0 -> #{dep.id}.#0 | imports")

    # ED calls
    for m in mlist:
        for caller_sid, (t_mid, t_sid) in m.calls:
            lines.append(f"ED: #{m.id}.#{caller_sid} -> #{t_mid}.#{t_sid} | calls")

    # IO
    for m in mlist:
        for (sid, verb, path_s, codes) in m.routes:
            codes_s = ",".join(codes)
            fn = next((s for s in m.symbols if s.sid == sid), None)
            sig = fn.signature if fn else "(…)->Any"
            in_sig = sig.split(")->")[0].lstrip("(") if ")->" in sig else ""
            out_sig = sig.split(")->")[-1] if ")->" in sig else "Any"
            lines.append(f"IO: {verb} {path_s} | {in_sig} | {out_sig} | {codes_s}")

    lines.append("CN: repos never import svc")
    lines.append("CN: async functions end with _async")
    lines.append("RV: public functions have signatures & docstrings")

    return RenderResult(text="\n".join(lines) + "\n")

# ---------- delta ----------

def load_existing_ctxcard(path: Path) -> List[str]:
    if not path.exists(): return []
    return [ln.rstrip("\n") for ln in path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]

def diff_lines(old: List[str], new: List[str]) -> List[str]:
    old_set, new_set = set(old), set(new)
    added = [ln for ln in new if ln not in old_set]
    removed = [ln for ln in old if ln not in new_set]
    return [f"Δ: + {ln}" for ln in added] + [f"Δ: - {ln}" for ln in removed]

# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(description="Generate CTX-CARD (Python: call semantics + properties + descriptors).")
    ap.add_argument("root", nargs="?", default=".", help="Repo root")
    ap.add_argument("--proj", default=None, help="Project slug (default: folder name)")
    ap.add_argument("--std", default="pep8", help="Style/standard hint")
    ap.add_argument("--include", default=None, help="Glob include (e.g., '**/*.py')")
    ap.add_argument("--exclude", default=None, help="Glob exclude (e.g., '**/tests/**')")
    ap.add_argument("--out", default="CTXCARD.md", help="Output file")
    ap.add_argument("--delta-from", default=None, help="Existing CTXCARD to compute Δ")
    ap.add_argument("--stdout", action="store_true", help="Print to stdout")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    proj = args.proj or root.name

    # Pass A
    scan = scan_repo_pass_a(root, args.include, args.exclude)
    # Pass B
    extract_calls_pass_b(root, scan)
    # Render
    rendered = render_ctxcard(proj, scan.lang_set, args.std, scan).text

    if args.delta_from:
        old_lines = load_existing_ctxcard(Path(args.delta_from))
        new_lines = [ln for ln in rendered.splitlines() if ln.strip()]
        delta = diff_lines(old_lines, new_lines)
        if delta: rendered = rendered + "\n".join(delta) + "\n"

    if args.stdout:
        print(rendered, end="")
        return

    Path(args.out).write_text(rendered, encoding="utf-8")
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()