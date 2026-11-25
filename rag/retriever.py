"""Query-side retrieval: embed the question and search Milvus."""

from __future__ import annotations

from typing import Any, Optional

from rag.config import COLLECTION_NAME, MILVUS_URI
from rag.embedder import BlogEmbedder
from rag.store import MilvusBlogStore


class BlogRetriever:
    def __init__(self) -> None:
        self.embedder = BlogEmbedder()
        self.store = MilvusBlogStore(MILVUS_URI, COLLECTION_NAME, self.embedder.dim)

    def search(self, query: str, top_k: int = 5, subcategory: Optional[str] = None) -> list[dict[str, Any]]:
        vector = self.embedder.embed_query(query)
        return self.store.search(vector, top_k=top_k, subcategory=subcategory)


def format_hits(hits: list[dict[str, Any]]) -> str:
    blocks = []
    for i, hit in enumerate(hits, start=1):
        category = " / ".join(x for x in (hit.get("category"), hit.get("subcategory")) if x)
        blocks.append(
            f"[{i}] 来源: {hit.get('source')} | 分类: {category or '-'} | "
            f"标题: {hit.get('heading') or hit.get('title')} | 相关度: {hit.get('score', 0):.3f}\n"
            f"{hit.get('text', '')}"
        )
    return "\n\n".join(blocks)
