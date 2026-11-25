"""Business rules for knowledge entries: list/search, facets, detail with relations and recommendations."""

from __future__ import annotations

from sqlalchemy.orm import Session

from core.models.knowledge import EntryRelation, KnowledgeEntry
from repositories import knowledge_repository as repo
from schemas.knowledge import (
    EntryBriefOut,
    EntryDetailOut,
    EntryListParams,
    EntryPageOut,
    EntrySummaryOut,
    FacetsOut,
    FacetValue,
    RecommendationOut,
    RelatedEntryOut,
    RelationOut,
    SubcategoryFacet,
)
from services.errors import ConflictError, NotFoundError, ServiceError

RECOMMENDATION_LIMIT = 8
SNIPPET_RADIUS = 40


def _brief(entry: KnowledgeEntry) -> EntryBriefOut:
    return EntryBriefOut(
        id=entry.id,
        title=entry.title,
        summary=entry.summary,
        category=entry.category,
        subcategory=entry.subcategory,
        type=entry.entry_type,
        tags=[tag.name for tag in entry.tags],
    )


def _summary(entry: KnowledgeEntry, snippet: str | None) -> EntrySummaryOut:
    brief = _brief(entry)
    return EntrySummaryOut(
        **brief.model_dump(by_alias=False),
        source_path=entry.source_path,
        source_created_at=entry.source_created_at,
        source_updated_at=entry.source_updated_at,
        snippet=snippet,
    )


def _like_snippet(content: str, needle_lower: str) -> str | None:
    """Short queries (< trigram length) use LIKE; build a plain window with [[ ]] markers like FTS does."""
    index = content.lower().find(needle_lower)
    if index == -1:
        return None
    start = max(0, index - SNIPPET_RADIUS)
    end = min(len(content), index + len(needle_lower) + SNIPPET_RADIUS)
    window = content[start:end].replace("\n", " ")
    match_start = index - start
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(content) else ""
    return (
        f"{prefix}{window[:match_start]}[[{window[match_start:match_start + len(needle_lower)]}]]"
        f"{window[match_start + len(needle_lower):]}{suffix}"
    )


def list_entries(db: Session, params: EntryListParams) -> EntryPageOut:
    rows, total = repo.search_entries(db, params)
    snippets: dict[str, str] = {}
    if params.q and rows:
        if repo.keyword_mode(params.q) == "fts":
            snippets = repo.fts_snippets(db, params.q, [row.id for row in rows])
        else:
            needle = params.q.lower()
            for row in rows:
                found = _like_snippet(row.content, needle)
                if found:
                    snippets[row.id] = found
    items = [_summary(row, snippets.get(row.id)) for row in rows]
    return EntryPageOut(items=items, total=total, page=params.page, page_size=params.page_size)


def get_facets(db: Session, params: EntryListParams) -> FacetsOut:
    raw = repo.facet_counts(db, params)
    return FacetsOut(
        categories=[FacetValue(value=value, count=count) for value, count in raw["categories"]],
        subcategories=[
            SubcategoryFacet(category=category, value=value, count=count)
            for category, value, count in raw["subcategories"]
        ],
        types=[FacetValue(value=value, count=count) for value, count in raw["types"]],
        tags=[FacetValue(value=name, count=count) for name, count in raw["tags"]],
    )


def _other_side(relation: EntryRelation, entry_id: str) -> KnowledgeEntry:
    return relation.target if relation.source_id == entry_id else relation.source


def get_entry_detail(db: Session, entry_id: str) -> EntryDetailOut:
    entry = repo.get_entry(db, entry_id)
    if entry is None:
        raise NotFoundError("知识条目不存在")

    related: list[RelatedEntryOut] = []
    related_ids: set[str] = set()
    for relation in repo.list_relations_for(db, entry_id):
        other = _other_side(relation, entry_id)
        if other.is_deleted:
            continue  # hide relations pointing at archived entries; the row itself is kept
        related.append(RelatedEntryOut(relation_id=relation.id, entry=_brief(other)))
        related_ids.add(other.id)

    recommendations = [
        RecommendationOut(entry=_brief(candidate), shared_tag_count=shared)
        for candidate, shared in repo.recommend_by_tags(
            db, entry, exclude_ids={entry.id} | related_ids, limit=RECOMMENDATION_LIMIT
        )
    ]

    return EntryDetailOut(
        **_brief(entry).model_dump(by_alias=False),
        content=entry.content,
        source_path=entry.source_path,
        source_created_at=entry.source_created_at,
        source_updated_at=entry.source_updated_at,
        relations=related,
        recommendations=recommendations,
    )


def create_relation(db: Session, entry_id: str, target_id: str) -> RelationOut:
    if entry_id == target_id:
        raise ServiceError("不能关联条目自身")
    source = repo.get_entry(db, entry_id)
    if source is None:
        raise NotFoundError("知识条目不存在")
    target = repo.get_entry(db, target_id)
    if target is None:
        raise NotFoundError("关联的目标条目不存在")
    if repo.find_relation_pair(db, entry_id, target_id) is not None:
        raise ConflictError("两条知识已经关联")

    relation = repo.add_relation(db, entry_id, target_id)
    db.commit()
    return RelationOut(
        relation_id=relation.id,
        source_id=relation.source_id,
        target_id=relation.target_id,
        created_at=relation.created_at,
    )


def delete_relation(db: Session, relation_id: str) -> None:
    relation = repo.get_relation(db, relation_id)
    if relation is None:
        raise NotFoundError("关联不存在")
    repo.delete_relation(db, relation)
    db.commit()
