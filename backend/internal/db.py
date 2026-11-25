"""Engine/session setup and the SQLite FTS5 table used by keyword search."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from core.models.base import Base

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None

# trigram tokenizer gives substring matching for Chinese text (queries need >= 3 characters).
FTS_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    entry_id UNINDEXED,
    title,
    summary,
    content,
    tokenize = 'trigram'
)
"""


def configure_database(database_url: str) -> None:
    global _engine, _session_factory
    url = make_url(database_url)
    is_sqlite = url.get_backend_name() == "sqlite"
    connect_args: dict[str, object] = {}
    if is_sqlite:
        connect_args["check_same_thread"] = False
        if url.database and url.database != ":memory:":
            Path(url.database).parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(url, connect_args=connect_args)
    if is_sqlite:

        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_connection, _record) -> None:  # type: ignore[no-untyped-def]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()

    if _engine is not None:
        _engine.dispose()
    _engine = engine
    _session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Database is not configured. Call configure_database() first.")
    return _engine


def session_factory() -> sessionmaker[Session]:
    if _session_factory is None:
        raise RuntimeError("Database is not configured. Call configure_database() first.")
    return _session_factory


def init_database() -> None:
    import core.models  # noqa: F401  (registers all ORM models on Base.metadata)

    engine = get_engine()
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text(FTS_DDL))


def get_db() -> Iterator[Session]:
    db = session_factory()()
    try:
        yield db
    finally:
        db.close()
