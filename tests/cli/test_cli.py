"""
Tests for CLI functionality.

This module tests the command-line interface of the CTX-CARD generator.
"""

import subprocess
import sys

# Note: pytest import is handled by test runner
try:
    import pytest
except ImportError:
    pytest = None


def test_cli_help():
    """Test that CLI help works."""
    result = subprocess.run(
        [sys.executable, "-m", "ctxcard_gen", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout
    assert "CTX-CARD" in result.stdout
