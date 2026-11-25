"""FastAPI entry point: uvicorn main:app --port 8020 (run from the backend/ directory)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import Settings, load_settings
from internal.db import configure_database, init_database, session_factory
from routers.knowledge import router as knowledge_router
from services import blog_sync_service
from services.errors import ServiceError

logger = logging.getLogger("knowledge")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    configure_database(settings.database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        init_database()
        if settings.sync_on_startup:
            try:
                with session_factory()() as db:
                    result = blog_sync_service.sync_blogs(db, settings.blogs_dir)
                logger.info("blogs sync on startup: %s", result.model_dump())
            except ServiceError as exc:
                logger.warning("blogs sync skipped: %s", exc.message)
        yield

    app = FastAPI(title="Weakly Knowledge API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    @app.exception_handler(ServiceError)
    async def _service_error_handler(_request: Request, exc: ServiceError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    app.include_router(knowledge_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
