"""Turn one blogs/*.md file into knowledge entry fields (frontmatter + body)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import yaml

# Bump when parsing rules change: the sync hashes this into content_hash, so every file is re-indexed once.
PARSER_VERSION = 4

DEFAULT_ENTRY_TYPE = "technical_note"
VALID_ENTRY_TYPES = frozenset(
    {"concept", "technical_note", "paper", "tutorial", "experiment", "project", "post", "reflection", "resource"}
)
MAX_TAG_LENGTH = 64
MAX_SUMMARY_LENGTH = 160
DATE_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d")

_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)|<img[^>]*>", re.IGNORECASE)
_LAYOUT_TAG_RE = re.compile(r"</?(div|span|br|p|center|sup|sub)\b[^>]*>", re.IGNORECASE)
_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_MD_MARK_RE = re.compile(r"^\s{0,3}#{1,6}\s+|^\s*>\s?|\*\*|`{1,3}|~~", re.MULTILINE)
_TAG_SPLIT_RE = re.compile(r"[,，、;；]")


@dataclass(frozen=True)
class ParsedBlog:
    title: str
    category: str | None
    subcategory: str | None
    entry_type: str
    tags: list[str]
    source_created_at: datetime | None
    content: str
    search_text: str
    summary: str


def split_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
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
    return meta, raw[end + len("\n---") :]


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _to_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None) if value.tzinfo else value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
    return None


def _normalize_tags(value: Any) -> list[str]:
    if value is None:
        return []
    items = _TAG_SPLIT_RE.split(value) if isinstance(value, str) else list(value)
    tags: list[str] = []
    for item in items:
        name = str(item).strip()[:MAX_TAG_LENGTH]
        if name and name not in tags:
            tags.append(name)
    return tags


def _search_text(body: str) -> str:
    """Plain text for FTS and snippets: no images, no HTML layout tags, no markdown syntax."""
    text = _IMAGE_RE.sub(" ", body)
    text = _LAYOUT_TAG_RE.sub(" ", text)
    text = _LINK_RE.sub(r"\1", text)
    text = _MD_MARK_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


_QUOTE_PREFIX_RE = re.compile(r"^\s*(>\s*)+")
_HEADING_PREFIX_RE = re.compile(r"^\s{0,3}#{1,6}(\s|$)")
_INLINE_MARK_RE = re.compile(r"\*\*|`|~~")


def _plain_line(line: str) -> str:
    text = _IMAGE_RE.sub("", line)
    text = _LINK_RE.sub(r"\1", text)
    text = _QUOTE_PREFIX_RE.sub("", text)  # "> text" and nested quotes
    text = _HEADING_PREFIX_RE.sub("", text)  # "> ## title" becomes a heading after the quote is removed
    text = _INLINE_MARK_RE.sub("", text)
    return text.strip(" -*|")


def _summary(body: str) -> str:
    """First real sentence-like line: skips code, headings, images and blank lines."""
    in_fence = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        unquoted = _QUOTE_PREFIX_RE.sub("", line)  # check headings after removing "> " but before removing "#"
        if in_fence or not stripped or _HEADING_PREFIX_RE.match(unquoted):
            continue
        plain = _plain_line(line)
        if plain:
            return plain[:MAX_SUMMARY_LENGTH]
    return ""


def parse_blog(filename_stem: str, raw: str) -> ParsedBlog:
    meta, body = split_frontmatter(raw)
    body = body.lstrip("\r\n")
    entry_type = _clean_text(meta.get("type")) or DEFAULT_ENTRY_TYPE
    if entry_type not in VALID_ENTRY_TYPES:
        entry_type = DEFAULT_ENTRY_TYPE
    return ParsedBlog(
        title=_clean_text(meta.get("title")) or filename_stem,
        category=_clean_text(meta.get("category")),
        subcategory=_clean_text(meta.get("subcategory")),
        entry_type=entry_type,
        tags=_normalize_tags(meta.get("tags")),
        source_created_at=_to_datetime(meta.get("date")),
        content=body,
        search_text=_search_text(body),
        summary=_summary(body),
    )
