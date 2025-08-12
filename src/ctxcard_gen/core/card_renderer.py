"""
CTX-CARD renderer for CTX-CARD generator.

This module handles CTX-CARD format generation with all advanced features.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ..exceptions import ValidationError
from ..types import ModuleInfo, ScanResult
from ..utils.helpers import ascii_only, today_stamp
from ..utils.validation import validate_prefix_free


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
        proj: str,
        langs: List[str],
        std: str,
        modules: Dict[str, ModuleInfo],
        emit_ty: bool = False,
    ) -> str:
        """
        Render CTX-CARD format output.

        Args:
            proj: Project name
            langs: Detected languages
            std: Coding standard
            modules: Module information
            emit_ty: Whether to emit TY lines

        Returns:
            CTX-CARD formatted string
        """
        lines: List[str] = []

        # ID line
        lines.append(
            f"ID: proj|{proj} lang|{','.join(langs)} std|{std} ts|{today_stamp()}"
        )

        # AL lines (aliases)
        for al in self.HEADER_ALIASES:
            lines.append(f"AL: {al}")

        # NM lines (naming grammar)
        for scope, regex, example in self.NAMING_GRAMMAR_DEFAULT:
            lines.append(f"NM: {scope} | {regex} | {example}")

        # Sort modules by ID for deterministic output
        mlist = sorted(modules.values(), key=lambda m: m.id)

        # MO lines (modules)
        for m in mlist:
            tags = "{" + ",".join(sorted(m.role_tags)) + "}"
            lines.append(f"MO: #{m.id} | {m.path} | {tags}")

        # SY, SG, IN, MD lines (symbols, signatures, invariants, modifiers)
        for m in mlist:
            for s in m.symbols:
                lines.append(f"SY: #{m.id}.#{s.sid} | {s.kind} | {s.name}")

                if s.kind == "fn" and s.signature:
                    # Add raises information if available
                    raises_part = f" !raises[{','.join(s.raises)}]" if s.raises else ""
                    lines.append(f"SG: #{m.id}.#{s.sid} | {s.signature}{raises_part}")

                if s.invariants:
                    lines.append(f"IN: {s.name} ⇒ {s.invariants}")

                if s.modifiers:
                    lines.append(
                        f"MD: #{m.id}.#{s.sid} | {{{','.join(sorted(s.modifiers))}}}"
                    )

        # DT lines (data transfer objects)
        for m in mlist:
            for name, fields in m.dts:
                field_s = ",".join(f"{k}:{v}" for k, v in fields.items())
                lines.append(f"DT: {name} | {{{field_s}}}")

        # ER lines (errors)
        for m in mlist:
            for name, category, meaning in m.errors:
                lines.append(f"ER: {name} | {category} | {meaning}")

        # TK lines (tokens/enums)
        for m in mlist:
            for name, keys in m.tokens:
                keys_s = ",".join(keys)
                lines.append(f"TK: {name} | {{{keys_s}}}")

        # ED lines (edges - imports)
        for m in mlist:
            for dep_path in sorted(m.imports_paths):
                dep = modules.get(dep_path)
                if dep:
                    lines.append(f"ED: #{m.id}.#0 -> #{dep.id}.#0 | imports")

        # ED lines (edges - calls)
        for m in mlist:
            for caller_sid, (t_mid, t_sid) in m.calls:
                lines.append(f"ED: #{m.id}.#{caller_sid} -> #{t_mid}.#{t_sid} | calls")

        # IO lines (API contracts)
        for m in mlist:
            for sid, verb, path_s, codes in m.routes:
                codes_s = ",".join(codes)
                fn = next((s for s in m.symbols if s.sid == sid), None)
                sig = fn.signature if fn else "(…)->Any"
                in_sig = sig.split(")->")[0].lstrip("(") if ")->" in sig else ""
                out_sig = sig.split(")->")[-1] if ")->" in sig else "Any"
                lines.append(f"IO: {verb} {path_s} | {in_sig} | {out_sig} | {codes_s}")

        # PX lines (prohibited patterns)
        for m in mlist:
            for rule, reason in m.px:
                lines.append(f"PX: {rule} | {reason}")

        # CN lines (conventions)
        lines.append("CN: repos never import svc")
        lines.append("CN: async functions end with _async")

        # RV lines (review focus)
        lines.append("RV: public functions have signatures & docstrings")

        # TY lines (type signatures) - optional
        if emit_ty:
            self._append_ty_lines(lines, modules)

        # Ensure ASCII-only output
        result = "\n".join(lines) + "\n"
        return ascii_only(result)

    def _append_ty_lines(
        self, lines: List[str], modules: Dict[str, ModuleInfo]
    ) -> None:
        """Append TY lines for type signatures."""
        for m in modules.values():
            for s in m.symbols:
                if s.kind == "fn" and s.signature:
                    raises_part = f" !raises[{','.join(s.raises)}]" if s.raises else ""
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
        pkg: str,
        pkg_modules: List[ModuleInfo],
        langs: List[str],
        std: str,
        proj: str,
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
            valid_aliases, invalid_aliases = validate_prefix_free(aliases)
            if invalid_aliases:
                raise ValidationError(f"Non-prefix-free aliases: {invalid_aliases}")
