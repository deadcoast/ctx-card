#!/usr/bin/env python3
# CTX-CARD generator (v1)
# - Scans repo, builds compact CTX-CARD with ID/AL/NM/MO/SY/SG/ED/CN/RV.
# - Python: AST parse to extract classes, functions, signatures, imports.
# - Delta mode: emit only changed/added/removed lines vs existing CTXCARD.md.

from __future__ import annotations
import argparse
import ast
import hashlib
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

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

def sha_short(s: str, n: int = 8) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:n]

def is_probably_binary(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(1024)
        return b"\0" in chunk
    except Exception:
        return True

def detect_langs(root: Path) -> List[str]:
    exts = {p.suffix.lower() for p in root.rglob("*") if p.is_file()}
    lang_map = {
        ".py": "py",
        ".ts": "ts",
        ".tsx": "tsx",
        ".js": "js",
        ".jsx": "jsx",
        ".go": "go",
        ".rs": "rs",
        ".java": "java",
        ".kt": "kt",
        ".swift": "swift",
        ".c": "c",
        ".h": "c-h",
        ".cpp": "cpp",
        ".hpp": "cpp-h",
        ".cs": "cs",
    }
    langs = sorted({lang_map[e] for e in exts if e in lang_map})
    return langs or ["unknown"]

# -----------------------------
# Data structures
# -----------------------------

@dataclass
class Symbol:
    mid: int                  # module id
    sid: int                  # symbol id within module
    kind: str                 # "cls" | "fn" | "mod"
    name: str
    signature: Optional[str] = None  # for functions
    # You can extend with visibility, decorators, etc.

@dataclass
class ModuleInfo:
    id: int
    path: str                 # posix relative path
    role_tags: Set[str] = field(default_factory=set)
    symbols: List[Symbol] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)  # module paths (normalized)

# -----------------------------
# Python extractor (AST)
# -----------------------------

def py_extract(path: Path) -> Tuple[List[Tuple[str, str]], Set[str]]:
    """
    Returns: (symbols, imports)
    symbols: list of (kind, name)
    imports: set of import module names (dotted)
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return [], set()

    symbols: List[Tuple[str, str]] = []
    imports: Set[str] = set()

    # Top-level only
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            symbols.append(("cls", node.name))
        elif isinstance(node, ast.FunctionDef):
            symbols.append(("fn", node.name))
        elif isinstance(node, ast.AsyncFunctionDef):
            symbols.append(("fn", node.name))

    # Imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.add(n.name)  # e.g., "pkg.mod"
        elif isinstance(node, ast.ImportFrom):
            # node.module can be None for "from . import x"
            base = node.module or ""
            level = getattr(node, "level", 0) or 0
            dot_prefix = "." * level
            imports.add(dot_prefix + base if base else dot_prefix)

    return symbols, imports

def py_signature_for(path: Path, func_name: str) -> Optional[str]:
    """
    Attempt a minimal signature string: (arg[:type], ...)->ret[:type]
    Ignores defaults; includes *args/**kwargs by name only.
    """
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src, filename=str(path))
    except Exception:
        return None

    def ann_to_str(ann) -> str:
        if ann is None:
            return ""
        try:
            return ast.unparse(ann)  # Py3.9+; benign if not available
        except Exception:
            return ""

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            args = []
            for a in node.args.args:
                t = ann_to_str(a.annotation)
                args.append(f"{a.arg}:{t}" if t else a.arg)
            if node.args.vararg:
                args.append(f"*{node.args.vararg.arg}")
            for a in node.args.kwonlyargs:
                t = ann_to_str(a.annotation)
                args.append(f"{a.arg}:{t}" if t else a.arg)
            if node.args.kwarg:
                args.append(f"**{node.args.kwarg.arg}")
            ret = ann_to_str(node.returns)
            ret_s = ret if ret else "Any"
            return f"({','.join(args)})->{ret_s}"
    return None

# -----------------------------
# Repo scan
# -----------------------------

CODE_EXTS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".kt", ".swift", ".c", ".h", ".cpp", ".hpp", ".cs"
}

def is_code_file(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in CODE_EXTS and not is_probably_binary(p)

def default_role_tags(path: str) -> Set[str]:
    tags = set()
    if "test" in path or "tests" in path:
        tags.add("test")
    if "auth" in path:
        tags.add("auth")
    if "api" in path:
        tags.add("api")
    if "repo" in path or "repository" in path:
        tags.add("repo")
    if "service" in path or "svc" in path:
        tags.add("svc")
    return tags or {"mod"}

def normalize_import(module_str: str, file_path: Path, root: Path) -> str:
    """Convert a python dotted import or relative into a best-effort relative module path."""
    # For simplicity, we return dotted names except relative (leading dots) -> path-based hints.
    if not module_str:
        return ""
    if module_str.startswith("."):
        # Count dots to go up; without resolving fully, attach to current package directory.
        up = len(module_str) - len(module_str.lstrip("."))
        base_dir = file_path.parent
        for _ in range(up):
            base_dir = base_dir.parent
        remainder = module_str.lstrip(".")
        if remainder:
            return relpath(base_dir / (remainder.replace(".", "/") + ".py"), root)
        return relpath(base_dir, root)
    return module_str  # leave dotted import as-is; later mapping tries to match

@dataclass
class ScanResult:
    modules: Dict[str, ModuleInfo]  # key: module path (posix)
    lang_set: List[str]

def scan_repo(root: Path, include_glob: Optional[str], exclude_glob: Optional[str]) -> ScanResult:
    files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if include_glob and not p.match(include_glob):
            # Allow code files outside include_glob if it's too restrictive? Keep strict.
            pass
        # Decide inclusion:
        if is_code_file(p):
            files.append(p)

    # Exclude patterns
    if exclude_glob:
        files = [p for p in files if not p.match(exclude_glob)]

    # Sort for deterministic IDs
    files = sorted(files, key=lambda x: relpath(x, root))

    modules: Dict[str, ModuleInfo] = {}
    mid_counter = 1
    for path in files:
        rp = relpath(path, root)
        mi = ModuleInfo(id=mid_counter, path=rp, role_tags=default_role_tags(rp))
        # Add module pseudo-symbol (#mid.#0)
        mi.symbols.append(Symbol(mid=mi.id, sid=0, kind="mod", name=Path(rp).stem))
        # Language specific:
        if path.suffix.lower() == ".py":
            symbols, imports = py_extract(path)
            for kind, name in symbols:
                sid = len(mi.symbols)
                sym = Symbol(mid=mi.id, sid=sid, kind=kind, name=name)
                if kind == "fn":
                    sig = py_signature_for(path, name)
                    sym.signature = sig or None
                mi.symbols.append(sym)
            # Normalize imports
            norm_imports = set()
            for imp in imports:
                norm_imports.add(normalize_import(imp, path, root))
            mi.imports = norm_imports
        modules[rp] = mi
        mid_counter += 1

    # Build import edges across modules (module->module via #mid.#0)
    # Attempt to map dotted imports to file paths if possible (best effort).
    # Create a name index to help: stem and dotted heuristic.
    path_by_stem: Dict[str, List[str]] = {}
    for mp in modules.keys():
        stem = Path(mp).stem
        path_by_stem.setdefault(stem, []).append(mp)

    # Resolve dotted imports to module files by last component match
    for mp, mi in modules.items():
        resolved = set()
        for imp in mi.imports:
            if not imp:
                continue
            if imp.endswith(".py"):
                # already a path-ish relative import
                cand = imp
                if cand in modules:
                    resolved.add(cand)
                else:
                    # try without .py
                    cand2 = imp[:-3]
                    if cand2 in modules:
                        resolved.add(cand2)
                continue
            last = imp.split(".")[-1]
            if last in path_by_stem:
                # pick same-package first
                candidates = path_by_stem[last]
                # crude heuristic: prefer same dir
                same_dir = [c for c in candidates if Path(c).parent == Path(mp).parent]
                resolved.add((same_dir or candidates)[0])
        mi.imports = resolved

    langs = detect_langs(root)
    return ScanResult(modules=modules, lang_set=langs)

# -----------------------------
# CTX-CARD render
# -----------------------------

HEADER_ALIASES = [
    "cfg=>Configuration",
    "svc=>Service",
    "repo=>Repository",
    "dto=>DataTransferObject",
    "uc=>UseCase",
    "http=>HTTP",
    "db=>Database",
    "jwt=>JWT",
]

NAMING_GRAMMAR_DEFAULT = [
    ("module", r"^[a-z_]+$", "auth_service"),
    ("class",  r"^[A-Z][A-Za-z0-9]+$", "AuthService"),
    ("func",   r"^[a-z_]+$", "issue_token"),
    ("var",    r"^[a-z_]+$", "user_repo"),
]

def render_ctxcard(proj: str, langs: List[str], std: str, scan: ScanResult) -> str:
    lines: List[str] = []
    # ID
    lines.append(f"ID: proj|{proj} lang|{','.join(langs)} std|{std} ts|{today_stamp()}")

    # AL
    for al in HEADER_ALIASES:
        lines.append(f"AL: {al}")

    # NM
    for scope, regex, example in NAMING_GRAMMAR_DEFAULT:
        lines.append(f"NM: {scope} | {regex} | {example}")

    # Modules
    # stable order by id
    module_list = sorted(scan.modules.values(), key=lambda m: m.id)
    for m in module_list:
        tags = "{" + "," + "".join(sorted(m.role_tags)).replace(",{", "{")  # tidy
        tags = "{" + ",".join(sorted(m.role_tags)) + "}" if m.role_tags else "{mod}"
        lines.append(f"MO: #{m.id} | {m.path} | {tags}")

    # Symbols
    for m in module_list:
        for s in m.symbols:
            lines.append(f"SY: #{m.id}.#{s.sid} | {s.kind} | {s.name}")
            if s.kind == "fn" and s.signature:
                lines.append(f"SG: #{m.id}.#{s.sid} | {s.signature}")

    # Edges (module-level import edges via #mid.#0)
    for m in module_list:
        for dep_path in sorted(m.imports):
            if dep_path in scan.modules:
                dep = scan.modules[dep_path]
                lines.append(f"ED: #{m.id}.#0 -> #{dep.id}.#0 | imports")

    # Minimal repo policies
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
    txt = path.read_text(encoding="utf-8", errors="replace")
    return [ln.rstrip("\n") for ln in txt.splitlines() if ln.strip()]

def diff_lines(old: List[str], new: List[str]) -> List[str]:
    old_set = set(old)
    new_set = set(new)
    added = [ln for ln in new if ln not in old_set]
    removed = [ln for ln in old if ln not in new_set]
    delta = []
    # Keep the same tag format; prefix with Δ: and a state.
    for ln in added:
        delta.append(f"Δ: + {ln}")
    for ln in removed:
        delta.append(f"Δ: - {ln}")
    return delta

# -----------------------------
# CLI
# -----------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Generate CTX-CARD for a repository (token-cheap codebase map)."
    )
    ap.add_argument("root", nargs="?", default=".", help="Repository root")
    ap.add_argument("--proj", default=None, help="Project slug (default: folder name)")
    ap.add_argument("--std", default="pep8", help="Primary style/standard hint")
    ap.add_argument("--include", default=None, help="Glob to include (e.g., '**/*.py')")
    ap.add_argument("--exclude", default=None, help="Glob to exclude (e.g., '**/tests/**')")
    ap.add_argument("--out", default="CTXCARD.md", help="Output file path")
    ap.add_argument("--delta-from", default=None, help="Existing CTXCARD to compute Δ section")
    ap.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing file")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Root not found: {root}", file=sys.stderr)
        sys.exit(1)

    proj = args.proj or root.name
    scan = scan_repo(root, args.include, args.exclude)
    card = render_ctxcard(proj, scan.lang_set, args.std, scan)

    # Optionally append Δ against an existing CTXCARD
    if args.delta_from:
        old_lines = load_existing_ctxcard(Path(args.delta_from))
        new_lines = [ln for ln in card.splitlines() if ln.strip()]
        delta = diff_lines(old_lines, new_lines)
        if delta:
            card = card + "\n".join(delta) + "\n"

    if args.stdout:
        print(card, end="")
        return

    outp = Path(args.out)
    outp.write_text(card, encoding="utf-8")
    print(f"Wrote {outp}")

if __name__ == "__main__":
    main()