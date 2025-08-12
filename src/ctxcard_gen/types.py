"""
Core data types for CTX-CARD generator.

This module defines the fundamental data structures used throughout the CTX-CARD
generation process, including symbols, modules, and scan results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class Symbol:
    """Represents a code symbol (class, function, property, module)."""

    mid: int  # Module ID
    sid: int  # Symbol ID within module
    kind: str  # "mod" | "cls" | "fn" | "prop"
    name: str  # "func" or "Class.method" or "Class.attr"
    signature: Optional[str] = None
    deco: List[str] = field(default_factory=list)  # Decorator names
    modifiers: Set[str] = field(
        default_factory=set
    )  # staticmethod, classmethod, property, descriptor
    invariants: Optional[str] = None  # Docstring invariants
    raises: List[str] = field(default_factory=list)  # Exception types raised


@dataclass
class ModuleInfo:
    """Represents a module with its symbols and metadata."""

    id: int
    path: str  # Relative path
    dotted: str  # Dotted module name
    role_tags: Set[str] = field(default_factory=set)  # Role tags (svc, repo, etc.)
    symbols: List[Symbol] = field(default_factory=list)
    imports_paths: Set[str] = field(default_factory=set)  # Resolved import paths
    import_names: Dict[str, str] = field(default_factory=dict)  # Alias -> dotted origin
    fn_to_sid: Dict[str, int] = field(
        default_factory=dict
    )  # Function name -> symbol ID
    prop_to_sid: Dict[str, int] = field(
        default_factory=dict
    )  # Property name -> symbol ID
    dts: List[Tuple[str, Dict[str, str]]] = field(
        default_factory=list
    )  # Data transfer objects
    errors: List[Tuple[str, str, str]] = field(default_factory=list)  # Error types
    routes: List[Tuple[int, str, str, List[str]]] = field(
        default_factory=list
    )  # API routes
    calls: List[Tuple[int, Tuple[int, int]]] = field(
        default_factory=list
    )  # Function calls
    tokens: List[Tuple[str, List[str]]] = field(default_factory=list)  # Enum tokens
    reexports: Dict[str, str] = field(default_factory=dict)  # Re-export mappings
    px: List[Tuple[str, str]] = field(default_factory=list)  # Prohibited patterns


@dataclass
class ScanResult:
    """Result of repository scanning."""

    modules: Dict[str, ModuleInfo]  # Path -> ModuleInfo
    langs: List[str]  # Detected languages


@dataclass
class GeneratorConfig:
    """Configuration for CTX-CARD generation."""

    project_name: str
    root_path: Path
    output_path: Path
    include_pattern: Optional[str] = None
    exclude_pattern: Optional[str] = None
    emit_type_signatures: bool = False
    delta_from: Optional[Path] = None
    stdout_output: bool = False
    per_package: bool = False
