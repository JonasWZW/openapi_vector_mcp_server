# -*- coding: utf-8 -*-
"""Configuration management - reads from .env file and yaml configs."""

from pathlib import Path
from dotenv import load_dotenv
import os
import yaml

# Load .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
FETCH_RAW_DIR = BASE_DIR / "fetch" / "raw"
FETCH_DATAS_DIR = BASE_DIR / "fetch" / "datas"
DOCS_DIR = BASE_DIR / "docs"
FETCH_YAML = BASE_DIR / "fetch.yaml"

# Milvus
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))
MILVUS_COLLECTION = os.getenv("MILVUS_COLLECTION", "openapi_vectors")

# OpenAI Embeddings
OPENAI_API_BASE_URL = os.getenv("OPENAI_API_BASE_URL", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-4B")
DIM = int(os.getenv("OPENAI_EMBEDDING_DIM", "2560"))

# MCP Server
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "15277"))


def get_fetch_apps() -> list[dict]:
    """Load fetch app config from fetch.yaml."""
    if not FETCH_YAML.exists():
        print(f"Warning: {FETCH_YAML} not found")
        return []
    with open(FETCH_YAML, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config.get("apps", [])
