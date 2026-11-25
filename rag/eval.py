"""Retrieval sanity check: does each question surface a blog that should answer it?

Run: python -m rag.eval
"""

from __future__ import annotations

import sys

from rag.retriever import BlogRetriever

# (question, substring of the expected source file name)
EVAL_SET: list[tuple[str, str]] = [
    ("Unet 的网络结构是什么样的", "Unet"),
    ("语义分割和实例分割有什么区别", "语义分割汇总"),
    ("RAG 和微调各自适用什么场景", "rag_0初步认识"),
    ("多目标跟踪 MOT 的基本流程", "目标追踪2MOT"),
    ("TensorRT 安装与运行实例", "TensorRT安装与实例"),
    ("ONNX 图优化做了哪些事情", "ONNX4-图优化"),
    ("注意力机制中 Query Key Value 的含义", "attention"),
    ("向量数据库 Milvus 和 Chroma 的对比", "向量数据库"),
    ("MCP 协议解决什么问题", "agent协议mcp"),
    ("训练后量化 PTQ 与 QAT 的区别", "训练后量化"),
    ("阿里天池比赛中的特征工程怎么做", "阿里天池1特征工程"),
    ("Agent 上下文工程的核心思路", "agent上下文工程"),
]

TOP_K = 5


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    retriever = BlogRetriever()
    top1 = 0
    recall = 0
    for question, expected in EVAL_SET:
        hits = retriever.search(question, top_k=TOP_K)
        sources = [h.get("source", "") for h in hits]
        rank = next((i for i, s in enumerate(sources, start=1) if expected.lower() in s.lower()), None)
        if rank == 1:
            top1 += 1
        if rank is not None:
            recall += 1
        status = f"rank {rank}" if rank else "MISS"
        print(f"[{status}] {question}\n    top1: {sources[0] if sources else '-'}")
    total = len(EVAL_SET)
    print(f"\nRecall@{TOP_K}: {recall}/{total}  Top1: {top1}/{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
