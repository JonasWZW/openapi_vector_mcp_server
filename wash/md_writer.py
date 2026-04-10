# -*- coding: utf-8 -*-
"""MD writer - writes washed OpenAPI data to structured Markdown."""

import json
from pathlib import Path
from typing import Any

from .schema_resolver import SchemaResolver


def build_operation_text(operation: dict) -> str:
    """Build the full Markdown text for a single API operation."""
    lines = []

    operation_id = operation.get("operation_id", "")
    path = operation.get("path", "")
    method = operation.get("method", "").upper()
    summary = operation.get("summary", "")
    description = operation.get("description", "")
    tags = operation.get("tags", [])
    version = operation.get("version", "")
    deprecated = operation.get("deprecated", False)
    request_schema = operation.get("request_schema")
    response_schema = operation.get("response_schema")

    # Section header
    lines.append(f"## {operation_id}\n")
    lines.append(f"**{method}** `{path}`\n")

    # Metadata table
    lines.append("| 字段 | 值 |")
    lines.append("|------|-----|")
    lines.append(f"| operation_id | `{operation_id}` |")
    lines.append(f"| tags | {', '.join(tags)} |")
    lines.append(f"| summary | {summary} |")
    if version:
        lines.append(f"| version | {version} |")
    if deprecated:
        lines.append(f"| deprecated | {deprecated} |")
    lines.append("")

    # Description
    if description:
        lines.append(f"**description**: {description}\n")

    # Request schema
    lines.append("### Request\n")
    if request_schema is None:
        lines.append("*(无请求体)*\n")
    elif isinstance(request_schema, str) and request_schema.startswith("$ref"):
        lines.append(f"```\n{request_schema}\n```\n")
    else:
        lines.append("```json\n")
        lines.append(json.dumps(request_schema, ensure_ascii=False, indent=2))
        lines.append("\n```\n")

    # Response schema
    lines.append("### Response\n")
    if response_schema is None:
        lines.append("*(无响应体)*\n")
    elif isinstance(response_schema, str) and response_schema.startswith("$ref"):
        lines.append(f"```\n{response_schema}\n```\n")
    else:
        lines.append("```json\n")
        lines.append(json.dumps(response_schema, ensure_ascii=False, indent=2))
        lines.append("\n```\n")

    lines.append("---\n")
    return "\n".join(lines)


def extract_examples(schema: Any) -> list[Any]:
    """Extract example values from a schema if present."""
    examples = []
    if isinstance(schema, dict):
        if "example" in schema:
            examples.append(schema["example"])
        if "examples" in schema:
            examples.extend(schema.get("examples", []))
        # Check properties recursively
        if "properties" in schema:
            for prop in schema["properties"].values():
                examples.extend(extract_examples(prop))
    return examples


def build_app_header(app_name: str, operations: list[dict]) -> str:
    """Build the header section for an app's Markdown file."""
    lines = []
    lines.append(f"# {app_name}\n")

    # Extract metadata from first operation
    first = operations[0] if operations else {}
    version = first.get("version", "")
    title = first.get("title", app_name)

    lines.append(f"> **module**: {app_name}  ")
    lines.append(f"> **version**: {version}  ")
    lines.append(f"> **app_name**: {app_name}  ")
    lines.append(f"> **total_apis**: {len(operations)}  ")
    lines.append(f"> **description**: {title}\n")
    lines.append("---\n")

    return "\n".join(lines)


def write_app_md(app_name: str, operations: list[dict], output_path: Path) -> None:
    """Write all operations for an app to a single Markdown file."""
    lines = [build_app_header(app_name, operations)]

    resolver = SchemaResolver()
    for operation in operations:
        resolved = resolver.resolve_operation(operation)
        lines.append(build_operation_text(resolved))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
