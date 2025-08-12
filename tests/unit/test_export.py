"""
Unit tests for export module.

This module tests the CTX-CARD export functionality.
"""

import json

# Note: pytest import is handled by test runner
try:
    import pytest
except ImportError:
    pytest = None

from src.ctxcard_gen.utils.export import (
    parse_ctx_card,
    export_to_json,
    export_to_yaml,
    export_to_xml,
    export_to_markdown,
)


class TestExportFunctions:
    """Test cases for export functionality."""

    def test_parse_ctx_card_basic(self):
        """Test basic CTX-CARD parsing."""
        content = """ID: proj|test-project lang|py std|pep8 ts|20241201
AL: cfg=>Configuration
AL: svc=>Service
NM: module | ^[a-z_]+$ | auth_service
MO: #1 | main_pkg/service.py | {svc}
SY: #1.#1 | cls | AuthService
CN: repos never import svc
RV: public functions have signatures & docstrings
"""

        result = parse_ctx_card(content)

        assert result["metadata"]["project"] == "test-project"
        assert result["metadata"]["languages"] == ["py"]
        assert len(result["aliases"]) == 2
        assert len(result["modules"]) == 1
        assert len(result["symbols"]) == 1

    def test_parse_ctx_card_new_tags(self):
        """Test parsing with new CTX-CARD tags."""
        content = """ID: proj|test-project lang|py std|pep8 ts|20241201
DEPS: database | external | PostgreSQL database connection
ENV: DATABASE_URL | config | Database connection string
SEC: auth_required | access | Authentication required for all endpoints
EVT: user_created | notification | User creation event
ASYNC: async_handler | pattern | Async event handler pattern
"""

        result = parse_ctx_card(content)

        assert len(result["dependencies"]) == 1
        assert len(result["environment"]) == 1
        assert len(result["security"]) == 1
        assert len(result["events"]) == 1
        assert len(result["async_patterns"]) == 1

    def test_parse_ctx_card_complex(self):
        """Test parsing complex CTX-CARD content."""
        content = """ID: proj|complex-project lang|py,js std|pep8,eslint ts|20241201
AL: cfg=>Configuration
AL: svc=>Service
AL: repo=>Repository
AL: api=>API
NM: module | ^[a-z_]+$ | auth_service
NM: class  | ^[A-Z][A-Za-z0-9]+$ | AuthService
MO: #1 | main_pkg/service.py | {svc}
MO: #2 | main_pkg/repository.py | {repo}
MO: #3 | api/routes.py | {api}
SY: #1.#1 | cls | AuthService
SY: #1.#2 | fn | AuthService.login
SY: #2.#1 | cls | UserRepository
SY: #3.#1 | fn | login_route
DEPS: database | external | PostgreSQL database
ENV: DATABASE_URL | config | Database connection string
SEC: auth_required | access | Authentication required
EVT: user_created | notification | User creation event
ASYNC: async_handler | pattern | Async event handler
CN: repos never import svc
RV: public functions have signatures & docstrings
"""

        result = parse_ctx_card(content)

        assert result["metadata"]["project"] == "complex-project"
        assert "py" in result["metadata"]["languages"]
        assert "js" in result["metadata"]["languages"]
        assert len(result["aliases"]) == 4
        assert len(result["modules"]) == 3
        assert len(result["symbols"]) == 4
        assert len(result["dependencies"]) == 1
        assert len(result["environment"]) == 1
        assert len(result["security"]) == 1
        assert len(result["events"]) == 1
        assert len(result["async_patterns"]) == 1
        assert len(result["conventions"]) == 1
        assert len(result["review_items"]) == 1

    def test_export_to_json(self):
        """Test JSON export."""
        content = """ID: proj|test-project lang|py std|pep8 ts|20241201
AL: cfg=>Configuration
MO: #1 | main.py | {mod}
SY: #1.#1 | fn | main
"""

        result = export_to_json(content)

        assert result is not None
        parsed = json.loads(result)
        assert parsed["metadata"]["project"] == "test-project"

    def test_export_to_yaml(self):
        """Test YAML export."""
        content = """ID: proj|test-project lang|py std|pep8 ts|20241201
AL: cfg=>Configuration
MO: #1 | main.py | {mod}
SY: #1.#1 | fn | main
"""

        result = export_to_yaml(content)

        assert result is not None
        assert "project: test-project" in result

    def test_export_to_xml(self):
        """Test XML export."""
        content = """ID: proj|test-project lang|py std|pep8 ts|20241201
AL: cfg=>Configuration
MO: #1 | main.py | {mod}
SY: #1.#1 | fn | main
"""

        result = export_to_xml(content)

        assert result is not None
        assert "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" in result
        assert "<ctxcard>" in result
        assert "<project>test-project</project>" in result

    def test_export_to_markdown(self):
        """Test Markdown export."""
        content = """ID: proj|test-project lang|py std|pep8 ts|20241201
AL: cfg=>Configuration
MO: #1 | main.py | {mod}
SY: #1.#1 | fn | main
"""

        result = export_to_markdown(content)

        assert result is not None
        assert "# CTX-CARD Documentation" in result
        assert "## Project Information" in result
        assert "## Aliases" in result

    def test_export_without_output_path(self):
        """Test export without specifying output path."""
        content = """ID: proj|test-project lang|py std|pep8 ts|20241201
AL: cfg=>Configuration
"""

        # Test all export formats without output path
        json_result = export_to_json(content)
        yaml_result = export_to_yaml(content)
        xml_result = export_to_xml(content)
        md_result = export_to_markdown(content)

        assert json_result is not None
        assert yaml_result is not None
        assert xml_result is not None
        assert md_result is not None

    def test_parse_edge_cases(self):
        """Test parsing edge cases."""
        # Empty content
        result = parse_ctx_card("")
        assert not result["metadata"]
        assert not result["aliases"]
        assert not result["modules"]
        assert not result["symbols"]

        # Content with only comments
        result = parse_ctx_card("# This is a comment\n# Another comment")
        assert not result["metadata"]
        assert not result["aliases"]
        assert not result["modules"]
        assert not result["symbols"]

        # Content with malformed lines
        content = """ID: proj|test-project lang|py std|pep8 ts|20241201
AL: cfg=>Configuration
MO: #1 | main.py | {mod}
SY: #1.#1 | fn | main
INVALID: line
"""
        result = parse_ctx_card(content)
        # Should handle malformed lines gracefully
        assert result["metadata"]["project"] == "test-project"

    def test_parse_empty_content(self):
        """Test parsing empty content."""
        result = parse_ctx_card("")

        assert not result["metadata"]
        assert not result["aliases"]
        assert not result["modules"]
        assert not result["symbols"]
        assert not result["dependencies"]
        assert not result["environment"]
        assert not result["security"]
        assert not result["events"]
        assert not result["async_patterns"]
        assert not result["conventions"]
        assert not result["review_items"]

    def test_parse_comments_only(self):
        """Test parsing content with only comments."""
        content = """# This is a comment
# Another comment
# Yet another comment
"""
        result = parse_ctx_card(content)

        assert not result["metadata"]
        assert not result["aliases"]
        assert not result["modules"]
        assert not result["symbols"]
        assert not result["dependencies"]
        assert not result["environment"]
        assert not result["security"]
        assert not result["events"]
        assert not result["async_patterns"]
        assert not result["conventions"]
        assert not result["review_items"]
