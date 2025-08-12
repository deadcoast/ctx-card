"""
Unit tests for the repository scanner.
"""

from pathlib import Path
from typing import Set

import pytest

from ctxcard_gen.core.scanner import RepoScanner
from ctxcard_gen.types import ModuleInfo, Symbol


class TestRepoScanner:
    """Test cases for RepoScanner."""

    def test_is_code_file(self):
        """Test code file detection."""
        scanner = RepoScanner()

        # Test Python files - create a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            assert scanner.is_code_file(temp_path)
        finally:
            temp_path.unlink()  # Clean up
        
        # Test __init__.py file - create directory and file
        import tempfile
        import os
        temp_dir = tempfile.mkdtemp()
        try:
            init_path = Path(temp_dir) / "module" / "__init__.py"
            init_path.parent.mkdir(exist_ok=True)
            init_path.write_text("# init file")
            assert scanner.is_code_file(init_path)
        finally:
            import shutil
            shutil.rmtree(temp_dir)

        # Test other code files - create temporary files
        for ext in [".ts", ".js", ".go"]:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                temp_path = Path(f.name)
            try:
                assert scanner.is_code_file(temp_path)
            finally:
                temp_path.unlink()

        # Test non-code files
        assert not scanner.is_code_file(Path("test.txt"))
        assert not scanner.is_code_file(Path("test.md"))
        assert not scanner.is_code_file(Path("test.json"))

    def test_role_tags_for(self):
        """Test role tag detection."""
        scanner = RepoScanner()

        # Test service tags
        assert "svc" in scanner.role_tags_for("service.py")
        assert "svc" in scanner.role_tags_for("auth_service.py")

        # Test repository tags
        assert "repo" in scanner.role_tags_for("repository.py")
        assert "repo" in scanner.role_tags_for("user_repo.py")

        # Test API tags
        assert "api" in scanner.role_tags_for("api.py")
        assert "api" in scanner.role_tags_for("rest_api.py")

        # Test auth tags
        assert "auth" in scanner.role_tags_for("auth.py")
        assert "auth" in scanner.role_tags_for("authentication.py")

        # Test test tags
        assert "test" in scanner.role_tags_for("test_service.py")
        assert "test" in scanner.role_tags_for("tests/test_auth.py")

        # Test default tag
        tags = scanner.role_tags_for("utils.py")
        assert "mod" in tags

    def test_detect_langs(self, tmp_path: Path):
        """Test language detection."""
        scanner = RepoScanner()

        # Create files with different extensions
        (tmp_path / "test.py").touch()
        (tmp_path / "test.ts").touch()
        (tmp_path / "test.js").touch()
        (tmp_path / "test.txt").touch()  # Should be ignored

        langs = scanner.detect_langs(tmp_path)
        assert "py" in langs
        assert "ts" in langs
        assert "js" in langs
        assert "txt" not in langs

    def test_build_indices(self):
        """Test repository index building."""
        scanner = RepoScanner()

        # Create sample modules
        modules = {}
        mi1 = ModuleInfo(id=1, path="auth/service.py", dotted="auth.service")
        mi2 = ModuleInfo(id=2, path="auth/models.py", dotted="auth.models")
        mi3 = ModuleInfo(id=3, path="utils/helpers.py", dotted="utils.helpers")

        modules["auth/service.py"] = mi1
        modules["auth/models.py"] = mi2
        modules["utils/helpers.py"] = mi3

        dotted_to_path, stem_to_paths = scanner.build_indices(modules)

        # Test dotted to path mapping
        assert dotted_to_path["auth.service"] == "auth/service.py"
        assert dotted_to_path["auth.models"] == "auth/models.py"
        assert dotted_to_path["utils.helpers"] == "utils/helpers.py"

        # Test stem to paths mapping
        assert "service" in stem_to_paths
        assert "models" in stem_to_paths
        assert "helpers" in stem_to_paths
        assert len(stem_to_paths["service"]) == 1
        assert stem_to_paths["service"][0] == "auth/service.py"

    def test_longest_prefix_module(self):
        """Test longest prefix module resolution."""
        scanner = RepoScanner()

        dotted_to_path = {
            "auth": "auth/__init__.py",
            "auth.service": "auth/service.py",
            "auth.models": "auth/models.py",
            "utils": "utils/__init__.py",
            "utils.helpers": "utils/helpers.py",
        }

        # Test exact matches
        assert (
            scanner.longest_prefix_module("auth.service", dotted_to_path)
            == "auth/service.py"
        )
        assert (
            scanner.longest_prefix_module("utils.helpers", dotted_to_path)
            == "utils/helpers.py"
        )

        # Test partial matches
        assert (
            scanner.longest_prefix_module("auth.service.method", dotted_to_path)
            == "auth/service.py"
        )
        assert (
            scanner.longest_prefix_module("utils.helpers.format", dotted_to_path)
            == "utils/helpers.py"
        )

        # Test no matches
        assert (
            scanner.longest_prefix_module("nonexistent.module", dotted_to_path) is None
        )

    def test_scan_repo_basic(self, sample_project_dir: Path):
        """Test basic repository scanning."""
        scanner = RepoScanner()

        scan_result = scanner.scan_repo(sample_project_dir, None, None)

        # Check that modules were found
        assert len(scan_result.modules) > 0

        # Check that Python was detected
        assert "py" in scan_result.langs

        # Check that specific files were processed
        expected_files = [
            "main_pkg/__init__.py",
            "main_pkg/service.py",
            "main_pkg/models.py",
            "main_pkg/repository.py",
            "api/routes.py",
            "utils/helpers.py",
        ]

        for expected_file in expected_files:
            found = any(mi.path == expected_file for mi in scan_result.modules.values())
            assert found, f"Expected file {expected_file} not found in scan result"

    def test_scan_repo_with_include(self, sample_project_dir: Path):
        """Test repository scanning with include pattern."""
        scanner = RepoScanner()

        # Only include Python files
        scan_result = scanner.scan_repo(sample_project_dir, "**/*.py", None)

        # Check that only Python files were included
        for mi in scan_result.modules.values():
            assert mi.path.endswith(".py")

    def test_scan_repo_with_exclude(self, sample_project_dir: Path):
        """Test repository scanning with exclude pattern."""
        scanner = RepoScanner()

        # Exclude test files
        scan_result = scanner.scan_repo(sample_project_dir, None, "**/tests/**")

        # Check that test files were excluded
        for mi in scan_result.modules.values():
            assert "tests" not in mi.path

    def test_symbol_extraction(self, sample_project_dir: Path):
        """Test symbol extraction from Python files."""
        scanner = RepoScanner()

        scan_result = scanner.scan_repo(sample_project_dir, None, None)

        # Find the service module
        service_module = None
        for mi in scan_result.modules.values():
            if "service.py" in mi.path:
                service_module = mi
                break

        assert service_module is not None

        # Check that symbols were extracted
        symbols = {s.name for s in service_module.symbols}
        assert "AuthService" in symbols

        # Check that functions were extracted
        fn_symbols = [s for s in service_module.symbols if s.kind == "fn"]
        assert len(fn_symbols) > 0

        # Check that properties were extracted
        prop_symbols = [s for s in service_module.symbols if s.kind == "prop"]
        assert len(prop_symbols) > 0

    def test_dto_detection(self, sample_project_dir: Path):
        """Test DTO detection."""
        scanner = RepoScanner()

        scan_result = scanner.scan_repo(sample_project_dir, None, None)

        # Find the models module
        models_module = None
        for mi in scan_result.modules.values():
            if "models.py" in mi.path:
                models_module = mi
                break

        assert models_module is not None

        # Check that DTOs were detected
        assert len(models_module.dts) > 0

        # Check for specific DTOs
        dto_names = [name for name, _ in models_module.dts]
        assert "UserCreds" in dto_names
        assert "User" in dto_names

    def test_error_detection(self, sample_project_dir: Path):
        """Test error detection."""
        scanner = RepoScanner()

        scan_result = scanner.scan_repo(sample_project_dir, None, None)

        # Find the models module
        models_module = None
        for mi in scan_result.modules.values():
            if "models.py" in mi.path:
                models_module = mi
                break

        assert models_module is not None

        # Check that errors were detected
        assert len(models_module.errors) > 0

        # Check for specific errors
        error_names = [name for name, _, _ in models_module.errors]
        assert "AuthError" in error_names
        assert "ValidationError" in error_names

    def test_linting_violations(self, sample_project_dir: Path):
        """Test linting violation detection."""
        scanner = RepoScanner()

        scan_result = scanner.scan_repo(sample_project_dir, None, None)

        # Find the bad_code module
        bad_code_module = None
        for mi in scan_result.modules.values():
            if "bad_code.py" in mi.path:
                bad_code_module = mi
                break

        assert bad_code_module is not None

        # Check that linting violations were detected
        assert len(bad_code_module.px) > 0

        # Check for specific violations
        violation_rules = [rule for rule, _ in bad_code_module.px]
        assert any("bare except" in rule for rule in violation_rules)
        assert any("eval/exec" in rule for rule in violation_rules)
        assert any("mutable default" in rule for rule in violation_rules)
        assert any("print in production" in rule for rule in violation_rules)

    def test_route_detection(self, sample_project_dir: Path):
        """Test API route detection."""
        scanner = RepoScanner()

        scan_result = scanner.scan_repo(sample_project_dir, None, None)

        # Find the routes module
        routes_module = None
        for mi in scan_result.modules.values():
            if "routes.py" in mi.path:
                routes_module = mi
                break

        assert routes_module is not None

        # Check that routes were detected
        assert len(routes_module.routes) > 0

        # Check for specific routes
        route_paths = [path for _, _, path, _ in routes_module.routes]
        assert "/login" in route_paths
        assert "/users/{user_id}" in route_paths

    def test_import_resolution(self, sample_project_dir: Path):
        """Test import resolution."""
        scanner = RepoScanner()

        scan_result = scanner.scan_repo(sample_project_dir, None, None)

        # Check that imports were resolved
        for mi in scan_result.modules.values():
            if "service.py" in mi.path:
                # Should have imports to models and repository
                assert len(mi.imports_paths) > 0
                break

    def test_reexport_processing(self, sample_project_dir: Path):
        """Test re-export processing."""
        from ctxcard_gen.core.ast_analyzer import ASTAnalyzer

        analyzer = ASTAnalyzer()
        scan_result = analyzer.analyze_repository(sample_project_dir, None, None)

        # Find the __init__.py module
        init_module = None
        for mi in scan_result.modules.values():
            if "__init__.py" in mi.path:
                init_module = mi
                break

        assert init_module is not None

        # Check that re-exports were processed
        assert len(init_module.reexports) > 0

    def test_enum_detection(self, tmp_path: Path):
        """Test enum detection."""
        scanner = RepoScanner()

        # Create a file with enum
        enum_file = tmp_path / "test_enum.py"
        enum_file.write_text(
            """
from enum import Enum

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
"""
        )

        scan_result = scanner.scan_repo(tmp_path, None, None)

        # Check that enum was detected
        for mi in scan_result.modules.values():
            if "test_enum.py" in mi.path:
                assert len(mi.tokens) > 0
                token_names = [name for name, _ in mi.tokens]
                assert "UserRole" in token_names
                break

    def test_descriptor_detection(self, tmp_path: Path):
        """Test descriptor detection."""
        scanner = RepoScanner()

        # Create a file with descriptor
        desc_file = tmp_path / "test_descriptor.py"
        desc_file.write_text(
            """
class Descriptor:
    def __get__(self, obj, objtype=None):
        return "value"
    
    def __set__(self, obj, value):
        pass
"""
        )

        scan_result = scanner.scan_repo(tmp_path, None, None)

        # Check that descriptor was detected
        for mi in scan_result.modules.values():
            if "test_descriptor.py" in mi.path:
                for symbol in mi.symbols:
                    if symbol.name == "Descriptor":
                        assert "descriptor" in symbol.modifiers
                        break
                break
