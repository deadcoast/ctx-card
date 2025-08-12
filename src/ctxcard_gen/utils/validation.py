"""
Validation functions for CTX-CARD generator.

This module contains validation utilities for CTX-CARD format compliance.
"""

from __future__ import annotations

import re
from typing import List, Tuple, Dict, Optional


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


def validate_ctx_card_structure(content: str) -> Tuple[bool, List[str]]:
    """
    Validate CTX-CARD structure and format compliance.

    Args:
        content: CTX-CARD content as string

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    lines = content.splitlines()

    # Check for required sections
    required_tags = {"ID:", "AL:", "NM:", "MO:", "SY:"}
    found_tags = set()

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Check for valid tag format
        if ":" in line:
            tag = line.split(":")[0] + ":"
            found_tags.add(tag)

            # Validate tag format - updated to include new tags
            if not re.match(r"^[A-Z]{2,6}:$", tag):
                errors.append(f"Line {line_num}: Invalid tag format '{tag}'")

    # Check for missing required tags
    missing_tags = required_tags - found_tags
    if missing_tags:
        errors.append(f"Missing required tags: {', '.join(missing_tags)}")

    # Check for ASCII-only content
    if not content.isascii():
        errors.append("CTX-CARD must be ASCII-only")

    return len(errors) == 0, errors


def validate_role_tags(modules: dict) -> Tuple[bool, List[str]]:
    """
    Validate role tags consistency across modules.

    Args:
        modules: Dictionary of module information

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    all_role_tags = set()

    # Collect all role tags
    for module_info in modules.values():
        all_role_tags.update(module_info.role_tags)

    # Validate role tag format (should be lowercase, no spaces)
    for tag in all_role_tags:
        if not re.match(r"^[a-z_]+$", tag):
            errors.append(f"Invalid role tag format: '{tag}' (should be lowercase with underscores)")  # pylint: disable=line-too-long

    return len(errors) == 0, errors


def validate_function_signatures(modules: dict) -> Tuple[bool, List[str]]:
    """
    Validate function signature format and consistency.

    Args:
        modules: Dictionary of module information

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    for module_info in modules.values():
        for symbol in module_info.symbols:
            if symbol.signature:
                # Validate signature format
                if not re.match(r"^\([^)]*\)->[^!]*(\s*!raises\[[^\]]*\])?$", symbol.signature):
                    errors.append(f"Invalid function signature format: '{symbol.signature}'")

    return len(errors) == 0, errors


def validate_naming_conventions(modules: dict, naming_patterns: Dict[str, str]) -> Tuple[bool, List[str]]:  # pylint: disable=line-too-long
    """
    Validate that symbols follow naming conventions.

    Args:
        modules: Dictionary of module information
        naming_patterns: Dictionary of naming patterns by symbol type

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    for module_info in modules.values():
        for symbol in module_info.symbols:
            if symbol.kind in naming_patterns:
                pattern = naming_patterns[symbol.kind]
                if not re.match(pattern, symbol.name):
                    errors.append(f"Symbol '{symbol.name}' does not match naming pattern for {symbol.kind}: {pattern}")  # pylint: disable=line-too-long

    return len(errors) == 0, errors


def validate_ascii_compliance(content: str) -> Tuple[bool, List[str]]:
    """
    Validate that content is ASCII-only as required by CTX-CARD spec.

    Args:
        content: Content to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    for line_num, line in enumerate(content.splitlines(), 1):
        if not line.isascii():
            non_ascii_chars = [char for char in line if not char.isascii()]
            errors.append(f"Line {line_num}: Non-ASCII characters found: {non_ascii_chars}")

    return len(errors) == 0, errors


def validate_semantic_tokens(content: str) -> List[Dict]:
    """
    Generate semantic tokens for LSP support.

    Args:
        content: CTX-CARD content as string

    Returns:
        List of semantic token dictionaries
    """
    tokens = []
    lines = content.splitlines()

    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Tokenize CTX-CARD tags
        if ":" in line:
            tag_end = line.find(":")
            tag = line[:tag_end + 1]

            # Add tag token
            tokens.append({
                "line": line_num,
                "start": 0,
                "length": len(tag),
                "tokenType": "keyword",
                "tokenModifiers": ["definition"]
            })

            # Add payload token
            payload_start = tag_end + 1
            if payload_start < len(line):
                payload = line[payload_start:].strip()
                tokens.append({
                    "line": line_num,
                    "start": payload_start,
                    "length": len(payload),
                    "tokenType": "string",
                    "tokenModifiers": []
                })

    return tokens


def validate_cross_references(content: str) -> Tuple[bool, List[str]]:
    """
    Validate cross-references in CTX-CARD content.

    Args:
        content: CTX-CARD content as string

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Extract all index references
    index_pattern = r"#(\d+)\.(\d+)"
    re.findall(index_pattern, content)

    # Check for malformed indices
    malformed_pattern = r"#\d+\.\d+[^\s]"
    malformed = re.findall(malformed_pattern, content)
    if malformed:
        errors.append(f"Malformed index references: {malformed}")

    return len(errors) == 0, errors


def get_validation_report(content: str, modules: dict = None) -> Dict:
    """
    Generate comprehensive validation report for CTX-CARD content.

    Args:
        content: CTX-CARD content as string
        modules: Optional module information for cross-validation

    Returns:
        Dictionary with validation results and errors
    """
    report = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "semantic_tokens": []
    }

    # Structure validation
    is_valid, errors = validate_ctx_card_structure(content)
    if not is_valid:
        report["valid"] = False
        report["errors"].extend(errors)

    # ASCII compliance
    is_ascii, ascii_errors = validate_ascii_compliance(content)
    if not is_ascii:
        report["valid"] = False
        report["errors"].extend(ascii_errors)

    # Cross-reference validation
    is_refs_valid, ref_errors = validate_cross_references(content)
    if not is_refs_valid:
        report["warnings"].extend(ref_errors)

    # Module-specific validation if available
    if modules:
        # Role tags validation
        is_roles_valid, role_errors = validate_role_tags(modules)
        if not is_roles_valid:
            report["warnings"].extend(role_errors)

        # Function signature validation
        is_sigs_valid, sig_errors = validate_function_signatures(modules)
        if not is_sigs_valid:
            report["warnings"].extend(sig_errors)

    # Generate semantic tokens for LSP
    report["semantic_tokens"] = validate_semantic_tokens(content)

    return report


def get_completion_items(content: str, position: int) -> List[Dict]:
    """
    Generate LSP completion items for CTX-CARD content.

    Args:
        content: CTX-CARD content as string
        position: Cursor position in the content

    Returns:
        List of completion items for LSP
    """
    completion_items = []
    lines = content.splitlines()

    # Get current line and position
    current_line = 0
    current_pos = 0
    for i, line in enumerate(lines):
        if current_pos + len(line) + 1 > position:
            current_line = i
            current_pos_in_line = position - current_pos
            break
        current_pos += len(line) + 1

    if current_line >= len(lines):
        return completion_items

    line = lines[current_line]

    # Tag completion
    if line.strip() == "" or line.startswith("#"):
        tags = [
            "ID:", "AL:", "NM:", "DEPS:", "ENV:", "SEC:", "MO:", "SY:", "SG:",
            "MD:", "ED:", "EVT:", "TY:", "IN:", "CN:", "ER:", "IO:", "DT:",
            "TK:", "ASYNC:", "PX:", "EX:", "RV:", "DELTA:"
        ]
        for tag in tags:
            completion_items.append({
                "label": tag,
                "kind": "keyword",
                "detail": f"CTX-CARD tag: {tag}",
                "insertText": tag + " ",
                "sortText": tag
            })

    # Index completion
    if "#" in line and current_pos_in_line > line.find("#"):
        # Extract existing indices from content
        indices = set()
        for l in lines:
            index_matches = re.findall(r"#(\d+)\.(\d+)", l)
            for mid, sid in index_matches:
                indices.add(f"#{mid}.#{sid}")
            single_indices = re.findall(r"#(\d+)(?!\.)", l)
            for mid in single_indices:
                indices.add(f"#{mid}")

        for index in sorted(indices):
            completion_items.append({
                "label": index,
                "kind": "constant",
                "detail": f"Index reference: {index}",
                "insertText": index,
                "sortText": index
            })

    # Role tag completion
    if "{" in line and "}" not in line[current_pos_in_line:]:
        role_tags = ["svc", "auth", "api", "repo", "db", "dto", "cfg", "uc", "http", "jwt"]
        for tag in role_tags:
            completion_items.append({
                "label": tag,
                "kind": "string",
                "detail": f"Role tag: {tag}",
                "insertText": tag,
                "sortText": tag
            })

    return completion_items


def get_definition_location(content: str, position: int) -> Optional[Dict]:
    """
    Get definition location for cross-references in CTX-CARD content.

    Args:
        content: CTX-CARD content as string
        position: Cursor position in the content

    Returns:
        Definition location or None if not found
    """
    lines = content.splitlines()

    # Get current line and position
    current_line = 0
    current_pos = 0
    for i, line in enumerate(lines):
        if current_pos + len(line) + 1 > position:
            current_line = i
            current_pos_in_line = position - current_pos
            break
        current_pos += len(line) + 1

    if current_line >= len(lines):
        return None

    line = lines[current_line]

    # Find index reference at cursor position
    index_pattern = r"#(\d+)\.(\d+)"
    matches = list(re.finditer(index_pattern, line))

    for match in matches:
        if match.start() <= current_pos_in_line <= match.end():
            index = match.group(0)
            # Find definition of this index
            for i, l in enumerate(lines):
                if l.strip().startswith("SY:") and index in l:
                    return {
                        "line": i,
                        "character": l.find(index),
                        "index": index
                    }

    return None


def find_all_references(content: str, symbol: str) -> List[Dict]:
    """
    Find all references to a symbol in CTX-CARD content.

    Args:
        content: CTX-CARD content as string
        symbol: Symbol to find references for

    Returns:
        List of reference locations
    """
    references = []
    lines = content.splitlines()

    for i, line in enumerate(lines):
        if symbol in line:
            references.append({
                "line": i,
                "character": line.find(symbol),
                "symbol": symbol
            })

    return references
