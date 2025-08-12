"""
Integration tests for full CTX-CARD generation.

This module tests the complete CTX-CARD generation pipeline.
"""

import time
from pathlib import Path

# Note: pytest import is handled by test runner
try:
    import pytest
except ImportError:
    pytest = None

from src.ctxcard_gen import CTXCardGenerator
from src.ctxcard_gen.types import GeneratorConfig


@pytest.fixture
def sample_project_dir(tmp_path: Path) -> Path:
    """Create a sample project directory for testing."""
    project_dir = tmp_path / "sample_project"
    project_dir.mkdir()

    # Create main package
    main_pkg = project_dir / "main_pkg"
    main_pkg.mkdir()
    (main_pkg / "__init__.py").write_text("")

    # Create service module
    service_file = main_pkg / "service.py"
    service_file.write_text(
        '''
"""
Service module for testing.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class UserCreds:
    """User credentials data transfer object."""
    email: str
    password: str


class AuthService:
    """Authentication service."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def login(self, creds: UserCreds) -> Optional[str]:
        """
        Authenticate user and return token.
        
        Args:
            creds: User credentials
            
        Returns:
            Authentication token or None if failed
            
        Raises:
            AuthError: If authentication fails
        """
        if creds.email == "test@example.com" and creds.password == "password":
            return "valid_token"
        return None
    
    def logout(self, token: str) -> bool:
        """
        Logout user.
        
        Args:
            token: Authentication token
            
        Returns:
            True if logout successful
        """
        return True


class AuthError(Exception):
    """Authentication error."""
    pass


# Global configuration
CONFIG = {
    "database_url": "postgresql://localhost/test",
    "secret_key": "test_secret"
}
'''
    )

    # Create repository module
    repo_file = main_pkg / "repository.py"
    repo_file.write_text(
        '''
"""
Repository module for testing.
"""

from typing import List, Optional
from .service import UserCreds


class UserRepository:
    """User repository for data access."""
    
    def __init__(self):
        self.users = []
    
    def find_by_email(self, email: str) -> Optional[UserCreds]:
        """
        Find user by email.
        
        Args:
            email: User email
            
        Returns:
            User credentials or None if not found
        """
        for user in self.users:
            if user.email == email:
                return user
        return None
    
    def save(self, user: UserCreds) -> bool:
        """
        Save user.
        
        Args:
            user: User to save
            
        Returns:
            True if save successful
        """
        self.users.append(user)
        return True


# Repository instance
user_repo = UserRepository()
'''
    )

    # Create tests directory
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")

    test_file = tests_dir / "test_service.py"
    test_file.write_text(
        '''
"""
Tests for service module.
"""

import pytest
from main_pkg.service import AuthService, UserCreds, AuthError


def test_login_success():
    """Test successful login."""
    service = AuthService({})
    creds = UserCreds("test@example.com", "password")
    token = service.login(creds)
    assert token == "valid_token"


def test_login_failure():
    """Test failed login."""
    service = AuthService({})
    creds = UserCreds("wrong@example.com", "wrong")
    token = service.login(creds)
    assert token is None
'''
    )

    return project_dir


def test_full_generation(project_dir: Path, tmp_path: Path):
    """Test complete CTX-CARD generation."""
    output_path = tmp_path / "CTXCARD.md"

    config = GeneratorConfig(
        project_name="test-project",
        root_path=project_dir,
        output_path=output_path,
    )

    generator = CTXCardGenerator(config)
    content = generator.generate()
    generator.save_output(content)

    assert output_path.exists()
    assert len(content) > 0

    # Check for required sections
    lines = content.splitlines()
    required_sections = ["ID:", "AL:", "NM:", "MO:", "SY:"]
    for section in required_sections:
        assert any(line.startswith(section) for line in lines), f"Missing {section}"

    # Check for project-specific content
    assert "proj|test-project" in content
    assert "main_pkg/service.py" in content
    assert "AuthService" in content
    assert "UserCreds" in content


def test_generation_with_type_signatures(project_dir: Path, tmp_path: Path):
    """Test generation with type signatures."""
    output_path = tmp_path / "CTXCARD.md"

    config = GeneratorConfig(
        project_name="test-project",
        root_path=project_dir,
        output_path=output_path,
        emit_type_signatures=True,
    )

    generator = CTXCardGenerator(config)
    content = generator.generate()
    generator.save_output(content)

    assert output_path.exists()
    lines = content.splitlines()
    assert any(line.startswith("TY:") for line in lines)


def test_generation_with_delta(project_dir: Path, tmp_path: Path):
    """Test generation with delta comparison."""
    # Create old CTX-CARD file
    old_content = """ID: proj|test-project lang|py std|pep8 ts|20241201

AL: cfg=>Configuration
AL: svc=>Service

NM: module | ^[a-z_]+$ | auth_service
NM: class  | ^[A-Z][A-Za-z0-9]+$ | AuthService

MO: #1 | main_pkg/service.py | {svc}

SY: #1.#1 | cls | AuthService

CN: repos never import svc
RV: public functions have signatures & docstrings
"""

    old_path = tmp_path / "old_CTXCARD.md"
    old_path.write_text(old_content)

    output_path = tmp_path / "CTXCARD.md"

    config = GeneratorConfig(
        project_name="test-project",
        root_path=project_dir,
        output_path=output_path,
        delta_from=old_path,
    )

    generator = CTXCardGenerator(config)
    content = generator.generate()
    generator.save_output(content)

    assert output_path.exists()
    lines = content.splitlines()
    assert any(line.startswith("DELTA:") for line in lines)


def test_generation_with_per_package(project_dir: Path, tmp_path: Path):
    """Test generation with per-package output."""
    output_path = tmp_path / "CTXCARD.md"

    config = GeneratorConfig(
        project_name="test-project",
        root_path=project_dir,
        output_path=output_path,
        per_package=True,
    )

    generator = CTXCardGenerator(config)
    content = generator.generate()
    packages = generator.generate_per_package(content)
    generator.save_per_package(packages)

    assert output_path.exists()

    # Check that package files were created
    for pkg_file in tmp_path.glob("CTXCARD.*.md"):
        assert pkg_file.exists()
        assert len(pkg_file.read_text()) > 0


def test_generation_with_include_pattern(project_dir: Path, tmp_path: Path):
    """Test generation with include pattern."""
    output_path = tmp_path / "CTXCARD.md"

    config = GeneratorConfig(
        project_name="test-project",
        root_path=project_dir,
        output_path=output_path,
        include_pattern="**/*.py",
    )

    generator = CTXCardGenerator(config)
    content = generator.generate()
    generator.save_output(content)

    assert output_path.exists()

    # Check that only Python files were processed
    lines = content.splitlines()
    mo_lines = [line for line in lines if line.startswith("MO:")]
    for mo_line in mo_lines:
        parts = mo_line.split(" | ")
        if len(parts) >= 2:
            file_path = parts[1]
            assert file_path.endswith(".py")


def test_generation_with_exclude_pattern(project_dir: Path, tmp_path: Path):
    """Test generation with exclude pattern."""
    output_path = tmp_path / "CTXCARD.md"

    config = GeneratorConfig(
        project_name="test-project",
        root_path=project_dir,
        output_path=output_path,
        exclude_pattern="**/tests/**",
    )

    generator = CTXCardGenerator(config)
    content = generator.generate()
    generator.save_output(content)

    assert output_path.exists()

    # Check that test files were excluded
    lines = content.splitlines()
    mo_lines = [line for line in lines if line.startswith("MO:")]
    for mo_line in mo_lines:
        parts = mo_line.split(" | ")
        if len(parts) >= 2:
            file_path = parts[1]
            assert "tests" not in file_path


def test_generation_error_handling(tmp_path: Path):
    """Test generation error handling."""
    # Test with non-existent directory
    non_existent_dir = tmp_path / "nonexistent"
    output_path = tmp_path / "CTXCARD.md"

    try:
        config = GeneratorConfig(
            project_name="test-project",
            root_path=non_existent_dir,
            output_path=output_path,
        )
        generator = CTXCardGenerator(config)
        content = generator.generate()
        # Should handle gracefully
        assert len(content) >= 0
    except (FileNotFoundError, OSError, ValueError):
        # Specific exceptions are acceptable
        pass


def test_generation_performance(project_dir: Path, tmp_path: Path):
    """Test generation performance."""
    output_path = tmp_path / "CTXCARD.md"

    config = GeneratorConfig(
        project_name="test-project",
        root_path=project_dir,
        output_path=output_path,
    )

    generator = CTXCardGenerator(config)

    # Time the generation
    start_time = time.time()
    content = generator.generate()
    end_time = time.time()

    generator.save_output(content)

    assert output_path.exists()
    assert len(content) > 0

    # Generation should complete in reasonable time
    generation_time = end_time - start_time
    assert generation_time < 10.0  # Should complete within 10 seconds
