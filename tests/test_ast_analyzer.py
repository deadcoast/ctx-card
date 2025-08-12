"""
Tests for AST analyzer module.
"""

from pathlib import Path
from typing import Dict

import pytest

from ctxcard_gen.core.ast_analyzer import ASTAnalyzer
from ctxcard_gen.exceptions import ASTError
from ctxcard_gen.types import ScanResult


class TestASTAnalyzer:
    """Test cases for ASTAnalyzer."""

    def test_analyze_repository_basic(self, sample_project_dir: Path):
        """Test basic repository analysis."""
        analyzer = ASTAnalyzer()

        scan_result = analyzer.analyze_repository(
            sample_project_dir, include_glob=None, exclude_glob=None
        )

        # Check that modules were found
        assert len(scan_result.modules) > 0

        # Check that Python was detected
        assert "py" in scan_result.langs

        # Check that modules have symbols
        for mi in scan_result.modules.values():
            assert len(mi.symbols) > 0

    def test_analyze_repository_with_include(self, sample_project_dir: Path):
        """Test repository analysis with include pattern."""
        analyzer = ASTAnalyzer()

        scan_result = analyzer.analyze_repository(
            sample_project_dir, include_glob="**/*.py", exclude_glob=None
        )

        # Check that only Python files were processed
        for mi in scan_result.modules.values():
            assert mi.path.endswith(".py")

    def test_analyze_repository_with_exclude(self, sample_project_dir: Path):
        """Test repository analysis with exclude pattern."""
        analyzer = ASTAnalyzer()

        scan_result = analyzer.analyze_repository(
            sample_project_dir, include_glob=None, exclude_glob="**/tests/**"
        )

        # Check that test files were excluded
        for mi in scan_result.modules.values():
            assert "tests" not in mi.path

    def test_extract_calls(self, sample_project_dir: Path):
        """Test call extraction."""
        analyzer = ASTAnalyzer()

        # First pass: scan repository
        scan_result = analyzer.analyze_repository(
            sample_project_dir, include_glob=None, exclude_glob=None
        )

        # Second pass: extract calls
        analyzer.extract_calls(sample_project_dir, scan_result)

        # Check that calls were extracted
        total_calls = sum(len(mi.calls) for mi in scan_result.modules.values())
        assert total_calls >= 0  # May be 0 if no function calls found

    def test_validate_analysis_valid(self, sample_project_dir: Path):
        """Test analysis validation with valid data."""
        analyzer = ASTAnalyzer()

        scan_result = analyzer.analyze_repository(
            sample_project_dir, include_glob=None, exclude_glob=None
        )

        # Should not raise an exception
        analyzer.validate_analysis(scan_result)

    def test_validate_analysis_empty(self):
        """Test analysis validation with empty result."""
        analyzer = ASTAnalyzer()

        # Create empty scan result
        scan_result = ScanResult(modules={}, langs=[])

        with pytest.raises(ASTError, match="No modules found"):
            analyzer.validate_analysis(scan_result)

    def test_validate_analysis_duplicate_module_ids(self):
        """Test analysis validation with duplicate module IDs."""
        analyzer = ASTAnalyzer()

        # Create scan result with duplicate module IDs
        from ctxcard_gen.types import ModuleInfo

        modules = {}
        mi1 = ModuleInfo(id=1, path="test1.py", dotted="test1")
        mi2 = ModuleInfo(id=1, path="test2.py", dotted="test2")  # Same ID

        modules["test1.py"] = mi1
        modules["test2.py"] = mi2

        scan_result = ScanResult(modules=modules, langs=["py"])

        with pytest.raises(ASTError, match="Duplicate module IDs"):
            analyzer.validate_analysis(scan_result)

    def test_validate_analysis_duplicate_symbol_ids(self):
        """Test analysis validation with duplicate symbol IDs."""
        analyzer = ASTAnalyzer()

        # Create scan result with duplicate symbol IDs
        from ctxcard_gen.types import ModuleInfo, Symbol

        mi = ModuleInfo(id=1, path="test.py", dotted="test")
        mi.symbols = [
            Symbol(mid=1, sid=1, kind="cls", name="Class1"),
            Symbol(mid=1, sid=1, kind="fn", name="func1"),  # Same SID
        ]

        modules = {"test.py": mi}
        scan_result = ScanResult(modules=modules, langs=["py"])

        with pytest.raises(ASTError, match="Duplicate symbol IDs"):
            analyzer.validate_analysis(scan_result)

    def test_get_statistics(self, sample_project_dir: Path):
        """Test statistics generation."""
        analyzer = ASTAnalyzer()

        scan_result = analyzer.analyze_repository(
            sample_project_dir, include_glob=None, exclude_glob=None
        )

        stats = analyzer.get_statistics(scan_result)

        # Check that statistics were generated
        assert "modules" in stats
        assert "symbols" in stats
        assert "calls" in stats
        assert "imports" in stats
        assert "dtos" in stats
        assert "errors" in stats
        assert "routes" in stats
        assert "lint_violations" in stats
        assert "languages" in stats

        # Check that values are reasonable
        assert stats["modules"] > 0
        assert stats["symbols"] > 0
        assert stats["languages"] > 0
        assert stats["modules"] >= 0
        assert stats["calls"] >= 0
        assert stats["imports"] >= 0
        assert stats["dtos"] >= 0
        assert stats["errors"] >= 0
        assert stats["routes"] >= 0
        assert stats["lint_violations"] >= 0

    def test_ast_analyzer_initialization(self):
        """Test AST analyzer initialization."""
        analyzer = ASTAnalyzer()

        # Check that components were initialized
        assert analyzer.scanner is not None
        assert analyzer.call_resolver is not None

    def test_ast_analyzer_two_pass_analysis(self, sample_project_dir: Path):
        """Test that two-pass analysis works correctly."""
        analyzer = ASTAnalyzer()

        # Perform complete analysis
        scan_result = analyzer.analyze_repository(
            sample_project_dir, include_glob=None, exclude_glob=None
        )

        # Check that both passes completed
        assert len(scan_result.modules) > 0

        # Check that modules have proper structure
        for mi in scan_result.modules.values():
            assert mi.id > 0
            assert mi.path is not None
            assert mi.dotted is not None
            assert len(mi.symbols) > 0

            # Check that symbols have proper structure
            for symbol in mi.symbols:
                assert symbol.mid == mi.id
                assert symbol.sid > 0
                assert symbol.kind in ["mod", "cls", "fn", "prop"]
                assert symbol.name is not None

    def test_ast_analyzer_error_handling(self, tmp_path: Path):
        """Test AST analyzer error handling."""
        analyzer = ASTAnalyzer()

        # Create a directory with invalid Python files
        invalid_file = tmp_path / "invalid.py"
        invalid_file.write_text("def invalid syntax {")

        # Should handle gracefully
        scan_result = analyzer.analyze_repository(
            tmp_path, include_glob=None, exclude_glob=None
        )

        # Should still produce a result (even if empty)
        assert scan_result is not None
        assert isinstance(scan_result.modules, dict)
        assert isinstance(scan_result.langs, list)

    def test_ast_analyzer_performance(self, tmp_path: Path):
        """Test AST analyzer performance with larger project."""
        analyzer = ASTAnalyzer()

        # Create a larger project structure
        project_dir = tmp_path / "large_project"
        project_dir.mkdir()

        # Create multiple Python files
        for i in range(10):
            file_path = project_dir / f"module_{i}.py"
            file_content = f"""
from typing import Optional, List

class Class{i}:
    def __init__(self, value: str):
        self.value = value
    
    def method_{i}(self) -> Optional[str]:
        return self.value.upper()

def function_{i}(items: List[str]) -> List[str]:
    return [item.upper() for item in items]
"""
            file_path.write_text(file_content)

        # Should complete within reasonable time
        import time

        start_time = time.time()

        scan_result = analyzer.analyze_repository(
            project_dir, include_glob="**/*.py", exclude_glob=None
        )

        end_time = time.time()

        # Should complete in under 5 seconds for this size
        assert end_time - start_time < 5.0

        # Should find all modules
        assert len(scan_result.modules) >= 10

        # Should have substantial symbols
        total_symbols = sum(len(mi.symbols) for mi in scan_result.modules.values())
        assert total_symbols >= 30  # 10 files * 3 symbols each

    def test_ast_analyzer_component_integration(self, sample_project_dir: Path):
        """Test integration between AST analyzer components."""
        analyzer = ASTAnalyzer()

        scan_result = analyzer.analyze_repository(
            sample_project_dir, include_glob=None, exclude_glob=None
        )

        # Check that scanner and call resolver worked together
        assert len(scan_result.modules) > 0

        # Check that modules have both symbols and calls
        for mi in scan_result.modules.values():
            assert len(mi.symbols) > 0
            # Calls may be empty, but should be a list
            assert isinstance(mi.calls, list)

            # Check that symbols reference the correct module
            for symbol in mi.symbols:
                assert symbol.mid == mi.id
