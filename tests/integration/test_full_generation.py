"""
Integration tests for full CTX-CARD generation.
"""

from pathlib import Path
from typing import Dict

import pytest

from ctxcard_gen import CTXCardGenerator
from ctxcard_gen.core.ast_analyzer import ASTAnalyzer
from ctxcard_gen.core.card_renderer import CardRenderer
from ctxcard_gen.types import GeneratorConfig


class TestFullGeneration:
    """Integration tests for complete CTX-CARD generation."""

    def test_full_generation_basic(self, sample_project_dir: Path, tmp_path: Path):
        """Test complete CTX-CARD generation from a real project."""
        output_path = tmp_path / "CTXCARD.md"

        config = GeneratorConfig(
            project_name="test-project",
            root_path=sample_project_dir,
            output_path=output_path,
            include_pattern=None,
            exclude_pattern=None,
            emit_type_signatures=False,
            delta_from=None,
            stdout_output=False,
            per_package=False,
        )

        generator = CTXCardGenerator(config)
        content = generator.generate()

        # Check that content was generated
        assert content is not None
        assert len(content) > 0

        # Check for required sections
        lines = content.splitlines()
        assert any(line.startswith("ID:") for line in lines)
        assert any(line.startswith("AL:") for line in lines)
        assert any(line.startswith("NM:") for line in lines)
        assert any(line.startswith("MO:") for line in lines)
        assert any(line.startswith("SY:") for line in lines)

        # Save output and check that file was created
        generator.save_output(content)
        assert output_path.exists()
        assert output_path.read_text() == content

    def test_full_generation_with_type_signatures(
        self, sample_project_dir: Path, tmp_path: Path
    ):
        """Test CTX-CARD generation with type signatures."""
        output_path = tmp_path / "CTXCARD.md"

        config = GeneratorConfig(
            project_name="test-project",
            root_path=sample_project_dir,
            output_path=output_path,
            include_pattern=None,
            exclude_pattern=None,
            emit_type_signatures=True,
            delta_from=None,
            stdout_output=False,
            per_package=False,
        )

        generator = CTXCardGenerator(config)
        content = generator.generate()

        # Check that TY lines were included
        lines = content.splitlines()
        assert any(line.startswith("TY:") for line in lines)
        
        # Save output
        generator.save_output(content)

    def test_full_generation_with_include_pattern(
        self, sample_project_dir: Path, tmp_path: Path
    ):
        """Test CTX-CARD generation with include pattern."""
        output_path = tmp_path / "CTXCARD.md"

        config = GeneratorConfig(
            project_name="test-project",
            root_path=sample_project_dir,
            output_path=output_path,
            include_pattern="**/*.py",
            exclude_pattern=None,
            emit_type_signatures=False,
            delta_from=None,
            stdout_output=False,
            per_package=False,
        )

        generator = CTXCardGenerator(config)
        content = generator.generate()

        # Check that content was generated
        assert content is not None
        assert len(content) > 0

        # Check that only Python files were processed
        lines = content.splitlines()
        mo_lines = [line for line in lines if line.startswith("MO:")]
        for mo_line in mo_lines:
            # Extract file path from MO line
            parts = mo_line.split(" | ")
            if len(parts) >= 2:
                file_path = parts[1]
                assert file_path.endswith(".py")
        
        # Save output
        generator.save_output(content)

    def test_full_generation_with_exclude_pattern(
        self, sample_project_dir: Path, tmp_path: Path
    ):
        """Test CTX-CARD generation with exclude pattern."""
        output_path = tmp_path / "CTXCARD.md"

        config = GeneratorConfig(
            project_name="test-project",
            root_path=sample_project_dir,
            output_path=output_path,
            include_pattern=None,
            exclude_pattern="**/tests/**",
            emit_type_signatures=False,
            delta_from=None,
            stdout_output=False,
            per_package=False,
        )

        generator = CTXCardGenerator(config)
        content = generator.generate()

        # Check that test files were excluded
        lines = content.splitlines()
        mo_lines = [line for line in lines if line.startswith("MO:")]
        for mo_line in mo_lines:
            # Extract file path from MO line
            parts = mo_line.split(" | ")
            if len(parts) >= 2:
                file_path = parts[1]
                assert "tests" not in file_path
        
        # Save output
        generator.save_output(content)

    def test_full_generation_stdout(self, sample_project_dir: Path, capsys):
        """Test CTX-CARD generation to stdout."""
        config = GeneratorConfig(
            project_name="test-project",
            root_path=sample_project_dir,
            output_path=Path("dummy.md"),
            include_pattern=None,
            exclude_pattern=None,
            emit_type_signatures=False,
            delta_from=None,
            stdout_output=True,
            per_package=False,
        )

        generator = CTXCardGenerator(config)
        content = generator.generate()
        generator.save_output(content)

        # Check that content was written to stdout
        captured = capsys.readouterr()
        assert captured.out == content
        assert len(captured.out) > 0

    def test_full_generation_per_package(
        self, sample_project_dir: Path, tmp_path: Path
    ):
        """Test CTX-CARD generation with per-package files."""
        output_path = tmp_path / "CTXCARD.md"

        config = GeneratorConfig(
            project_name="test-project",
            root_path=sample_project_dir,
            output_path=output_path,
            include_pattern=None,
            exclude_pattern=None,
            emit_type_signatures=False,
            delta_from=None,
            stdout_output=False,
            per_package=True,
        )

        generator = CTXCardGenerator(config)
        content = generator.generate()
        generator.save_output(content)

        # Generate per-package files
        packages = generator.generate_per_package(content)
        generator.save_per_package(packages)

        # Check that package files were created
        for pkg_name in packages.keys():
            pkg_file = tmp_path / f"CTXCARD.{pkg_name}.md"
            assert pkg_file.exists()
            assert len(pkg_file.read_text()) > 0

    def test_full_generation_with_delta(self, sample_project_dir: Path, tmp_path: Path):
        """Test CTX-CARD generation with delta computation."""
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
            root_path=sample_project_dir,
            output_path=output_path,
            include_pattern=None,
            exclude_pattern=None,
            emit_type_signatures=False,
            delta_from=old_path,
            stdout_output=False,
            per_package=False,
        )

        generator = CTXCardGenerator(config)
        content = generator.generate()

        # Check that delta was included
        lines = content.splitlines()
        delta_lines = [line for line in lines if line.startswith("DELTA:")]
        assert len(delta_lines) > 0
        
        # Save output
        generator.save_output(content)

    def test_ast_analyzer_integration(self, sample_project_dir: Path):
        """Test AST analyzer integration."""
        analyzer = ASTAnalyzer()

        scan_result = analyzer.analyze_repository(
            sample_project_dir, include_glob=None, exclude_glob=None
        )

        # Check that modules were found
        assert len(scan_result.modules) > 0

        # Check that Python was detected
        assert "py" in scan_result.langs

        # Validate analysis
        analyzer.validate_analysis(scan_result)

        # Get statistics
        stats = analyzer.get_statistics(scan_result)
        assert stats["modules"] > 0
        assert stats["symbols"] > 0
        assert stats["languages"] > 0

    def test_card_renderer_integration(self, sample_project_dir: Path):
        """Test card renderer integration."""
        analyzer = ASTAnalyzer()
        renderer = CardRenderer()

        # Analyze repository
        scan_result = analyzer.analyze_repository(
            sample_project_dir, include_glob=None, exclude_glob=None
        )

        # Render CTX-CARD
        content = renderer.render_card(
            "test-project",
            scan_result.langs,
            "pep8",
            scan_result.modules,
            emit_ty=False,
        )

        # Validate output
        renderer.validate_output(content)

        # Check that content was generated
        assert content is not None
        assert len(content) > 0

        # Check for required sections
        lines = content.splitlines()
        assert any(line.startswith("ID:") for line in lines)
        assert any(line.startswith("AL:") for line in lines)
        assert any(line.startswith("NM:") for line in lines)
        assert any(line.startswith("MO:") for line in lines)
        assert any(line.startswith("SY:") for line in lines)

    def test_end_to_end_workflow(self, sample_project_dir: Path, tmp_path: Path):
        """Test complete end-to-end workflow."""
        output_path = tmp_path / "CTXCARD.md"

        config = GeneratorConfig(
            project_name="test-project",
            root_path=sample_project_dir,
            output_path=output_path,
            include_pattern="**/*.py",
            exclude_pattern="**/tests/**",
            emit_type_signatures=True,
            delta_from=None,
            stdout_output=False,
            per_package=True,
        )

        generator = CTXCardGenerator(config)

        # Generate main CTX-CARD
        content = generator.generate()
        generator.save_output(content)

        # Generate per-package files
        packages = generator.generate_per_package(content)
        generator.save_per_package(packages)

        # Verify main file
        assert output_path.exists()
        main_content = output_path.read_text()
        assert len(main_content) > 0

        # Verify package files
        for pkg_name, pkg_content in packages.items():
            pkg_file = tmp_path / f"CTXCARD.{pkg_name}.md"
            assert pkg_file.exists()
            assert pkg_file.read_text() == pkg_content

        # Verify content structure
        lines = main_content.splitlines()

        # Check for all required sections
        required_sections = ["ID:", "AL:", "NM:", "MO:", "SY:"]
        for section in required_sections:
            assert any(line.startswith(section) for line in lines)

        # Check for optional sections that should be present
        optional_sections = ["SG:", "DT:", "ER:", "ED:", "CN:", "RV:"]
        for section in optional_sections:
            assert any(line.startswith(section) for line in lines)

        # Check for type signatures (since emit_ty=True)
        assert any(line.startswith("TY:") for line in lines)

    def test_error_handling_invalid_path(self, tmp_path: Path):
        """Test error handling with invalid project path."""
        output_path = tmp_path / "CTXCARD.md"
        invalid_path = tmp_path / "nonexistent"

        config = GeneratorConfig(
            project_name="test-project",
            root_path=invalid_path,
            output_path=output_path,
            include_pattern=None,
            exclude_pattern=None,
            emit_type_signatures=False,
            delta_from=None,
            stdout_output=False,
            per_package=False,
        )

        generator = CTXCardGenerator(config)

        # Should handle gracefully or raise appropriate exception
        try:
            content = generator.generate()
            # If it doesn't raise, content should be empty or minimal
            assert content is not None
        except Exception as e:
            # Should raise a meaningful exception
            assert "modules" in str(e).lower() or "repository" in str(e).lower()

    def test_performance_large_project(self, tmp_path: Path):
        """Test performance with a larger project structure."""
        # Create a larger project structure
        project_dir = tmp_path / "large_project"
        project_dir.mkdir()

        # Create multiple packages with many files
        for pkg_num in range(3):
            pkg_dir = project_dir / f"pkg_{pkg_num}"
            pkg_dir.mkdir()

            # Create __init__.py
            (pkg_dir / "__init__.py").write_text(f"# Package {pkg_num}")

            # Create multiple modules
            for mod_num in range(5):
                mod_file = pkg_dir / f"module_{mod_num}.py"
                mod_content = f"""
from typing import Optional, List

class Class{mod_num}:
    def __init__(self, value: str):
        self.value = value
    
    def method_{mod_num}(self) -> Optional[str]:
        return self.value.upper()

def function_{mod_num}(items: List[str]) -> List[str]:
    return [item.upper() for item in items]
"""
                mod_file.write_text(mod_content)

        output_path = tmp_path / "CTXCARD.md"

        config = GeneratorConfig(
            project_name="large-project",
            root_path=project_dir,
            output_path=output_path,
            include_pattern="**/*.py",
            exclude_pattern=None,
            emit_type_signatures=False,
            delta_from=None,
            stdout_output=False,
            per_package=False,
        )

        generator = CTXCardGenerator(config)

        # Should complete within reasonable time
        import time

        start_time = time.time()
        content = generator.generate()
        end_time = time.time()

        # Should complete in under 10 seconds for this size
        assert end_time - start_time < 10.0

        # Should generate substantial content
        assert len(content) > 1000

        # Should have multiple modules
        lines = content.splitlines()
        mo_lines = [line for line in lines if line.startswith("MO:")]
        assert len(mo_lines) >= 15  # 3 packages * 5 modules + __init__.py files
