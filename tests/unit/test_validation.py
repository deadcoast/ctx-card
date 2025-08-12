"""
Tests for CTX-CARD validation functions.

This module tests the validation utilities for CTX-CARD format compliance.
"""

from pathlib import Path
import pytest

from ctxcard_gen.utils.validation import (
    validate_prefix_free,
    validate_regex_patterns,
    validate_indices,
    validate_edges,
    validate_ctx_card_structure,
    validate_ascii_compliance,
    validate_semantic_tokens,
    validate_cross_references,
    get_validation_report,
)


class TestValidationFunctions:
    """Test validation utility functions."""

    def test_validate_prefix_free_valid(self):
        """Test prefix-free validation with valid aliases."""
        aliases = ["cfg", "svc", "repo", "dto"]
        valid, invalid = validate_prefix_free(aliases)

        assert len(valid) == 4
        assert len(invalid) == 0
        assert set(valid) == {"cfg", "svc", "repo", "dto"}

    def test_validate_prefix_free_invalid(self):
        """Test prefix-free validation with invalid aliases."""
        aliases = ["cfg", "config", "svc", "service"]
        valid, invalid = validate_prefix_free(aliases)

        assert len(valid) == 2
        assert len(invalid) == 2
        assert "config" in invalid  # prefix of "config"
        assert "service" in invalid  # prefix of "service"

    def test_validate_regex_patterns_valid(self):
        """Test regex pattern validation with valid patterns."""
        patterns = [r"^[a-z_]+$", r"^[A-Z][A-Za-z0-9]+$", r"\d+"]
        valid, invalid = validate_regex_patterns(patterns)

        assert len(valid) == 3
        assert len(invalid) == 0

    def test_validate_regex_patterns_invalid(self):
        """Test regex pattern validation with invalid patterns."""
        patterns = [r"^[a-z_]+$", r"[invalid", r"^[A-Z][A-Za-z0-9]+$"]
        valid, invalid = validate_regex_patterns(patterns)

        assert len(valid) == 2
        assert len(invalid) == 1
        assert "[invalid" in invalid

    def test_validate_ctx_card_structure_valid(self):
        """Test CTX-CARD structure validation with valid content."""
        content = """ID: proj|test lang|py std|pep8 ts|20241201
AL: cfg=>Configuration svc=>Service
NM: module | ^[a-z_]+$ | auth_service
MO: #1 | auth/service.py | {svc,auth}
SY: #1.#1 | cls | AuthService"""

        is_valid, errors = validate_ctx_card_structure(content)

        assert is_valid
        assert len(errors) == 0

    def test_validate_ctx_card_structure_invalid(self):
        """Test CTX-CARD structure validation with invalid content."""
        content = """ID: proj|test lang|py std|pep8 ts|20241201
INVALID: some content
MO: #1 | auth/service.py | {svc,auth}"""

        is_valid, errors = validate_ctx_card_structure(content)

        assert not is_valid
        assert len(errors) > 0
        assert any("Invalid tag format" in error for error in errors)

    def test_validate_ctx_card_structure_missing_required(self):
        """Test CTX-CARD structure validation with missing required tags."""
        content = """AL: cfg=>Configuration svc=>Service
MO: #1 | auth/service.py | {svc,auth}"""

        is_valid, errors = validate_ctx_card_structure(content)

        assert not is_valid
        assert len(errors) > 0
        assert any("Missing required tags" in error for error in errors)

    def test_validate_ascii_compliance_valid(self):
        """Test ASCII compliance validation with valid content."""
        content = "ID: proj|test lang|py std|pep8 ts|20241201"

        is_valid, errors = validate_ascii_compliance(content)

        assert is_valid
        assert len(errors) == 0

    def test_validate_ascii_compliance_invalid(self):
        """Test ASCII compliance validation with non-ASCII content."""
        content = "ID: proj|test lang|py std|pep8 ts|20241201\nAL: cfg=>Configurätion"

        is_valid, errors = validate_ascii_compliance(content)

        assert not is_valid
        assert len(errors) > 0
        assert any("Non-ASCII characters" in error for error in errors)

    def test_validate_semantic_tokens(self):
        """Test semantic token generation."""
        content = """ID: proj|test lang|py std|pep8 ts|20241201
AL: cfg=>Configuration svc=>Service
MO: #1 | auth/service.py | {svc,auth}"""

        tokens = validate_semantic_tokens(content)

        assert len(tokens) > 0
        assert all("line" in token for token in tokens)
        assert all("start" in token for token in tokens)
        assert all("length" in token for token in tokens)
        assert all("tokenType" in token for token in tokens)

    def test_validate_cross_references_valid(self):
        """Test cross-reference validation with valid references."""
        content = "SY: #1.#1 | cls | AuthService\nED: #1.#1 -> #2.#1 | calls"

        is_valid, errors = validate_cross_references(content)

        assert is_valid
        assert len(errors) == 0

    def test_validate_cross_references_invalid(self):
        """Test cross-reference validation with malformed references."""
        content = "SY: #1.#1 | cls | AuthService\nED: #1.#1->#2.#1 | calls"

        is_valid, errors = validate_cross_references(content)

        assert not is_valid
        assert len(errors) > 0
        assert any("Malformed index references" in error for error in errors)

    def test_get_validation_report_complete(self):
        """Test comprehensive validation report generation."""
        content = """ID: proj|test lang|py std|pep8 ts|20241201
AL: cfg=>Configuration svc=>Service
NM: module | ^[a-z_]+$ | auth_service
MO: #1 | auth/service.py | {svc,auth}
SY: #1.#1 | cls | AuthService"""

        report = get_validation_report(content)

        assert "valid" in report
        assert "errors" in report
        assert "warnings" in report
        assert "semantic_tokens" in report
        assert report["valid"]
        assert len(report["errors"]) == 0

    def test_get_validation_report_with_errors(self):
        """Test validation report with errors."""
        content = """ID: proj|test lang|py std|pep8 ts|20241201
INVALID: some content
MO: #1 | auth/service.py | {svc,auth}"""

        report = get_validation_report(content)

        assert not report["valid"]
        assert len(report["errors"]) > 0
        assert len(report["semantic_tokens"]) > 0


class TestValidationIntegration:
    """Test validation integration with real CTX-CARD content."""

    def test_complete_ctx_card_validation(self):
        """Test validation of a complete CTX-CARD example."""
        content = """ID: proj|milkBottle lang|py std|pep8 ts|20250808

AL: cfg=>Configuration svc=>Service repo=>Repository dto=>DataTransferObject
AL: uc=>UseCase http=>HTTP db=>Database jwt=>JWT

NM: module | ^[a-z_]+$ | auth_service
NM: class  | ^[A-Z][A-Za-z0-9]+$ | AuthService
NM: func   | ^[a-z_]+$ | issue_token
NM: var    | ^[a-z_]+$ | user_repo

DT: UserCreds | {email:str, pwd:secret(>=12)}
DT: AuthToken | {jwt:str, exp:utc}

TK: Role | {admin,staff,viewer}

MO: #1 | auth/service.py | {svc,auth}
MO: #2 | auth/repository.py | {repo,auth}
MO: #3 | auth/dto.py | {dto,auth}

SY: #1.#1 | cls | AuthService
SY: #1.#2 | fn  | login
SY: #2.#1 | cls | UserRepository
SY: #3.#1 | cls | UserCreds
SY: #3.#2 | cls | AuthToken

TY: fn | AuthService.login | (UserCreds)->AuthToken !raises[AuthError]
SG: #1.#2 | (UserCreds)->AuthToken !raises[AuthError]

ED: #1.#2 -> #2.#1 | uses:repo
ED: #1.#2 -> #3.#2 | returns:dto

ER: AuthError | domain | bad credentials
IN: login ⇒ requires(valid(creds)) ∧ ensures(token.exp>now)

CN: async fn end with _async
CN: repos never import svc

IO: POST /v1/login | UserCreds | AuthToken | 200,401,429

EX: var(repo) => user_repo
RV: Check invariants (IN) on public fn"""

        report = get_validation_report(content)

        assert report["valid"]
        assert len(report["errors"]) == 0
        assert len(report["semantic_tokens"]) > 0
