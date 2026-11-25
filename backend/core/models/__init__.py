"""Import all ORM models so they register on Base.metadata."""

from core.models.base import Base, BaseMixin
from core.models.knowledge import EntryRelation, KnowledgeEntry, Tag, entry_tags

__all__ = ["Base", "BaseMixin", "EntryRelation", "KnowledgeEntry", "Tag", "entry_tags"]
