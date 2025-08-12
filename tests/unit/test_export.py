"""
Tests for CTX-CARD export functionality.

This module tests the export utilities for CTX-CARD format conversion.
"""

import pytest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from ctxcard_gen.utils.export import (
    parse_ctx_card,
    export_to_json,
    export_to_yaml,
    export_to_xml,
    export_to_markdown,
)


class TestExportFunctions:
    """Test export utility functions."""

    def test_parse_ctx_card_basic(self):
        """Test basic CTX-CARD parsing."""
        content = """ID: proj|test lang|py std|pep8 ts|20241201
AL: cfg=>Configuration svc=>Service
NM: module | ^[a-z_]+$ | auth_service
MO: #1 | auth/service.py | {svc,auth}
SY: #1.#1 | cls | AuthService"""

        result = parse_ctx_card(content)

        assert "metadata" in result
        assert result["metadata"]["proj"] == "test"
        assert result["metadata"]["lang"] == "py"
        assert len(result["aliases"]) == 2
        assert len(result["modules"]) == 1
        assert len(result["symbols"]) == 1

    def test_parse_ctx_card_new_tags(self):
        """Test parsing of new tag types."""
        content = """ID: proj|test lang|py std|pep8 ts|20241201
DEPS: requests | external | HTTP client library
ENV: database_url | environment | config
SEC: AuthService | authentication | required
EVT: #1.#2 | event | login_event
ASYNC: #1.#2 | async | login_async"""

        result = parse_ctx_card(content)

        assert len(result["dependencies"]) == 1
        assert result["dependencies"][0]["name"] == "requests"
        assert len(result["environment"]) == 1
        assert result["environment"][0]["name"] == "database_url"
        assert len(result["security"]) == 1
        assert result["security"][0]["name"] == "AuthService"
        assert len(result["events"]) == 1
        assert result["events"][0]["name"] == "login_event"
        assert len(result["async_patterns"]) == 1
        assert result["async_patterns"][0]["name"] == "login_async"

    def test_parse_ctx_card_complex(self):
        """Test parsing of complex CTX-CARD content."""
        content = """ID: proj|complexApp lang|py,ts std|pep8,eslint ts|20241201

AL: cfg=>Configuration svc=>Service repo=>Repository
DEPS: fastapi | external | Web framework
ENV: database_url | environment | config
SEC: AuthService | authentication | required

NM: module | ^[a-z_]+$ | auth_service
NM: class  | ^[A-Z][A-Za-z0-9]+$ | AuthService

MO: #1 | auth/service.py | {svc,auth}
SY: #1.#1 | cls | AuthService
SY: #1.#2 | fn  | login

SG: #1.#2 | (UserCreds)->AuthToken !raises[AuthError]
ED: #1.#2 -> #2.#1 | calls

EVT: #1.#2 | event | login_event
ASYNC: #1.#2 | async | login_async

DT: UserCreds | {email:str,password:str}
TK: Role | {admin,staff,viewer}

ER: AuthError | domain | bad credentials
IN: login ⇒ requires(valid(creds)) ∧ ensures(token.exp>now)

CN: async fn end with _async
IO: POST /v1/login | UserCreds | AuthToken | 200,401,429

PX: forbid bare except | error-handling
EX: var(repo) => user_repo
RV: Check invariants (IN) on public fn"""

        result = parse_ctx_card(content)

        # Check all sections are parsed
        assert result["metadata"]["proj"] == "complexApp"
        assert len(result["aliases"]) == 3
        assert len(result["dependencies"]) == 1
        assert len(result["environment"]) == 1
        assert len(result["security"]) == 1
        assert len(result["naming"]) == 2
        assert len(result["modules"]) == 1
        assert len(result["symbols"]) == 2
        assert len(result["signatures"]) == 1
        assert len(result["edges"]) == 1
        assert len(result["events"]) == 1
        assert len(result["async_patterns"]) == 1
        assert len(result["data_types"]) == 1
        assert len(result["tokens"]) == 1
        assert len(result["errors"]) == 1
        assert len(result["invariants"]) == 1
        assert len(result["conventions"]) == 1
        assert len(result["io_contracts"]) == 1
        assert len(result["prohibited"]) == 1
        assert len(result["examples"]) == 1
        assert len(result["review"]) == 1

    def test_export_to_json(self):
        """Test JSON export functionality."""
        content = """ID: proj|test lang|py std|pep8 ts|20241201
AL: cfg=>Configuration
MO: #1 | auth/service.py | {svc,auth}
SY: #1.#1 | cls | AuthService"""

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.json"
            json_str = export_to_json(content, output_path)

            # Check file was created
            assert output_path.exists()

            # Check JSON is valid
            parsed_json = json.loads(json_str)
            assert "metadata" in parsed_json
            assert parsed_json["metadata"]["proj"] == "test"
            assert len(parsed_json["aliases"]) == 1
            assert len(parsed_json["modules"]) == 1
            assert len(parsed_json["symbols"]) == 1

    def test_export_to_yaml(self):
        """Test YAML export functionality."""
        content = """ID: proj|test lang|py std|pep8 ts|20241201
AL: cfg=>Configuration
MO: #1 | auth/service.py | {svc,auth}"""

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.yaml"
            yaml_str = export_to_yaml(content, output_path)

            # Check file was created
            assert output_path.exists()

            # Check YAML contains expected content
            assert "metadata:" in yaml_str
            assert "proj: test" in yaml_str
            assert "aliases:" in yaml_str

    def test_export_to_xml(self):
        """Test XML export functionality."""
        content = """ID: proj|test lang|py std|pep8 ts|20241201
AL: cfg=>Configuration
MO: #1 | auth/service.py | {svc,auth}"""

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.xml"
            xml_str = export_to_xml(content, output_path)

            # Check file was created
            assert output_path.exists()

            # Check XML contains expected content
            assert '<?xml version="1.0" encoding="UTF-8"?>' in xml_str
            assert "<ctxcard>" in xml_str
            assert "</ctxcard>" in xml_str
            assert "<metadata>" in xml_str
            assert "<proj>test</proj>" in xml_str

    def test_export_to_markdown(self):
        """Test Markdown export functionality."""
        content = """ID: proj|test lang|py std|pep8 ts|20241201
AL: cfg=>Configuration svc=>Service
DEPS: requests | external | HTTP client library
ENV: database_url | environment | config
SEC: AuthService | authentication | required
MO: #1 | auth/service.py | {svc,auth}
SY: #1.#1 | cls | AuthService
CN: async fn end with _async
RV: Check invariants (IN) on public fn"""

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.md"
            md_str = export_to_markdown(content, output_path)

            # Check file was created
            assert output_path.exists()

            # Check Markdown contains expected sections
            assert "# CTX-CARD Documentation" in md_str
            assert "## Project Information" in md_str
            assert "## Aliases" in md_str
            assert "## Dependencies" in md_str
            assert "## Environment Configuration" in md_str
            assert "## Security Constraints" in md_str
            assert "## Modules" in md_str
            assert "## Symbols" in md_str
            assert "## Coding Conventions" in md_str
            assert "## Review Checklist" in md_str

    def test_export_without_output_path(self):
        """Test export functions without output path."""
        content = """ID: proj|test lang|py std|pep8 ts|20241201
AL: cfg=>Configuration"""

        # Test JSON export without path
        json_str = export_to_json(content)
        assert json_str is not None
        parsed_json = json.loads(json_str)
        assert "metadata" in parsed_json

        # Test YAML export without path
        yaml_str = export_to_yaml(content)
        assert yaml_str is not None
        assert "metadata:" in yaml_str

        # Test XML export without path
        xml_str = export_to_xml(content)
        assert xml_str is not None
        assert "<ctxcard>" in xml_str

        # Test Markdown export without path
        md_str = export_to_markdown(content)
        assert md_str is not None
        assert "# CTX-CARD Documentation" in md_str

    def test_parse_edge_cases(self):
        """Test parsing of edge cases and malformed content."""
        content = """ID: proj|test lang|py std|pep8 ts|20241201
# This is a comment
AL: cfg=>Configuration
INVALID: some invalid content
MO: #1 | auth/service.py | {svc,auth}
SY: #1.#1 | cls | AuthService
"""

        result = parse_ctx_card(content)

        # Should parse valid content and ignore invalid
        assert result["metadata"]["proj"] == "test"
        assert len(result["aliases"]) == 1
        assert len(result["modules"]) == 1
        assert len(result["symbols"]) == 1

    def test_parse_empty_content(self):
        """Test parsing of empty content."""
        result = parse_ctx_card("")

        # Should return empty structure
        assert result["metadata"] == {}
        assert result["aliases"] == []
        assert result["modules"] == []
        assert result["symbols"] == []

    def test_parse_comments_only(self):
        """Test parsing of content with only comments."""
        content = """# This is a comment
# Another comment
# No actual CTX-CARD content"""

        result = parse_ctx_card(content)

        # Should return empty structure
        assert result["metadata"] == {}
        assert result["aliases"] == []
        assert result["modules"] == []
        assert result["symbols"] == []
