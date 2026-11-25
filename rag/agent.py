"""Blog Q&A agent built on weakagent's ToolCallAgent."""

from __future__ import annotations

from pydantic import Field

from weakagent.agent.toolcall import ToolCallAgent
from weakagent.llm.llm import LLM
from weakagent.tools import ToolCollection

from rag.config import RAG_LLM_CONFIG
from rag.tools import SearchBlogsTool

RAG_SYSTEM_PROMPT = """你是个人技术博客知识库的问答助手。
规则：
1. 回答前必须先调用 search_blogs 检索，只依据检索到的内容作答，不要编造。
2. 检索结果不足以回答时，明确说明知识库中没有相关内容。
3. 使用简体中文，回答结构清晰。
4. 在回答末尾列出引用的来源文件名。
5. 给出最终回答后不再调用工具。
"""


class BlogRagAgent(ToolCallAgent):
    name: str = "blog_rag"
    description: str = "基于个人博客知识库回答问题的 Agent"
    system_prompt: str = RAG_SYSTEM_PROMPT
    next_step_prompt: str = ""
    llm: LLM = Field(default_factory=lambda: LLM(config_name=RAG_LLM_CONFIG))
    mcp_enabled: bool = False
    available_tools: ToolCollection = ToolCollection(SearchBlogsTool())
    max_steps: int = 4
