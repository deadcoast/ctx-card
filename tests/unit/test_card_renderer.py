"""
Unit tests for card renderer module.

This module tests the CTX-CARD rendering functionality.
"""

from pathlib import Path

# Note: pytest import is handled by test runner
try:
    import pytest
except ImportError:
    pytest = None

from src.ctxcard_gen.core.card_renderer import CardRenderer
from src.ctxcard_gen.types import ModuleInfo, Symbol


class TestCardRenderer:
    """Test cases for card renderer functionality."""

    def test_init(self):
        """Test card renderer initialization."""
        renderer = CardRenderer()
        assert renderer is not None

    def test_render_card_basic(self):
        """Test basic card rendering."""
        renderer = CardRenderer()
        modules = {
            "test_module.py": ModuleInfo(
                id=1,
                path="test_module.py",
                dotted="test_module",
                symbols=[
                    Symbol(
                        mid=1,
                        sid=1,
                        kind="fn",
                        name="test_function",
                    )
                ],
                role_tags=set(),
            )
        }

        content = renderer.render_card(
            "test-project",
            ["py"],
            "pep8",
            modules,
            emit_type_signatures=False,
        )

        assert content is not None
        assert len(content) > 0
        assert "ID:" in content
        assert "proj|test-project" in content

    def test_render_card_with_type_signatures(self):
        """Test card rendering with type signatures."""
        renderer = CardRenderer()
        modules = {
            "test_module.py": ModuleInfo(
                id=1,
                path="test_module.py",
                dotted="test_module",
                symbols=[
                    Symbol(
                        mid=1,
                        sid=1,
                        kind="fn",
                        name="test_function",
                        signature="(arg: str) -> str",
                    )
                ],
                role_tags=set(),
            )
        }

        content = renderer.render_card(
            "test-project",
            ["py"],
            "pep8",
            modules,
            emit_type_signatures=True,
        )

        assert content is not None
        assert len(content) > 0
        assert "TY:" in content

    def test_render_card_with_classes(self):
        """Test card rendering with classes."""
        renderer = CardRenderer()
        modules = {
            "test_module.py": ModuleInfo(
                id=1,
                path="test_module.py",
                dotted="test_module",
                symbols=[
                    Symbol(
                        mid=1,
                        sid=1,
                        kind="cls",
                        name="TestClass",
                    ),
                    Symbol(
                        mid=1,
                        sid=2,
                        kind="fn",
                        name="TestClass.method",
                    ),
                ],
                role_tags=set(),
            )
        }

        content = renderer.render_card(
            "test-project",
            ["py"],
            "pep8",
            modules,
            emit_type_signatures=False,
        )

        assert content is not None
        assert "TestClass" in content

    def test_render_card_with_properties(self):
        """Test card rendering with properties."""
        renderer = CardRenderer()
        modules = {
            "test_module.py": ModuleInfo(
                id=1,
                path="test_module.py",
                dotted="test_module",
                symbols=[
                    Symbol(
                        mid=1,
                        sid=1,
                        kind="prop",
                        name="TestClass.property",
                    )
                ],
                role_tags=set(),
            )
        }

        content = renderer.render_card(
            "test-project",
            ["py"],
            "pep8",
            modules,
            emit_type_signatures=False,
        )

        assert content is not None
        assert "property" in content

    def test_render_card_with_decorators(self):
        """Test card rendering with decorators."""
        renderer = CardRenderer()
        modules = {
            "test_module.py": ModuleInfo(
                id=1,
                path="test_module.py",
                dotted="test_module",
                symbols=[
                    Symbol(
                        mid=1,
                        sid=1,
                        kind="fn",
                        name="test_function",
                        deco=["property"],
                    )
                ],
                role_tags=set(),
            )
        }

        content = renderer.render_card(
            "test-project",
            ["py"],
            "pep8",
            modules,
            emit_type_signatures=False,
        )

        assert content is not None
        assert "property" in content

    def test_render_card_with_exceptions(self):
        """Test card rendering with exceptions."""
        renderer = CardRenderer()
        modules = {
            "test_module.py": ModuleInfo(
                id=1,
                path="test_module.py",
                dotted="test_module",
                symbols=[
                    Symbol(
                        mid=1,
                        sid=1,
                        kind="fn",
                        name="test_function",
                        raises=["ValueError", "TypeError"],
                    )
                ],
                role_tags=set(),
            )
        }

        content = renderer.render_card(
            "test-project",
            ["py"],
            "pep8",
            modules,
            emit_type_signatures=False,
        )

        assert content is not None
        assert "ValueError" in content or "TypeError" in content

    def test_render_card_with_role_tags(self):
        """Test card rendering with role tags."""
        renderer = CardRenderer()
        modules = {
            "test_module.py": ModuleInfo(
                id=1,
                path="test_module.py",
                dotted="test_module",
                symbols=[
                    Symbol(
                        mid=1,
                        sid=1,
                        kind="fn",
                        name="test_function",
                    )
                ],
                role_tags={"service", "api"},
            )
        }

        content = renderer.render_card(
            "test-project",
            ["py"],
            "pep8",
            modules,
            emit_type_signatures=False,
        )

        assert content is not None
        assert "service" in content or "api" in content

    def test_render_card_empty_modules(self):
        """Test card rendering with empty modules."""
        renderer = CardRenderer()
        modules = {}

        content = renderer.render_card(
            "test-project",
            ["py"],
            "pep8",
            modules,
            emit_type_signatures=False,
        )

        assert content is not None
        assert len(content) > 0
        assert "ID:" in content

    def test_render_card_multiple_languages(self):
        """Test card rendering with multiple languages."""
        renderer = CardRenderer()
        modules = {
            "test_module.py": ModuleInfo(
                id=1,
                path="test_module.py",
                dotted="test_module",
                symbols=[],
                role_tags=set(),
            )
        }

        content = renderer.render_card(
            "test-project",
            ["py", "js"],
            "pep8",
            modules,
            emit_type_signatures=False,
        )

        assert content is not None
        assert "py" in content
        assert "js" in content

    def test_generate_delta_empty(self):
        """Test delta generation with empty content."""
        renderer = CardRenderer()

        delta = renderer.generate_delta(Path("nonexistent.md"), "new content")
        assert delta is not None

    def test_generate_delta_with_changes(self):
        """Test delta generation with actual changes."""
        renderer = CardRenderer()

        new_content = """ID: proj|test-project lang|py std|pep8 ts|20241201
AL: new=>NewAlias
MO: #1 | new_module.py | {new}
SY: #1.#1 | fn | new_function
"""

        delta = renderer.generate_delta(Path("nonexistent.md"), new_content)
        assert delta is not None

    def test_group_modules_by_package(self):
        """Test grouping modules by package."""
        renderer = CardRenderer()
        modules = {
            "pkg1/module1.py": ModuleInfo(
                id=1,
                path="pkg1/module1.py",
                dotted="pkg1.module1",
                symbols=[],
                role_tags=set(),
            ),
            "pkg1/module2.py": ModuleInfo(
                id=2,
                path="pkg1/module2.py",
                dotted="pkg1.module2",
                symbols=[],
                role_tags=set(),
            ),
            "pkg2/module3.py": ModuleInfo(
                id=3,
                path="pkg2/module3.py",
                dotted="pkg2.module3",
                symbols=[],
                role_tags=set(),
            ),
        }

        packages = renderer._group_modules_by_package(modules)  # pylint: disable=protected-access
        assert "pkg1" in packages
        assert "pkg2" in packages
        assert len(packages["pkg1"]) == 2
        assert len(packages["pkg2"]) == 1

    def test_render_for_package(self):
        """Test rendering for specific package."""
        renderer = CardRenderer()
        package_modules = [
            ModuleInfo(
                id=1,
                path="pkg1/module1.py",
                dotted="pkg1.module1",
                symbols=[],
                role_tags=set(),
            ),
            ModuleInfo(
                id=2,
                path="pkg1/module2.py",
                dotted="pkg1.module2",
                symbols=[],
                role_tags=set(),
            ),
        ]

        # Create a simple root card
        root_card = """ID: proj|test-project lang|py std|pep8 ts|20241201
AL: test=>TestAlias
MO: #1 | pkg1/module1.py | {test}
MO: #2 | pkg1/module2.py | {test}
SY: #1.#1 | fn | test_function
"""

        content = renderer._render_for_package(  # pylint: disable=protected-access
            root_card,
            "pkg1",
            package_modules,
            ["py"],
            "pep8",
            "test-project",
        )

        assert content is not None
        assert "pkg1" in content

    def test_append_ty_lines(self):
        """Test appending type signature lines."""
        renderer = CardRenderer()
        lines = []
        symbol = Symbol(
            mid=1,
            sid=1,
            kind="fn",
            name="test_function",
            signature="(arg: str) -> str",
        )

        renderer._append_ty_lines(lines, symbol)  # pylint: disable=protected-access
        assert len(lines) > 0
        assert any("TY:" in line for line in lines)
