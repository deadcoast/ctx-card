#!/usr/bin/env python3
# CTX-CARD generator (v1.3, Python-extended)
# Features:
# - Module + symbol index (classes, functions)
# - Function signatures (Python, from type hints)
# - Module-level import edges
# - Function-level call graph (best-effort local & qualified)
# - DTO detection: @dataclass and pydantic.BaseModel -> DT:
# - Error taxonomy: classes inheriting Exception -> ER:
# - IO contracts: FastAPI/Flask route decorators -> IO:
# - Invariants from docstrings: "Requires:" / "Ensures:" -> IN:
#
# No third-party deps.

from __future__ import annotations
import argparse
import ast
import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Any

# -----------------------------
# Utilities
# -----------------------------

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

def detect_langs(root: Path) -> List[str]:
    exts = {p.suffix.lower() for p in root.rglob("*") if p.is_file()}
    lang_map = {
        ".py": "py",".ts":"ts",".tsx":"tsx",".js":"js",".jsx":"jsx",".go":"go",
        ".rs":"rs",".java":"java",".kt":"kt",".swift":"swift",".c":"c",".h":"c-h",
        ".cpp":"cpp",".hpp":"cpp-h",".cs":"cs",
    }
    langs = sorted({lang_map[e] for e in exts if e in lang_map})
    return langs or ["unknown"]

def ann_to_str(ann: Optional[ast.AST]) -> str:
    if ann is None:
        return ""
    try:
        return ast.unparse(ann)  # py3.9+
    except Exception:
        return ""

# -----------------------------
# Data structures
# -----------------------------

@dataclass
class Symbol:
    mid: int
    sid: int
    kind: str           # "mod" | "cls" | "fn"
    name: str
    signature: Optional[str] = None
    bases: List[str] = field(default_factory=list)  # for classes
    deco: List[str] = field(default_factory=list)   # decorator names
    doc_invariants: Optional[str] = None            # compact Hoare-style

@dataclass
class ModuleInfo:
    id: int
    path: str
    role_tags: Set[str] = field(default_factory=set)
    symbols: List[Symbol] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)       # resolved module paths (best effort)
    import_names: Dict[str,str] = field(default_factory=dict)  # local alias -> dotted or path

    # Extended extraction caches
    routes: List[Tuple[int,str,str,List[str]]] = field(default_factory=list)
    # list of (sid, verb, path, codes_guess)

    dts: List[Tuple[str,Dict[str,str]]] = field(default_factory=list) # (Name, {field:type})
    errors: List[Tuple[str,str,str]] = field(default_factory=list)     # (Name, category, meaning)
    calls: List[Tuple[int,Tuple[int,int]]] = field(default_factory=list) # (caller_sid, (mid,sid))

# -----------------------------
# Heuristics
# -----------------------------

CODE_EXTS = {".py",".ts",".tsx",".js",".jsx",".go",".rs",".java",".kt",".swift",".c",".h",".cpp",".hpp",".cs"}

def is_code_file(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in CODE_EXTS and not is_probably_binary(p)

def default_role_tags(path: str) -> Set[str]:
    tags = set()
    low = path.lower()
    for k,t in [
        ("test","test"),("auth","auth"),("api","api"),
        ("repo","repo"),("repository","repo"),("service","svc"),("svc","svc")
    ]:
        if k in low: tags.add(t)
    return tags or {"mod"}

# -----------------------------
# Python parsing helpers
# -----------------------------

ROUTE_DECORATOR_PREFIXES = {
    # FastAPI
    "app.get": "GET", "app.post":"POST", "app.put":"PUT", "app.delete":"DELETE",
    "router.get":"GET","router.post":"POST","router.put":"PUT","router.delete":"DELETE",
    # Flask
    "app.route": None, "bp.route": None, "blueprint.route": None,
}

def dotted_name(expr: ast.AST) -> str:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        base = dotted_name(expr.value)
        return f"{base}.{expr.attr}" if base else expr.attr
    return ""

def collect_deco_names(func: ast.AST) -> List[str]:
    decos = []
    for d in getattr(func, "decorator_list", []):
        decos.append(dotted_name(d))
    return decos

def parse_route_from_decos(decos: List[str], node: ast.AST) -> Optional[Tuple[str,str]]:
    """Return (verb, path) if route-like decorator present."""
    # Handle FastAPI: app.get("/x") etc. and Flask: app.route("/x", methods=["GET"])
    call_nodes = getattr(node, "decorator_list", [])
    for d in call_nodes:
        if isinstance(d, ast.Call):
            name = dotted_name(d.func)
            # FastAPI simple verbs
            if name in ("app.get","app.post","app.put","app.delete","router.get","router.post","router.put","router.delete"):
                verb = name.split(".")[-1].upper()
                if d.args and isinstance(d.args[0], ast.Constant) and isinstance(d.args[0].value, str):
                    return verb, d.args[0].value
            # Flask route
            if name.endswith(".route"):
                route_path = None
                method_verb = None
                if d.args and isinstance(d.args[0], ast.Constant) and isinstance(d.args[0].value, str):
                    route_path = d.args[0].value
                for kw in d.keywords or []:
                    if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                        for elt in kw.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                method_verb = method_verb or elt.value.upper()
                if route_path:
                    return method_verb or "GET", route_path
    return None

def function_signature(node: ast.AST) -> str:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return ""
    args_list = []
    for a in node.args.args:
        t = ann_to_str(a.annotation)
        args_list.append(f"{a.arg}:{t}" if t else a.arg)
    if node.args.vararg:
        args_list.append(f"*{node.args.vararg.arg}")
    for a in node.args.kwonlyargs:
        t = ann_to_str(a.annotation)
        args_list.append(f"{a.arg}:{t}" if t else a.arg)
    if node.args.kwarg:
        args_list.append(f"**{node.args.kwarg.arg}")
    ret = ann_to_str(node.returns) or "Any"
    return f"({','.join(args_list)})->{ret}"

def docstring_invariants(node: ast.AST) -> Optional[str]:
    doc = ast.get_docstring(node) or ""
    if not doc: return None
    req = None; ens = None
    for line in doc.splitlines():
        ls = line.strip()
        if ls.lower().startswith("requires:"):
            req = ls.split(":",1)[1].strip()
        elif ls.lower().startswith("ensures:"):
            ens = ls.split(":",1)[1].strip()
    if req or ens:
        if req and ens:
            return f"requires({req}) ∧ ensures({ens})"
        return f"requires({req})" if req else f"ensures({ens})"
    return None

def class_is_exception(node: ast.ClassDef) -> bool:
    for b in node.bases:
        nm = ann_to_str(b) or dotted_name(b)
        if nm.endswith("Exception") or nm == "Exception":
            return True
    return False

def class_is_dataclass(node: ast.ClassDef) -> bool:
    names = [dotted_name(d.func) for d in node.decorator_list if isinstance(d, ast.Call)]
    names += [dotted_name(d) for d in node.decorator_list if not isinstance(d, ast.Call)]
    return any(n.endswith("dataclass") for n in names)

def class_is_pydantic(node: ast.ClassDef) -> bool:
    for b in node.bases:
        nm = ann_to_str(b) or dotted_name(b)
        if nm.endswith("BaseModel") or nm.endswith("pydantic.BaseModel"):
            return True
    return False

def class_fields_from_annotations(node: ast.ClassDef) -> Dict[str,str]:
    fields: Dict[str,str] = {}
    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            t = ann_to_str(stmt.annotation) or "Any"
            fields[stmt.target.id] = t
    return fields

# -----------------------------
# Scan + Extract
# -----------------------------

@dataclass
class ScanResult:
    modules: Dict[str, ModuleInfo]
    lang_set: List[str]

def normalize_import_token(token: str, file_path: Path, root: Path) -> str:
    if not token:
        return ""
    if token.startswith("."):
        # relative import
        up = len(token) - len(token.lstrip("."))
        base_dir = file_path.parent
        for _ in range(up):
            base_dir = base_dir.parent
        remainder = token.lstrip(".").replace(".", "/")
        cand = base_dir / (remainder + ".py") if remainder else base_dir
        return relpath(cand, root)
    return token  # keep dotted; we map later

def is_python(p: Path) -> bool:
    return p.suffix.lower() == ".py"

def scan_repo(root: Path, include_glob: Optional[str], exclude_glob: Optional[str]) -> ScanResult:
    files = []
    for p in root.rglob("**/*" if include_glob is None else include_glob):
        if not p.is_file(): continue
        if exclude_glob and p.match(exclude_glob): continue
        if is_code_file(p):
            files.append(p)
    files = sorted(set(files), key=lambda x: relpath(x, root))

    modules: Dict[str, ModuleInfo] = {}
    mid = 1
    for path in files:
        rp = relpath(path, root)
        mi = ModuleInfo(id=mid, path=rp, role_tags=default_role_tags(rp))
        mi.symbols.append(Symbol(mid=mid, sid=0, kind="mod", name=Path(rp).stem))
        modules[rp] = mi
        mid += 1

    # Pre-build a reverse index by stem for import mapping
    by_stem: Dict[str,List[str]] = {}
    for mp in modules.keys():
        stem = Path(mp).stem
        by_stem.setdefault(stem, []).append(mp)

    # Parse Python modules
    for rp, mi in modules.items():
        full = (root / rp)
        if not is_python(full):
            continue
        try:
            src = full.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(src, filename=str(full))
        except Exception:
            continue

        # import aliases
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    mi.import_names[n.asname or n.name] = n.name
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                dots = "." * (node.level or 0)
                base_full = dots + base if base else dots
                for n in node.names:
                    alias = n.asname or n.name
                    mi.import_names[alias] = (base_full + "." + n.name) if base_full else n.name

        # symbols (top-level)
        sid_counter = 1
        local_fn_names: Dict[str,int] = {}

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                sym = Symbol(mid=mi.id, sid=sid_counter, kind="cls", name=node.name)
                sym.bases = [ann_to_str(b) or dotted_name(b) for b in node.bases]
                inv = docstring_invariants(node)
                if inv: sym.doc_invariants = inv
                mi.symbols.append(sym)
                # DTOs
                if class_is_dataclass(node) or class_is_pydantic(node):
                    fields = class_fields_from_annotations(node)
                    mi.dts.append((node.name, fields))
                # Errors
                if class_is_exception(node):
                    mi.errors.append((node.name, "domain", "custom exception"))
                sid_counter += 1

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sig = function_signature(node)
                decos = collect_deco_names(node)
                sym = Symbol(mid=mi.id, sid=sid_counter, kind="fn", name=node.name, signature=sig, deco=decos)
                inv = docstring_invariants(node)
                if inv: sym.doc_invariants = inv
                mi.symbols.append(sym)
                local_fn_names[node.name] = sid_counter
                # IO: route decorators
                rt = parse_route_from_decos(decos, node)
                if rt:
                    verb, path_s = rt
                    codes = ["200"]  # cheap default
                    mi.routes.append((sid_counter, verb, path_s, codes))
                sid_counter += 1

        # imports (module-level)
        imports_raw: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports_raw.add(n.name)
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                dots = "." * (node.level or 0)
                imports_raw.add(dots + base if base or dots else "")

        resolved: Set[str] = set()
        for tok in imports_raw:
            norm = normalize_import_token(tok, full, root)
            if norm.endswith(".py"):
                if norm in modules: resolved.add(norm)
                else:
                    n2 = norm[:-3]
                    if n2 in modules: resolved.add(n2)
                continue
            # dotted -> map by last component
            last = tok.split(".")[-1] if tok else ""
            if last and last in by_stem:
                cands = by_stem[last]
                # prefer same directory
                same_dir = [c for c in cands if Path(c).parent == Path(rp).parent]
                resolved.add((same_dir or cands)[0])
        mi.imports = resolved

        # Calls: best-effort
        # - local direct calls: Name() resolve to local functions
        # - qualified calls: alias.func() where alias maps to imported module -> map to module anchor (#mid.#0)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                callee_mid_sid: Optional[Tuple[int,int]] = None
                # unqualified
                if isinstance(node.func, ast.Name):
                    fn = node.func.id
                    if fn in local_fn_names:
                        callee_mid_sid = (mi.id, local_fn_names[fn])
                # qualified
                elif isinstance(node.func, ast.Attribute):
                    base = node.func.value
                    if isinstance(base, ast.Name):
                        alias = base.id
                        dotted = mi.import_names.get(alias)
                        if dotted:
                            # map last component to module
                            last = dotted.split(".")[-1]
                            if last in by_stem:
                                mod_path = by_stem[last][0]
                                # We don't know symbol id in that module -> link to module anchor (#mid.#0)
                                callee_mid_sid = (modules[mod_path].id, 0)
                # record if resolved
                if callee_mid_sid:
                    # find current function sid (caller)
                    caller_sid = None
                    parent = node
                    while parent:
                        parent = getattr(parent, "parent", None)
                        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            caller_sid = local_fn_names.get(parent.name)
                            break
                    if caller_sid:
                        mi.calls.append((caller_sid, callee_mid_sid))

        # Patch parents to walk upwards (cheap parent links)
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                setattr(child, "parent", parent)

    langs = detect_langs(root)
    return ScanResult(modules=modules, lang_set=langs)

# -----------------------------
# Render CTX-CARD
# -----------------------------

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

def render_ctxcard(proj: str, langs: List[str], std: str, scan: ScanResult) -> str:
    lines: List[str] = []
    lines.append(f"ID: proj|{proj} lang|{','.join(langs)} std|{std} ts|{today_stamp()}")

    for al in HEADER_ALIASES:
        lines.append(f"AL: {al}")
    for scope, regex, example in NAMING_GRAMMAR_DEFAULT:
        lines.append(f"NM: {scope} | {regex} | {example}")

    # Modules
    mlist = sorted(scan.modules.values(), key=lambda m: m.id)
    for m in mlist:
        tags = "{" + ",".join(sorted(m.role_tags)) + "}"
        lines.append(f"MO: #{m.id} | {m.path} | {tags}")

    # Symbols + signatures + invariants
    for m in mlist:
        for s in m.symbols:
            lines.append(f"SY: #{m.id}.#{s.sid} | {s.kind} | {s.name}")
            if s.kind == "fn" and s.signature:
                lines.append(f"SG: #{m.id}.#{s.sid} | {s.signature}")
            if s.doc_invariants:
                lines.append(f"IN: {s.name} ⇒ {s.doc_invariants}")

    # DTOs
    for m in mlist:
        for name, fields in m.dts:
            field_s = ",".join(f"{k}:{v}" for k,v in fields.items())
            lines.append(f"DT: {name} | {{{field_s}}}")

    # Errors
    for m in mlist:
        for (name, category, meaning) in m.errors:
            lines.append(f"ER: {name} | {category} | {meaning}")

    # Module import edges
    for m in mlist:
        for dep_path in sorted(m.imports):
            dep = scan.modules.get(dep_path)
            if dep:
                lines.append(f"ED: #{m.id}.#0 -> #{dep.id}.#0 | imports")

    # Function call graph
    for m in mlist:
        for caller_sid, (t_mid, t_sid) in m.calls:
            lines.append(f"ED: #{m.id}.#{caller_sid} -> #{t_mid}.#{t_sid} | calls")

    # IO Contracts
    for m in mlist:
        for (sid, verb, path_s, codes) in m.routes:
            codes_s = ",".join(codes)
            # Try to infer in/out types from signature:
            fn = next((s for s in m.symbols if s.sid == sid), None)
            sig = fn.signature if fn else "(…)->Any"
            # crude split
            in_sig = sig.split(")->")[0].lstrip("(") if ")->" in sig else ""
            out_sig = sig.split(")->")[-1] if ")->" in sig else "Any"
            lines.append(f"IO: {verb} {path_s} | {in_sig} | {out_sig} | {codes_s}")

    # Minimal policy
    lines.append("CN: repos never import svc")
    lines.append("CN: async functions end with _async")
    lines.append("RV: public functions have signatures & docstrings")

    return "\n".join(lines) + "\n"

# -----------------------------
# Delta computation
# -----------------------------

def load_existing_ctxcard(path: Path) -> List[str]:
    if not path.exists():
        return []
    return [ln.rstrip("\n") for ln in path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]

def diff_lines(old: List[str], new: List[str]) -> List[str]:
    old_set, new_set = set(old), set(new)
    added = [ln for ln in new if ln not in old_set]
    removed = [ln for ln in old if ln not in new_set]
    delta = []
    for ln in added: delta.append(f"Δ: + {ln}")
    for ln in removed: delta.append(f"Δ: - {ln}")
    return delta

# -----------------------------
# CLI
# -----------------------------

def main():
    ap = argparse.ArgumentParser(description="Generate CTX-CARD (Python enhanced).")
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

    scan = scan_repo(root, args.include, args.exclude)
    card = render_ctxcard(proj, scan.lang_set, args.std, scan)

    if args.delta_from:
        old_lines = load_existing_ctxcard(Path(args.delta_from))
        new_lines = [ln for ln in card.splitlines() if ln.strip()]
        delta = diff_lines(old_lines, new_lines)
        if delta:
            card = card + "\n".join(delta) + "\n"

    if args.stdout:
        print(card, end="")
        return

    Path(args.out).write_text(card, encoding="utf-8")
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()