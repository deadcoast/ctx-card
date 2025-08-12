"""
Tests for ignore file functionality.

This module tests the .ctxignore file parsing and pattern matching.
"""

import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile

from ctxcard_gen.utils.ignore import IgnorePattern, IgnoreFile, load_ignore_file


class TestIgnorePattern:
    """Test cases for IgnorePattern class."""

    def test_basic_pattern_matching(self):
        """Test basic pattern matching."""
        pattern = IgnorePattern("*.py", 1)

        assert pattern.matches("test.py")
        assert pattern.matches("module.py")
        assert not pattern.matches("test.txt")
        assert not pattern.matches("test.pyc")

    def test_directory_pattern_matching(self):
        """Test directory pattern matching."""
        pattern = IgnorePattern("venv/", 1)

        assert pattern.matches("venv")
        assert pattern.matches("venv/")
        assert pattern.matches("venv/lib")
        assert pattern.matches("venv/lib/python3.8")
        assert not pattern.matches("venv_file")

    def test_negation_pattern(self):
        """Test negation pattern."""
        pattern = IgnorePattern("!important.py", 1)

        assert pattern.is_negation
        assert pattern.matches("important.py")
        assert not pattern.matches("other.py")

    def test_character_class_pattern(self):
        """Test character class pattern."""
        pattern = IgnorePattern("test[abc].py", 1)

        assert pattern.matches("testa.py")
        assert pattern.matches("testb.py")
        assert pattern.matches("testc.py")
        assert not pattern.matches("testd.py")

    def test_negated_character_class_pattern(self):
        """Test negated character class pattern."""
        pattern = IgnorePattern("test[!abc].py", 1)

        assert not pattern.matches("testa.py")
        assert not pattern.matches("testb.py")
        assert not pattern.matches("testc.py")
        assert pattern.matches("testd.py")

    def test_question_mark_pattern(self):
        """Test question mark pattern."""
        pattern = IgnorePattern("test?.py", 1)

        assert pattern.matches("test1.py")
        assert pattern.matches("testa.py")
        assert not pattern.matches("test12.py")

    def test_complex_pattern(self):
        """Test complex pattern with multiple wildcards."""
        pattern = IgnorePattern("src/**/*.py", 1)

        assert pattern.matches("src/module.py")
        assert pattern.matches("src/utils/helper.py")
        assert pattern.matches("src/core/parser.py")
        assert not pattern.matches("test.py")


class TestIgnoreFile:
    """Test cases for IgnoreFile class."""

    def test_empty_ignore_file(self, tmp_path: Path):
        """Test ignore file with no patterns."""
        ignore_file = IgnoreFile(tmp_path)

        assert len(ignore_file.patterns) == 0
        assert not ignore_file.should_ignore(tmp_path / "test.py")

    def test_basic_ignore_file(self, tmp_path: Path):
        """Test basic ignore file functionality."""
        # Create .ctxignore file
        ignore_file_path = tmp_path / ".ctxignore"
        ignore_file_path.write_text("*.pyc\n__pycache__/\n.venv/")

        ignore_file = IgnoreFile(tmp_path)

        assert len(ignore_file.patterns) == 3
        assert ignore_file.should_ignore(tmp_path / "test.pyc")
        assert ignore_file.should_ignore(tmp_path / "__pycache__")
        assert ignore_file.should_ignore(tmp_path / ".venv")
        assert not ignore_file.should_ignore(tmp_path / "test.py")

    def test_ignore_file_with_comments(self, tmp_path: Path):
        """Test ignore file with comments."""
        # Create .ctxignore file with comments
        ignore_file_path = tmp_path / ".ctxignore"
        ignore_file_path.write_text(
            "# Python cache files\n"
            "*.pyc\n"
            "\n"
            "# Virtual environments\n"
            ".venv/\n"
        )

        ignore_file = IgnoreFile(tmp_path)

        assert len(ignore_file.patterns) == 2
        assert ignore_file.should_ignore(tmp_path / "test.pyc")
        assert ignore_file.should_ignore(tmp_path / ".venv")

    def test_ignore_file_with_negation(self, tmp_path: Path):
        """Test ignore file with negation patterns."""
        # Create .ctxignore file with negation
        ignore_file_path = tmp_path / ".ctxignore"
        ignore_file_path.write_text("*.py\n!important.py")

        ignore_file = IgnoreFile(tmp_path)

        assert len(ignore_file.patterns) == 2
        assert ignore_file.should_ignore(tmp_path / "test.py")
        assert not ignore_file.should_ignore(tmp_path / "important.py")

    def test_ignore_file_with_empty_lines(self, tmp_path: Path):
        """Test ignore file with empty lines."""
        # Create .ctxignore file with empty lines
        ignore_file_path = tmp_path / ".ctxignore"
        ignore_file_path.write_text("*.pyc\n\n*.log\n")

        ignore_file = IgnoreFile(tmp_path)

        assert len(ignore_file.patterns) == 2
        assert ignore_file.should_ignore(tmp_path / "test.pyc")
        assert ignore_file.should_ignore(tmp_path / "test.log")

    def test_ignore_file_error_handling(self, tmp_path: Path):
        """Test ignore file error handling."""
        # Create a directory with the same name as .ctxignore
        ignore_file_path = tmp_path / ".ctxignore"
        ignore_file_path.mkdir()

        # Should not raise an exception
        ignore_file = IgnoreFile(tmp_path)
        assert len(ignore_file.patterns) == 0

    def test_get_ignored_patterns(self, tmp_path: Path):
        """Test getting ignored patterns."""
        # Create .ctxignore file
        ignore_file_path = tmp_path / ".ctxignore"
        ignore_file_path.write_text("*.pyc\n__pycache__/\n.venv/")

        ignore_file = IgnoreFile(tmp_path)
        patterns = ignore_file.get_ignored_patterns()

        assert len(patterns) == 3
        assert "*.pyc" in patterns
        assert "__pycache__/" in patterns
        assert ".venv/" in patterns

    def test_path_outside_root(self, tmp_path: Path):
        """Test path outside root directory."""
        ignore_file = IgnoreFile(tmp_path)

        # Path outside root should not be ignored
        outside_path = Path("/tmp/outside.py")
        assert not ignore_file.should_ignore(outside_path)


class TestLoadIgnoreFile:
    """Test cases for load_ignore_file function."""

    def test_load_ignore_file(self, tmp_path: Path):
        """Test loading ignore file."""
        # Create .ctxignore file
        ignore_file_path = tmp_path / ".ctxignore"
        ignore_file_path.write_text("*.pyc\n__pycache__/")

        ignore_file = load_ignore_file(tmp_path)

        assert isinstance(ignore_file, IgnoreFile)
        assert len(ignore_file.patterns) == 2

    def test_load_ignore_file_nonexistent(self, tmp_path: Path):
        """Test loading ignore file when it doesn't exist."""
        ignore_file = load_ignore_file(tmp_path)

        assert isinstance(ignore_file, IgnoreFile)
        assert len(ignore_file.patterns) == 0


class TestIgnoreIntegration:
    """Integration tests for ignore functionality."""

    def test_ignore_in_scanner(self, tmp_path: Path):
        """Test ignore functionality in scanner."""
        from ctxcard_gen.core.scanner import RepoScanner

        # Create project structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        (src_dir / "main.py").write_text("print('hello')")
        (src_dir / "cache.pyc").write_text("compiled")
        (src_dir / "__pycache__").mkdir()
        (src_dir / "__pycache__" / "main.pyc").write_text("compiled")

        # Create .ctxignore file
        ignore_file_path = tmp_path / ".ctxignore"
        ignore_file_path.write_text("*.pyc\n__pycache__/")

        # Scan repository
        scanner = RepoScanner()
        scan_result = scanner.scan_repo(tmp_path, None, None)

        # Check that ignored files are not included
        module_paths = [mi.path for mi in scan_result.modules.values()]
        assert "src/cache.pyc" not in module_paths
        assert "src/__pycache__/main.pyc" not in module_paths
        assert "src/main.py" in module_paths
