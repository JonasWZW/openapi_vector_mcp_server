# -*- coding: utf-8 -*-
"""List collections tool - list all Milvus collections with caching."""

import time
from threading import Lock

from vector.milvus_client import MilvusVectorStore

# Cache: (data, timestamp)
_cache: tuple[list[dict], float] | None = None
_CACHE_TTL_SECONDS = 2 * 60 * 60  # 2 hours
_lock = Lock()


def list_collections_impl() -> list[dict]:
    """
    List all Milvus collections (each represents an app).
    Returns list of {collection, app_name, description}.
    Uses in-memory cache with 2-hour TTL.
    """
    global _cache

    with _lock:
        if _cache is not None:
            data, timestamp = _cache
            if time.time() - timestamp < _CACHE_TTL_SECONDS:
                return data

        store = MilvusVectorStore()
        data = store.get_app_list()
        _cache = (data, time.time())
        return data
