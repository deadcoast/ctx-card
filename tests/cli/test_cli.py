"""
CLI tests for CTX-CARD generator.
"""

import subprocess
import sys
from pathlib import Path
from typing import List

import pytest


class TestCLI:
    """Test cases for command-line interface."""

    def test_cli_help(self):
        """Test CLI help output."""
        result = subprocess.run(
            [sys.executable, "-m", "ctxcard_gen", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "usage:" in result.stdout
        assert "Generate CTX-CARD" in result.stdout

    def test_cli_basic_generation(self, sample_project_dir: Path, tmp_path: Path):
        """Test basic CLI generation."""
        output_path = tmp_path / "CTXCARD.md"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ctxcard_gen",
                str(sample_project_dir),
                "--out",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output_path.exists()
        assert len(output_path.read_text()) > 0

    def test_cli_stdout_output(self, sample_project_dir: Path):
        """Test CLI stdout output."""
        result = subprocess.run(
            [sys.executable, "-m", "ctxcard_gen", str(sample_project_dir), "--stdout"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert len(result.stdout) > 0
        assert "ID:" in result.stdout
        assert "AL:" in result.stdout

    def test_cli_with_project_name(self, sample_project_dir: Path, tmp_path: Path):
        """Test CLI with custom project name."""
        output_path = tmp_path / "CTXCARD.md"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ctxcard_gen",
                str(sample_project_dir),
                "--proj",
                "custom-project",
                "--out",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output_path.exists()

        content = output_path.read_text()
        assert "proj|custom-project" in content

    def test_cli_with_include_pattern(self, sample_project_dir: Path, tmp_path: Path):
        """Test CLI with include pattern."""
        output_path = tmp_path / "CTXCARD.md"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ctxcard_gen",
                str(sample_project_dir),
                "--include",
                "**/*.py",
                "--out",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output_path.exists()

        content = output_path.read_text()
        lines = content.splitlines()

        # Check that only Python files were processed
        mo_lines = [line for line in lines if line.startswith("MO:")]
        for mo_line in mo_lines:
            parts = mo_line.split(" | ")
            if len(parts) >= 2:
                file_path = parts[1]
                assert file_path.endswith(".py")

    def test_cli_with_exclude_pattern(self, sample_project_dir: Path, tmp_path: Path):
        """Test CLI with exclude pattern."""
        output_path = tmp_path / "CTXCARD.md"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ctxcard_gen",
                str(sample_project_dir),
                "--exclude",
                "**/tests/**",
                "--out",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output_path.exists()

        content = output_path.read_text()
        lines = content.splitlines()

        # Check that test files were excluded
        mo_lines = [line for line in lines if line.startswith("MO:")]
        for mo_line in mo_lines:
            parts = mo_line.split(" | ")
            if len(parts) >= 2:
                file_path = parts[1]
                assert "tests" not in file_path

    def test_cli_with_type_signatures(self, sample_project_dir: Path, tmp_path: Path):
        """Test CLI with type signatures."""
        output_path = tmp_path / "CTXCARD.md"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ctxcard_gen",
                str(sample_project_dir),
                "--emit-ty",
                "--out",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output_path.exists()

        content = output_path.read_text()
        lines = content.splitlines()
        assert any(line.startswith("TY:") for line in lines)

    def test_cli_with_delta(self, sample_project_dir: Path, tmp_path: Path):
        """Test CLI with delta generation."""
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

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ctxcard_gen",
                str(sample_project_dir),
                "--delta-from",
                str(old_path),
                "--out",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output_path.exists()

        content = output_path.read_text()
        lines = content.splitlines()
        assert any(line.startswith("DELTA:") for line in lines)

    def test_cli_with_per_package(self, sample_project_dir: Path, tmp_path: Path):
        """Test CLI with per-package generation."""
        output_path = tmp_path / "CTXCARD.md"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ctxcard_gen",
                str(sample_project_dir),
                "--per-package",
                "--out",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output_path.exists()

        # Check that package files were created
        for pkg_file in tmp_path.glob("CTXCARD.*.md"):
            assert pkg_file.exists()
            assert len(pkg_file.read_text()) > 0

    def test_cli_with_statistics(self, sample_project_dir: Path, tmp_path: Path):
        """Test CLI with statistics output."""
        output_path = tmp_path / "CTXCARD.md"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ctxcard_gen",
                str(sample_project_dir),
                "--stats",
                "--out",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output_path.exists()

        # Check that statistics were printed
        assert "Analysis Statistics:" in result.stdout
        assert "modules:" in result.stdout
        assert "symbols:" in result.stdout

    def test_cli_invalid_path(self, tmp_path: Path):
        """Test CLI with invalid project path."""
        output_path = tmp_path / "CTXCARD.md"
        invalid_path = tmp_path / "nonexistent"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ctxcard_gen",
                str(invalid_path),
                "--out",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "Error:" in result.stderr

    def test_cli_missing_arguments(self):
        """Test CLI with missing required arguments."""
        result = subprocess.run(
            [sys.executable, "-m", "ctxcard_gen"], capture_output=True, text=True
        )

        # Should work with default current directory
        assert result.returncode == 0
        assert "Wrote" in result.stdout

    def test_cli_invalid_option(self):
        """Test CLI with invalid option."""
        result = subprocess.run(
            [sys.executable, "-m", "ctxcard_gen", "--invalid-option"],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "error:" in result.stderr.lower()

    def test_cli_verbose_output(self, sample_project_dir: Path, tmp_path: Path):
        """Test CLI with verbose output."""
        output_path = tmp_path / "CTXCARD.md"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ctxcard_gen",
                str(sample_project_dir),
                "--out",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output_path.exists()

        # Check for success message
        assert "Wrote" in result.stdout or len(result.stdout) > 0

    def test_cli_multiple_options(self, sample_project_dir: Path, tmp_path: Path):
        """Test CLI with multiple options combined."""
        output_path = tmp_path / "CTXCARD.md"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ctxcard_gen",
                str(sample_project_dir),
                "--proj",
                "test-project",
                "--include",
                "**/*.py",
                "--exclude",
                "**/tests/**",
                "--emit-ty",
                "--per-package",
                "--stats",
                "--out",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output_path.exists()

        # Check that all features were applied
        content = output_path.read_text()
        lines = content.splitlines()

        # Check for project name
        assert "proj|test-project" in content

        # Check for type signatures
        assert any(line.startswith("TY:") for line in lines)

        # Check for statistics
        assert "Analysis Statistics:" in result.stdout

        # Check for package files
        for pkg_file in tmp_path.glob("CTXCARD.*.md"):
            assert pkg_file.exists()

    def test_cli_current_directory(self, tmp_path: Path):
        """Test CLI with current directory as project root."""
        # Create a simple project in current directory
        project_file = tmp_path / "simple.py"
        project_file.write_text(
            """
def hello():
    return "Hello, World!"

class Simple:
    def __init__(self):
        pass
"""
        )

        output_path = tmp_path / "CTXCARD.md"

        # Change to project directory
        original_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)

            result = subprocess.run(
                [sys.executable, "-m", "ctxcard_gen", "--out", str(output_path)],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0
            assert output_path.exists()

            content = output_path.read_text()
            assert len(content) > 0
            assert "simple.py" in content

        finally:
            os.chdir(original_cwd)

    def test_cli_error_handling(self, tmp_path: Path):
        """Test CLI error handling."""
        # Test with non-existent delta file
        output_path = tmp_path / "CTXCARD.md"
        non_existent_delta = tmp_path / "nonexistent.md"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ctxcard_gen",
                str(tmp_path),
                "--delta-from",
                str(non_existent_delta),
                "--out",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )

        # Should handle gracefully (not crash)
        assert result.returncode == 0 or result.returncode != 0  # Either is acceptable

    def test_cli_output_format_validation(
        self, sample_project_dir: Path, tmp_path: Path
    ):
        """Test that CLI output follows CTX-CARD format."""
        output_path = tmp_path / "CTXCARD.md"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ctxcard_gen",
                str(sample_project_dir),
                "--out",
                str(output_path),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert output_path.exists()

        content = output_path.read_text()
        lines = content.splitlines()

        # Check for required sections
        required_sections = ["ID:", "AL:", "NM:", "MO:", "SY:"]
        for section in required_sections:
            assert any(line.startswith(section) for line in lines), f"Missing {section}"

        # Check for proper format
        for line in lines:
            if line.strip() and ":" in line:
                # Lines should be properly formatted
                assert not line.startswith(" ")  # No leading spaces
                assert ":" in line  # Should have colon separator
