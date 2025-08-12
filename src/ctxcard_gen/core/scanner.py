"""
Repository scanner for CTX-CARD generator.

This module handles file discovery, module indexing, and initial scanning.
"""

from __future__ import annotations

import ast
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ..types import ModuleInfo, Symbol, ScanResult
from ..utils.helpers import is_probably_binary, relpath, file_to_dotted, ann_to_str
from ..utils.ignore import load_ignore_file


class RepoScanner:
    """Scans repositories and builds module indices."""

    # Supported code file extensions
    CODE_EXTS = {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".go",
        ".rs",
        ".java",
        ".kt",
        ".swift",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".cs",
    }

    def __init__(self, max_workers: int = 4, cache_size: int = 1000):
        """
        Initialize the repository scanner.

        Args:
            max_workers: Maximum number of parallel workers for file processing
            cache_size: Maximum size of file content cache
        """
        self.max_workers = max_workers
        self.cache_size = cache_size
        self._file_cache: Dict[Path, str] = {}
        self._cache_lock = threading.Lock()

    def _get_cached_content(self, file_path: Path) -> Optional[str]:
        """Get file content from cache if available."""
        with self._cache_lock:
            return self._file_cache.get(file_path)

    def _set_cached_content(self, file_path: Path, content: str) -> None:
        """Cache file content with size limit."""
        with self._cache_lock:
            if len(self._file_cache) >= self.cache_size:
                # Remove oldest entry (simple LRU)
                oldest_key = next(iter(self._file_cache))
                del self._file_cache[oldest_key]
            self._file_cache[file_path] = content

    def is_code_file(self, path: Path) -> bool:
        """Check if a file is a code file."""
        return (
            path.is_file()
            and path.suffix.lower() in self.CODE_EXTS
            and not is_probably_binary(path)
        )

    def role_tags_for(self, path: str) -> Set[str]:
        """Determine role tags for a file path."""
        low = path.lower()
        tags = set()
        for k, t in [
            ("test", "test"),
            ("auth", "auth"),
            ("api", "api"),
            ("repo", "repo"),
            ("repository", "repo"),
            ("service", "svc"),
            ("svc", "svc"),
        ]:
            if k in low:
                tags.add(t)
        return tags or {"mod"}

    def detect_langs(self, root: Path) -> List[str]:
        """Detect programming languages in the repository."""
        # Load ignore file
        ignore_file = load_ignore_file(root)

        exts = set()
        for p in root.rglob("*"):
            if p.is_file() and not ignore_file.should_ignore(p):
                exts.add(p.suffix.lower())

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

    def build_indices(
        self, modules: Dict[str, ModuleInfo]
    ) -> Tuple[Dict[str, str], Dict[str, List[str]]]:
        """Build repository indices for module resolution."""
        dotted_to_path: Dict[str, str] = {}
        stem_to_paths: Dict[str, List[str]] = {}

        for rp, mi in modules.items():
            dotted_to_path[mi.dotted] = rp
            stem_to_paths.setdefault(Path(rp).stem, []).append(rp)

        return dotted_to_path, stem_to_paths

    def longest_prefix_module(
        self, dotted: str, dotted_to_path: Dict[str, str]
    ) -> Optional[str]:
        """Find the longest prefix module for a dotted name."""
        parts = dotted.split(".")
        for i in range(len(parts), 0, -1):
            cand = ".".join(parts[:i])
            rp = dotted_to_path.get(cand)
            if rp:
                return rp
        return None

    def scan_repository(
        self, root: Path, include_pattern: Optional[str] = None, exclude_pattern: Optional[str] = None  # pylint: disable=line-too-long
    ) -> ScanResult:
        """Scan repository and build module indices."""
        # Load ignore file
        ignore_file = load_ignore_file(root)

        # Find all code files
        code_files = []
        for p in root.rglob("*"):
            if (
                p.is_file()
                and self.is_code_file(p)
                and not ignore_file.should_ignore(p)
            ):
                rel_path = relpath(p, root)
                if include_pattern and not p.match(include_pattern):
                    continue
                if exclude_pattern and p.match(exclude_pattern):
                    continue
                code_files.append(rel_path)

        # Build initial module info
        modules: Dict[str, ModuleInfo] = {}
        mid = 1
        for rp in sorted(code_files):
            mi = ModuleInfo(
                id=mid,
                path=rp,
                dotted=file_to_dotted(rp),
                role_tags=self.role_tags_for(rp),
            )
            mi.symbols.append(Symbol(mid=mid, sid=1, kind="mod", name=Path(rp).stem))
            modules[rp] = mi
            mid += 1

        # Build indices for resolution
        dotted_to_path, stem_to_paths = self.build_indices(modules)

        # Process Python files with parallel processing for large codebases
        if len(code_files) > 50:  # Use parallel processing for large codebases
            self._process_files_parallel(root, modules, dotted_to_path, stem_to_paths)
        else:
            self._process_files_sequential(root, modules, dotted_to_path, stem_to_paths)

        # Detect languages
        langs = self.detect_langs(root)

        return ScanResult(modules=modules, langs=langs)

    def _process_files_sequential(
        self,
        root: Path,
        modules: Dict[str, ModuleInfo],
        dotted_to_path: Dict[str, str],
        stem_to_paths: Dict[str, List[str]],
    ):
        """Process files sequentially (original method)."""
        for rp, mi in modules.items():
            full = root / rp
            if full.suffix.lower() != ".py":
                continue

            try:
                src = full.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(src, filename=str(full))
            except Exception:  # pylint: disable=broad-except
                # Skip files that can't be parsed
                continue

            # Process imports and build import paths
            self._process_imports(tree, mi, full, root, dotted_to_path, stem_to_paths)

            # Process symbols and extract metadata
            self._process_symbols(tree, mi, rp)

    def _process_files_parallel(
        self,
        root: Path,
        modules: Dict[str, ModuleInfo],
        dotted_to_path: Dict[str, str],
        stem_to_paths: Dict[str, List[str]],
    ):
        """Process files in parallel for better performance."""
        def process_single_file(rp: str) -> Tuple[str, Optional[ast.AST]]:
            """Process a single file and return AST if successful."""
            full = root / rp
            if full.suffix.lower() != ".py":
                return rp, None

            try:
                # Check cache first
                cached_content = self._get_cached_content(full)
                if cached_content is None:
                    cached_content = full.read_text(encoding="utf-8", errors="replace")
                    self._set_cached_content(full, cached_content)

                tree = ast.parse(cached_content, filename=str(full))
                return rp, tree
            except Exception:  # pylint: disable=broad-except
                # Skip files that can't be parsed
                return rp, None

        # Process files in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_rp = {
                executor.submit(process_single_file, rp): rp
                for rp in modules.keys()
            }

            for future in as_completed(future_to_rp):
                rp, tree = future.result()
                if tree is not None:
                    mi = modules[rp]
                    full = root / rp

                    # Process imports and build import paths
                    self._process_imports(tree, mi, full, root, dotted_to_path, stem_to_paths)

                    # Process symbols and extract metadata
                    self._process_symbols(tree, mi, rp)

    def _process_imports(
        self,
        tree: ast.AST,
        mi: ModuleInfo,
        _full: Path,  # pylint: disable=unused-argument
        _root: Path,  # pylint: disable=unused-argument
        dotted_to_path: Dict[str, str],
        stem_to_paths: Dict[str, List[str]],
    ):
        """Process imports and build import paths."""
        imports_raw: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    mi.import_names[n.asname or n.name] = n.name
                    imports_raw.add(n.name)
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                dots = "." * (node.level or 0)
                base_full = (dots + base) if base or dots else ""
                imports_raw.add(dots + base if base or dots else "")

                for n in node.names:
                    if isinstance(n, ast.alias) and n.name == "*":
                        mi.px.append(("forbid wildcard import", "namespace"))

                    alias = n.asname or n.name
                    dotted = (
                        (base_full + "." + n.name)
                        if base_full and n.name != "*"
                        else n.name
                    )
                    mi.import_names[alias] = dotted

        # Resolve imports to module paths
        for tok in imports_raw:
            if not tok:
                continue
            if tok in dotted_to_path:
                mi.imports_paths.add(dotted_to_path[tok])
                continue

            last = tok.split(".")[-1]
            for rp2 in stem_to_paths.get(last, []):
                mi.imports_paths.add(rp2)

    def _process_symbols(self, tree: ast.AST, mi: ModuleInfo, rp: str):
        """Process symbols and extract metadata from AST."""
        # Pre-scan for lint items
        self._scan_lint_items(tree, mi, rp)

        sid = 2  # Start at 2 since module symbol is already at 1

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                sid = self._process_class(node, mi, sid)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sid = self._process_function(node, mi, sid, rp)

        # Check for global state in service modules
        if "svc" in mi.role_tags:
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    mi.px.append(("forbid global state in svc", "concurrency"))

    def _scan_lint_items(self, tree: ast.AST, mi: ModuleInfo, rp: str):
        """Scan for linting violations."""
        for n in ast.walk(tree):
            if isinstance(n, ast.ExceptHandler) and n.type is None:
                mi.px.append(("forbid bare except", "error-handling"))
            if (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id in {"eval", "exec"}
            ):
                mi.px.append(("forbid eval/exec", "security"))
            if (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id == "print"
            ):
                if "test" not in rp.lower():
                    mi.px.append(("forbid print in production", "logging"))

    def _process_class(self, node: ast.ClassDef, mi: ModuleInfo, sid: int) -> int:
        """Process a class definition."""
        cls = node.name

        # Create class symbol
        sym_cls = Symbol(mid=mi.id, sid=sid, kind="cls", name=cls)
        if self._class_has_descriptor_dunders(node):
            sym_cls.modifiers.add("descriptor")
        mi.symbols.append(sym_cls)
        sid += 1

        # Process DTOs, Errors, and Enums
        self._process_dto_error_enum(node, mi, cls)

        # Process class methods and properties
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sid = self._process_class_member(stmt, mi, sid, cls)

        return sid

    def _process_class_member(
        self,
        stmt: ast.FunctionDef | ast.AsyncFunctionDef,
        mi: ModuleInfo,
        sid: int,
        cls: str,
    ) -> int:
        """Process a class method or property."""
        decos = [
            self._dotted_from_ast(d if not isinstance(d, ast.Call) else d.func)
            for d in stmt.decorator_list
        ]
        mods = self._method_modifiers(decos)

        if "property" in mods:
            # Handle as property
            sp = Symbol(
                mid=mi.id,
                sid=sid,
                kind="prop",
                name=f"{cls}.{stmt.name}",
                deco=decos,
                modifiers={"property"},
            )
            mi.symbols.append(sp)
            mi.prop_to_sid[sp.name] = sid
            sid += 1
        else:
            # Handle as method
            sig = self._function_signature(stmt)
            raises = self._collect_raises_in_function(stmt)
            sm = Symbol(
                mid=mi.id,
                sid=sid,
                kind="fn",
                name=f"{cls}.{stmt.name}",
                signature=sig,
                deco=decos,
                modifiers=mods,
                raises=raises,
            )
            mi.symbols.append(sm)
            mi.fn_to_sid[sm.name] = sid
            sid += 1

        return sid

    def _process_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        mi: ModuleInfo,
        sid: int,
        rp: str,  # pylint: disable=unused-argument
    ) -> int:
        """Process a function definition."""
        name = node.name
        sig = self._function_signature(node)
        raises = self._collect_raises_in_function(node)

        sym = Symbol(
            mid=mi.id, sid=sid, kind="fn", name=name, signature=sig, raises=raises
        )

        # Check for mutable defaults
        if self._has_mutable_default(node):
            mi.px.append(("forbid mutable default arguments", "bug-risk"))

        # Process API routes
        self._process_routes(node, mi, sid)

        mi.symbols.append(sym)
        mi.fn_to_sid[name] = sid
        sid += 1

        return sid

    def _process_dto_error_enum(self, node: ast.ClassDef, mi: ModuleInfo, cls: str):
        """Process DTOs, Errors, and Enums."""
        # Check for enums
        if self._is_enum_class(node):
            keys = []
            for b in node.body:
                if isinstance(b, ast.Assign):
                    for t in b.targets:
                        if isinstance(t, ast.Name) and t.id.isupper():
                            keys.append(t.id)
            if keys:
                mi.tokens.append((cls, keys))

        # Check for exceptions
        for b in node.bases:
            bn = ann_to_str(b) or self._dotted_from_ast(b)
            if bn.endswith("Exception") or bn == "Exception":
                mi.errors.append((cls, "domain", "custom exception"))

        # Check for DTOs
        decos = [
            self._dotted_from_ast(d if not isinstance(d, ast.Call) else d.func)
            for d in node.decorator_list
        ]
        is_dataclass = any(n.endswith("dataclass") for n in decos)
        is_pyd = False

        for b in node.bases:
            bn = ann_to_str(b) or self._dotted_from_ast(b)
            if bn.endswith("BaseModel") or bn.endswith("pydantic.BaseModel"):
                is_pyd = True

        if is_dataclass or is_pyd:
            fields = {}
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(
                    stmt.target, ast.Name
                ):
                    t = ann_to_str(stmt.annotation) or "Any"
                    fields[stmt.target.id] = t
            mi.dts.append((cls, fields))

    def _process_routes(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, mi: ModuleInfo, _sid: int  # pylint: disable=unused-argument
    ):
        """Process API route decorators."""
        for d in node.decorator_list:
            if isinstance(d, ast.Call):
                nm = self._dotted_from_ast(d.func)
                if nm in (
                    "app.get",
                    "app.post",
                    "app.put",
                    "app.delete",
                    "router.get",
                    "router.post",
                    "router.put",
                    "router.delete",
                ):
                    verb = nm.split(".")[-1].upper()
                    if (
                        d.args
                        and isinstance(d.args[0], ast.Constant)
                        and isinstance(d.args[0].value, str)
                    ):
                        mi.routes.append((_sid, verb, d.args[0].value, ["200"]))

                if nm and nm.endswith(".route"):
                    pathv = None
                    verb = "GET"
                    if (
                        d.args
                        and isinstance(d.args[0], ast.Constant)
                        and isinstance(d.args[0].value, str)
                    ):
                        pathv = d.args[0].value
                    for kw in d.keywords or []:
                        if kw.arg == "methods" and isinstance(
                            kw.value, (ast.List, ast.Tuple)
                        ):
                            for elt in kw.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(
                                    elt.value, str
                                ):
                                    verb = elt.value.upper()
                                    break
                    if pathv:
                        mi.routes.append((_sid, verb, pathv, ["200"]))

    # Helper methods for AST analysis
    def _dotted_from_ast(self, expr: ast.AST) -> str:
        """Extract dotted name from AST expression."""
        if isinstance(expr, ast.Name):
            return expr.id
        if isinstance(expr, ast.Attribute):
            base = self._dotted_from_ast(expr.value)
            return f"{base}.{expr.attr}" if base else expr.attr
        return ""

    def _function_signature(self, node: ast.AST) -> str:
        """Extract function signature."""
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return ""

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

        ret = ann_to_str(node.returns) or "Any"
        return f"({','.join(args)})->{ret}"

    def _method_modifiers(self, decos: List[str]) -> Set[str]:
        """Extract method modifiers from decorators."""
        mods = set()
        for nm in decos:
            tail = nm.split(".")[-1]
            if tail == "staticmethod":
                mods.add("staticmethod")
            elif tail == "classmethod":
                mods.add("classmethod")
            elif tail == "property":
                mods.add("property")
            elif tail == "cached_property":
                mods.add("property")
        return mods

    def _class_has_descriptor_dunders(self, node: ast.ClassDef) -> bool:
        """Check if class has descriptor dunder methods."""
        names = {
            stmt.name
            for stmt in node.body
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        return bool({"__get__", "__set__", "__set_name__"} & names)

    def _is_enum_class(self, node: ast.ClassDef) -> bool:
        """Check if class is an enum."""
        for b in node.bases:
            bn = ann_to_str(b) or self._dotted_from_ast(b)
            if bn.endswith("Enum") or bn == "Enum":
                return True
        return False

    def _has_mutable_default(self, fn: ast.AST) -> bool:
        """Check if function has mutable default arguments."""
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False

        muts = (ast.List, ast.Dict, ast.Set)
        for d in fn.args.defaults:
            if isinstance(d, muts):
                return True
        for d in fn.args.kw_defaults:
            if d is not None and isinstance(d, muts):
                return True
        return False

    def _collect_raises_in_function(self, fn_node: ast.AST) -> List[str]:
        """Collect exception types raised in function."""
        seen: List[str] = []
        for n in self._walk_ignoring_nested(fn_node):
            if isinstance(n, ast.Raise):
                nm = self._exception_name_from_raise(n.exc)
                if nm not in seen:
                    seen.append(nm)
        return seen

    def _walk_ignoring_nested(self, fn_node: ast.AST):
        """Walk AST ignoring nested function definitions."""
        for n in ast.walk(fn_node):
            if (
                isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n is not fn_node
            ):
                continue
            yield n

    def _exception_name_from_raise(self, exc: Optional[ast.AST]) -> str:
        """Extract exception name from raise statement."""
        if exc is None:
            return "ReRaise"
        if isinstance(exc, ast.Call):
            return self._dotted_from_ast(exc.func) or "Exception"
        if isinstance(exc, (ast.Name, ast.Attribute)):
            return self._dotted_from_ast(exc) or "Exception"
        return "Exception"
