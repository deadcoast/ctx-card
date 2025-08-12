"""
Unit tests for call resolver module.

This module tests the cross-module function call resolution functionality.
"""

# Note: pytest import is handled by test runner
try:
    import pytest
except ImportError:
    pytest = None

from src.ctxcard_gen.core.call_resolver import CallResolver
from src.ctxcard_gen.types import ModuleInfo, Symbol


class TestCallResolver:
    """Test cases for call resolver functionality."""

    def test_init(self):
        """Test call resolver initialization."""
        resolver = CallResolver()
        assert resolver is not None

    def test_build_reexports_global_empty(self):
        """Test building re-exports with empty modules."""
        resolver = CallResolver()
        modules = {}
        reexports = resolver.build_reexports_global(modules)
        assert not reexports

    def test_build_reexports_global_single_module(self):
        """Test building re-exports with single module."""
        resolver = CallResolver()
        modules = {
            "test_module": ModuleInfo(
                id=1,
                path="test_module.py",
                dotted="test_module",
                role_tags=set(),
            )
        }
        reexports = resolver.build_reexports_global(modules)
        assert not reexports

    def test_build_reexports_global_with_reexports(self):
        """Test building re-exports with actual re-export patterns."""
        resolver = CallResolver()
        modules = {
            "test_module": ModuleInfo(
                id=1,
                path="test_module.py",
                dotted="test_module",
                symbols=[
                    Symbol(
                        mid=1,
                        sid=1,
                        kind="var",
                        name="__all__",
                    )
                ],
                role_tags=set(),
            )
        }
        reexports = resolver.build_reexports_global(modules)
        # Should handle __all__ exports
        assert isinstance(reexports, dict)

    def test_build_indices_empty(self):
        """Test building indices with empty modules."""
        resolver = CallResolver()
        modules = {}
        dotted_to_path, stem_to_paths = resolver.build_indices(modules)
        assert not dotted_to_path
        assert not stem_to_paths

    def test_build_indices_single_module(self):
        """Test building indices with single module."""
        resolver = CallResolver()
        modules = {
            "test_module.py": ModuleInfo(
                id=1,
                path="test_module.py",
                dotted="test_module",
                role_tags=set(),
            )
        }
        dotted_to_path, stem_to_paths = resolver.build_indices(modules)
        assert dotted_to_path["test_module"] == "test_module.py"
        assert stem_to_paths["test_module"] == ["test_module.py"]

    def test_longest_prefix_module_exact_match(self):
        """Test longest prefix module with exact match."""
        resolver = CallResolver()
        dotted_to_path = {
            "test_module": "test_module.py",
            "test_module.submodule": "test_module/submodule.py",
        }

        result = resolver.longest_prefix_module("test_module", dotted_to_path)
        assert result == "test_module.py"

    def test_longest_prefix_module_nested(self):
        """Test longest prefix module with nested match."""
        resolver = CallResolver()
        dotted_to_path = {
            "test_module": "test_module.py",
            "test_module.submodule": "test_module/submodule.py",
        }

        result = resolver.longest_prefix_module(
            "test_module.submodule.function", dotted_to_path
        )
        assert result == "test_module/submodule.py"

    def test_longest_prefix_module_no_match(self):
        """Test longest prefix module with no match."""
        resolver = CallResolver()
        dotted_to_path = {
            "test_module": "test_module.py",
        }

        result = resolver.longest_prefix_module("nonexistent.module", dotted_to_path)
        assert result is None

    def test_resolve_target_function(self):
        """Test resolving function target."""
        resolver = CallResolver()
        modules = {
            "test_module.py": ModuleInfo(
                id=1,
                path="test_module.py",
                dotted="test_module",
                fn_to_sid={"function": 1},
                role_tags=set(),
            )
        }
        dotted_to_path = {"test_module": "test_module.py"}

        mid, sid, reason = resolver.resolve_target(
            "test_module.function", dotted_to_path, modules
        )
        assert mid == 1
        assert sid == 1
        assert reason == "function"

    def test_resolve_target_class_method(self):
        """Test resolving class method target."""
        resolver = CallResolver()
        modules = {
            "test_module.py": ModuleInfo(
                id=1,
                path="test_module.py",
                dotted="test_module",
                fn_to_sid={"Class.method": 1},
                role_tags=set(),
            )
        }
        dotted_to_path = {"test_module": "test_module.py"}

        mid, sid, reason = resolver.resolve_target(
            "test_module.Class.method", dotted_to_path, modules
        )
        assert mid == 1
        assert sid == 1
        assert reason == "class_method"

    def test_resolve_target_module_anchor(self):
        """Test resolving to module anchor when function not found."""
        resolver = CallResolver()
        modules = {
            "test_module.py": ModuleInfo(
                id=1,
                path="test_module.py",
                dotted="test_module",
                role_tags=set(),
            )
        }
        dotted_to_path = {"test_module": "test_module.py"}

        mid, sid, reason = resolver.resolve_target(
            "test_module.nonexistent", dotted_to_path, modules
        )
        assert mid == 1
        assert sid == 0
        assert reason == "module_anchor"

    def test_resolve_target_not_found(self):
        """Test resolving target that doesn't exist."""
        resolver = CallResolver()
        modules = {}
        dotted_to_path = {}

        mid, sid, reason = resolver.resolve_target(
            "nonexistent.module.function", dotted_to_path, modules
        )
        assert mid is None
        assert sid is None
        assert reason == "not_found"
