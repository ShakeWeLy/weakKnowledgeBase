"""Runtime settings for the knowledge API. Every value can be overridden by an environment variable."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent


@dataclass(frozen=True)
class Settings:
    database_url: str
    blogs_dir: Path
    sync_on_startup: bool
    cors_origins: tuple[str, ...]


def load_settings() -> Settings:
    default_db = BACKEND_DIR / "data" / "knowledge.sqlite3"
    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return Settings(
        database_url=os.getenv("DATABASE_URL", f"sqlite:///{default_db.as_posix()}"),
        blogs_dir=Path(os.getenv("BLOGS_DIR", PROJECT_ROOT / "blogs")).resolve(),
        sync_on_startup=os.getenv("KNOWLEDGE_SYNC_ON_STARTUP", "1").lower() not in {"0", "false", "no"},
        cors_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
    )
