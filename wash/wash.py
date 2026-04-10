# -*- coding: utf-8 -*-
"""Wash module - clean OpenAPI JSON and output structured Markdown."""

import json
from pathlib import Path

from config import FETCH_DATAS_DIR, DOCS_DIR
from md_writer import write_app_md


def infer_app_name(file_path: Path) -> str:
    """Infer app name from file name, e.g. 'bcm接口文档.json' -> 'bcm'."""
    return file_path.stem.replace("接口文档", "")


def wash_file(json_path: Path) -> Path:
    """Wash a single app's JSON file and output to docs/{app_name}.md."""
    with open(json_path, encoding="utf-8") as f:
        operations = json.load(f)

    app_name = infer_app_name(json_path)
    output_path = DOCS_DIR / f"{app_name}.md"

    write_app_md(app_name, operations, output_path)
    print(f"Washed: {json_path.name} -> {output_path}")
    return output_path


def wash_all(input_dir: Path | None = None) -> list[Path]:
    """Wash all JSON files in the input directory."""
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
