# -*- coding: utf-8 -*-
"""Schema resolver - resolves $ref references within OpenAPI JSON."""

import json
from typing import Any


class SchemaResolver:
    """Resolves $ref references in OpenAPI schemas."""

    def __init__(self, schemas: dict[str, Any] | None = None):
        """
        Args:
            schemas: Dict of schema name -> schema definition, typically from
                     components/schemas in OpenAPI spec.
        """
        self._schemas = schemas or {}

    def resolve(self, schema: Any) -> Any:
        """Resolve a schema, handling $ref recursively."""
        if isinstance(schema, dict):
            if "$ref" in schema:
                return self._resolve_ref(schema["$ref"])
            return {k: self.resolve(v) for k, v in schema.items()}
        elif isinstance(schema, list):
            return [self.resolve(item) for item in schema]
        return schema

    def _resolve_ref(self, ref: str) -> Any:
        """
        Resolve a $ref string like '#/components/schemas/ExecCmdRequest'.
        Returns the resolved schema, or the original ref string if not found.
        """
        if not ref.startswith("#/components/schemas/"):
            return ref

        schema_name = ref.removeprefix("#/components/schemas/")
        if schema_name in self._schemas:
            return self.resolve(self._schemas[schema_name])
        return ref

    @classmethod
    def from_json(cls, json_data: list[dict]) -> "SchemaResolver":
        """
        Build a SchemaResolver from a loaded OpenAPI JSON (list of operations).
        Extracts components/schemas if present in any operation's parent context.
        Note: The fetch/datas/*.json files are operation lists, not full specs,
        so components may not be present. This is a no-op in that case.
        """
        schemas = {}
        # These files are operation arrays, not full specs
        # If they somehow contain a top-level 'components' key, extract it
        if isinstance(json_data, dict) and "components" in json_data:
            components = json_data.get("components", {})
            schemas = components.get("schemas", {})
        return cls(schemas)

    def resolve_operation(self, operation: dict) -> dict:
        """Resolve $ref in a single operation's request/response schemas."""
        resolved = dict(operation)

        if "request_schema" in resolved and resolved["request_schema"]:
            resolved["request_schema"] = self.resolve(resolved["request_schema"])

        if "response_schema" in resolved and resolved["response_schema"]:
            resolved["response_schema"] = self.resolve(resolved["response_schema"])

        return resolved
