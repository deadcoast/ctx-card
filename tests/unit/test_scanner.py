"""
Unit tests for scanner module.

This module tests the repository scanning functionality.
"""

from pathlib import Path

# Note: pytest import is handled by test runner
try:
    import pytest
except ImportError:
    pytest = None

from src.ctxcard_gen.core.scanner import RepoScanner


class TestRepoScanner:
    """Test cases for repository scanner functionality."""

    def test_init(self):
        """Test scanner initialization."""
        scanner = RepoScanner()
        assert scanner is not None

    def test_scan_repository_empty(self, tmp_path: Path):
        """Test scanning empty repository."""
        scanner = RepoScanner()
        result = scanner.scan_repository(tmp_path)

        assert result is not None
        assert len(result.modules) == 0
        assert len(result.langs) == 0

    def test_scan_repository_single_python_file(self, tmp_path: Path):
        """Test scanning repository with single Python file."""
        # Create a simple Python file
        test_file = tmp_path / "test.py"
        test_file.write_text(
            '''
def hello():
    return "Hello, World!"

class TestClass:
    def __init__(self):
        pass
'''
        )

        scanner = RepoScanner()
        result = scanner.scan_repository(tmp_path)

        assert result is not None
        assert len(result.modules) == 1
        assert "py" in result.langs
        assert "test.py" in result.modules

    def test_scan_repository_multiple_files(self, tmp_path: Path):
        """Test scanning repository with multiple files."""
        # Create multiple Python files
        (tmp_path / "module1.py").write_text("def func1(): pass")
        (tmp_path / "module2.py").write_text("def func2(): pass")
        (tmp_path / "README.md").write_text("# Test Project")

        scanner = RepoScanner()
        result = scanner.scan_repository(tmp_path)

        assert result is not None
        assert len(result.modules) == 2  # Only Python files
        assert "py" in result.langs

    def test_scan_repository_with_packages(self, tmp_path: Path):
        """Test scanning repository with package structure."""
        # Create package structure
        pkg_dir = tmp_path / "mypackage"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "module.py").write_text("def package_func(): pass")

        scanner = RepoScanner()
        result = scanner.scan_repository(tmp_path)

        assert result is not None
        assert len(result.modules) == 2  # __init__.py and module.py
        assert "py" in result.langs

    def test_scan_repository_with_ignore_patterns(self, tmp_path: Path):
        """Test scanning repository with ignore patterns."""
        # Create files including some to ignore
        (tmp_path / "main.py").write_text("def main(): pass")
        (tmp_path / "test_main.py").write_text("def test_main(): pass")
        (tmp_path / "temp.py").write_text("def temp(): pass")

        scanner = RepoScanner()
        result = scanner.scan_repository(
            tmp_path,
            exclude_pattern="**/test_*.py"
        )

        assert result is not None
        # Should exclude test_main.py
        assert "main.py" in result.modules
        assert "test_main.py" not in result.modules

    def test_scan_repository_with_include_patterns(self, tmp_path: Path):
        """Test scanning repository with include patterns."""
        # Create files of different types
        (tmp_path / "main.py").write_text("def main(): pass")
        (tmp_path / "utils.py").write_text("def utils(): pass")
        (tmp_path / "config.json").write_text('{"key": "value"}')

        scanner = RepoScanner()
        result = scanner.scan_repository(
            tmp_path,
            include_pattern="**/main.py"
        )

        assert result is not None
        # Should only include main.py
        assert "main.py" in result.modules
        assert "utils.py" not in result.modules

    def test_scan_repository_with_complex_structure(self, tmp_path: Path):
        """Test scanning repository with complex structure."""
        # Create complex package structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        pkg1_dir = src_dir / "package1"
        pkg1_dir.mkdir()
        (pkg1_dir / "__init__.py").write_text("")
        (pkg1_dir / "module1.py").write_text("def pkg1_func(): pass")

        pkg2_dir = src_dir / "package2"
        pkg2_dir.mkdir()
        (pkg2_dir / "__init__.py").write_text("")
        (pkg2_dir / "module2.py").write_text("def pkg2_func(): pass")

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_module1.py").write_text("def test_pkg1(): pass")

        scanner = RepoScanner()
        result = scanner.scan_repository(tmp_path)

        assert result is not None
        assert len(result.modules) == 5  # All Python files
        assert "py" in result.langs

    def test_scan_repository_with_binary_files(self, tmp_path: Path):
        """Test scanning repository with binary files."""
        # Create Python file and binary file
        (tmp_path / "main.py").write_text("def main(): pass")
        (tmp_path / "binary.dat").write_bytes(b"\x00\x01\x02\x03")

        scanner = RepoScanner()
        result = scanner.scan_repository(tmp_path)

        assert result is not None
        # Should only include Python files
        assert "main.py" in result.modules
        assert len(result.modules) == 1

    def test_scan_repository_with_syntax_errors(self, tmp_path: Path):
        """Test scanning repository with syntax errors."""
        # Create Python file with syntax error
        (tmp_path / "broken.py").write_text("def broken(: pass")  # Invalid syntax

        scanner = RepoScanner()
        result = scanner.scan_repository(tmp_path)

        # Should handle syntax errors gracefully
        assert result is not None
        # May or may not include the file, but shouldn't crash

    def test_scan_repository_with_encoding_issues(self, tmp_path: Path):
        """Test scanning repository with encoding issues."""
        # Create Python file with encoding issues
        (tmp_path / "encoding_test.py").write_text("def test(): pass", encoding="utf-8")

        # Try to read with wrong encoding (this is just a test setup)
        scanner = RepoScanner()
        result = scanner.scan_repository(tmp_path)

        # Should handle encoding issues gracefully
        assert result is not None

    def test_scan_repository_performance(self, tmp_path: Path):
        """Test scanning repository performance."""
        # Create many small files
        for i in range(10):
            (tmp_path / f"module_{i}.py").write_text(f"def func_{i}(): pass")

        scanner = RepoScanner()
        result = scanner.scan_repository(tmp_path)

        assert result is not None
        assert len(result.modules) == 10

    def test_scan_repository_with_ast_analyzer_integration(self, tmp_path: Path):
        """Test scanner integration with AST analyzer."""
        # Create a file with complex Python code
        test_file = tmp_path / "complex.py"
        test_file.write_text(
            '''
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str

class UserService:
    def __init__(self, db_url: str):
        self.db_url = db_url

    def get_user(self, user_id: int) -> Optional[User]:
        return User("test", "test@example.com")

    def list_users(self) -> List[User]:
        return []

def main():
    service = UserService("sqlite:///test.db")
    user = service.get_user(1)
    print(user)
'''
        )

        scanner = RepoScanner()
        result = scanner.scan_repository(tmp_path)

        assert result is not None
        assert "complex.py" in result.modules

        # Check that symbols were extracted
        module_info = result.modules["complex.py"]
        assert len(module_info.symbols) > 0

        # Check for specific symbols
        symbol_names = [s.name for s in module_info.symbols]
        assert "User" in symbol_names
        assert "UserService" in symbol_names
        assert "main" in symbol_names
