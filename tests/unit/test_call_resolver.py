"""
Unit tests for the call resolver.
"""

from pathlib import Path
from typing import Dict, Tuple

import pytest

from ctxcard_gen.core.call_resolver import CallResolver
from ctxcard_gen.types import ModuleInfo, ScanResult, Symbol


class TestCallResolver:
    """Test cases for CallResolver."""

    def test_build_reexports_global(self):
        """Test building global re-export mappings."""
        resolver = CallResolver()

        # Create sample modules with re-exports
        modules = {}
        mi1 = ModuleInfo(id=1, path="pkg/__init__.py", dotted="pkg")
        mi1.reexports = {"pkg.helper": "pkg.utils.helper"}

        mi2 = ModuleInfo(id=2, path="pkg/utils/__init__.py", dotted="pkg.utils")
        mi2.reexports = {"pkg.utils.format": "pkg.utils.formatter.format"}

        modules["pkg/__init__.py"] = mi1
        modules["pkg/utils/__init__.py"] = mi2

        reexports = resolver.build_reexports_global(modules)

        # Check that re-exports were combined
        assert "pkg.helper" in reexports
        assert "pkg.utils.format" in reexports
        assert reexports["pkg.helper"] == "pkg.utils.helper"
        assert reexports["pkg.utils.format"] == "pkg.utils.formatter.format"

    def test_build_indices(self):
        """Test building repository indices."""
        resolver = CallResolver()

        # Create sample modules
        modules = {}
        mi1 = ModuleInfo(id=1, path="auth/service.py", dotted="auth.service")
        mi2 = ModuleInfo(id=2, path="auth/models.py", dotted="auth.models")
        mi3 = ModuleInfo(id=3, path="utils/helpers.py", dotted="utils.helpers")

        modules["auth/service.py"] = mi1
        modules["auth/models.py"] = mi2
        modules["utils/helpers.py"] = mi3

        dotted_to_path, stem_to_paths = resolver.build_indices(modules)

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
        resolver = CallResolver()

        dotted_to_path = {
            "auth": "auth/__init__.py",
            "auth.service": "auth/service.py",
            "auth.models": "auth/models.py",
            "utils": "utils/__init__.py",
            "utils.helpers": "utils/helpers.py",
        }

        # Test exact matches
        assert (
            resolver.longest_prefix_module("auth.service", dotted_to_path)
            == "auth/service.py"
        )
        assert (
            resolver.longest_prefix_module("utils.helpers", dotted_to_path)
            == "utils/helpers.py"
        )

        # Test partial matches
        assert (
            resolver.longest_prefix_module("auth.service.login", dotted_to_path)
            == "auth/service.py"
        )
        assert (
            resolver.longest_prefix_module("utils.helpers.format", dotted_to_path)
            == "utils/helpers.py"
        )

        # Test no matches
        assert (
            resolver.longest_prefix_module("nonexistent.module", dotted_to_path) is None
        )

    def test_resolve_target_function(self):
        """Test resolving function targets."""
        resolver = CallResolver()

        # Create sample modules
        modules = {}
        mi1 = ModuleInfo(id=1, path="auth/service.py", dotted="auth.service")
        mi1.fn_to_sid = {"login": 1, "logout": 2}
        mi1.prop_to_sid = {"is_authenticated": 3}

        modules["auth/service.py"] = mi1

        dotted_to_path = {"auth.service": "auth/service.py"}

        # Test function resolution
        mid, sid, reason = resolver.resolve_target(
            "auth.service.login", dotted_to_path, modules
        )
        assert mid == 1
        assert sid == 1
        assert reason == "function"

        # Test property resolution
        mid, sid, reason = resolver.resolve_target(
            "auth.service.is_authenticated", dotted_to_path, modules
        )
        assert mid == 1
        assert sid == 3
        assert reason == "function"  # Properties are treated as functions in lookup

    def test_resolve_target_class_method(self):
        """Test resolving class method targets."""
        resolver = CallResolver()

        # Create sample modules
        modules = {}
        mi1 = ModuleInfo(id=1, path="auth/service.py", dotted="auth.service")
        mi1.fn_to_sid = {"AuthService.login": 1, "AuthService.logout": 2}

        modules["auth/service.py"] = mi1

        dotted_to_path = {"auth.service": "auth/service.py"}

        # Test class method resolution
        mid, sid, reason = resolver.resolve_target(
            "auth.service.AuthService.login", dotted_to_path, modules
        )
        assert mid == 1
        assert sid == 1
        assert reason == "class_method"

    def test_resolve_target_module_anchor(self):
        """Test resolving to module anchor when function not found."""
        resolver = CallResolver()

        # Create sample modules
        modules = {}
        mi1 = ModuleInfo(id=1, path="auth/service.py", dotted="auth.service")
        mi1.fn_to_sid = {"login": 1}

        modules["auth/service.py"] = mi1

        dotted_to_path = {"auth.service": "auth/service.py"}

        # Test module anchor fallback
        mid, sid, reason = resolver.resolve_target(
            "auth.service.nonexistent", dotted_to_path, modules
        )
        assert mid == 1
        assert sid == 0
        assert reason == "module_anchor"

    def test_resolve_target_module_not_found(self):
        """Test handling when module is not found."""
        resolver = CallResolver()

        modules = {}
        dotted_to_path = {"auth.service": "auth/service.py"}

        # Test module not found
        mid, sid, reason = resolver.resolve_target(
            "nonexistent.module.func", dotted_to_path, modules
        )
        assert mid is None
        assert sid is None
        assert reason == "not_found"

    def test_dotted_from_ast(self):
        """Test extracting dotted names from AST."""
        resolver = CallResolver()

        # Test simple name
        import ast

        name_node = ast.Name(id="func")
        assert resolver._dotted_from_ast(name_node) == "func"

        # Test attribute
        attr_node = ast.Attribute(value=ast.Name(id="module"), attr="func")
        assert resolver._dotted_from_ast(attr_node) == "module.func"

        # Test nested attribute
        nested_attr = ast.Attribute(
            value=ast.Attribute(value=ast.Name(id="pkg"), attr="module"), attr="func"
        )
        assert resolver._dotted_from_ast(nested_attr) == "pkg.module.func"

    def test_process_reexports(self):
        """Test processing re-exports in __init__.py files."""
        resolver = CallResolver()

        # Create sample modules
        modules = {}
        mi1 = ModuleInfo(id=1, path="pkg/__init__.py", dotted="pkg")
        mi1.import_names = {"helper": "pkg.utils.helper", "format": "pkg.utils.format"}

        modules["pkg/__init__.py"] = mi1

        resolver.process_reexports(modules)

        # Check that re-exports were created
        assert "pkg.helper" in mi1.reexports
        assert "pkg.format" in mi1.reexports
        assert mi1.reexports["pkg.helper"] == "pkg.utils.helper"
        assert mi1.reexports["pkg.format"] == "pkg.utils.format"

    def test_extract_calls_basic(self, tmp_path: Path):
        """Test basic call extraction."""
        resolver = CallResolver()

        # Create a simple Python file with function calls
        test_file = tmp_path / "test_calls.py"
        test_file.write_text(
            """
def caller():
    local_func()
    module.func()
    pkg.module.func()

def local_func():
    pass
"""
        )

        # Create scan result
        modules = {}
        mi = ModuleInfo(id=1, path="test_calls.py", dotted="test_calls")
        mi.fn_to_sid = {"caller": 1, "local_func": 2}
        modules["test_calls.py"] = mi

        scan_result = ScanResult(modules=modules, langs=["py"])

        # Extract calls
        resolver.extract_calls(tmp_path, scan_result)

        # Check that calls were extracted
        assert len(mi.calls) > 0

    def test_extract_calls_with_imports(self, tmp_path: Path):
        """Test call extraction with import resolution."""
        resolver = CallResolver()

        # Create files with imports and calls
        main_file = tmp_path / "main.py"
        main_file.write_text(
            """
from utils import helper
from pkg.module import func

def caller():
    helper.format_name("test")
    func()
"""
        )

        utils_file = tmp_path / "utils.py"
        utils_file.write_text(
            """
def format_name(name):
    return name.upper()
"""
        )

        pkg_dir = tmp_path / "pkg"
        pkg_dir.mkdir()
        module_file = pkg_dir / "module.py"
        module_file.write_text(
            """
def func():
    return "hello"
"""
        )

        # Create scan result
        modules = {}
        mi1 = ModuleInfo(id=1, path="main.py", dotted="main")
        mi1.fn_to_sid = {"caller": 1}
        mi1.import_names = {"helper": "utils", "func": "pkg.module.func"}
        modules["main.py"] = mi1

        mi2 = ModuleInfo(id=2, path="utils.py", dotted="utils")
        mi2.fn_to_sid = {"format_name": 1}
        modules["utils.py"] = mi2

        mi3 = ModuleInfo(id=3, path="pkg/module.py", dotted="pkg.module")
        mi3.fn_to_sid = {"func": 1}
        modules["pkg/module.py"] = mi3

        scan_result = ScanResult(modules=modules, langs=["py"])

        # Extract calls
        resolver.extract_calls(tmp_path, scan_result)

        # Check that calls were extracted
        assert len(mi1.calls) > 0

    def test_extract_calls_property_suppression(self, tmp_path: Path):
        """Test that calls to properties are suppressed."""
        resolver = CallResolver()

        # Create a file with property access
        test_file = tmp_path / "test_property.py"
        test_file.write_text(
            """
class Service:
    @property
    def config(self):
        return {"setting": "value"}
    
    def method(self):
        return self.config  # This should not create a call edge
"""
        )

        # Create scan result
        modules = {}
        mi = ModuleInfo(id=1, path="test_property.py", dotted="test_property")
        mi.fn_to_sid = {"Service.method": 1}
        mi.prop_to_sid = {"Service.config": 2}

        # Add property symbol
        prop_symbol = Symbol(mid=1, sid=2, kind="prop", name="Service.config")
        mi.symbols = [prop_symbol]

        modules["test_property.py"] = mi

        scan_result = ScanResult(modules=modules, langs=["py"])

        # Extract calls
        resolver.extract_calls(tmp_path, scan_result)

        # Check that no calls to properties were created
        for caller_sid, (t_mid, t_sid) in mi.calls:
            # Should not have calls to property symbols
            assert t_sid != 2

    def test_find_caller_sid(self):
        """Test finding caller symbol ID."""
        resolver = CallResolver()

        # Create a simple AST with function calls
        import ast

        # Create AST for: def caller(): local_func()
        func_def = ast.FunctionDef(
            name="caller",
            args=ast.arguments(
                posonlyargs=[], args=[], kwonlyargs=[], defaults=[], kw_defaults=[]
            ),
            body=[
                ast.Expr(
                    value=ast.Call(func=ast.Name(id="local_func"), args=[], keywords=[])
                )
            ],
            decorator_list=[],
            returns=None,
        )

        # Add parent links
        func_def.parent = None
        for child in ast.iter_child_nodes(func_def):
            setattr(child, "parent", func_def)
            for grandchild in ast.iter_child_nodes(child):
                setattr(grandchild, "parent", child)

        # Find caller for the function call
        call_node = func_def.body[0].value
        local_lookup = {"caller": 1}

        caller_sid = resolver._find_caller_sid(call_node, local_lookup)
        assert caller_sid == 1

    def test_find_caller_sid_class_method(self):
        """Test finding caller symbol ID for class methods."""
        resolver = CallResolver()

        # Create AST for class method
        import ast

        class_def = ast.ClassDef(
            name="Service",
            bases=[],
            keywords=[],
            body=[
                ast.FunctionDef(
                    name="method",
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[ast.arg(arg="self")],
                        kwonlyargs=[],
                        defaults=[],
                        kw_defaults=[],
                    ),
                    body=[
                        ast.Expr(
                            value=ast.Call(
                                func=ast.Name(id="func"), args=[], keywords=[]
                            )
                        )
                    ],
                    decorator_list=[],
                    returns=None,
                )
            ],
            decorator_list=[],
        )

        # Add parent links
        class_def.parent = None
        for child in ast.iter_child_nodes(class_def):
            setattr(child, "parent", class_def)
            for grandchild in ast.iter_child_nodes(child):
                setattr(grandchild, "parent", child)
                for great_grandchild in ast.iter_child_nodes(grandchild):
                    setattr(great_grandchild, "parent", grandchild)

        # Find caller for the function call
        call_node = class_def.body[0].body[0].value
        local_lookup = {"Service.method": 1}

        caller_sid = resolver._find_caller_sid(call_node, local_lookup)
        assert caller_sid == 1

    def test_resolve_call_target_direct(self):
        """Test resolving direct function calls."""
        resolver = CallResolver()

        import ast

        # Create AST for: func()
        call_node = ast.Call(func=ast.Name(id="func"), args=[], keywords=[])

        # Create module info
        mi = ModuleInfo(id=1, path="test.py", dotted="test")
        mi.fn_to_sid = {"func": 1}

        dotted_to_path = {"test": "test.py"}
        modules = {"test.py": mi}
        reexports = {}

        target = resolver._resolve_call_target(
            call_node, mi, dotted_to_path, modules, reexports
        )
        assert target == (1, 1)

    def test_resolve_call_target_qualified(self):
        """Test resolving qualified function calls."""
        resolver = CallResolver()

        import ast

        # Create AST for: module.func()
        call_node = ast.Call(
            func=ast.Attribute(value=ast.Name(id="module"), attr="func"),
            args=[],
            keywords=[],
        )

        # Create module info
        mi = ModuleInfo(id=1, path="test.py", dotted="test")
        mi.import_names = {"module": "other.module"}

        dotted_to_path = {"other.module": "other/module.py"}
        other_mi = ModuleInfo(id=2, path="other/module.py", dotted="other.module")
        other_mi.fn_to_sid = {"func": 1}

        modules = {"test.py": mi, "other/module.py": other_mi}
        reexports = {}

        target = resolver._resolve_call_target(
            call_node, mi, dotted_to_path, modules, reexports
        )
        assert target == (2, 1)
