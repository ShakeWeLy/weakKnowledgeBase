"""Command line entry: python -m rag build | search | ask"""

from __future__ import annotations

import argparse
import asyncio
import sys

from rag.config import COLLECTION_NAME, EMBED_MODEL_PATH, MILVUS_URI


def _cmd_build(args: argparse.Namespace) -> int:
    from rag.indexer import build_index

    print(f"embedding model: {EMBED_MODEL_PATH}")
    print(f"milvus: {MILVUS_URI} collection={COLLECTION_NAME}")
    stats = build_index(rebuild=args.rebuild)
    print("done:", dict(stats))
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    from rag.retriever import BlogRetriever, format_hits

    hits = BlogRetriever().search(args.query, top_k=args.top_k, subcategory=args.subcategory)
    print(format_hits(hits) if hits else "no hits")
    return 0


def _cmd_ask(args: argparse.Namespace) -> int:
    from rag.agent import BlogRagAgent

    async def _run() -> str:
        agent = BlogRagAgent()
        return await agent.run(args.question)

    print(asyncio.run(_run()))
    return 0


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="rag", description="Blog RAG pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="incrementally index blogs/*.md into Milvus")
    p_build.add_argument("--rebuild", action="store_true", help="drop collection and re-embed everything")
    p_build.set_defaults(func=_cmd_build)

    p_search = sub.add_parser("search", help="semantic search without the LLM")
    p_search.add_argument("query")
    p_search.add_argument("--top-k", type=int, default=5)
    p_search.add_argument("--subcategory")
    p_search.set_defaults(func=_cmd_search)

    p_ask = sub.add_parser("ask", help="ask the blog agent (uses config.toml LLM)")
    p_ask.add_argument("question")
    p_ask.set_defaults(func=_cmd_ask)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
