"""RAG pipeline settings. Every value can be overridden by an environment variable."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BLOGS_DIR = PROJECT_ROOT / "blogs"
DATA_DIR = PROJECT_ROOT / "rag" / "data"
MANIFEST_PATH = DATA_DIR / "manifest.json"

# multilingual-e5-large: the blogs are Chinese, so this is preferred over all-MiniLM-L6-v2 (English-only).
EMBED_MODEL_PATH = os.getenv("RAG_EMBED_MODEL", r"F:\models\multilingual-e5-large")
EMBED_DEVICE = os.getenv("RAG_EMBED_DEVICE", "cpu")
EMBED_BATCH_SIZE = int(os.getenv("RAG_EMBED_BATCH_SIZE", "16"))

# Named [llm.*] section in config.toml. The default [llm] section (dashscope) returned 401 with the current key.
RAG_LLM_CONFIG = os.getenv("RAG_LLM_CONFIG", "deepseek_default")

MILVUS_URI = os.getenv("RAG_MILVUS_URI", "http://localhost:19530")
COLLECTION_NAME = os.getenv("RAG_COLLECTION", "blog_chunks")

CHUNK_MAX_CHARS = 800
CHUNK_OVERLAP_CHARS = 80
MIN_CHUNK_CHARS = 10
