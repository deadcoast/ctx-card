"""
Unit tests for the card renderer.
"""

from pathlib import Path
from typing import Dict

import pytest

from ctxcard_gen.core.card_renderer import CardRenderer
from ctxcard_gen.exceptions import ValidationError
from ctxcard_gen.types import ModuleInfo, Symbol


class TestCardRenderer:
    """Test cases for CardRenderer."""

    def test_render_card_basic(self, sample_modules: Dict[str, ModuleInfo]):
        """Test basic CTX-CARD rendering."""
        renderer = CardRenderer()

        content = renderer.render_card(
            "test-project", ["py"], "pep8", sample_modules, emit_ty=False
        )

        # Check that content was generated
        assert content is not None
        assert len(content) > 0

        # Check for required sections
        lines = content.splitlines()
        assert any(line.startswith("ID:") for line in lines)
        assert any(line.startswith("AL:") for line in lines)
        assert any(line.startswith("NM:") for line in lines)
        assert any(line.startswith("MO:") for line in lines)
        assert any(line.startswith("SY:") for line in lines)

    def test_render_card_with_type_signatures(
        self, sample_modules: Dict[str, ModuleInfo]
    ):
        """Test CTX-CARD rendering with type signatures."""
        renderer = CardRenderer()

        content = renderer.render_card(
            "test-project", ["py"], "pep8", sample_modules, emit_ty=True
        )

        # Check that TY lines were included
        lines = content.splitlines()
        assert any(line.startswith("TY:") for line in lines)

    def test_render_card_with_raises(self, sample_modules: Dict[str, ModuleInfo]):
        """Test CTX-CARD rendering with raises information."""
        renderer = CardRenderer()

        # Add raises information to a symbol
        for mi in sample_modules.values():
            for symbol in mi.symbols:
                if symbol.kind == "fn":
                    symbol.raises = ["AuthError", "ValidationError"]
                    break

        content = renderer.render_card(
            "test-project", ["py"], "pep8", sample_modules, emit_ty=False
        )

        # Check that raises information was included
        lines = content.splitlines()
        sg_lines = [line for line in lines if line.startswith("SG:")]
        assert any("!raises[" in line for line in sg_lines)

    def test_render_card_with_modifiers(self, sample_modules: Dict[str, ModuleInfo]):
        """Test CTX-CARD rendering with method modifiers."""
        renderer = CardRenderer()

        # Add modifiers to a symbol
        for mi in sample_modules.values():
            for symbol in mi.symbols:
                if symbol.kind == "fn":
                    symbol.modifiers = {"classmethod", "staticmethod"}
                    break

        content = renderer.render_card(
            "test-project", ["py"], "pep8", sample_modules, emit_ty=False
        )

        # Check that modifiers were included
        lines = content.splitlines()
        md_lines = [line for line in lines if line.startswith("MD:")]
        assert len(md_lines) > 0
        assert any("{classmethod,staticmethod}" in line for line in md_lines)

    def test_render_card_with_dtos(self, sample_modules: Dict[str, ModuleInfo]):
        """Test CTX-CARD rendering with DTOs."""
        renderer = CardRenderer()

        content = renderer.render_card(
            "test-project", ["py"], "pep8", sample_modules, emit_ty=False
        )

        # Check that DTO lines were included
        lines = content.splitlines()
        dt_lines = [line for line in lines if line.startswith("DT:")]
        assert len(dt_lines) > 0

    def test_render_card_with_errors(self, sample_modules: Dict[str, ModuleInfo]):
        """Test CTX-CARD rendering with errors."""
        renderer = CardRenderer()

        content = renderer.render_card(
            "test-project", ["py"], "pep8", sample_modules, emit_ty=False
        )

        # Check that error lines were included
        lines = content.splitlines()
        er_lines = [line for line in lines if line.startswith("ER:")]
        assert len(er_lines) > 0

    def test_render_card_with_routes(self, sample_modules: Dict[str, ModuleInfo]):
        """Test CTX-CARD rendering with API routes."""
        renderer = CardRenderer()

        content = renderer.render_card(
            "test-project", ["py"], "pep8", sample_modules, emit_ty=False
        )

        # Check that route lines were included
        lines = content.splitlines()
        io_lines = [line for line in lines if line.startswith("IO:")]
        assert len(io_lines) > 0

    def test_render_card_with_linting(self, sample_modules: Dict[str, ModuleInfo]):
        """Test CTX-CARD rendering with linting violations."""
        renderer = CardRenderer()

        content = renderer.render_card(
            "test-project", ["py"], "pep8", sample_modules, emit_ty=False
        )

        # Check that linting lines were included
        lines = content.splitlines()
        px_lines = [line for line in lines if line.startswith("PX:")]
        assert len(px_lines) > 0

    def test_render_card_with_calls(self, sample_modules: Dict[str, ModuleInfo]):
        """Test CTX-CARD rendering with function calls."""
        renderer = CardRenderer()

        # Add some calls to the modules
        for mi in sample_modules.values():
            if "service.py" in mi.path:
                mi.calls = [(2, (2, 1))]  # Call from symbol 2 to module 2, symbol 1
                break

        content = renderer.render_card(
            "test-project", ["py"], "pep8", sample_modules, emit_ty=False
        )

        # Check that call lines were included
        lines = content.splitlines()
        call_lines = [line for line in lines if line.endswith("| calls")]
        assert len(call_lines) > 0

    def test_generate_delta_new_file(self, tmp_path: Path):
        """Test delta generation with new file."""
        renderer = CardRenderer()

        new_content = (
            "ID: proj|test lang|py std|pep8 ts|20241201\nAL: cfg=>Configuration"
        )
        old_path = tmp_path / "nonexistent.md"

        delta = renderer.generate_delta(old_path, new_content)

        # Should return empty string for non-existent file
        assert delta == ""

    def test_generate_delta_with_changes(
        self, tmp_path: Path, old_ctxcard_content: str
    ):
        """Test delta generation with actual changes."""
        renderer = CardRenderer()

        # Write old content to file
        old_path = tmp_path / "old.md"
        old_path.write_text(old_ctxcard_content)

        # Create new content with changes
        new_content = old_ctxcard_content + "\nSY: #1.#2 | fn | new_function\n"

        delta = renderer.generate_delta(old_path, new_content)

        # Check that delta was generated
        assert delta is not None
        assert len(delta) > 0

        # Check for delta lines
        delta_lines = delta.splitlines()
        assert any(line.startswith("DELTA: +") for line in delta_lines)

    def test_generate_delta_with_removals(
        self, tmp_path: Path, old_ctxcard_content: str
    ):
        """Test delta generation with removals."""
        renderer = CardRenderer()

        # Write old content to file
        old_path = tmp_path / "old.md"
        old_path.write_text(old_ctxcard_content)

        # Create new content with removals
        lines = old_ctxcard_content.splitlines()
        new_content = "\n".join(lines[:-2])  # Remove last two lines

        delta = renderer.generate_delta(old_path, new_content)

        # Check that delta was generated
        assert delta is not None
        assert len(delta) > 0

        # Check for removal lines
        delta_lines = delta.splitlines()
        assert any(line.startswith("DELTA: -") for line in delta_lines)

    def test_diff_lines(self):
        """Test diff line generation."""
        renderer = CardRenderer()

        old_lines = ["line1", "line2", "line3"]
        new_lines = ["line1", "line2", "line4"]

        delta_lines = renderer._diff_lines(old_lines, new_lines)

        # Check that differences were detected
        assert len(delta_lines) == 2
        assert any(line.startswith("DELTA: +") for line in delta_lines)
        assert any(line.startswith("DELTA: -") for line in delta_lines)

    def test_render_per_package(self, sample_modules: Dict[str, ModuleInfo]):
        """Test per-package CTX-CARD generation."""
        renderer = CardRenderer()

        # Create root content
        root_content = renderer.render_card(
            "test-project", ["py"], "pep8", sample_modules, emit_ty=False
        )

        # Generate per-package content
        packages = renderer.render_per_package(
            root_content, sample_modules, ["py"], "pep8", "test-project"
        )

        # Check that packages were generated
        assert len(packages) > 0

        # Check that each package has content
        for pkg, content in packages.items():
            assert content is not None
            assert len(content) > 0

            # Check that package content has required sections
            lines = content.splitlines()
            assert any(line.startswith("ID:") for line in lines)
            assert any(line.startswith("AL:") for line in lines)

    def test_group_modules_by_package(self, sample_modules: Dict[str, ModuleInfo]):
        """Test module grouping by package."""
        renderer = CardRenderer()

        packages = renderer._group_modules_by_package(sample_modules)

        # Check that modules were grouped
        assert len(packages) > 0

        # Check that each package has modules
        for pkg, modules in packages.items():
            assert len(modules) > 0

    def test_render_for_package(self, sample_modules: Dict[str, ModuleInfo]):
        """Test rendering for specific package."""
        renderer = CardRenderer()

        # Create root content
        root_content = renderer.render_card(
            "test-project", ["py"], "pep8", sample_modules, emit_ty=False
        )

        # Get modules for a specific package
        packages = renderer._group_modules_by_package(sample_modules)
        pkg_name = list(packages.keys())[0]
        pkg_modules = packages[pkg_name]

        # Render for package
        pkg_content = renderer._render_for_package(
            root_content, pkg_name, pkg_modules, ["py"], "pep8", "test-project"
        )

        # Check that package content was generated
        assert pkg_content is not None
        assert len(pkg_content) > 0

        # Check that it contains package-specific modules
        lines = pkg_content.splitlines()
        mo_lines = [line for line in lines if line.startswith("MO:")]
        assert len(mo_lines) > 0

    def test_validate_output_valid(self, sample_ctxcard_content: str):
        """Test output validation with valid content."""
        renderer = CardRenderer()

        # Should not raise an exception
        renderer.validate_output(sample_ctxcard_content)

    def test_validate_output_missing_tags(self):
        """Test output validation with missing required tags."""
        renderer = CardRenderer()

        invalid_content = """ID: proj|test lang|py std|pep8 ts|20241201
MO: #1 | test.py | {mod}
"""

        with pytest.raises(ValidationError, match="Missing required tags"):
            renderer.validate_output(invalid_content)

    def test_validate_output_non_ascii(self):
        """Test output validation with non-ASCII characters."""
        renderer = CardRenderer()

        non_ascii_content = """ID: proj|test lang|py std|pep8 ts|20241201
AL: cfg=>Configuration
NM: module | ^[a-z_]+$ | auth_service
MO: #1 | test.py | {mod}
SY: #1.#1 | cls | TestClass
CN: repos never import svc
RV: public functions have signatures & docstrings
"""

        # Add non-ASCII character
        non_ascii_content += "SY: #1.#2 | fn | test_функция\n"

        with pytest.raises(ValidationError, match="non-ASCII characters"):
            renderer.validate_output(non_ascii_content)

    def test_validate_output_prefix_free_aliases(self):
        """Test output validation with prefix-free aliases."""
        renderer = CardRenderer()

        # Valid aliases (prefix-free)
        valid_content = """ID: proj|test lang|py std|pep8 ts|20241201
AL: cfg=>Configuration
AL: svc=>Service
AL: repo=>Repository
NM: module | ^[a-z_]+$ | auth_service
MO: #1 | test.py | {mod}
SY: #1.#1 | cls | TestClass
CN: repos never import svc
RV: public functions have signatures & docstrings
"""

        # Should not raise an exception
        renderer.validate_output(valid_content)

    def test_validate_output_non_prefix_free_aliases(self):
        """Test output validation with non-prefix-free aliases."""
        renderer = CardRenderer()

        # Invalid aliases (not prefix-free)
        invalid_content = """ID: proj|test lang|py std|pep8 ts|20241201
AL: cfg=>Configuration
AL: cfg_svc=>Service
NM: module | ^[a-z_]+$ | auth_service
MO: #1 | test.py | {mod}
SY: #1.#1 | cls | TestClass
CN: repos never import svc
RV: public functions have signatures & docstrings
"""

        with pytest.raises(ValidationError, match="Non-prefix-free aliases"):
            renderer.validate_output(invalid_content)

    def test_append_ty_lines(self, sample_modules: Dict[str, ModuleInfo]):
        """Test appending type signature lines."""
        renderer = CardRenderer()

        lines = []

        # Add raises information to symbols
        for mi in sample_modules.values():
            for symbol in mi.symbols:
                if symbol.kind == "fn":
                    symbol.raises = ["AuthError"]
                    break

        renderer._append_ty_lines(lines, sample_modules)

        # Check that TY lines were added
        ty_lines = [line for line in lines if line.startswith("TY:")]
        assert len(ty_lines) > 0

        # Check that raises information was included
        assert any("!raises[" in line for line in ty_lines)

    def test_deterministic_output(self, sample_modules: Dict[str, ModuleInfo]):
        """Test that output is deterministic."""
        renderer = CardRenderer()

        # Generate content multiple times
        content1 = renderer.render_card(
            "test-project", ["py"], "pep8", sample_modules, emit_ty=False
        )

        content2 = renderer.render_card(
            "test-project", ["py"], "pep8", sample_modules, emit_ty=False
        )

        # Content should be identical
        assert content1 == content2

    def test_ascii_only_output(self, sample_modules: Dict[str, ModuleInfo]):
        """Test that output is ASCII-only."""
        renderer = CardRenderer()

        # Add non-ASCII content to modules
        for mi in sample_modules.values():
            for symbol in mi.symbols:
                if symbol.kind == "fn":
                    symbol.name = "test_функция"  # Non-ASCII
                    break

        content = renderer.render_card(
            "test-project", ["py"], "pep8", sample_modules, emit_ty=False
        )

        # Check that output is ASCII-only
        try:
            content.encode("ascii")
        except UnicodeEncodeError:
            pytest.fail("Output contains non-ASCII characters")
