"""
Validation functions for CTX-CARD generator.

This module contains validation utilities for CTX-CARD format compliance.
"""

from __future__ import annotations

import re
from typing import List, Tuple


def validate_prefix_free(aliases: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate that aliases are prefix-free.

    Args:
        aliases: List of alias strings

    Returns:
        Tuple of (valid_aliases, invalid_aliases)
    """
    valid = []
    invalid = []

    for i, alias in enumerate(aliases):
        is_valid = True
        for j, other in enumerate(aliases):
            if i != j:
                if alias.startswith(other) or other.startswith(alias):
                    is_valid = False
                    break

        if is_valid:
            valid.append(alias)
        else:
            invalid.append(alias)

    return valid, invalid


def validate_regex_patterns(patterns: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate regex patterns.

    Args:
        patterns: List of regex pattern strings

    Returns:
        Tuple of (valid_patterns, invalid_patterns)
    """
    valid = []
    invalid = []

    for pattern in patterns:
        try:
            re.compile(pattern)
            valid.append(pattern)
        except re.error:
            invalid.append(pattern)

    return valid, invalid


def validate_indices(modules: dict) -> bool:
    """
    Validate that module and symbol indices are consistent.

    Args:
        modules: Dictionary of module information

    Returns:
        True if indices are valid
    """
    # Check for duplicate module IDs
    module_ids = set()
    for module_info in modules.values():
        if module_info.id in module_ids:
            return False
        module_ids.add(module_info.id)
        
        # Check that module ID is positive
        if module_info.id <= 0:
            return False

        # Check that symbol IDs are consistent within module
        symbol_ids = set()
        for symbol in module_info.symbols:
            if symbol.sid in symbol_ids:
                return False
            symbol_ids.add(symbol.sid)

            # Check that symbol belongs to this module
            if symbol.mid != module_info.id:
                return False

    return True


def validate_edges(modules: dict) -> bool:
    """
    Validate that edges reference valid modules and symbols.

    Args:
        modules: Dictionary of module information

    Returns:
        True if edges are valid
    """
    # Build lookup of valid module and symbol IDs
    valid_modules = {mi.id for mi in modules.values()}
    valid_symbols = {}

    for mi in modules.values():
        valid_symbols[mi.id] = {s.sid for s in mi.symbols}

    # Validate edges
    for mi in modules.values():
        for caller_sid, (t_mid, t_sid) in mi.calls:
            # Check target module exists
            if t_mid not in valid_modules:
                return False

            # Check target symbol exists in target module
            if t_sid not in valid_symbols.get(t_mid, set()):
                return False

            # Check caller symbol exists in this module
            if caller_sid not in valid_symbols.get(mi.id, set()):
                return False

    return True
