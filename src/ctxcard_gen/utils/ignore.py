"""
Ignore file utilities for CTX-CARD generator.

This module handles .ctxignore file parsing and pattern matching to exclude
files and directories from CTX-CARD generation.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List


class IgnorePattern:
    """Represents a single ignore pattern with its properties."""

    def __init__(self, pattern: str, line_number: int):
        """
        Initialize an ignore pattern.

        Args:
            pattern: The glob pattern to match
            line_number: Line number in the .ctxignore file
        """
        self.pattern = pattern
        self.line_number = line_number
        self.is_negation = pattern.startswith("!")
        self.is_directory = pattern.endswith("/")

        # Convert glob pattern to regex
        self.regex = self._glob_to_regex(pattern)

    def _glob_to_regex(self, pattern: str) -> re.Pattern:
        """
        Convert glob pattern to regex pattern.

        Args:
            pattern: Glob pattern string

        Returns:
            Compiled regex pattern
        """
        # Handle negation
        if pattern.startswith("!"):
            pattern = pattern[1:]

        # Convert glob wildcards to regex
        # Handle ** (recursive directory matching)
        pattern = pattern.replace("**", "__RECURSIVE__")

        # Handle character classes before escaping
        # Replace [!abc] with a special marker
        pattern = re.sub(r"\[!([^\]]+)\]", r"__NEGATED__\1__END__", pattern)

        # Escape regex special characters
        pattern = re.escape(pattern)

        # Convert glob wildcards to regex
        pattern = pattern.replace("\\*", ".*")  # * -> .*
        pattern = pattern.replace("\\?", ".")   # ? -> .

        # Handle recursive directory matching
        pattern = pattern.replace("__RECURSIVE__", ".*")

        # Fix **/* patterns to match files directly in directory
        pattern = re.sub(r"\.\*/\.\*", ".*", pattern)

        # Handle character classes like [abc]
        pattern = pattern.replace("\\[", "[")
        pattern = pattern.replace("\\]", "]")

        # Handle negated character classes
        pattern = re.sub(r"__NEGATED__([^_]+)__END__", r"[^\1]", pattern)

        # Handle regular character classes
        pattern = re.sub(r"\[([^\\]+)\]", r"[\1]", pattern)

        # Handle directory patterns
        if pattern.endswith("/"):
            pattern = pattern[:-1] + "(/.*)?"

        # Anchor to start and end
        pattern = f"^{pattern}$"

        return re.compile(pattern, re.IGNORECASE)

    def matches(self, path: str) -> bool:
        """
        Check if a path matches this pattern.

        Args:
            path: Path string to check

        Returns:
            True if path matches the pattern
        """
        return bool(self.regex.match(path))


class IgnoreFile:
    """Handles .ctxignore file parsing and matching."""

    def __init__(self, root_path: Path):
        """
        Initialize ignore file handler.

        Args:
            root_path: Root directory path
        """
        self.root_path = root_path
        self.patterns: List[IgnorePattern] = []
        self._load_ignore_file()

    def _load_ignore_file(self) -> None:
        """Load and parse .ctxignore file."""
        ignore_file = self.root_path / ".ctxignore"

        if not ignore_file.exists():
            return

        try:
            with ignore_file.open("r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Create pattern
                    pattern = IgnorePattern(line, line_num)
                    self.patterns.append(pattern)

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Log error but continue without ignore file
            print(f"Warning: Could not read .ctxignore file: {e}")

    def should_ignore(self, path: Path) -> bool:
        """
        Check if a path should be ignored.

        Args:
            path: Path to check

        Returns:
            True if path should be ignored
        """
        # Convert to relative path from root
        try:
            rel_path = path.relative_to(self.root_path)
            path_str = str(rel_path).replace("\\", "/")  # Normalize separators
        except ValueError:
            # Path is not under root, don't ignore
            return False

        # Check against all patterns
        negations: List[IgnorePattern] = []
        positives: List[IgnorePattern] = []

        for pattern in self.patterns:
            if pattern.is_negation:
                negations.append(pattern)
            else:
                positives.append(pattern)

        # Check positive patterns first
        for pattern in positives:
            if pattern.matches(path_str):
                # Check if any negation pattern overrides this
                for negation in negations:
                    if negation.matches(path_str):
                        return False
                return True

        return False

    def get_ignored_patterns(self) -> List[str]:
        """
        Get list of ignore patterns for debugging.

        Returns:
            List of pattern strings
        """
        return [p.pattern for p in self.patterns]


def load_ignore_file(root_path: Path) -> IgnoreFile:
    """
    Load ignore file for a given root path.

    Args:
        root_path: Root directory path

    Returns:
        IgnoreFile instance
    """
    return IgnoreFile(root_path)
