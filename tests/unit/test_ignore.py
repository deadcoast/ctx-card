"""
Unit tests for ignore module.

This module tests the .ctxignore file functionality.
"""

from pathlib import Path

# Note: pytest import is handled by test runner
try:
    import pytest
except ImportError:
    pytest = None

from src.ctxcard_gen.utils.ignore import IgnoreFile, IgnorePattern, load_ignore_file


class TestIgnoreFile:
    """Test cases for ignore file functionality."""

    def test_init(self):
        """Test ignore file initialization."""
        ignore_file = IgnoreFile(Path("/tmp"))
        assert ignore_file is not None
        assert len(ignore_file.patterns) == 0

    def test_add_pattern(self):
        """Test adding patterns to ignore file."""
        ignore_file = IgnoreFile(Path("/tmp"))
        pattern = IgnorePattern("*.pyc", 1)
        ignore_file.patterns.append(pattern)

        assert len(ignore_file.patterns) == 1
        assert ignore_file.patterns[0].pattern == "*.pyc"

    def test_should_ignore_file(self):
        """Test file ignore decision."""
        ignore_file = IgnoreFile(Path("/tmp"))
        ignore_file.patterns.append(IgnorePattern("*.pyc", 1))
        ignore_file.patterns.append(IgnorePattern("__pycache__", 2))

        assert ignore_file.should_ignore(Path("/tmp/test.pyc"))
        assert ignore_file.should_ignore(Path("/tmp/__pycache__/module.pyc"))
        assert not ignore_file.should_ignore(Path("/tmp/test.py"))

    def test_should_ignore_directory(self):
        """Test directory ignore decision."""
        ignore_file = IgnoreFile(Path("/tmp"))
        ignore_file.patterns.append(IgnorePattern("node_modules", 1))
        ignore_file.patterns.append(IgnorePattern(".git", 2))

        assert ignore_file.should_ignore(Path("/tmp/node_modules"))
        assert ignore_file.should_ignore(Path("/tmp/.git"))
        assert not ignore_file.should_ignore(Path("/tmp/src"))

    def test_should_ignore_with_paths(self):
        """Test ignore with relative paths."""
        ignore_file = IgnoreFile(Path("/tmp"))
        ignore_file.patterns.append(IgnorePattern("tests/", 1))
        ignore_file.patterns.append(IgnorePattern("*.log", 2))

        assert ignore_file.should_ignore(Path("/tmp/tests/test_file.py"))
        assert ignore_file.should_ignore(Path("/tmp/app.log"))
        assert not ignore_file.should_ignore(Path("/tmp/src/main.py"))

    def test_should_ignore_complex_patterns(self):
        """Test ignore with complex patterns."""
        ignore_file = IgnoreFile(Path("/tmp"))
        ignore_file.patterns.append(IgnorePattern("**/__pycache__/**", 1))
        ignore_file.patterns.append(IgnorePattern("*.{pyc,pyo}", 2))
        ignore_file.patterns.append(IgnorePattern("build/", 3))

        assert ignore_file.should_ignore(Path("/tmp/src/__pycache__/module.pyc"))
        assert ignore_file.should_ignore(Path("/tmp/module.pyc"))
        assert ignore_file.should_ignore(Path("/tmp/build/dist/package.tar.gz"))
        assert not ignore_file.should_ignore(Path("/tmp/src/main.py"))

    def test_should_ignore_regex_patterns(self):
        """Test ignore with regex patterns."""
        ignore_file = IgnoreFile(Path("/tmp"))
        ignore_file.patterns.append(IgnorePattern(r"\.pyc$", 1))
        ignore_file.patterns.append(IgnorePattern(r"__pycache__", 2))

        assert ignore_file.should_ignore(Path("/tmp/test.pyc"))
        assert ignore_file.should_ignore(Path("/tmp/__pycache__/module.pyc"))
        assert not ignore_file.should_ignore(Path("/tmp/test.py"))

    def test_should_ignore_mixed_patterns(self):
        """Test ignore with mixed pattern types."""
        ignore_file = IgnoreFile(Path("/tmp"))
        ignore_file.patterns.append(IgnorePattern("*.pyc", 1))
        ignore_file.patterns.append(IgnorePattern(r"\.log$", 2))
        ignore_file.patterns.append(IgnorePattern("temp/", 3))

        assert ignore_file.should_ignore(Path("/tmp/module.pyc"))
        assert ignore_file.should_ignore(Path("/tmp/app.log"))
        assert ignore_file.should_ignore(Path("/tmp/temp/file.txt"))
        assert not ignore_file.should_ignore(Path("/tmp/src/main.py"))

    def test_should_ignore_case_sensitivity(self):
        """Test case sensitivity in ignore patterns."""
        ignore_file = IgnoreFile(Path("/tmp"))
        ignore_file.patterns.append(IgnorePattern("*.TXT", 1))
        ignore_file.patterns.append(IgnorePattern("BACKUP", 2))

        # Should match case-insensitively
        assert ignore_file.should_ignore(Path("/tmp/file.txt"))
        assert ignore_file.should_ignore(Path("/tmp/backup"))
        assert ignore_file.should_ignore(Path("/tmp/BACKUP"))

    def test_should_ignore_negation_patterns(self):
        """Test negation patterns in ignore file."""
        ignore_file = IgnoreFile(Path("/tmp"))
        ignore_file.patterns.append(IgnorePattern("*.pyc", 1))
        ignore_file.patterns.append(IgnorePattern("!important.pyc", 2))

        assert ignore_file.should_ignore(Path("/tmp/module.pyc"))
        assert not ignore_file.should_ignore(Path("/tmp/important.pyc"))

    def test_should_ignore_directory_patterns(self):
        """Test directory-specific patterns."""
        ignore_file = IgnoreFile(Path("/tmp"))
        ignore_file.patterns.append(IgnorePattern("logs/", 1))
        ignore_file.patterns.append(IgnorePattern("temp/", 2))

        assert ignore_file.should_ignore(Path("/tmp/logs/"))
        assert ignore_file.should_ignore(Path("/tmp/logs/error.log"))
        assert ignore_file.should_ignore(Path("/tmp/temp/"))
        assert ignore_file.should_ignore(Path("/tmp/temp/file.txt"))

    def test_should_ignore_character_classes(self):
        """Test character class patterns."""
        ignore_file = IgnoreFile(Path("/tmp"))
        ignore_file.patterns.append(IgnorePattern("*.{pyc,pyo}", 1))
        ignore_file.patterns.append(IgnorePattern("test[0-9].py", 2))

        assert ignore_file.should_ignore(Path("/tmp/module.pyc"))
        assert ignore_file.should_ignore(Path("/tmp/module.pyo"))
        assert ignore_file.should_ignore(Path("/tmp/test1.py"))
        assert ignore_file.should_ignore(Path("/tmp/test9.py"))
        assert not ignore_file.should_ignore(Path("/tmp/test.py"))

    def test_should_ignore_recursive_patterns(self):
        """Test recursive directory patterns."""
        ignore_file = IgnoreFile(Path("/tmp"))
        ignore_file.patterns.append(IgnorePattern("**/__pycache__", 1))
        ignore_file.patterns.append(IgnorePattern("**/*.pyc", 2))

        assert ignore_file.should_ignore(Path("/tmp/__pycache__/module.pyc"))
        assert ignore_file.should_ignore(Path("/tmp/src/__pycache__/module.pyc"))
        assert ignore_file.should_ignore(Path("/tmp/src/subdir/__pycache__/module.pyc"))
        assert ignore_file.should_ignore(Path("/tmp/src/module.pyc"))

    def test_should_ignore_path_outside_root(self):
        """Test paths outside the root directory."""
        ignore_file = IgnoreFile(Path("/tmp"))

        # Path outside root should not be ignored
        assert not ignore_file.should_ignore(Path("/other/file.pyc"))

    def test_get_ignored_patterns(self):
        """Test getting ignored patterns list."""
        ignore_file = IgnoreFile(Path("/tmp"))
        ignore_file.patterns.append(IgnorePattern("*.pyc", 1))
        ignore_file.patterns.append(IgnorePattern("__pycache__", 2))

        patterns = ignore_file.get_ignored_patterns()
        assert "*.pyc" in patterns
        assert "__pycache__" in patterns
        assert len(patterns) == 2


class TestIgnorePattern:
    """Test cases for ignore pattern functionality."""

    def test_init(self):
        """Test ignore pattern initialization."""
        pattern = IgnorePattern("*.pyc", 1)
        assert pattern.pattern == "*.pyc"
        assert pattern.line_number == 1
        assert not pattern.is_negation
        assert not pattern.is_directory

    def test_negation_pattern(self):
        """Test negation pattern detection."""
        pattern = IgnorePattern("!important.pyc", 1)
        assert pattern.is_negation
        assert pattern.pattern == "!important.pyc"

    def test_directory_pattern(self):
        """Test directory pattern detection."""
        pattern = IgnorePattern("logs/", 1)
        assert pattern.is_directory
        assert pattern.pattern == "logs/"

    def test_matches_simple_glob(self):
        """Test simple glob pattern matching."""
        pattern = IgnorePattern("*.pyc", 1)
        assert pattern.matches("module.pyc")
        assert pattern.matches("test.pyc")
        assert not pattern.matches("module.py")

    def test_matches_directory_glob(self):
        """Test directory glob pattern matching."""
        pattern = IgnorePattern("logs/", 1)
        assert pattern.matches("logs")
        assert pattern.matches("logs/error.log")
        assert not pattern.matches("src/logs")

    def test_matches_recursive_glob(self):
        """Test recursive glob pattern matching."""
        pattern = IgnorePattern("**/__pycache__", 1)
        assert pattern.matches("__pycache__")
        assert pattern.matches("src/__pycache__")
        assert pattern.matches("src/subdir/__pycache__")

    def test_matches_character_classes(self):
        """Test character class pattern matching."""
        pattern = IgnorePattern("test[0-9].py", 1)
        assert pattern.matches("test1.py")
        assert pattern.matches("test9.py")
        assert not pattern.matches("test.py")
        assert not pattern.matches("test10.py")

    def test_matches_negated_character_classes(self):
        """Test negated character class pattern matching."""
        pattern = IgnorePattern("test[!0-9].py", 1)
        assert pattern.matches("testa.py")
        assert pattern.matches("test_.py")
        assert not pattern.matches("test1.py")
        assert not pattern.matches("test9.py")


class TestLoadIgnoreFile:
    """Test cases for loading ignore files."""

    def test_load_ignore_file(self):
        """Test loading ignore file."""
        ignore_file = load_ignore_file(Path("/tmp"))
        assert isinstance(ignore_file, IgnoreFile)
        assert ignore_file.root_path == Path("/tmp")

    def test_load_ignore_file_with_patterns(self, tmp_path):
        """Test loading ignore file with actual patterns."""
        # Create a .ctxignore file
        ignore_file_path = tmp_path / ".ctxignore"
        ignore_file_path.write_text("*.pyc\n__pycache__\n*.log\n")

        ignore_file = load_ignore_file(tmp_path)
        assert len(ignore_file.patterns) == 3
        assert ignore_file.patterns[0].pattern == "*.pyc"
        assert ignore_file.patterns[1].pattern == "__pycache__"
        assert ignore_file.patterns[2].pattern == "*.log"
