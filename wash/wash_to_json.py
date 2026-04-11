# -*- coding: utf-8 -*-
"""Wash to JSON - convert OpenAPI 3.0 JSON to Milvus-ready format.

1. Extract info as document metadata
2. Resolve $ref to actual schema data
3. Include parameters
4. Exclude unimportant fields
"""

import json
from pathlib import Path

from config import FETCH_DATAS_DIR, DOCS_DIR, get_fetch_apps


def infer_app_name(file_path: Path) -> str:
    """Infer app name from file name, e.g. 'bcm接口文档.json' -> 'bcm'."""
    return file_path.stem.replace("接口文档", "")


def get_app_info_map() -> dict[str, dict]:
    """Build mapping from app_name to {collection_name, description} from fetch.yaml."""
    apps = get_fetch_apps()
    return {
        a["app_name"]: {
            "collection_name": a.get("collection_name") or f"{a['app_name']}_rest",
            "description": a.get("description", ""),
        }
        for a in apps
    }


def resolve_ref(ref: str, schemas: dict) -> dict | None:
    """Resolve a $ref to actual schema."""
    if not ref.startswith("#/components/schemas/"):
        return None
    return schemas.get(ref.removeprefix("#/components/schemas/"))


def resolve_schema(schema: dict, schemas: dict, depth: int = 0) -> dict:
    """Resolve schema, replacing $ref with actual data."""
    if depth > 10:
        return {"type": "unknown"}
    if not isinstance(schema, dict):
        return schema

    if "$ref" in schema:
        resolved = resolve_ref(schema["$ref"], schemas)
        if resolved:
            return resolve_schema(dict(resolved), schemas, depth + 1)
        return schema

    result = {}
    for k, v in schema.items():
        if k == "$ref":
            continue
        if isinstance(v, dict):
            result[k] = resolve_schema(v, schemas, depth + 1)
        elif isinstance(v, list):
            result[k] = [resolve_schema(i, schemas, depth + 1) if isinstance(i, dict) else i for i in v]
        else:
            result[k] = v
    return result


def extract_parameters(parameters: list) -> list[dict]:
    """Extract parameters - only name, in, required, type, description."""
    result = []
    for param in parameters:
        result.append({
            "name": param.get("name"),
            "in": param.get("in"),
            "required": param.get("required"),
            "type": param.get("schema", {}).get("type"),
            "description": param.get("description"),
        })
    return result


def extract_request_body(request_body: dict, schemas: dict) -> dict | None:
    """Extract request body, resolving $ref."""
    if not request_body:
        return None

    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema")

    if not schema:
        return None

    return resolve_schema(schema, schemas)


def extract_response(response: dict, schemas: dict) -> dict | None:
    """Extract response, resolving $ref."""
    if not response:
        return None

    content = response.get("content", {})
    json_content = content.get("*/*") or content.get("application/json", {})
    schema = json_content.get("schema")

    if not schema:
        desc = response.get("description", "")
        return {"description": desc} if desc else None

    return resolve_schema(schema, schemas)


def parse_operation(path: str, method: str, op_spec: dict, schemas: dict) -> dict:
    """Parse operation into Milvus-ready format."""
    method = method.upper()

    # Get response (prefer 200)
    responses = op_spec.get("responses", {})
    response = responses.get("200") or responses.get("default")

    return {
        "operation_id": op_spec.get("operationId", f"{method}_{path}"),
        "path": path,
        "method": method,
        "summary": op_spec.get("summary", ""),
        "description": op_spec.get("description", ""),
        "tags": op_spec.get("tags", []),
        "deprecated": op_spec.get("deprecated", False),
        "parameters": extract_parameters(op_spec.get("parameters", [])),
        "request": extract_request_body(op_spec.get("requestBody"), schemas),
        "response": extract_response(response, schemas),
    }


def wash_file(json_path: Path) -> Path:
    """Wash OpenAPI JSON to Milvus-ready format."""
    with open(json_path, encoding="utf-8") as f:
        spec = json.load(f)

    app_name = infer_app_name(json_path)
    app_info_map = get_app_info_map()
    app_info = app_info_map.get(app_name, {})
    collection_name = app_info.get("collection_name", f"{app_name}_rest")
    description = app_info.get("description", "")
    info = spec.get("info", {})
    schemas = spec.get("components", {}).get("schemas", {})
    paths = spec.get("paths", {})

    # Parse all operations (only keep paths containing 'innerService')
    operations = []
    for path, path_item in paths.items():
        # todo filter uri
        # if "/api/v1" not in path:
        #     continue
        for method, op_spec in path_item.items():
            if method.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"):
                if isinstance(op_spec, dict) and op_spec.get("operationId"):
                    operations.append(parse_operation(path, method, op_spec, schemas))

    result = {
        "app_name": app_name,
        "collection_name": collection_name,
        "description": description or info.get("description", ""),
        "version": info.get("version", ""),
        "title": info.get("title", ""),
        "total_apis": len(operations),
        "operations": operations,
    }

    output_path = DOCS_DIR / f"{app_name}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Washed: {json_path.name} -> {output_path} ({len(operations)} operations)")
    return output_path


def wash_all(input_dir: Path | None = None) -> list[Path]:
    """Wash all JSON files."""
    input_dir = input_dir or FETCH_DATAS_DIR
    json_files = sorted(input_dir.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return []

    results = []
    for json_path in json_files:
        try:
            results.append(wash_file(json_path))
        except Exception as e:
            print(f"Failed to wash {json_path.name}: {e}")

    return results


if __name__ == "__main__":
    wash_all()
