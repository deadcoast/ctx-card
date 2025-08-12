"""
Export utilities for CTX-CARD generator.

This module provides functions to export CTX-CARD content to various formats.
"""

from __future__ import annotations

import json
from typing import Dict, Any, Optional
from pathlib import Path


def parse_ctx_card(content: str) -> Dict[str, Any]:
    """
    Parse CTX-CARD content into a structured dictionary.

    Args:
        content: CTX-CARD content as string

    Returns:
        Structured dictionary representation
    """
    result = {
        "metadata": {},
        "aliases": [],
        "naming": [],
        "dependencies": [],
        "environment": [],
        "security": [],
        "modules": [],
        "symbols": [],
        "signatures": [],
        "edges": [],
        "events": [],
        "async_patterns": [],
        "invariants": [],
        "conventions": [],
        "errors": [],
        "io_contracts": [],
        "data_types": [],
        "tokens": [],
        "prohibited": [],
        "examples": [],
        "review": []
    }

    lines = content.splitlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if ":" not in line:
            continue

        tag, payload = line.split(":", 1)
        payload = payload.strip()

        if tag == "ID":
            # Parse ID line: proj|name lang|py std|pep8 ts|20241201
            parts = payload.split()
            for part in parts:
                if "|" in part:
                    key, value = part.split("|", 1)
                    result["metadata"][key] = value

        elif tag == "AL":
            # Parse alias: cfg=>Configuration
            if "=>" in payload:
                alias, value = payload.split("=>", 1)
                result["aliases"].append({"alias": alias.strip(), "value": value.strip()})

        elif tag == "NM":
            # Parse naming: module | ^[a-z_]+$ | auth_service
            if "|" in payload:
                parts = payload.split("|")
                if len(parts) >= 3:
                    result["naming"].append({
                        "scope": parts[0].strip(),
                        "pattern": parts[1].strip(),
                        "example": parts[2].strip()
                    })

        elif tag == "DEPS":
            # Parse dependencies: requests | external | HTTP client library
            if "|" in payload:
                parts = payload.split("|")
                if len(parts) >= 3:
                    result["dependencies"].append({
                        "name": parts[0].strip(),
                        "category": parts[1].strip(),
                        "description": parts[2].strip()
                    })

        elif tag == "ENV":
            # Parse environment: database_url | environment | config
            if "|" in payload:
                parts = payload.split("|")
                if len(parts) >= 3:
                    result["environment"].append({
                        "name": parts[0].strip(),
                        "category": parts[1].strip(),
                        "description": parts[2].strip()
                    })

        elif tag == "SEC":
            # Parse security: AuthService | authentication | required
            if "|" in payload:
                parts = payload.split("|")
                if len(parts) >= 3:
                    result["security"].append({
                        "name": parts[0].strip(),
                        "category": parts[1].strip(),
                        "description": parts[2].strip()
                    })

        elif tag == "MO":
            # Parse module: #1 | auth/service.py | {svc,auth}
            if "|" in payload:
                parts = payload.split("|")
                if len(parts) >= 3:
                    module_id = parts[0].strip()
                    path = parts[1].strip()
                    role_tags = parts[2].strip().strip("{}").split(",")
                    result["modules"].append({
                        "id": module_id,
                        "path": path,
                        "role_tags": [tag.strip() for tag in role_tags if tag.strip()]
                    })

        elif tag == "SY":
            # Parse symbol: #1.#1 | cls | AuthService
            if "|" in payload:
                parts = payload.split("|")
                if len(parts) >= 3:
                    result["symbols"].append({
                        "index": parts[0].strip(),
                        "kind": parts[1].strip(),
                        "name": parts[2].strip()
                    })

        elif tag == "SG":
            # Parse signature: #1.#2 | (UserCreds)->AuthToken !raises[AuthError]
            if "|" in payload:
                parts = payload.split("|")
                if len(parts) >= 2:
                    result["signatures"].append({
                        "index": parts[0].strip(),
                        "signature": parts[1].strip()
                    })

        elif tag == "ED":
            # Parse edge: #1.#2 -> #2.#1 | calls
            if "->" in payload:
                parts = payload.split("->")
                if len(parts) >= 2:
                    source = parts[0].strip()
                    rest = parts[1].split("|")
                    target = rest[0].strip()
                    reason = rest[1].strip() if len(rest) > 1 else ""
                    result["edges"].append({
                        "source": source,
                        "target": target,
                        "reason": reason
                    })

        elif tag == "EVT":
            # Parse event: #1.#2 | event | login_event
            if "|" in payload:
                parts = payload.split("|")
                if len(parts) >= 3:
                    result["events"].append({
                        "index": parts[0].strip(),
                        "type": parts[1].strip(),
                        "name": parts[2].strip()
                    })

        elif tag == "ASYNC":
            # Parse async: #1.#2 | async | login_async
            if "|" in payload:
                parts = payload.split("|")
                if len(parts) >= 3:
                    result["async_patterns"].append({
                        "index": parts[0].strip(),
                        "type": parts[1].strip(),
                        "name": parts[2].strip()
                    })

        elif tag == "IN":
            # Parse invariant: login ⇒ requires(valid(creds)) ∧ ensures(token.exp>now)
            if "⇒" in payload:
                parts = payload.split("⇒")
                if len(parts) >= 2:
                    result["invariants"].append({
                        "function": parts[0].strip(),
                        "condition": parts[1].strip()
                    })

        elif tag == "CN":
            # Parse convention: async fn end with _async
            result["conventions"].append(payload)

        elif tag == "ER":
            # Parse error: AuthError | domain | bad credentials
            if "|" in payload:
                parts = payload.split("|")
                if len(parts) >= 3:
                    result["errors"].append({
                        "name": parts[0].strip(),
                        "category": parts[1].strip(),
                        "meaning": parts[2].strip()
                    })

        elif tag == "IO":
            # Parse I/O contract: POST /v1/login | UserCreds | AuthToken | 200,401,429
            if "|" in payload:
                parts = payload.split("|")
                if len(parts) >= 4:
                    result["io_contracts"].append({
                        "endpoint": parts[0].strip(),
                        "input": parts[1].strip(),
                        "output": parts[2].strip(),
                        "codes": parts[3].strip()
                    })

        elif tag == "DT":
            # Parse data type: UserCreds | {email:str, pwd:secret(>=12)}
            if "|" in payload:
                parts = payload.split("|")
                if len(parts) >= 2:
                    result["data_types"].append({
                        "name": parts[0].strip(),
                        "fields": parts[1].strip()
                    })

        elif tag == "TK":
            # Parse token: Role | {admin,staff,viewer}
            if "|" in payload:
                parts = payload.split("|")
                if len(parts) >= 2:
                    tokens = parts[1].strip().strip("{}").split(",")
                    result["tokens"].append({
                        "name": parts[0].strip(),
                        "values": [token.strip() for token in tokens if token.strip()]
                    })

        elif tag == "PX":
            # Parse prohibited: forbid bare except | error-handling
            if "|" in payload:
                parts = payload.split("|")
                if len(parts) >= 2:
                    result["prohibited"].append({
                        "rule": parts[0].strip(),
                        "reason": parts[1].strip()
                    })

        elif tag == "EX":
            # Parse example: var(repo) => user_repo
            result["examples"].append(payload)

        elif tag == "RV":
            # Parse review: Check invariants (IN) on public fn
            result["review"].append(payload)

    return result


def export_to_json(content: str, output_path: Optional[Path] = None) -> str:
    """
    Export CTX-CARD content to JSON format.

    Args:
        content: CTX-CARD content as string
        output_path: Optional output file path

    Returns:
        JSON string representation
    """
    parsed = parse_ctx_card(content)
    json_str = json.dumps(parsed, indent=2, ensure_ascii=False)

    if output_path:
        output_path.write_text(json_str, encoding="utf-8")

    return json_str


def export_to_yaml(content: str, output_path: Optional[Path] = None) -> str:
    """
    Export CTX-CARD content to YAML format.

    Args:
        content: CTX-CARD content as string
        output_path: Optional output file path

    Returns:
        YAML string representation
    """
    try:
        import yaml  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        raise ImportError("PyYAML is required for YAML export. Install with: pip install PyYAML") from exc

    parsed = parse_ctx_card(content)
    yaml_str = yaml.dump(parsed, default_flow_style=False, allow_unicode=True, sort_keys=False)

    if output_path:
        output_path.write_text(yaml_str, encoding="utf-8")

    return yaml_str


def export_to_xml(content: str, output_path: Optional[Path] = None) -> str:
    """
    Export CTX-CARD content to XML format.

    Args:
        content: CTX-CARD content as string
        output_path: Optional output file path

    Returns:
        XML string representation
    """
    parsed = parse_ctx_card(content)

    def dict_to_xml(data: Dict[str, Any], root_name: str = "ctxcard") -> str:
        """Convert dictionary to XML string."""
        xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', f'<{root_name}>']

        for key, value in data.items():
            if isinstance(value, list):
                xml_parts.append(f'  <{key}>')
                for item in value:
                    if isinstance(item, dict):
                        xml_parts.append(f'    <{key[:-1]}>')  # Remove 's' for singular
                        for k, v in item.items():
                            xml_parts.append(f'      <{k}>{v}</{k}>')
                        xml_parts.append(f'    </{key[:-1]}>')
                    else:
                        xml_parts.append(f'    <{key[:-1]}>{item}</{key[:-1]}>')
                xml_parts.append(f'  </{key}>')
            elif isinstance(value, dict):
                xml_parts.append(f'  <{key}>')
                for k, v in value.items():
                    xml_parts.append(f'    <{k}>{v}</{k}>')
                xml_parts.append(f'  </{key}>')
            else:
                xml_parts.append(f'  <{key}>{value}</{key}>')

        xml_parts.append(f'</{root_name}>')
        return '\n'.join(xml_parts)

    xml_str = dict_to_xml(parsed)

    if output_path:
        output_path.write_text(xml_str, encoding="utf-8")

    return xml_str


def export_to_markdown(content: str, output_path: Optional[Path] = None) -> str:
    """
    Export CTX-CARD content to enhanced Markdown format.

    Args:
        content: CTX-CARD content as string
        output_path: Optional output file path

    Returns:
        Markdown string representation
    """
    parsed = parse_ctx_card(content)

    md_parts = ["# CTX-CARD Documentation\n"]

    # Metadata
    if parsed["metadata"]:
        md_parts.append("## Project Information")
        for key, value in parsed["metadata"].items():
            md_parts.append(f"- **{key.title()}**: {value}")
        md_parts.append("")

    # Aliases
    if parsed["aliases"]:
        md_parts.append("## Aliases")
        for alias in parsed["aliases"]:
            md_parts.append(f"- `{alias['alias']}` → {alias['value']}")
        md_parts.append("")

    # Dependencies
    if parsed["dependencies"]:
        md_parts.append("## Dependencies")
        for dep in parsed["dependencies"]:
            md_parts.append(f"- **{dep['name']}** ({dep['category']}): {dep['description']}")
        md_parts.append("")

    # Environment
    if parsed["environment"]:
        md_parts.append("## Environment Configuration")
        for env in parsed["environment"]:
            md_parts.append(f"- **{env['name']}** ({env['category']}): {env['description']}")
        md_parts.append("")

    # Security
    if parsed["security"]:
        md_parts.append("## Security Constraints")
        for sec in parsed["security"]:
            md_parts.append(f"- **{sec['name']}** ({sec['category']}): {sec['description']}")
        md_parts.append("")

    # Modules
    if parsed["modules"]:
        md_parts.append("## Modules")
        for module in parsed["modules"]:
            tags = ", ".join(module["role_tags"])
            md_parts.append(f"- **{module['id']}** `{module['path']}` [{tags}]")
        md_parts.append("")

    # Symbols
    if parsed["symbols"]:
        md_parts.append("## Symbols")
        for symbol in parsed["symbols"]:
            md_parts.append(f"- **{symbol['index']}** `{symbol['kind']}` {symbol['name']}")
        md_parts.append("")

    # Signatures
    if parsed["signatures"]:
        md_parts.append("## Function Signatures")
        for sig in parsed["signatures"]:
            md_parts.append(f"- **{sig['index']}**: `{sig['signature']}`")
        md_parts.append("")

    # Edges
    if parsed["edges"]:
        md_parts.append("## Relationships")
        for edge in parsed["edges"]:
            md_parts.append(f"- {edge['source']} → {edge['target']} ({edge['reason']})")
        md_parts.append("")

    # Data Types
    if parsed["data_types"]:
        md_parts.append("## Data Types")
        for dt in parsed["data_types"]:
            md_parts.append(f"- **{dt['name']}**: {dt['fields']}")
        md_parts.append("")

    # Conventions
    if parsed["conventions"]:
        md_parts.append("## Coding Conventions")
        for conv in parsed["conventions"]:
            md_parts.append(f"- {conv}")
        md_parts.append("")

    # Errors
    if parsed["errors"]:
        md_parts.append("## Error Taxonomy")
        for error in parsed["errors"]:
            md_parts.append(f"- **{error['name']}** ({error['category']}): {error['meaning']}")
        md_parts.append("")

    # Review
    if parsed["review"]:
        md_parts.append("## Review Checklist")
        for item in parsed["review"]:
            md_parts.append(f"- [ ] {item}")
        md_parts.append("")

    md_str = "\n".join(md_parts)

    if output_path:
        output_path.write_text(md_str, encoding="utf-8")

    return md_str
