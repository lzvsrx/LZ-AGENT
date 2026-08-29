from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .config import Settings
from .database import Database
from .providers import LocalFallbackProvider
from .service import AgentService


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    private: bool = False


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.load()
    database = Database(settings.database, settings.root / "data" / "migrations")
    database.migrate()
    service = AgentService(database, LocalFallbackProvider())
    app = FastAPI(title="LZ Agent Local API", version=__version__)
    web = settings.root / "apps" / "web"

    @app.get("/api/v1/system/health")
    def health() -> dict:
        return {
            "status": "ok",
            "version": __version__,
            "agent": "LZ Agent",
            "database": "connected",
            "provider": "local",
            "stats": database.stats(),
        }

    @app.get("/api/v1/config")
    def config() -> dict:
        return settings.config

    @app.post("/api/v1/chat")
    def chat(request: ChatRequest) -> dict:
        return service.chat(request.message, request.private)

    @app.get("/api/v1/actions")
    def actions(limit: int = Query(50, ge=1, le=500)) -> list[dict]:
        return database.list_actions(limit)

    @app.get("/api/v1/actions/{action_id}")
    def action(action_id: str) -> dict:
        try:
            return database.get_action(action_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Ação não encontrada") from error

    app.mount("/static", StaticFiles(directory=web / "static"), name="static")

    @app.get("/", include_in_schema=False)
    def home() -> FileResponse:
        return FileResponse(Path(web / "index.html"))

    return app
