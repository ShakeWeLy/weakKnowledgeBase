"""All SQL for knowledge entries, tags, FTS and relations lives here (no business rules)."""

from __future__ import annotations

import json
from collections.abc import Iterable

from sqlalchemy import Float, String, and_, func, or_, select, text
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import ColumnElement, Select

from core.models.knowledge import EntryRelation, KnowledgeEntry, Tag, entry_tags
from schemas.knowledge import EntryListParams

NO_CATEGORY = "__none__"  # filter value meaning "category IS NULL"
FTS_MIN_QUERY_LEN = 3  # trigram tokenizer cannot match shorter strings


def fts_phrase(q: str) -> str:
    """Quote user input as one FTS5 phrase so operators like AND/OR/* cannot break the query."""
    return '"' + q.replace('"', '""') + '"'


def keyword_mode(q: str | None) -> str | None:
    if not q:
        return None
    return "fts" if len(q) >= FTS_MIN_QUERY_LEN else "like"


def _fts_subquery(q: str):  # type: ignore[no-untyped-def]
    return (
        text("SELECT entry_id, bm25(knowledge_fts) AS rank FROM knowledge_fts WHERE knowledge_fts MATCH :q")
        .bindparams(q=fts_phrase(q))
        .columns(entry_id=String(36), rank=Float)
        .subquery("fts")
    )


def apply_filters(stmt: Select, params: EntryListParams) -> tuple[Select, ColumnElement | None]:
    """Apply deleted/category/type/tag/keyword conditions. Returns the statement and the FTS rank column if any."""
    conds: list[ColumnElement] = [KnowledgeEntry.is_deleted.is_(False)]

    if params.category is not None:
        if params.category == NO_CATEGORY:
            conds.append(KnowledgeEntry.category.is_(None))
        else:
            conds.append(KnowledgeEntry.category == params.category)
    if params.subcategory is not None:
        if params.subcategory == NO_CATEGORY:
            conds.append(KnowledgeEntry.subcategory.is_(None))
        else:
            conds.append(KnowledgeEntry.subcategory == params.subcategory)
    if params.entry_type:
        conds.append(KnowledgeEntry.entry_type == params.entry_type)
    for tag_name in params.tags:
        tagged = (
            select(entry_tags.c.entry_id)
            .join(Tag, Tag.id == entry_tags.c.tag_id)
            .where(Tag.name == tag_name)
        )
        conds.append(KnowledgeEntry.id.in_(tagged))

    rank: ColumnElement | None = None
    mode = keyword_mode(params.q)
    if mode == "fts":
        fts = _fts_subquery(params.q or "")
        stmt = stmt.join(fts, fts.c.entry_id == KnowledgeEntry.id)
        rank = fts.c.rank
    elif mode == "like":
        needle = (params.q or "").lower()
        conds.append(
            or_(
                func.instr(func.lower(KnowledgeEntry.title), needle) > 0,
                func.instr(func.lower(KnowledgeEntry.summary), needle) > 0,
                func.instr(func.lower(KnowledgeEntry.content), needle) > 0,
            )
        )
    return stmt.where(*conds), rank


def _order_clauses(params: EntryListParams, rank: ColumnElement | None) -> list:
    sort = params.sort or ("relevance" if rank is not None else "source_created_at")
    desc = params.order == "desc"
    if sort == "relevance":
        if rank is not None:
            return [rank.asc(), KnowledgeEntry.id.asc()]
        sort = "source_created_at"  # no keyword: relevance is meaningless, fall back to newest
    if sort == "title":
        col = KnowledgeEntry.title
        return [col.desc() if desc else col.asc(), KnowledgeEntry.id.asc()]
    col = KnowledgeEntry.source_created_at if sort == "source_created_at" else KnowledgeEntry.source_updated_at
    ordered = col.desc().nulls_last() if desc else col.asc().nulls_last()
    return [ordered, KnowledgeEntry.id.asc()]


def search_entries(db: Session, params: EntryListParams) -> tuple[list[KnowledgeEntry], int]:
    base, rank = apply_filters(select(KnowledgeEntry), params)
    count_stmt, _ = apply_filters(select(func.count()).select_from(KnowledgeEntry), params)
    total = db.scalar(count_stmt) or 0

    offset = (params.page - 1) * params.page_size
    stmt = (
        base.order_by(*_order_clauses(params, rank))
        .offset(offset)
        .limit(params.page_size)
        .options(selectinload(KnowledgeEntry.tags))
    )
    return list(db.scalars(stmt).all()), int(total)


def fts_snippets(db: Session, q: str, entry_ids: list[str]) -> dict[str, str]:
    """One query for a whole page of FTS snippets. Matches are wrapped in [[ ]] by the FTS engine."""
    if not entry_ids:
        return {}
    rows = db.execute(
        text(
            "SELECT entry_id, snippet(knowledge_fts, 3, '[[', ']]', '...', 24) AS snip "
            "FROM knowledge_fts WHERE knowledge_fts MATCH :q "
            "AND entry_id IN (SELECT value FROM json_each(:ids))"
        ),
        {"q": fts_phrase(q), "ids": json.dumps(entry_ids)},
    ).all()
    return {row[0]: row[1] for row in rows if row[1]}


def facet_counts(db: Session, params: EntryListParams) -> dict[str, list]:
    matched = apply_filters(select(KnowledgeEntry.id), params)[0]
    in_matched = KnowledgeEntry.id.in_(matched)

    categories = db.execute(
        select(KnowledgeEntry.category, func.count())
        .where(in_matched)
        .group_by(KnowledgeEntry.category)
        .order_by(func.count().desc(), KnowledgeEntry.category)
    ).all()
    subcategories = db.execute(
        select(KnowledgeEntry.category, KnowledgeEntry.subcategory, func.count())
        .where(in_matched)
        .group_by(KnowledgeEntry.category, KnowledgeEntry.subcategory)
        .order_by(func.count().desc(), KnowledgeEntry.subcategory)
    ).all()
    types = db.execute(
        select(KnowledgeEntry.entry_type, func.count())
        .where(in_matched)
        .group_by(KnowledgeEntry.entry_type)
        .order_by(func.count().desc(), KnowledgeEntry.entry_type)
    ).all()
    tags = db.execute(
        select(Tag.name, func.count(entry_tags.c.entry_id))
        .join(entry_tags, entry_tags.c.tag_id == Tag.id)
        .where(entry_tags.c.entry_id.in_(matched))
        .group_by(Tag.name)
        .order_by(func.count(entry_tags.c.entry_id).desc(), Tag.name)
        .limit(80)
    ).all()
    return {
        "categories": categories,
        "subcategories": subcategories,
        "types": types,
        "tags": tags,
    }


def get_entry(db: Session, entry_id: str) -> KnowledgeEntry | None:
    return db.scalar(
        select(KnowledgeEntry)
        .where(KnowledgeEntry.id == entry_id, KnowledgeEntry.is_deleted.is_(False))
        .options(selectinload(KnowledgeEntry.tags))
    )


def all_entries_by_source(db: Session) -> dict[str, KnowledgeEntry]:
    rows = db.scalars(select(KnowledgeEntry).options(selectinload(KnowledgeEntry.tags))).all()
    return {row.source_path: row for row in rows}


def get_or_create_tags(db: Session, names: Iterable[str]) -> list[Tag]:
    wanted = sorted({name for name in names if name})
    if not wanted:
        return []
    existing = {tag.name: tag for tag in db.scalars(select(Tag).where(Tag.name.in_(wanted))).all()}
    for name in wanted:
        if name not in existing:
            tag = Tag(name=name)
            db.add(tag)
            existing[name] = tag
    db.flush()
    return [existing[name] for name in wanted]


def fts_delete(db: Session, entry_id: str) -> None:
    db.execute(text("DELETE FROM knowledge_fts WHERE entry_id = :id"), {"id": entry_id})


def fts_upsert(db: Session, entry_id: str, title: str, summary: str, content: str) -> None:
    fts_delete(db, entry_id)
    db.execute(
        text("INSERT INTO knowledge_fts (entry_id, title, summary, content) VALUES (:id, :title, :summary, :content)"),
        {"id": entry_id, "title": title, "summary": summary, "content": content},
    )


def list_relations_for(db: Session, entry_id: str) -> list[EntryRelation]:
    stmt = (
        select(EntryRelation)
        .where(or_(EntryRelation.source_id == entry_id, EntryRelation.target_id == entry_id))
        .options(
            selectinload(EntryRelation.source).selectinload(KnowledgeEntry.tags),
            selectinload(EntryRelation.target).selectinload(KnowledgeEntry.tags),
        )
        .order_by(EntryRelation.created_at.desc(), EntryRelation.id)
    )
    return list(db.scalars(stmt).all())


def get_relation(db: Session, relation_id: str) -> EntryRelation | None:
    return db.get(EntryRelation, relation_id)


def find_relation_pair(db: Session, a: str, b: str) -> EntryRelation | None:
    return db.scalar(
        select(EntryRelation).where(
            or_(
                and_(EntryRelation.source_id == a, EntryRelation.target_id == b),
                and_(EntryRelation.source_id == b, EntryRelation.target_id == a),
            )
        )
    )


def add_relation(db: Session, source_id: str, target_id: str) -> EntryRelation:
    relation = EntryRelation(source_id=source_id, target_id=target_id)
    db.add(relation)
    db.flush()
    return relation


def delete_relation(db: Session, relation: EntryRelation) -> None:
    db.delete(relation)


def recommend_by_tags(
    db: Session, entry: KnowledgeEntry, exclude_ids: set[str], limit: int
) -> list[tuple[KnowledgeEntry, int]]:
    """Entries sharing at least one tag, ranked by number of shared tags. One query, tags eager-loaded."""
    tag_ids = [tag.id for tag in entry.tags]
    if not tag_ids:
        return []
    shared = func.count(entry_tags.c.tag_id)
    stmt = (
        select(KnowledgeEntry, shared)
        .join(entry_tags, entry_tags.c.entry_id == KnowledgeEntry.id)
        .where(
            entry_tags.c.tag_id.in_(tag_ids),
            KnowledgeEntry.is_deleted.is_(False),
            KnowledgeEntry.id.not_in(list(exclude_ids)),
        )
        .group_by(KnowledgeEntry.id)
        .order_by(shared.desc(), KnowledgeEntry.source_created_at.desc().nulls_last(), KnowledgeEntry.id)
        .limit(limit)
        .options(selectinload(KnowledgeEntry.tags))
    )
    return [(row[0], int(row[1])) for row in db.execute(stmt).all()]
