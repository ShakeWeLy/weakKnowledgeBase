"""Incremental indexing: only files whose content hash changed are re-embedded."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from rag.chunking import split_markdown
from rag.config import BLOGS_DIR, COLLECTION_NAME, EMBED_MODEL_PATH, MANIFEST_PATH, MILVUS_URI
from rag.embedder import BlogEmbedder
from rag.store import MilvusBlogStore


def _load_manifest() -> dict[str, Any]:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {}


def _save_manifest(manifest: dict[str, Any]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_index(rebuild: bool = False) -> Counter:
    stats: Counter = Counter()
    files = sorted(p for p in BLOGS_DIR.glob("*.md") if not p.name.startswith("."))

    embedder = BlogEmbedder()
    store = MilvusBlogStore(MILVUS_URI, COLLECTION_NAME, embedder.dim)

    manifest = _load_manifest()
    stale_model = manifest.get("model") != EMBED_MODEL_PATH or manifest.get("dim") != embedder.dim
    if rebuild or stale_model or not store.exists():
        store.drop()
        manifest = {"model": EMBED_MODEL_PATH, "dim": embedder.dim, "files": {}}
    store.ensure_collection()

    indexed_files = manifest.setdefault("files", {})
    seen: set[str] = set()

    for path in files:
        source = path.name
        seen.add(source)
        digest = _digest(path)
        if indexed_files.get(source) == digest:
            stats["unchanged"] += 1
            continue

        store.delete_source(source)
        chunks = split_markdown(path)
        if not chunks:
            indexed_files[source] = digest
            _save_manifest(manifest)
            stats["empty"] += 1
            continue

        vectors = embedder.embed_passages([c.embed_text for c in chunks])
        rows = [
            {
                "vector": vec,
                "source": c.source,
                "title": c.title,
                "heading": c.heading,
                "category": c.category,
                "subcategory": c.subcategory,
                "tags": c.tags,
                "text": c.text,
            }
            for c, vec in zip(chunks, vectors)
        ]
        store.insert(rows)
        indexed_files[source] = digest
        _save_manifest(manifest)
        stats["indexed"] += 1
        stats["chunks"] += len(rows)
        print(f"indexed {source}: {len(rows)} chunks", flush=True)

    for source in sorted(set(indexed_files) - seen):
        store.delete_source(source)
        del indexed_files[source]
        _save_manifest(manifest)
        stats["removed"] += 1

    store.flush()
    _save_manifest(manifest)
    return stats
