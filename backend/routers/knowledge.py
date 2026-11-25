"""HTTP layer for the knowledge API. Parameter parsing only; logic lives in services."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from internal.db import get_db
from schemas.knowledge import (
    EntryDetailOut,
    EntryListParams,
    EntryPageOut,
    EntryTypeName,
    FacetsOut,
    RelationCreate,
    RelationOut,
    SortKey,
    SyncResultOut,
)
from services import asset_service, blog_sync_service, knowledge_service

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


def _filter_params(
    q: str | None,
    category: str | None,
    subcategory: str | None,
    entry_type: str | None,
    tags: list[str],
    sort: SortKey | None,
    order: Literal["asc", "desc"],
    page: int,
    page_size: int,
) -> EntryListParams:
    return EntryListParams(
        q=(q or "").strip() or None,
        category=category,
        subcategory=subcategory,
        entry_type=entry_type,
        tags=[t for t in tags if t],
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )


@router.get("/entries", response_model=EntryPageOut)
def list_entries(
    q: str | None = Query(None, max_length=200),
    category: str | None = Query(None, max_length=64),
    subcategory: str | None = Query(None, max_length=64),
    entry_type: EntryTypeName | None = Query(None, alias="type"),
    tag: list[str] = Query(default=[], max_length=20),
    sort: SortKey | None = None,
    order: Literal["asc", "desc"] = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> EntryPageOut:
    params = _filter_params(q, category, subcategory, entry_type, tag, sort, order, page, page_size)
    return knowledge_service.list_entries(db, params)


@router.get("/facets", response_model=FacetsOut)
def get_facets(
    q: str | None = Query(None, max_length=200),
    category: str | None = Query(None, max_length=64),
    subcategory: str | None = Query(None, max_length=64),
    entry_type: EntryTypeName | None = Query(None, alias="type"),
    tag: list[str] = Query(default=[], max_length=20),
    db: Session = Depends(get_db),
) -> FacetsOut:
    params = _filter_params(q, category, subcategory, entry_type, tag, None, "desc", 1, 1)
    return knowledge_service.get_facets(db, params)


@router.get("/entries/{entry_id}", response_model=EntryDetailOut)
def get_entry(entry_id: str, db: Session = Depends(get_db)) -> EntryDetailOut:
    return knowledge_service.get_entry_detail(db, entry_id)


@router.post("/entries/{entry_id}/relations", response_model=RelationOut, status_code=status.HTTP_201_CREATED)
def create_relation(entry_id: str, body: RelationCreate, db: Session = Depends(get_db)) -> RelationOut:
    return knowledge_service.create_relation(db, entry_id, body.target_id)


@router.delete("/relations/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_relation(relation_id: str, db: Session = Depends(get_db)) -> Response:
    knowledge_service.delete_relation(db, relation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/sync", response_model=SyncResultOut)
def sync_blogs(request: Request, db: Session = Depends(get_db)) -> SyncResultOut:
    return blog_sync_service.sync_blogs(db, request.app.state.settings.blogs_dir)


@router.get("/assets/{asset_path:path}")
def get_asset(asset_path: str, request: Request) -> FileResponse:
    path = asset_service.resolve_asset(request.app.state.settings.blogs_dir, asset_path)
    return FileResponse(path)
