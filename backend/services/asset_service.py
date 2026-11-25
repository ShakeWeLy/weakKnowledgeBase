"""Serve images referenced by blog markdown. Only files inside blogs_dir with image extensions are allowed."""

from __future__ import annotations

from pathlib import Path

from services.errors import NotFoundError

ALLOWED_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"})


def resolve_asset(blogs_dir: Path, relative_path: str) -> Path:
    if not relative_path or "\x00" in relative_path:
        raise NotFoundError("资源不存在")
    root = blogs_dir.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:  # path traversal (../) or absolute path outside blogs_dir
        raise NotFoundError("资源不存在") from exc
    if candidate.suffix.lower() not in ALLOWED_SUFFIXES or not candidate.is_file():
        raise NotFoundError("资源不存在")
    return candidate
