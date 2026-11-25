"""Split blog markdown files into retrieval chunks that keep their metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from rag.config import CHUNK_MAX_CHARS, CHUNK_OVERLAP_CHARS, MIN_CHUNK_CHARS

HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*$")
MD_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
HTML_IMG_RE = re.compile(r"<img[^>]*>", re.IGNORECASE)
HTML_LAYOUT_RE = re.compile(r"</?(div|span|br|p|center|sup|sub)\b[^>]*>", re.IGNORECASE)


@dataclass
class Chunk:
    source: str
    title: str
    heading: str
    category: str
    subcategory: str
    tags: str
    text: str

    @property
    def embed_text(self) -> str:
        """Text sent to the embedding model; the heading path adds context to short chunks."""
        return f"{self.title} | {self.heading}\n{self.text}"


def parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    if not raw.startswith("---"):
        return {}, raw
    end = raw.find("\n---", 3)
    if end == -1:
        return {}, raw
    try:
        meta = yaml.safe_load(raw[3:end]) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, raw[end + len("\n---"):]


def split_sections(body: str) -> list[tuple[str, list[str]]]:
    """Split by markdown headings; lines inside fenced code blocks never start a section."""
    sections: list[tuple[str, list[str]]] = []
    stack: list[tuple[int, str]] = []
    lines: list[str] = []
    path = ""
    in_fence = False

    for line in body.splitlines():
        if line.strip().startswith(("```", "~~~")):
            in_fence = not in_fence
            lines.append(line)
            continue
        if not in_fence:
            match = HEADING_RE.match(line)
            if match:
                if lines:
                    sections.append((path, lines))
                lines = []
                level = len(match.group(1))
                title = match.group(2).strip().strip("#").strip()
                while stack and stack[-1][0] >= level:
                    stack.pop()
                stack.append((level, title))
                path = " > ".join(t for _, t in stack)
                continue
        lines.append(line)

    if lines:
        sections.append((path, lines))
    return sections


def clean_text(text: str) -> str:
    text = MD_IMAGE_RE.sub("", text)
    text = HTML_IMG_RE.sub("", text)
    text = HTML_LAYOUT_RE.sub("", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def pack_paragraphs(paragraphs: list[str]) -> list[str]:
    """Greedily pack paragraphs up to CHUNK_MAX_CHARS; oversized paragraphs are hard-split with overlap."""
    chunks: list[str] = []
    buf = ""
    step = CHUNK_MAX_CHARS - CHUNK_OVERLAP_CHARS
    for para in paragraphs:
        if len(para) > CHUNK_MAX_CHARS:
            if buf:
                chunks.append(buf)
                buf = ""
            for start in range(0, len(para), step):
                chunks.append(para[start : start + CHUNK_MAX_CHARS])
            continue
        if buf and len(buf) + 2 + len(para) > CHUNK_MAX_CHARS:
            chunks.append(buf)
            buf = para
        else:
            buf = f"{buf}\n\n{para}" if buf else para
    if buf:
        chunks.append(buf)
    return chunks


def split_markdown(path: Path) -> list[Chunk]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    meta, body = parse_frontmatter(raw)

    title = str(meta.get("title") or path.stem)
    category = str(meta.get("category") or "")
    subcategory = str(meta.get("subcategory") or "")
    tags_value = meta.get("tags") or []
    if isinstance(tags_value, str):
        tags_value = [tags_value]
    tags = ",".join(str(t) for t in tags_value)

    chunks: list[Chunk] = []
    for heading_path, lines in split_sections(body):
        text = clean_text("\n".join(lines))
        if len(text) < MIN_CHUNK_CHARS:
            continue
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        for piece in pack_paragraphs(paragraphs):
            if len(piece) < MIN_CHUNK_CHARS:
                continue
            chunks.append(
                Chunk(
                    source=path.name,
                    title=title,
                    heading=heading_path or title,
                    category=category,
                    subcategory=subcategory,
                    tags=tags,
                    text=piece,
                )
            )
    return chunks
