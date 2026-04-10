# -*- coding: utf-8 -*-
"""Vectorize module - load structured JSON, embed, and upsert to Milvus."""

import json
from pathlib import Path

from langchain_core.documents import Document

from config import DOCS_DIR
from vector.text_splitter import build_vector_text
from vector.milvus_client import MilvusVectorStore


def vectorize_file(json_path: Path) -> int:
    """Vectorize a single app's JSON file and upsert to Milvus."""
    with open(json_path, encoding="utf-8") as f:
        app_data = json.load(f)

    app_name = app_data.get("app_name", "")
    collection_name = app_data.get("collection_name", f"{app_name}_rest")
    description = app_data.get("description", "")
    operations = app_data.get("operations", [])
    if not operations:
        print(f"No operations found in {json_path}")
        return 0

    store = MilvusVectorStore(collection=collection_name)
    store.create_collection(description=description)

    docs = []
    texts_to_embed = []

    for op in operations:
        # Build vector text from operation fields
        tags = op.get("tags", [])
        method = op.get("method", "")
        path = op.get("path", "")
        operation_id = op.get("operation_id", "")
        summary = op.get("summary", "")
        description = op.get("description", "")
        vector_text = build_vector_text(tags, method, path, operation_id, summary, description)
        # Build full text including request/response for embedding
        full_text = vector_text
        texts_to_embed.append(full_text)

        # Create a doc-like object with metadata
        doc = Document(
            page_content=full_text,
            metadata={
                "app_name": app_name,
                "version": app_data.get("version", ""),
                "operation_id": op.get("operation_id", ""),
                "path": op.get("path", ""),
                "method": op.get("method", ""),
                "summary": summary,
                "description": description,
                "tags": tags,
                "deprecated": op.get("deprecated", False),
                "parameters": op.get("parameters", []),
                "request": op.get("request"),
                "response": op.get("response"),
            },
        )
        docs.append(doc)

    if not docs:
        return 0

    # Embed
    vectors = store.embedder.embed_documents(texts_to_embed)

    # Upsert
    store.upsert(docs, vectors, texts_to_embed)
    print(f"Vectorized: {json_path.name} -> collection:{collection_name} ({len(docs)} operations)")
    return len(docs)


def vectorize_all(docs_dir: Path | None = None) -> int:
    """Vectorize all JSON files in docs directory, each app to its own collection."""
    docs_dir = docs_dir or DOCS_DIR
    json_files = sorted(docs_dir.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {docs_dir}")
        return 0

    total = 0
    for json_path in json_files:
        try:
            total += vectorize_file(json_path)
        except Exception as e:
            print(f"Failed to vectorize {json_path.name}: {e}")

    print(f"Total: {total} operations vectorized")
    return total


if __name__ == "__main__":
    # vectorize_all()
    store = MilvusVectorStore(collection="dbbackup_manager")
    res = store.hybrid_search("库表配置 ClickHouse 创建表和物化视图 ")
    print(json.dumps(res, indent=2, ensure_ascii=False))
