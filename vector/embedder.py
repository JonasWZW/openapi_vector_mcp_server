# -*- coding: utf-8 -*-
"""Embedder - vectorize text using langchain OpenAIEmbeddings."""

from langchain_openai import OpenAIEmbeddings

from config import OPENAI_API_BASE_URL, OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL


def get_embedder() -> OpenAIEmbeddings:
    """Create an OpenAIEmbeddings instance from .env config."""
    return OpenAIEmbeddings(
        model=OPENAI_EMBEDDING_MODEL,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_API_BASE_URL,
    )


def embed_texts(embedder: OpenAIEmbeddings, texts: list[str]) -> list[list[float]]:
    """Embed a list of texts."""
    return embedder.embed_documents(texts)
