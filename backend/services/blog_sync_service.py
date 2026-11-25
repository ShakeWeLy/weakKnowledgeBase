"""Incremental sync of blogs/*.md into knowledge_entries. The md files stay the source of truth.

Rules:
- Unchanged files (same sha256) are skipped.
- Changed files update the existing row (ids stay stable, so relations survive).
- Files that disappear are soft-deleted; they come back automatically if the file reappears.
- Nothing is hard-deleted.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from core.models.base import utcnow
from core.models.knowledge import KnowledgeEntry
from repositories import knowledge_repository as repo
from schemas.knowledge import SyncResultOut
from services.blog_parser import PARSER_VERSION, parse_blog
from services.errors import ServiceUnavailableError


def _mtime_utc(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).replace(tzinfo=None)


def sync_blogs(db: Session, blogs_dir: Path) -> SyncResultOut:
    # A missing directory must not be treated as "all files deleted".
    if not blogs_dir.is_dir():
        raise ServiceUnavailableError(f"blogs 目录不存在：{blogs_dir}")

    counts = {"added": 0, "updated": 0, "unchanged": 0, "removed": 0}
    existing = repo.all_entries_by_source(db)
    seen: set[str] = set()

    try:
        for path in sorted(p for p in blogs_dir.glob("*.md") if p.is_file() and not p.name.startswith(".")):
            source = path.name
            seen.add(source)
            raw_bytes = path.read_bytes()
            digest = hashlib.sha256(f"parser-v{PARSER_VERSION}\n".encode() + raw_bytes).hexdigest()

            entry = existing.get(source)
            if entry is not None and not entry.is_deleted and entry.content_hash == digest:
                counts["unchanged"] += 1
                continue

            parsed = parse_blog(path.stem, raw_bytes.decode("utf-8", errors="replace"))
            if entry is None:
                entry = KnowledgeEntry(source_path=source, tags=[])  # init collection: lazy="raise" forbids implicit load
                db.add(entry)
                outcome = "added"
            else:
                outcome = "updated"
                if entry.is_deleted:
                    entry.is_deleted = False
                    entry.deleted_at = None
                    entry.status = "active"

            entry.title = parsed.title
            entry.summary = parsed.summary
            entry.content = parsed.content
            entry.category = parsed.category
            entry.subcategory = parsed.subcategory
            entry.entry_type = parsed.entry_type
            entry.source_created_at = parsed.source_created_at
            entry.source_updated_at = _mtime_utc(path)
            entry.content_hash = digest
            entry.tags = repo.get_or_create_tags(db, parsed.tags)
            db.flush()

            repo.fts_upsert(db, entry.id, parsed.title, parsed.summary, parsed.search_text)
            counts[outcome] += 1

        for source, entry in existing.items():
            if source in seen or entry.is_deleted:
                continue
            entry.is_deleted = True
            entry.deleted_at = utcnow()
            entry.status = "archived"
            repo.fts_delete(db, entry.id)
            counts["removed"] += 1

        db.commit()
    except Exception:
        db.rollback()
        raise

    return SyncResultOut(**counts)
