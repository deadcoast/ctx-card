"""
Call resolver for CTX-CARD generator.

This module handles cross-module function call resolution and re-export processing.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ..exceptions import ASTError
from ..types import ModuleInfo, ScanResult
from ..utils.helpers import file_to_dotted


class CallResolver:
    """Resolves cross-module function calls and handles re-exports."""

    def __init__(self):
        """Initialize the call resolver."""
        pass

    def build_reexports_global(self, modules: Dict[str, ModuleInfo]) -> Dict[str, str]:
        """Build global re-export mappings across all modules."""
        reexports: Dict[str, str] = {}
        for mi in modules.values():
            reexports.update(mi.reexports)
        return reexports

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

    def resolve_target(
        self,
        full_dotted: str,
        dotted_to_path: Dict[str, str],
        modules: Dict[str, ModuleInfo],
    ) -> Tuple[Optional[int], Optional[int], str]:
        """
        Resolve a qualified name to a specific module and symbol.

        Returns:
            Tuple of (module_id, symbol_id, reason)
        """

        def try_direct(dotted: str) -> Tuple[Optional[int], Optional[int], str]:
            rp_target = self.longest_prefix_module(dotted, dotted_to_path)
            if not rp_target:
                return None, None, "module_not_found"

            mt = modules[rp_target]
            mod_prefix_len = len(file_to_dotted(rp_target).split("."))
            parts = dotted.split(".")
            rest = parts[mod_prefix_len:]

            # Try Class.method first if 2+ tokens remain
            if len(rest) >= 2:
                cand = f"{rest[0]}.{rest[1]}"
                sid = mt.fn_to_sid.get(cand) or mt.prop_to_sid.get(cand)
                if sid:
                    return mt.id, sid, "class_method"

            # Then plain function
            if len(rest) >= 1:
                sid = mt.fn_to_sid.get(rest[0]) or mt.prop_to_sid.get(rest[0])
                if sid:
                    return mt.id, sid, "function"

            # Else module anchor
            return mt.id, 0, "module_anchor"

        # Try direct resolution
        mid, sid, reason = try_direct(full_dotted)
        if mid is not None:
            return mid, sid, reason

        return None, None, "not_found"

    def extract_calls(self, root: Path, scan: ScanResult) -> None:
        """
        Extract function calls from all modules (Pass B).

        This is the second pass that resolves cross-module function calls.
        """
        modules = scan.modules
        dotted_to_path, _ = self.build_indices(modules)
        reexports = self.build_reexports_global(modules)

        for rp, mi in modules.items():
            full = root / rp
            if full.suffix.lower() != ".py":
                continue

            try:
                src = full.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(src, filename=str(full))
            except Exception:
                continue

            # Add parent links for AST traversal
            for parent in ast.walk(tree):
                for child in ast.iter_child_nodes(parent):
                    setattr(child, "parent", parent)

            # Build local lookup for function names
            local_lookup = dict(mi.fn_to_sid)

            # Process all function calls
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue

                # Find caller context
                caller_sid = self._find_caller_sid(node, local_lookup)
                if not caller_sid:
                    continue

                # Resolve call target
                target = self._resolve_call_target(
                    node, mi, dotted_to_path, modules, reexports
                )
                if target:
                    # Suppress edges to properties (they're attribute access, not calls)
                    t_mid, t_sid = target
                    if t_sid != 0:
                        mt = next((m for m in modules.values() if m.id == t_mid), None)
                        if mt:
                            sym = next((s for s in mt.symbols if s.sid == t_sid), None)
                            if sym and sym.kind == "prop":
                                continue

                    mi.calls.append((caller_sid, target))

    def _find_caller_sid(
        self, node: ast.Call, local_lookup: Dict[str, int]
    ) -> Optional[int]:
        """Find the symbol ID of the function containing this call."""
        up = node
        while True:
            up = getattr(up, "parent", None)
            if up is None:
                break
            if isinstance(up, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Find class owner if this is a method
                cls_owner = None
                p2 = up
                while True:
                    p2 = getattr(p2, "parent", None)
                    if p2 is None:
                        break
                    if isinstance(p2, ast.ClassDef):
                        cls_owner = p2.name
                        break

                if cls_owner:
                    return local_lookup.get(f"{cls_owner}.{up.name}")
                else:
                    return local_lookup.get(up.name)
        return None

    def _resolve_call_target(
        self,
        node: ast.Call,
        mi: ModuleInfo,
        dotted_to_path: Dict[str, str],
        modules: Dict[str, ModuleInfo],
        reexports: Dict[str, str],
    ) -> Optional[Tuple[int, int]]:
        """Resolve a function call to its target module and symbol."""
        target: Optional[Tuple[int, int]] = None

        if isinstance(node.func, ast.Name):
            # Direct function call: Name()
            fn = node.func.id
            sid = mi.fn_to_sid.get(fn)
            if sid:
                target = (mi.id, sid)

        elif isinstance(node.func, ast.Attribute):
            # Qualified call: module.func() or module.Class.method()
            dotted = self._dotted_from_ast(node.func)
            if dotted:
                head = dotted.split(".")[0]
                mapped_head = mi.import_names.get(head)

                if mapped_head:
                    # Build full dotted path
                    full_dotted = ".".join([mapped_head] + dotted.split(".")[1:])

                    # Try direct resolution
                    t_mid, t_sid, _ = self.resolve_target(
                        full_dotted, dotted_to_path, modules
                    )
                    if t_mid is not None:
                        target = (t_mid, t_sid)
                    else:
                        # Try re-export resolution
                        origin = reexports.get(full_dotted)
                        if origin:
                            t_mid, t_sid, _ = self.resolve_target(
                                origin, dotted_to_path, modules
                            )
                            if t_mid is not None:
                                target = (t_mid, t_sid)
                else:
                    # Try direct resolution without import mapping
                    t_mid, t_sid, _ = self.resolve_target(
                        dotted, dotted_to_path, modules
                    )
                    if t_mid is not None:
                        target = (t_mid, t_sid)

        return target

    def _dotted_from_ast(self, expr: ast.AST) -> str:
        """Extract dotted name from AST expression."""
        if isinstance(expr, ast.Name):
            return expr.id
        if isinstance(expr, ast.Attribute):
            base = self._dotted_from_ast(expr.value)
            return f"{base}.{expr.attr}" if base else expr.attr
        return ""

    def process_reexports(self, modules: Dict[str, ModuleInfo]) -> None:
        """Process re-exports in __init__.py files and __all__ declarations."""
        for rp, mi in modules.items():
            if Path(rp).name != "__init__.py":
                continue

            # Process __init__.py re-exports
            pkg_dot = mi.dotted
            for local, origin in mi.import_names.items():
                mi.reexports[f"{pkg_dot}.{local}"] = origin

            # Process __all__ declarations
            # This would require re-parsing the file to find __all__ assignments
            # For now, we'll handle this in the scanner during initial parsing
