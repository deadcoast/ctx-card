"""
Card renderer for CTX-CARD generator.

This module handles the generation of CTX-CARD format output.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Any

from ..types import ModuleInfo
from ..utils.helpers import today_stamp, ascii_only
from ..utils.validation import validate_prefix_free
from ..exceptions import ValidationError


class CardRenderer:
    """Renders CTX-CARD format output."""

    # Default header aliases
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

    # Default naming grammar
    NAMING_GRAMMAR_DEFAULT = [
        ("module", r"^[a-z_]+$", "auth_service"),
        ("class", r"^[A-Z][A-Za-z0-9]+$", "AuthService"),
        ("func", r"^[a-z_]+$", "issue_token"),
        ("var", r"^[a-z_]+$", "user_repo"),
    ]

    def __init__(self):
        """Initialize the card renderer."""
        pass

    def render_card(
        self,
        project_name: str,
        langs: List[str],
        std: str,
        modules: Dict[str, ModuleInfo],
        emit_type_signatures: bool = False,
    ) -> str:
        """Render CTX-CARD content."""
        lines = []

        # ID: Global identity
        ts = today_stamp()
        lines.append(f"ID: proj|{project_name} lang|{','.join(langs)} std|{std} ts|{ts}")
        lines.append("")

        # AL: Alias table
        aliases = self._extract_aliases(modules)
        for alias in aliases:
            lines.append(f"AL: {alias}")
        lines.append("")

        # NM: Naming grammar
        naming_patterns = self._extract_naming_patterns(modules)
        for pattern in naming_patterns:
            lines.append(f"NM: {pattern}")
        lines.append("")

        # DEPS: External dependencies (NEW)
        dependencies = self._extract_dependencies(modules)
        if dependencies:
            for dep in dependencies:
                lines.append(f"DEPS: {dep}")
            lines.append("")

        # ENV: Environment configuration (NEW)
        env_configs = self._extract_environment_configs(modules)
        if env_configs:
            for env in env_configs:
                lines.append(f"ENV: {env}")
            lines.append("")

        # SEC: Security constraints (NEW)
        security_constraints = self._extract_security_constraints(modules)
        if security_constraints:
            for sec in security_constraints:
                lines.append(f"SEC: {sec}")
            lines.append("")

        # DT: Data shapes
        data_types = self._extract_data_types(modules)
        for dt in data_types:
            lines.append(f"DT: {dt}")
        lines.append("")

        # TK: Token/enum sets
        token_sets = self._extract_token_sets(modules)
        for tk in token_sets:
            lines.append(f"TK: {tk}")
        lines.append("")

        # MO: Module index
        for mi in modules.values():
            role_tags = ",".join(sorted(mi.role_tags))
            lines.append(f"MO: #{mi.id} | {mi.path} | {{{role_tags}}}")
        lines.append("")

        # SY: Symbol index
        for mi in modules.values():
            for symbol in mi.symbols:
                lines.append(f"SY: #{symbol.mid}.#{symbol.sid} | {symbol.kind} | {symbol.name}")
        lines.append("")

        # TY: Type signatures (optional)
        if emit_type_signatures:
            type_signatures = self._extract_type_signatures(modules)
            for ty in type_signatures:
                lines.append(f"TY: {ty}")
            lines.append("")

        # SG: Signatures
        signatures = self._extract_signatures(modules)
        for sg in signatures:
            lines.append(f"SG: {sg}")
        lines.append("")

        # ED: Edges
        edges = self._extract_edges(modules)
        for edge in edges:
            lines.append(f"ED: {edge}")
        lines.append("")

        # EVT: Event relationships (NEW)
        event_relationships = self._extract_event_relationships(modules)
        if event_relationships:
            for evt in event_relationships:
                lines.append(f"EVT: {evt}")
            lines.append("")

        # ASYNC: Async patterns (NEW)
        async_patterns = self._extract_async_patterns(modules)
        if async_patterns:
            for async_pattern in async_patterns:
                lines.append(f"ASYNC: {async_pattern}")
            lines.append("")

        # IN: Invariants
        invariants = self._extract_invariants(modules)
        for inv in invariants:
            lines.append(f"IN: {inv}")
        lines.append("")

        # CN: Conventions
        conventions = self._extract_conventions(modules)
        for cn in conventions:
            lines.append(f"CN: {cn}")
        lines.append("")

        # ER: Error taxonomy
        errors = self._extract_errors(modules)
        for er in errors:
            lines.append(f"ER: {er}")
        lines.append("")

        # IO: I/O contracts
        io_contracts = self._extract_io_contracts(modules)
        for io in io_contracts:
            lines.append(f"IO: {io}")
        lines.append("")

        # PX: Prohibited patterns
        prohibited = self._extract_prohibited_patterns(modules)
        for px in prohibited:
            lines.append(f"PX: {px}")
        lines.append("")

        # EX: Examples
        examples = self._extract_examples(modules)
        for ex in examples:
            lines.append(f"EX: {ex}")
        lines.append("")

        # RV: Review focus
        review_items = self._extract_review_items(modules)
        for rv in review_items:
            lines.append(f"RV: {rv}")

        return "\n".join(lines)

    def _extract_aliases(self, _modules: Dict[str, ModuleInfo]) -> List[str]:  # pylint: disable=unused-argument
        """Extract alias patterns from modules."""
        # Default aliases that are commonly used
        default_aliases = [
            "cfg=>Configuration",
            "svc=>Service",
            "repo=>Repository",
            "dto=>DataTransferObject",
            "uc=>UseCase",
            "http=>HTTP",
            "db=>Database",
            "jwt=>JWT"
        ]
        return default_aliases

    def _extract_naming_patterns(self, modules: Dict[str, ModuleInfo]) -> List[str]:
        """Extract naming patterns from modules."""
        patterns = []
        for mi in modules.values():
            for symbol in mi.symbols:
                if symbol.kind == "mod":
                    patterns.append(f"module | ^[a-z_]+$ | {symbol.name}")
                elif symbol.kind == "cls":
                    patterns.append(f"class | ^[A-Z][A-Za-z0-9]+$ | {symbol.name}")
                elif symbol.kind == "fn":
                    patterns.append(f"func | ^[a-z_]+$ | {symbol.name}")
        return list(set(patterns))  # Remove duplicates

    def _extract_dependencies(self, modules: Dict[str, ModuleInfo]) -> List[str]:
        """Extract external dependencies from modules."""
        dependencies = set()
        for mi in modules.values():
            # Look for common dependency patterns in imports
            for import_path in mi.imports_paths:
                deps = ['requests', 'pandas', 'numpy', 'fastapi', 'flask', 'sqlalchemy']
                if any(dep in import_path.lower() for dep in deps):
                    dependencies.add(f"{import_path} | external")
        return sorted(dependencies)

    def _extract_environment_configs(self, modules: Dict[str, ModuleInfo]) -> List[str]:
        """Extract environment configuration patterns."""
        env_configs = []
        for mi in modules.values():
            if 'cfg' in mi.role_tags or 'config' in mi.path.lower():
                env_configs.append(f"{mi.path} | environment | config")
        return env_configs

    def _extract_security_constraints(self, modules: Dict[str, ModuleInfo]) -> List[str]:
        """Extract security constraints from modules."""
        security_constraints = []
        for mi in modules.values():
            for symbol in mi.symbols:
                if 'auth' in symbol.name.lower() or 'security' in symbol.name.lower():
                    security_constraints.append(f"{symbol.name} | authentication | required")
        return security_constraints

    def _extract_data_types(self, modules: Dict[str, ModuleInfo]) -> List[str]:
        """Extract data types from modules."""
        data_types = []
        for mi in modules.values():
            for name, fields in mi.dts:
                field_str = ",".join(f"{k}:{v}" for k, v in fields.items())
                data_types.append(f"{name} | {{{field_str}}}")
        return data_types

    def _extract_token_sets(self, modules: Dict[str, ModuleInfo]) -> List[str]:
        """Extract token/enum sets from modules."""
        token_sets = []
        for mi in modules.values():
            for name, keys in mi.tokens:
                keys_str = ",".join(keys)
                token_sets.append(f"{name} | {{{keys_str}}}")
        return token_sets

    def _extract_type_signatures(self, modules: Dict[str, ModuleInfo]) -> List[str]:
        """Extract type signatures from modules."""
        type_signatures = []
        for mi in modules.values():
            for symbol in mi.symbols:
                if symbol.kind == "fn" and symbol.signature:
                    raises_part = ""
                    if symbol.raises:
                        raises_part = f" !raises[{','.join(symbol.raises)}]"
                    type_signatures.append(
                        f"fn | {symbol.name} | {symbol.signature}{raises_part}"
                    )
        return type_signatures

    def _extract_signatures(self, modules: Dict[str, ModuleInfo]) -> List[str]:
        """Extract function signatures from modules."""
        signatures = []
        for mi in modules.values():
            for symbol in mi.symbols:
                if symbol.kind == "fn" and symbol.signature:
                    raises_part = ""
                    if symbol.raises:
                        raises_part = f" !raises[{','.join(symbol.raises)}]"
                    signatures.append(
                        f"#{symbol.mid}.#{symbol.sid} | {symbol.signature}{raises_part}"
                    )
        return signatures

    def _extract_edges(self, modules: Dict[str, ModuleInfo]) -> List[str]:
        """Extract edge relationships from modules."""
        edges = []
        for mi in modules.values():
            # Import edges
            for dep_path in sorted(mi.imports_paths):
                dep = modules.get(dep_path)
                if dep:
                    edges.append(f"#{mi.id}.#0 -> #{dep.id}.#0 | imports")

            # Call edges
            for caller_sid, (t_mid, t_sid) in mi.calls:
                edges.append(f"#{mi.id}.#{caller_sid} -> #{t_mid}.#{t_sid} | calls")
        return edges

    def _extract_event_relationships(self, modules: Dict[str, ModuleInfo]) -> List[str]:
        """Extract event relationships from modules."""
        event_relationships = []
        for mi in modules.values():
            for symbol in mi.symbols:
                event_words = ['event', 'handler', 'callback', 'listener']
                if any(event_word in symbol.name.lower() for event_word in event_words):
                    event_relationships.append(
                        f"#{symbol.mid}.#{symbol.sid} | event | {symbol.name}"
                    )
        return event_relationships

    def _extract_async_patterns(self, modules: Dict[str, ModuleInfo]) -> List[str]:
        """Extract async patterns from modules."""
        async_patterns = []
        for mi in modules.values():
            for symbol in mi.symbols:
                async_words = ['async', 'await', 'future', 'coroutine']
                if (symbol.kind == "fn" and 
                    any(async_word in symbol.name.lower() for async_word in async_words)):
                    async_patterns.append(
                        f"#{symbol.mid}.#{symbol.sid} | async | {symbol.name}"
                    )
        return async_patterns

    def _extract_invariants(self, modules: Dict[str, ModuleInfo]) -> List[str]:
        """Extract invariants from modules."""
        invariants = []
        for mi in modules.values():
            for symbol in mi.symbols:
                if symbol.invariants:
                    invariants.append(f"{symbol.name} ⇒ {symbol.invariants}")
        return invariants

    def _extract_conventions(self, _modules: Dict[str, ModuleInfo]) -> List[str]:  # pylint: disable=unused-argument
        """Extract coding conventions from modules."""
        conventions = [
            "repos never import svc",
            "async functions end with _async"
        ]
        return conventions

    def _extract_errors(self, modules: Dict[str, ModuleInfo]) -> List[str]:
        """Extract error taxonomy from modules."""
        errors = []
        for mi in modules.values():
            for name, category, meaning in mi.errors:
                errors.append(f"{name} | {category} | {meaning}")
        return errors

    def _extract_io_contracts(self, modules: Dict[str, ModuleInfo]) -> List[str]:
        """Extract I/O contracts from modules."""
        io_contracts = []
        for mi in modules.values():
            for sid, verb, path_s, codes in mi.routes:
                codes_str = ",".join(codes)
                fn = next((s for s in mi.symbols if s.sid == sid), None)
                sig = fn.signature if fn else "(…)->Any"
                in_sig = sig.split(")->")[0].lstrip("(") if ")->" in sig else ""
                out_sig = sig.split(")->")[-1] if ")->" in sig else "Any"
                io_contracts.append(f"{verb} {path_s} | {in_sig} | {out_sig} | {codes_str}")
        return io_contracts

    def _extract_prohibited_patterns(self, modules: Dict[str, ModuleInfo]) -> List[str]:
        """Extract prohibited patterns from modules."""
        prohibited = []
        for mi in modules.values():
            for rule, reason in mi.px:
                prohibited.append(f"{rule} | {reason}")
        return prohibited

    def _extract_examples(self, _modules: Dict[str, ModuleInfo]) -> List[str]:  # pylint: disable=unused-argument
        """Extract canonical examples from modules."""
        examples = []
        # This is a placeholder - in a real implementation, you would analyze modules
        # for actual examples based on usage patterns
        examples.append("var(repo) => user_repo")
        return examples

    def _extract_review_items(self, _modules: Dict[str, ModuleInfo]) -> List[str]:  # pylint: disable=unused-argument
        """Extract review focus items from modules."""
        review_items = [
            "public functions have signatures & docstrings",
            "check invariants (IN) on public fn"
        ]
        return review_items

    def _append_ty_lines(
        self, lines: List[str], modules: Dict[str, ModuleInfo]
    ) -> None:
        """Append TY lines for type signatures."""
        for m in modules.values():
            for s in m.symbols:
                if s.kind == "fn" and s.signature:
                    raises_part = ""
                    if s.raises:
                        raises_part = f" !raises[{','.join(s.raises)}]"
                    lines.append(f"TY: fn | {s.name} | {s.signature}{raises_part}")

    def generate_delta(self, old_path: Path, new_content: str) -> str:
        """
        Generate delta (Δ) lines comparing new content with existing file.

        Args:
            old_path: Path to existing CTX-CARD file
            new_content: New CTX-CARD content

        Returns:
            Delta lines as string
        """
        if not old_path.exists():
            return ""

        try:
            old_content = old_path.read_text(encoding="utf-8", errors="replace")
            old_lines = [
                ln.rstrip("\n") for ln in old_content.splitlines() if ln.strip()
            ]
            new_lines = [
                ln.rstrip("\n") for ln in new_content.splitlines() if ln.strip()
            ]

            delta_lines = self._diff_lines(old_lines, new_lines)
            if delta_lines:
                return "\n" + "\n".join(delta_lines) + "\n"
        except Exception:
            pass

        return ""

    def _diff_lines(self, old: List[str], new: List[str]) -> List[str]:
        """Generate diff lines between old and new content."""
        old_set, new_set = set(old), set(new)
        added = [ln for ln in new if ln not in old_set]
        removed = [ln for ln in old if ln not in new_set]

        delta = []
        for ln in added:
            delta.append(f"DELTA: + {ln}")
        for ln in removed:
            delta.append(f"DELTA: - {ln}")

        return delta

    def render_per_package(
        self,
        root_card: str,
        modules: Dict[str, ModuleInfo],
        langs: List[str],
        std: str,
        proj: str,
    ) -> Dict[str, str]:
        """
        Generate per-package CTX-CARD files.

        Args:
            root_card: Root CTX-CARD content
            modules: Module information
            langs: Detected languages
            std: Coding standard
            proj: Project name

        Returns:
            Dict mapping package names to CTX-CARD content
        """
        # Group modules by top-level package
        packages = self._group_modules_by_package(modules)

        result = {}
        for pkg, pkg_modules in packages.items():
            if not pkg_modules:
                continue

            # Create package-specific CTX-CARD
            pkg_content = self._render_for_package(
                root_card, pkg, pkg_modules, langs, std, proj
            )
            result[pkg] = pkg_content

        return result

    def _group_modules_by_package(
        self, modules: Dict[str, ModuleInfo]
    ) -> Dict[str, List[ModuleInfo]]:
        """Group modules by their top-level package."""
        packages: Dict[str, List[ModuleInfo]] = {}

        for mi in modules.values():
            pkg = mi.dotted.split(".")[0] if mi.dotted else "root"
            packages.setdefault(pkg, []).append(mi)

        return packages

    def _render_for_package(
        self,
        root_card: str,
        _pkg: str,  # pylint: disable=unused-argument
        pkg_modules: List[ModuleInfo],
        _langs: List[str],  # pylint: disable=unused-argument
        _std: str,  # pylint: disable=unused-argument
        _proj: str,  # pylint: disable=unused-argument
    ) -> str:
        """Render CTX-CARD content for a specific package."""
        # Filter root card to only include relevant modules
        lines = root_card.splitlines()
        filtered_lines = []

        # Keep header lines
        for line in lines:
            if line.startswith(("ID:", "AL:", "NM:")):
                filtered_lines.append(line)
            elif line.startswith("MO:"):
                # Only include modules from this package
                module_id = line.split("|")[0].split("#")[1]
                if any(m.id == int(module_id) for m in pkg_modules):
                    filtered_lines.append(line)
            elif line.startswith(
                ("SY:", "SG:", "IN:", "MD:", "DT:", "ER:", "TK:", "ED:", "IO:", "PX:")
            ):
                # Only include if the module is in this package
                try:
                    parts = line.split("|")[0].split("#")
                    if len(parts) > 1:
                        module_id = parts[1].split(".")[0]
                        if any(m.id == int(module_id) for m in pkg_modules):
                            filtered_lines.append(line)
                except (IndexError, ValueError):
                    # Skip lines that don't have the expected format
                    continue
            elif line.startswith(("CN:", "RV:", "TY:")):
                filtered_lines.append(line)

        return "\n".join(filtered_lines) + "\n"

    def validate_output(self, content: str) -> None:
        """
        Validate CTX-CARD output format.

        Args:
            content: CTX-CARD content to validate

        Raises:
            ValidationError: If validation fails
        """
        lines = content.splitlines()

        # Check for required tags
        required_tags = {"ID:", "AL:", "NM:", "MO:", "SY:"}
        found_tags = set()

        for line in lines:
            if line.strip() and ":" in line:
                tag = line.split(":")[0] + ":"
                found_tags.add(tag)

        missing_tags = required_tags - found_tags
        if missing_tags:
            raise ValidationError(f"Missing required tags: {missing_tags}")

        # Validate ASCII-only
        if content != ascii_only(content):
            raise ValidationError("Output contains non-ASCII characters")

        # Validate prefix-free aliases
        alias_lines = [line for line in lines if line.startswith("AL:")]
        aliases = []
        for line in alias_lines:
            if "=>" in line:
                alias = line.split("=>")[0].split(":")[1].strip()
                aliases.append(alias)

        if aliases:
            _, invalid_aliases = validate_prefix_free(aliases)
            if invalid_aliases:
                raise ValidationError(f"Non-prefix-free aliases: {invalid_aliases}")
