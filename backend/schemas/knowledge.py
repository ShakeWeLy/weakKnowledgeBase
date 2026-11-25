"""Request/response schemas for the knowledge API (JSON keys are camelCase-free snake_case, same as photo-show)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EntryTypeName = Literal[
    "concept",
    "technical_note",
    "paper",
    "tutorial",
    "experiment",
    "project",
    "post",
    "reflection",
    "resource",
]
SortKey = Literal["relevance", "source_created_at", "source_updated_at", "title"]
SortOrder = Literal["asc", "desc"]


class EntryListParams(BaseModel):
    """Validated filter/sort/page parameters shared by the list and facet endpoints."""

    q: str | None = None
    category: str | None = None
    subcategory: str | None = None
    entry_type: str | None = None
    tags: list[str] = Field(default_factory=list)
    sort: SortKey | None = None
    order: SortOrder = "desc"
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class EntryBriefOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    summary: str
    category: str | None
    subcategory: str | None
    entry_type: str = Field(alias="type")
    tags: list[str]


class EntrySummaryOut(EntryBriefOut):
    source_path: str
    source_created_at: datetime | None
    source_updated_at: datetime | None
    snippet: str | None = None


class EntryPageOut(BaseModel):
    items: list[EntrySummaryOut]
    total: int
    page: int
    page_size: int


class RelatedEntryOut(BaseModel):
    relation_id: str
    entry: EntryBriefOut


class RecommendationOut(BaseModel):
    entry: EntryBriefOut
    shared_tag_count: int


class EntryDetailOut(EntryBriefOut):
    model_config = ConfigDict(populate_by_name=True)

    content: str
    source_path: str
    source_created_at: datetime | None
    source_updated_at: datetime | None
    relations: list[RelatedEntryOut]
    recommendations: list[RecommendationOut]


class RelationCreate(BaseModel):
    target_id: str = Field(min_length=1, max_length=36)


class RelationOut(BaseModel):
    relation_id: str
    source_id: str
    target_id: str
    created_at: datetime


class FacetValue(BaseModel):
    value: str | None
    count: int


class SubcategoryFacet(BaseModel):
    category: str | None
    value: str | None
    count: int


class FacetsOut(BaseModel):
    categories: list[FacetValue]
    subcategories: list[SubcategoryFacet]
    types: list[FacetValue]
    tags: list[FacetValue]


class SyncResultOut(BaseModel):
    added: int
    updated: int
    unchanged: int
    removed: int
