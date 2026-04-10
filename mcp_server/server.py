# -*- coding: utf-8 -*-
"""MCP Server - FastMCP server exposing list and search tools."""

from fastmcp import FastMCP

from config import MCP_SERVER_HOST, MCP_SERVER_PORT
from mcp_server.tools.list_collections import list_collections_impl
from mcp_server.tools.search_apis import search_apis_impl, get_api_detail_impl


mcp = FastMCP("OpenAPI Vector MCP Server")


@mcp.tool()
def list_collections() -> list[dict]:
    """
    List all Milvus collections (each represents an app).
    Returns:
        list[dict]: Each dict contains:
            - collection (str): Collection name in Milvus (e.g., 'bcm', 'auth_rest')
            - app_name (str): Human-readable app name (e.g., 'bcm', '权限管理')
            - description (str): App module description (e.g., '基线配置管理模块，它具备xxx功能')
    """
    return list_collections_impl()


@mcp.tool()
def search_apis(collection: str, query: str, limit: int = 3) -> list[dict]:
    """
    Search for APIs using Milvus hybrid search within a collection.
    Returns lightweight results for selection - use get_api_detail() for full info.

    Args:
        collection (str): Milvus collection name (e.g., 'bcm', 'auth_rest').
                          Use list_collections() to see available collections.
        query (str): Natural language query to search for.
        limit (int): Maximum number of results to return (default: 3).

    Returns:
        list[dict]: Each dict contains:
            - uri (str): API URI in format 'METHOD /path' (e.g., 'POST /api/v1/users')
            - text (str): Vector text summary (truncated to 300 chars)
    """
    if not query or not collection:
        return []
    return search_apis_impl(collection=collection, query=query, limit=limit)


@mcp.tool()
def get_api_detail(collection: str, uri: str) -> dict | None:
    """
    Get full API details by URI from a collection.
    Call this after search_apis() to get complete API information.

    Args:
        collection (str): Milvus collection name (e.g., 'bcm', 'auth_rest').
        uri (str): API URI in format 'METHOD /path' (e.g., 'POST /api/v1/users').

    Returns:
        dict | None: API details containing:
            - uri (str): API URI in format 'METHOD /path'
            - operation_id (str): Unique operation identifier
            - summary (str): API summary/description
            - parameters (list[dict]): Query/path parameters (nullable)
            - request (dict): Request body schema (nullable)
            - response (dict): Response schema (nullable)
            - deprecated (bool): Whether the API is deprecated
            - text (str): Full vector text
    """
    if not uri or not collection:
        return None
    return get_api_detail_impl(collection=collection, uri=uri)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)
