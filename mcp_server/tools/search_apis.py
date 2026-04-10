# -*- coding: utf-8 -*-
"""Search APIs tool - search APIs using Milvus hybrid search."""

from vector.milvus_client import MilvusVectorStore

# Cache stores per collection to avoid repeated client creation
_store_cache: dict[str, MilvusVectorStore] = {}


def _get_store(collection: str) -> MilvusVectorStore:
    """Get or create a cached store for the given collection."""
    if collection not in _store_cache:
        _store_cache[collection] = MilvusVectorStore(collection=collection)
    return _store_cache[collection]


def search_apis_impl(collection: str, query: str, limit: int = 3) -> list[dict]:
    """
    Search for APIs using Milvus hybrid search within a collection.
    Returns lightweight result with only text and uri for selection.
    """
    store = _get_store(collection)
    results = store.hybrid_search(query, limit=limit)

    return [
        {
            "uri": r.get("uri"),
            "text": r.get("text", "")[:500],
        }
        for r in results
    ]


def get_api_detail_impl(collection: str, uri: str) -> dict | None:
    """
    Get full API details by URI from a collection.
    Returns complete API info including request/response schemas.
    """
    store = _get_store(collection)
    results = store.client.get(collection_name=collection, ids=[uri],
                               output_fields=["uri", "app_name", "operation_id", "summary", "parameters",
                                              "request", "response", "deprecated"])

    for r in results:
        if r.get("uri") == uri:
            return {
                "uri": r.get("uri"),
                "operation_id": r.get("operation_id"),
                "summary": r.get("summary"),
                "parameters": r.get("parameters"),
                "request": r.get("request"),
                "response": r.get("response"),
                "deprecated": r.get("deprecated", False),
            }
    return None
