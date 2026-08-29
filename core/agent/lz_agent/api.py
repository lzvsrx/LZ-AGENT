from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .capabilities import AudioCapabilityRegistry, runtime_diagnostics
from .config import Settings
from .database import Database
from .localization import Translator, locale_fallbacks, normalize_locale, writing_direction
from .plugins import PluginRegistry
from .providers import LocalFallbackProvider
from .service import AgentService


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    private: bool = False


class ProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    objective: str = Field(default="", max_length=10_000)


class LessonRequest(BaseModel):
    problem: str = Field(min_length=1, max_length=10_000)
    solution: str = Field(min_length=1, max_length=20_000)
    evidence: str = Field(default="", max_length=20_000)
    confidence: float = Field(ge=0, le=1)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.load()
    database = Database(settings.database, settings.root / "data" / "migrations")
    database.migrate()
    service = AgentService(database, LocalFallbackProvider())
    audio_capabilities = AudioCapabilityRegistry()
    translator = Translator(settings.root / "shared" / "localization")
    plugins = PluginRegistry(settings.root / "plugins")
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

    @app.get("/api/v1/system/capabilities")
    def capabilities() -> dict:
        return runtime_diagnostics(settings.database)

    @app.get("/api/v1/audio/capabilities")
    def audio(locale: str | None = None) -> dict:
        try:
            rows = audio_capabilities.list(locale)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {
            "capabilities": rows,
            "fallback": "text",
            "notice": "Apenas idiomas e vozes verificados são anunciados como disponíveis.",
        }

    @app.get("/api/v1/plugins")
    def list_plugins() -> dict:
        return {
            "plugins": plugins.discover(),
            "policy": "Nenhum plugin recebe permissão ou execução apenas por estar instalado.",
        }

    @app.get("/api/v1/config")
    def config() -> dict:
        return settings.config

    @app.get("/api/v1/localization/{locale}")
    def localization(locale: str) -> dict:
        try:
            normalized = normalize_locale(locale)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        messages, resolved = translator.messages(normalized)
        return {
            "requested": normalized,
            "resolved": resolved,
            "fallbacks": locale_fallbacks(normalized),
            "direction": writing_direction(normalized),
            "messages": messages,
        }

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

    @app.get("/api/v1/projects")
    def projects() -> list[dict]:
        return database.list_projects()

    @app.post("/api/v1/projects", status_code=201)
    def create_project(request: ProjectRequest) -> dict:
        project = database.create_project(request.name, request.objective)
        database.record_action(
            "Criar projeto",
            "memory.projects.create",
            "succeeded",
            parameters={"project_id": project["id"]},
            project_id=project["id"],
            permission="memory.write",
        )
        return project

    @app.get("/api/v1/projects/{project_id}/lessons")
    def lessons(project_id: str) -> list[dict]:
        return database.list_lessons(project_id)

    @app.post("/api/v1/projects/{project_id}/lessons", status_code=201)
    def create_lesson(project_id: str, request: LessonRequest) -> dict:
        try:
            lesson = database.add_lesson(
                project_id,
                request.problem,
                request.solution,
                request.confidence,
                request.evidence,
            )
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Projeto não encontrado") from error
        database.record_action(
            "Registrar lição autorizada",
            "learning.lessons.create",
            "succeeded",
            parameters={"lesson_id": lesson["id"]},
            project_id=project_id,
            permission="learning.write",
        )
        return lesson

    @app.get("/api/v1/memory/export")
    def export_memory() -> dict:
        return database.export_memory()

    @app.delete("/api/v1/projects/{project_id}/memory")
    def delete_project_memory(project_id: str, confirm: bool = False) -> dict:
        if not confirm:
            raise HTTPException(status_code=409, detail="Confirmação explícita obrigatória")
        if not database.delete_project_memory(project_id):
            raise HTTPException(status_code=404, detail="Projeto não encontrado")
        database.record_action(
            "Apagar memória do projeto",
            "memory.projects.delete",
            "succeeded",
            parameters={"project_id": project_id},
            permission="memory.delete.confirmed",
        )
        return {"deleted": True, "project_id": project_id}

    app.mount("/static", StaticFiles(directory=web / "static"), name="static")

    @app.get("/", include_in_schema=False)
    def home() -> FileResponse:
        return FileResponse(Path(web / "index.html"))

    return app
