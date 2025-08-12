"""
Unit tests for utility modules.
"""

from pathlib import Path
from typing import List, Tuple

import pytest

from ctxcard_gen.utils.helpers import (
    ann_to_str,
    ascii_only,
    file_to_dotted,
    is_probably_binary,
    relpath,
    today_stamp,
)
from ctxcard_gen.utils.validation import (
    validate_edges,
    validate_indices,
    validate_prefix_free,
    validate_regex_patterns,
)


class TestHelpers:
    """Test cases for helper functions."""

    def test_today_stamp(self):
        """Test today's date stamp generation."""
        stamp = today_stamp()

        # Check format (YYYYMMDD)
        assert len(stamp) == 8
        assert stamp.isdigit()

        # Check it's a reasonable date
        year = int(stamp[:4])
        month = int(stamp[4:6])
        day = int(stamp[6:8])

        assert 2020 <= year <= 2030
        assert 1 <= month <= 12
        assert 1 <= day <= 31

    def test_relpath_success(self, tmp_path: Path):
        """Test relative path generation when possible."""
        root = tmp_path / "root"
        root.mkdir()

        file_path = root / "subdir" / "file.txt"
        file_path.parent.mkdir()
        file_path.touch()

        result = relpath(file_path, root)
        assert result == "subdir/file.txt"

    def test_relpath_fallback(self, tmp_path: Path):
        """Test relative path fallback to absolute."""
        root = tmp_path / "root"
        root.mkdir()

        file_path = tmp_path / "other" / "file.txt"
        file_path.parent.mkdir()
        file_path.touch()

        result = relpath(file_path, root)
        # Should fall back to absolute path
        assert result == str(file_path.as_posix())

    def test_is_probably_binary_text(self, tmp_path: Path):
        """Test binary detection with text file."""
        text_file = tmp_path / "text.txt"
        text_file.write_text("This is a text file\nwith multiple lines.")

        assert not is_probably_binary(text_file)

    def test_is_probably_binary_binary(self, tmp_path: Path):
        """Test binary detection with binary file."""
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")

        assert is_probably_binary(binary_file)

    def test_is_probably_binary_mixed(self, tmp_path: Path):
        """Test binary detection with mixed content."""
        mixed_file = tmp_path / "mixed.txt"
        mixed_file.write_bytes(b"Text content\x00\x01\x02\x03")

        assert is_probably_binary(mixed_file)

    def test_ascii_only_clean(self):
        """Test ASCII-only conversion with clean string."""
        clean_str = "Hello, World! 123"
        result = ascii_only(clean_str)

        assert result == clean_str

    def test_ascii_only_with_unicode(self):
        """Test ASCII-only conversion with Unicode characters."""
        unicode_str = "Hello, 世界! 123"
        result = ascii_only(unicode_str)

        # Should remove non-ASCII characters
        assert result == "Hello, ! 123"
        assert result.isascii()

    def test_file_to_dotted_python(self):
        """Test file path to dotted name conversion for Python files."""
        # Regular Python file
        assert file_to_dotted("module/file.py") == "module.file"
        assert file_to_dotted("pkg/subpkg/module.py") == "pkg.subpkg.module"

        # __init__.py file
        assert file_to_dotted("pkg/__init__.py") == "pkg"
        assert file_to_dotted("pkg/subpkg/__init__.py") == "pkg.subpkg"

        # Non-Python file
        assert file_to_dotted("module/file.txt") == "module.file.txt"

    def test_ann_to_str_none(self):
        """Test annotation to string conversion with None."""
        result = ann_to_str(None)
        assert result == ""

    def test_ann_to_str_simple(self):
        """Test annotation to string conversion with simple types."""
        import ast

        # Simple name
        name_ann = ast.Name(id="str")
        result = ann_to_str(name_ann)
        assert result == "str"

        # Simple attribute
        attr_ann = ast.Attribute(value=ast.Name(id="typing"), attr="Optional")
        result = ann_to_str(attr_ann)
        assert result == "typing.Optional"

    def test_ann_to_str_complex(self):
        """Test annotation to string conversion with complex types."""
        import ast

        # Union type
        union_ann = ast.BinOp(
            left=ast.Name(id="str"), op=ast.BitOr(), right=ast.Name(id="None")
        )
        result = ann_to_str(union_ann)
        assert result == "str | None"

    def test_ann_to_str_error_handling(self):
        """Test annotation to string conversion error handling."""
        import ast

        # Create an invalid AST node
        invalid_node = ast.Constant(value="invalid")

        # Should handle gracefully
        result = ann_to_str(invalid_node)
        assert result == "'invalid'"


class TestValidation:
    """Test cases for validation functions."""

    def test_validate_prefix_free_valid(self):
        """Test prefix-free validation with valid aliases."""
        aliases = ["cfg", "svc", "repo", "dto"]
        valid, invalid = validate_prefix_free(aliases)

        assert len(valid) == 4
        assert len(invalid) == 0
        assert set(valid) == set(aliases)

    def test_validate_prefix_free_invalid(self):
        """Test prefix-free validation with invalid aliases."""
        aliases = ["cfg", "cfg_svc", "repo", "repo_user"]
        valid, invalid = validate_prefix_free(aliases)

        assert len(valid) == 0
        assert len(invalid) == 4
        assert set(invalid) == set(aliases)

    def test_validate_prefix_free_mixed(self):
        """Test prefix-free validation with mixed valid/invalid aliases."""
        aliases = ["cfg", "svc", "cfg_svc", "repo"]
        valid, invalid = validate_prefix_free(aliases)

        assert len(valid) == 2
        assert len(invalid) == 2
        assert "svc" in valid
        assert "repo" in valid
        assert "cfg" in invalid
        assert "cfg_svc" in invalid

    def test_validate_regex_patterns_valid(self):
        """Test regex pattern validation with valid patterns."""
        patterns = [r"^[a-z_]+$", r"^[A-Z][A-Za-z0-9]+$", r"\d+"]
        valid, invalid = validate_regex_patterns(patterns)

        assert len(valid) == 3
        assert len(invalid) == 0
        assert set(valid) == set(patterns)

    def test_validate_regex_patterns_invalid(self):
        """Test regex pattern validation with invalid patterns."""
        patterns = [r"^[a-z_]+$", r"[unclosed", r"invalid)"]
        valid, invalid = validate_regex_patterns(patterns)

        assert len(valid) == 1
        assert len(invalid) == 2
        assert "[unclosed" in invalid
        assert "invalid)" in invalid

    def test_validate_indices_valid(self):
        """Test index validation with valid indices."""
        from ctxcard_gen.types import ModuleInfo, Symbol

        modules = {}

        # Module 1
        mi1 = ModuleInfo(id=1, path="test1.py", dotted="test1")
        mi1.symbols = [
            Symbol(mid=1, sid=1, kind="cls", name="Class1"),
            Symbol(mid=1, sid=2, kind="fn", name="func1"),
        ]
        modules["test1.py"] = mi1

        # Module 2
        mi2 = ModuleInfo(id=2, path="test2.py", dotted="test2")
        mi2.symbols = [
            Symbol(mid=2, sid=1, kind="cls", name="Class2"),
        ]
        modules["test2.py"] = mi2

        assert validate_indices(modules)

    def test_validate_indices_duplicate_module_id(self):
        """Test index validation with duplicate module IDs."""
        from ctxcard_gen.types import ModuleInfo, Symbol

        modules = {}

        # Two modules with same ID
        mi1 = ModuleInfo(id=1, path="test1.py", dotted="test1")
        mi1.symbols = [Symbol(mid=1, sid=1, kind="cls", name="Class1")]
        modules["test1.py"] = mi1

        mi2 = ModuleInfo(id=1, path="test2.py", dotted="test2")  # Same ID
        mi2.symbols = [Symbol(mid=1, sid=1, kind="cls", name="Class2")]
        modules["test2.py"] = mi2

        assert not validate_indices(modules)

    def test_validate_indices_duplicate_symbol_id(self):
        """Test index validation with duplicate symbol IDs."""
        from ctxcard_gen.types import ModuleInfo, Symbol

        modules = {}

        mi = ModuleInfo(id=1, path="test.py", dotted="test")
        mi.symbols = [
            Symbol(mid=1, sid=1, kind="cls", name="Class1"),
            Symbol(mid=1, sid=1, kind="fn", name="func1"),  # Same SID
        ]
        modules["test.py"] = mi

        assert not validate_indices(modules)

    def test_validate_indices_wrong_symbol_module(self):
        """Test index validation with symbol in wrong module."""
        from ctxcard_gen.types import ModuleInfo, Symbol

        modules = {}

        mi = ModuleInfo(id=1, path="test.py", dotted="test")
        mi.symbols = [
            Symbol(mid=2, sid=1, kind="cls", name="Class1"),  # Wrong MID
        ]
        modules["test.py"] = mi

        assert not validate_indices(modules)

    def test_validate_edges_valid(self):
        """Test edge validation with valid edges."""
        from ctxcard_gen.types import ModuleInfo, Symbol

        modules = {}

        # Module 1
        mi1 = ModuleInfo(id=1, path="test1.py", dotted="test1")
        mi1.symbols = [
            Symbol(mid=1, sid=1, kind="cls", name="Class1"),
            Symbol(mid=1, sid=2, kind="fn", name="func1"),
        ]
        mi1.calls = [(2, (2, 1))]  # Call from symbol 2 to module 2, symbol 1
        modules["test1.py"] = mi1

        # Module 2
        mi2 = ModuleInfo(id=2, path="test2.py", dotted="test2")
        mi2.symbols = [
            Symbol(mid=2, sid=1, kind="cls", name="Class2"),
        ]
        modules["test2.py"] = mi2

        assert validate_edges(modules)

    def test_validate_edges_invalid_target_module(self):
        """Test edge validation with invalid target module."""
        from ctxcard_gen.types import ModuleInfo, Symbol

        modules = {}

        mi = ModuleInfo(id=1, path="test.py", dotted="test")
        mi.symbols = [
            Symbol(mid=1, sid=1, kind="cls", name="Class1"),
            Symbol(mid=1, sid=2, kind="fn", name="func1"),
        ]
        mi.calls = [(2, (999, 1))]  # Non-existent target module
        modules["test.py"] = mi

        assert not validate_edges(modules)

    def test_validate_edges_invalid_target_symbol(self):
        """Test edge validation with invalid target symbol."""
        from ctxcard_gen.types import ModuleInfo, Symbol

        modules = {}

        # Module 1
        mi1 = ModuleInfo(id=1, path="test1.py", dotted="test1")
        mi1.symbols = [
            Symbol(mid=1, sid=1, kind="cls", name="Class1"),
            Symbol(mid=1, sid=2, kind="fn", name="func1"),
        ]
        mi1.calls = [(2, (2, 999))]  # Non-existent target symbol
        modules["test1.py"] = mi1

        # Module 2
        mi2 = ModuleInfo(id=2, path="test2.py", dotted="test2")
        mi2.symbols = [
            Symbol(mid=2, sid=1, kind="cls", name="Class2"),
        ]
        modules["test2.py"] = mi2

        assert not validate_edges(modules)

    def test_validate_edges_invalid_caller(self):
        """Test edge validation with invalid caller symbol."""
        from ctxcard_gen.types import ModuleInfo, Symbol

        modules = {}

        mi = ModuleInfo(id=1, path="test.py", dotted="test")
        mi.symbols = [
            Symbol(mid=1, sid=1, kind="cls", name="Class1"),
        ]
        mi.calls = [(999, (1, 1))]  # Non-existent caller symbol
        modules["test.py"] = mi

        assert not validate_edges(modules)
