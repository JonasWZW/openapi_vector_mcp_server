# -*- coding: utf-8 -*-
"""Text splitter - split Markdown by ## headers using langchain."""

from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document


def split_md_by_headers(md_text: str, app_name: str) -> list[Document]:
    """
    Split a Markdown file by ## headers.
    Each ## section becomes a separate Document.
    """
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("##", "operation_id"),
        ]
    )

    docs = splitter.split_text(md_text)

    # Tag each doc with app_name
    for doc in docs:
        doc.metadata["app_name"] = app_name

    return docs


def build_vector_text(
    tags: list[str],
    method: str,
    path: str,
    operation_id: str,
    summary: str,
    description: str,
) -> str:
    """
    Build the text used for vector embedding.

    Format: [标签: tag1, tag2] METHOD PATH。功能：summary (operationId)。详细描述：description

    This natural language format is optimized for embedding and LLM understanding.
    """
    tag_str = ", ".join(tags) if tags else ""
    tag_part = f"[标签: {tag_str}]" if tag_str else ""
    func_part = f"功能：{summary}" if summary else "功能："
    if operation_id:
        func_part += f" ({operation_id})"
    desc_part = f"详细描述：{description}" if description else ""

    parts = [p for p in [tag_part, f"{method.upper()} {path}", func_part, desc_part] if p and not p.endswith("：")]
    return "。".join(parts)
