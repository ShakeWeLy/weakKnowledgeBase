"""Knowledge entries (one per blogs/*.md file), tags, and manual relations between entries."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.models.base import Base, BaseMixin, utcnow

entry_tags = Table(
    "entry_tags",
    Base.metadata,
    Column("entry_id", String(36), ForeignKey("knowledge_entries.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Index("ix_entry_tags_tag_id", "tag_id"),
)


class Tag(BaseMixin, Base):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)


class KnowledgeEntry(BaseMixin, Base):
    __tablename__ = "knowledge_entries"
    __table_args__ = (
        Index("ix_knowledge_entries_category_subcategory", "category", "subcategory"),
        Index("ix_knowledge_entries_source_created_at", "source_created_at"),
        Index("ix_knowledge_entries_title", "title"),
    )

    source_path: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subcategory: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entry_type: Mapped[str] = mapped_column("type", String(32), nullable=False, default="technical_note")
    source_created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")

    tags: Mapped[list[Tag]] = relationship(
        secondary=entry_tags,
        order_by="Tag.name",
        lazy="raise",  # every query must eager-load tags explicitly (avoids hidden N+1)
    )


class EntryRelation(Base):
    """Manual, undirected relation between two entries; stored once per pair."""

    __tablename__ = "entry_relations"
    __table_args__ = (
        UniqueConstraint("source_id", "target_id", name="uq_entry_relation_pair"),
        CheckConstraint("source_id <> target_id", name="ck_entry_relation_not_self"),
        Index("ix_entry_relations_target_id", "target_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("knowledge_entries.id", ondelete="CASCADE"), nullable=False)
    target_id: Mapped[str] = mapped_column(String(36), ForeignKey("knowledge_entries.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    source: Mapped[KnowledgeEntry] = relationship(foreign_keys=[source_id], lazy="raise")
    target: Mapped[KnowledgeEntry] = relationship(foreign_keys=[target_id], lazy="raise")
