"""weakagent tool that lets an agent search the blog knowledge base."""

from __future__ import annotations

import asyncio
from typing import Optional

from weakagent.tools.base import BaseTool, ToolExecutionResult

from rag.retriever import BlogRetriever, format_hits

_retriever: Optional[BlogRetriever] = None


def get_retriever() -> BlogRetriever:
    """Load the embedding model once per process."""
    global _retriever
    if _retriever is None:
        _retriever = BlogRetriever()
    return _retriever


class SearchBlogsTool(BaseTool):
    name: str = "search_blogs"
    description: str = (
        "在个人技术博客知识库中做语义检索，返回最相关的文本片段及其来源文件名。"
        "回答关于博客内容的问题前应先调用本工具。"
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "检索问题或关键词，可用中文或英文。",
            },
            "subcategory": {
                "type": "string",
                "description": "可选，按二级分类过滤，例如 CV、DL、Agent、Deploy、MRI、Python、ML。",
            },
            "top_k": {
                "type": "integer",
                "description": "返回片段数量，1 到 10，默认 5。",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    async def execute(
        self,
        query: str,
        subcategory: Optional[str] = None,
        top_k: int = 5,
    ) -> ToolExecutionResult:
        query = (query or "").strip()
        if not query:
            return self.fail_response("query 不能为空。")
        top_k = max(1, min(int(top_k or 5), 10))
        hits = await asyncio.to_thread(get_retriever().search, query, top_k, subcategory or None)
        if not hits:
            return self.success_response("知识库中没有检索到相关内容。")
        return self.success_response(format_hits(hits))
