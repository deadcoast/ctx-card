"""
Helper functions for CTX-CARD generator.

This module contains utility functions used throughout the CTX-CARD generation process.
"""

from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path
from typing import Optional


def today_stamp() -> str:
    """Generate today's date stamp in YYYYMMDD format."""
    return datetime.utcnow().strftime("%Y%m%d")


def relpath(p: Path, root: Path) -> str:
    """Get relative path from root, falling back to absolute path if needed."""
    try:
        return str(p.relative_to(root).as_posix())
    except Exception:
        return str(p.as_posix())


def is_probably_binary(path: Path) -> bool:
    """Check if a file is probably binary by looking for null bytes."""
    try:
        with path.open("rb") as f:
            return b"\0" in f.read(2048)
    except Exception:
        return True


def ascii_only(s: str) -> str:
    """Convert string to ASCII-only by removing non-ASCII characters."""
    return s.encode("ascii", "ignore").decode("ascii")


def file_to_dotted(rp: str) -> str:
    """Convert file path to dotted module name."""
    p = Path(rp)
    if p.name == "__init__.py":
        return str(p.parent).replace("/", ".")
    return rp[:-3].replace("/", ".") if rp.endswith(".py") else rp.replace("/", ".")


def ann_to_str(ann: Optional[ast.AST]) -> str:
    """Convert AST annotation to string."""
    if ann is None:
        return ""
    try:
        return ast.unparse(ann)
    except Exception:
        return ""
