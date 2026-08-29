from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .capabilities import AudioCapabilityRegistry, runtime_diagnostics
from .config import Settings
from .database import Database
from .documents import DocumentError, inspect_document
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


class SuggestionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=20_000)
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    impact: str = Field(default="", max_length=10_000)
    justification: str = Field(min_length=1, max_length=20_000)
    source_lesson_id: str | None = None


class SuggestionDecisionRequest(BaseModel):
    decision: Literal["accepted", "rejected", "deferred"]


class PluginStateRequest(BaseModel):
    enabled: bool
    approved: bool = False


class PluginGrantRequest(BaseModel):
    permission: str = Field(min_length=3, max_length=200)
    granted: bool
    approved: bool = False


class RestoreBackupRequest(BaseModel):
    filename: str = Field(min_length=4, max_length=255)
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    confirmation: str


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

    @app.get("/api/v1/plugins/{plugin_id}/state")
    def plugin_state(plugin_id: str) -> dict:
        try:
            manifest = plugins.get(plugin_id)
            try:
                return database.get_plugin_state(plugin_id)
            except KeyError:
                return database.register_plugin(plugin_id, manifest.version)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Plugin não encontrado") from error

    @app.patch("/api/v1/plugins/{plugin_id}/state")
    def change_plugin_state(plugin_id: str, request: PluginStateRequest) -> dict:
        if request.enabled and not request.approved:
            raise HTTPException(status_code=409, detail="Confirmação explícita obrigatória")
        try:
            manifest = plugins.get(plugin_id)
            try:
                database.get_plugin_state(plugin_id)
            except KeyError:
                database.register_plugin(plugin_id, manifest.version)
            state = database.set_plugin_enabled(plugin_id, request.enabled)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Plugin não encontrado") from error
        database.record_action(
            "Alterar estado de plugin",
            "plugins.state.update",
            "succeeded",
            parameters={"plugin_id": plugin_id, "enabled": request.enabled},
            permission="plugins.manage.confirmed" if request.approved else "plugins.manage",
        )
        return state

    @app.put("/api/v1/plugins/{plugin_id}/grants")
    def change_plugin_grant(plugin_id: str, request: PluginGrantRequest) -> dict:
        if request.granted and not request.approved:
            raise HTTPException(status_code=409, detail="Confirmação explícita obrigatória")
        try:
            manifest = plugins.get(plugin_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Plugin não encontrado") from error
        if request.permission not in manifest.permissions:
            raise HTTPException(status_code=400, detail="Permissão não declarada pelo plugin")
        try:
            database.get_plugin_state(plugin_id)
        except KeyError:
            database.register_plugin(plugin_id, manifest.version)
        state = database.set_plugin_grant(plugin_id, request.permission, request.granted)
        database.record_action(
            "Alterar permissão de plugin",
            "plugins.grants.update",
            "succeeded",
            parameters={
                "plugin_id": plugin_id,
                "permission": request.permission,
                "granted": request.granted,
            },
            permission=(
                "plugins.permissions.confirmed" if request.approved else "plugins.permissions"
            ),
        )
        return state

    @app.post("/api/v1/documents/inspect")
    async def inspect(file: Annotated[UploadFile, File()]) -> dict:
        content = await file.read(25 * 1024 * 1024 + 1)
        try:
            metadata = inspect_document(
                file.filename or "documento",
                file.content_type or "application/octet-stream",
                content,
            )
        except DocumentError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        database.record_action(
            "Inspecionar documento sem retenção",
            "vision.documents.inspect",
            "succeeded",
            parameters={
                "filename": metadata["filename"],
                "media_type": metadata["media_type"],
                "sha256": metadata["sha256"],
            },
            result={"kind": metadata["kind"], "retained": False},
            permission="documents.read.selected",
        )
        return metadata

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

    @app.get("/api/v1/projects/{project_id}/suggestions")
    def suggestions(project_id: str) -> list[dict]:
        try:
            database.get_project(project_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Projeto não encontrado") from error
        return database.list_suggestions(project_id)

    @app.post("/api/v1/projects/{project_id}/suggestions", status_code=201)
    def create_suggestion(project_id: str, request: SuggestionRequest) -> dict:
        try:
            suggestion = database.create_suggestion(
                project_id,
                request.title,
                request.description,
                request.priority,
                request.justification,
                impact=request.impact,
                source_lesson_id=request.source_lesson_id,
            )
        except KeyError as error:
            raise HTTPException(
                status_code=404, detail="Projeto ou lição não encontrado"
            ) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        database.record_action(
            "Criar sugestão rastreável",
            "learning.suggestions.create",
            "succeeded",
            parameters={"suggestion_id": suggestion["id"]},
            project_id=project_id,
            permission="learning.suggest",
        )
        return suggestion

    @app.patch("/api/v1/suggestions/{suggestion_id}")
    def decide_suggestion(suggestion_id: str, request: SuggestionDecisionRequest) -> dict:
        try:
            suggestion = database.decide_suggestion(suggestion_id, request.decision)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Sugestão não encontrada") from error
        database.record_action(
            "Registrar decisão sobre sugestão",
            "learning.suggestions.decide",
            "succeeded",
            parameters={"suggestion_id": suggestion_id, "decision": request.decision},
            project_id=suggestion["project_id"],
            permission="learning.decide",
        )
        return suggestion

    @app.get("/api/v1/memory/export")
    def export_memory() -> dict:
        return database.export_memory()

    @app.post("/api/v1/memory/backup", status_code=201)
    def backup_memory() -> dict:
        backup = database.create_verified_backup(settings.data_dir / "backups")
        database.record_action(
            "Criar backup verificado da memória",
            "memory.backup.create",
            "succeeded",
            parameters={"filename": backup["filename"]},
            result={"sha256": backup["sha256"], "integrity": backup["integrity"]},
            permission="memory.backup",
        )
        return backup

    @app.post("/api/v1/memory/restore")
    def restore_memory(request: RestoreBackupRequest) -> dict:
        if request.confirmation != "RESTAURAR MEMÓRIA":
            raise HTTPException(status_code=409, detail="Confirmação textual obrigatória")
        try:
            restored = database.restore_verified_backup(
                settings.data_dir / "backups", request.filename, request.sha256
            )
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Backup não encontrado") from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        database.record_action(
            "Restaurar backup verificado da memória",
            "memory.backup.restore",
            "succeeded",
            parameters={"filename": request.filename, "sha256": request.sha256},
            result={"safety_backup": restored["safety_backup"]},
            permission="memory.restore.confirmed",
        )
        return restored

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
