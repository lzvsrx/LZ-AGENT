from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import httpx
from fastapi import FastAPI, File, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .audio_devices import input_devices
from .auth import AuthenticationError, AuthService
from .avatar import AvatarController, AvatarState
from .capabilities import AudioCapabilityRegistry, runtime_diagnostics
from .checkpoints import CheckpointError, GitCheckpointService
from .command_planner import CommandPlanner
from .config import Settings
from .database import Database
from .devices import DeviceDetector
from .documents import DocumentError, inspect_document
from .localization import Translator, locale_fallbacks, normalize_locale, writing_direction
from .plugins import PluginExecutionError, PluginRegistry, PluginRunner
from .providers import NativeAgentProvider
from .service import AgentService
from .voice_commands import VoiceCommandInterpreter
from .web_research import ResearchError, fetch_public_text, wikipedia_search


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    private: bool = False


class PrepareCommandRequest(BaseModel):
    command: str = Field(min_length=1, max_length=20_000)
    properties: dict = Field(default_factory=dict)
    approved: bool = False
    autonomy_level: int = Field(default=2, ge=0, le=4)


class VoiceCommandRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=20_000)
    locale: str = Field(default="pt-BR", max_length=35)
    approved: bool = False


class ProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    objective: str = Field(default="", max_length=10_000)


class LessonRequest(BaseModel):
    problem: str = Field(min_length=1, max_length=10_000)
    solution: str = Field(min_length=1, max_length=20_000)
    evidence: str = Field(default="", max_length=20_000)
    confidence: float = Field(ge=0, le=1)


class ArtifactRequest(BaseModel):
    kind: str = Field(min_length=1, max_length=100)
    path: str = Field(min_length=1, max_length=2_000)
    checksum: str | None = Field(default=None, max_length=200)
    metadata: dict = Field(default_factory=dict)


class MemorySourceRequest(BaseModel):
    source_type: str = Field(min_length=1, max_length=100)
    source_ref: str = Field(default="", max_length=2_000)
    title: str = Field(min_length=1, max_length=300)
    notes: str = Field(default="", max_length=20_000)
    consent: Literal["explicit", "revoked"] = "explicit"
    retention: str = Field(default="project", max_length=100)
    scope: str = Field(default="project", max_length=100)


class RetentionPolicyRequest(BaseModel):
    category: Literal["action_ledger", "private_session"]
    retention_days: int | None = Field(default=None, ge=1, le=3650)


class PurgeMemoryRequest(BaseModel):
    confirmation: str


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


class PluginExecuteRequest(BaseModel):
    command: str = Field(min_length=3, max_length=200)
    input: dict = Field(default_factory=dict)
    approved: bool = False


class RestoreBackupRequest(BaseModel):
    filename: str = Field(min_length=4, max_length=255)
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    confirmation: str


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12, max_length=1024)
    locale: str = Field(default="pt-BR", max_length=35)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=1, max_length=1024)


class ResearchSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    locale: str = Field(default="pt-BR", max_length=35)
    approved: bool = False


class ResearchFetchRequest(BaseModel):
    url: str = Field(min_length=10, max_length=2048)
    approved: bool = False


class AvatarStateRequest(BaseModel):
    state: AvatarState
    reduced_motion: bool | None = None
    enabled: bool | None = None


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.load()
    database = Database(settings.database, settings.root / "data" / "migrations")
    database.migrate()
    service = AgentService(database, NativeAgentProvider())
    auth = AuthService(database)
    audio_capabilities = AudioCapabilityRegistry()
    command_planner = CommandPlanner()
    voice_interpreter = VoiceCommandInterpreter(command_planner)
    translator = Translator(settings.root / "shared" / "localization")
    plugins = PluginRegistry(settings.root / "plugins")
    plugin_runner = PluginRunner()
    checkpoints = GitCheckpointService(settings.root)
    devices = DeviceDetector()
    avatar = AvatarController()
    app = FastAPI(title="LZ Agent Local API", version=__version__)
    web = settings.root / "apps" / "web"

    protected_prefixes = (
        "/api/v1/actions",
        "/api/v1/avatar",
        "/api/v1/chat",
        "/api/v1/documents",
        "/api/v1/memory",
        "/api/v1/plugins",
        "/api/v1/projects",
        "/api/v1/research",
        "/api/v1/suggestions",
    )

    @app.middleware("http")
    async def protect_personal_data(request: Request, call_next):
        if auth.has_users() and request.url.path.startswith(protected_prefixes):
            try:
                auth.authenticate(_raw_bearer_token(request.headers.get("authorization")))
            except AuthenticationError as error:
                return JSONResponse(status_code=401, content={"detail": str(error)})
        return await call_next(request)

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

    @app.post("/api/v1/auth/register", status_code=201)
    def register(
        request: RegisterRequest, authorization: Annotated[str | None, Header()] = None
    ) -> dict:
        if auth.has_users():
            try:
                auth.authenticate(_raw_bearer_token(authorization))
            except AuthenticationError as error:
                raise HTTPException(
                    status_code=403,
                    detail="Somente uma conta autenticada pode cadastrar outro usuário",
                ) from error
        try:
            locale = normalize_locale(request.locale)
            user = auth.register(
                request.username, request.display_name, request.password, locale
            )
        except (AuthenticationError, ValueError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        database.record_action(
            "Cadastrar usuário local",
            "auth.users.register",
            "succeeded",
            parameters={"user_id": user["id"]},
            permission="auth.register",
        )
        return user

    @app.post("/api/v1/auth/login")
    def login(request: LoginRequest) -> dict:
        try:
            session = auth.login(request.username, request.password)
        except AuthenticationError as error:
            raise HTTPException(status_code=401, detail=str(error)) from error
        return session

    @app.get("/api/v1/auth/me")
    def current_user(authorization: Annotated[str | None, Header()] = None) -> dict:
        token = _bearer_token(authorization)
        try:
            return auth.authenticate(token)
        except AuthenticationError as error:
            raise HTTPException(status_code=401, detail=str(error)) from error

    @app.post("/api/v1/auth/logout", status_code=204)
    def logout(authorization: Annotated[str | None, Header()] = None) -> None:
        token = _bearer_token(authorization)
        try:
            auth.authenticate(token)
        except AuthenticationError as error:
            raise HTTPException(status_code=401, detail=str(error)) from error
        auth.logout(token)

    @app.get("/api/v1/system/capabilities")
    def capabilities() -> dict:
        return runtime_diagnostics(settings.database)

    @app.get("/api/v1/system/device")
    def device(include_name: bool = False) -> dict:
        return devices.profile(include_name=include_name)

    @app.get("/api/v1/audio/devices")
    def microphones() -> dict:
        return input_devices()

    @app.get("/api/v1/avatar/state")
    def avatar_state() -> dict:
        return avatar.current()

    @app.get("/avatar-preview.png", include_in_schema=False)
    def avatar_preview() -> FileResponse:
        return FileResponse(
            settings.root / "assets" / "avatar" / "references" / "generated-preview.png",
            media_type="image/png",
        )

    @app.put("/api/v1/avatar/state")
    def set_avatar_state(request: AvatarStateRequest) -> dict:
        result = avatar.update(
            request.state,
            reduced_motion=request.reduced_motion,
            enabled=request.enabled,
        )
        database.record_action(
            f"Avatar: {request.state.value}",
            "avatar.state.update",
            "succeeded",
            result=result,
            permission="avatar.control",
        )
        return result

    @app.post("/api/v1/research/search")
    def research_search(request: ResearchSearchRequest) -> dict:
        if not request.approved:
            raise HTTPException(
                status_code=409, detail="Acesso à internet exige aprovação explícita"
            )
        try:
            results = wikipedia_search(request.query, normalize_locale(request.locale))
        except (ValueError, httpx.HTTPError) as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        database.record_action(
            request.query,
            "internet.research.search",
            "succeeded",
            result={"count": len(results), "source": "Wikipedia"},
            permission="internet.search.confirmed",
        )
        return {"query": request.query, "results": results}

    @app.post("/api/v1/research/fetch")
    def research_fetch(request: ResearchFetchRequest) -> dict:
        if not request.approved:
            raise HTTPException(
                status_code=409, detail="Acesso à internet exige aprovação explícita"
            )
        try:
            result = fetch_public_text(request.url)
        except (ResearchError, httpx.HTTPError) as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        database.record_action(
            request.url,
            "internet.research.fetch",
            "succeeded",
            result={"content_type": result["content_type"], "characters": len(result["text"])},
            permission="internet.fetch.confirmed",
        )
        return result

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

    @app.get("/api/v1/plugins/sandbox/status")
    def plugin_sandbox_status() -> dict:
        return plugin_runner.status()

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

    @app.post("/api/v1/plugins/{plugin_id}/execute")
    def execute_plugin(plugin_id: str, request: PluginExecuteRequest) -> dict:
        if not request.approved:
            raise HTTPException(status_code=409, detail="Confirmação explícita obrigatória")
        try:
            manifest = plugins.get(plugin_id)
            state = database.get_plugin_state(plugin_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Plugin não encontrado") from error
        if not state["enabled"]:
            raise HTTPException(status_code=409, detail="Plugin desativado")
        grants = {item["permission"] for item in state["grants"] if item["granted"]}
        missing = sorted(set(manifest.permissions) - grants)
        if missing:
            raise HTTPException(
                status_code=403, detail=f"Permissões não concedidas: {', '.join(missing)}"
            )
        sandbox = plugin_runner.status()
        if not sandbox["available"]:
            database.record_action(
                "Bloquear plugin sem sandbox forte", request.command, "blocked",
                parameters={"plugin_id": plugin_id}, error=sandbox["reason"],
                permission="plugins.execute.denied",
            )
            raise HTTPException(status_code=503, detail=sandbox["reason"])
        try:
            execution = plugin_runner.execute(manifest, request.command, request.input)
        except PluginExecutionError as error:
            database.record_action(
                "Executar plugin", request.command, "failed",
                parameters={"plugin_id": plugin_id}, error=str(error),
                permission="plugins.execute.confirmed",
            )
            raise HTTPException(status_code=422, detail=str(error)) from error
        database.record_action(
            "Executar plugin", request.command, "succeeded",
            parameters={"plugin_id": plugin_id}, result=execution,
            permission="plugins.execute.confirmed",
        )
        return execution

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
        avatar.update(AvatarState.THINKING)
        try:
            response = service.chat(request.message, request.private)
            avatar.update(AvatarState.PRIVATE if request.private else AvatarState.SUCCESS)
            return response
        except Exception:
            avatar.update(AvatarState.ERROR)
            raise

    @app.post("/api/v1/commands/prepare")
    def prepare_command(request: PrepareCommandRequest) -> dict:
        properties = command_planner.prepare(
            request.command,
            supplied=request.properties,
            approved=request.approved,
            autonomy_level=request.autonomy_level,
        ).as_dict()
        action = database.record_action(
            request.command,
            "agent.commands.prepare",
            "ready" if properties["executable"] else "needs_input",
            parameters={"supplied_properties": sorted(request.properties)},
            result=properties,
            permission=properties["permission"],
        )
        return {"command": request.command, "properties": properties, "action_id": action["id"]}

    @app.post("/api/v1/voice/commands/interpret")
    def interpret_voice_command(request: VoiceCommandRequest) -> dict:
        try:
            locale = normalize_locale(request.locale)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        interpretation = voice_interpreter.interpret(
            request.transcript, locale=locale, approved=request.approved
        ).as_dict()
        action = database.record_action(
            interpretation["canonical_command"],
            "voice.commands.interpret",
            "ready" if interpretation["command_properties"]["executable"] else "needs_review",
            parameters={"locale": locale, "transcript_retained": False},
            result={
                "intent": interpretation["command_properties"]["intent"],
                "confidence": interpretation["confidence"],
                "review_required": interpretation["review_required"],
            },
            permission="microphone.transcript.selected",
        )
        interpretation["action_id"] = action["id"]
        return interpretation

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

    @app.put("/api/v1/projects/{project_id}")
    def update_project(project_id: str, request: ProjectRequest) -> dict:
        try:
            project = database.update_project(project_id, request.name, request.objective)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Projeto não encontrado") from error
        database.record_action(
            "Editar projeto", "memory.projects.update", "succeeded",
            parameters={"project_id": project_id}, project_id=project_id,
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

    @app.put("/api/v1/lessons/{lesson_id}")
    def update_lesson(lesson_id: str, request: LessonRequest) -> dict:
        try:
            lesson = database.update_lesson(
                lesson_id, request.problem, request.solution, request.confidence, request.evidence
            )
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Lição não encontrada") from error
        database.record_action(
            "Editar lição autorizada", "learning.lessons.update", "succeeded",
            parameters={"lesson_id": lesson_id}, project_id=lesson["project_id"],
            permission="learning.write",
        )
        return lesson

    @app.get("/api/v1/projects/{project_id}/artifacts")
    def artifacts(project_id: str) -> list[dict]:
        try:
            return database.list_artifacts(project_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Projeto não encontrado") from error

    @app.post("/api/v1/projects/{project_id}/artifacts", status_code=201)
    def create_artifact(project_id: str, request: ArtifactRequest) -> dict:
        try:
            artifact = database.create_artifact(
                project_id, request.kind, request.path, request.checksum, request.metadata
            )
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Projeto não encontrado") from error
        database.record_action(
            "Registrar artefato autorizado", "memory.artifacts.create", "succeeded",
            parameters={"artifact_id": artifact["id"]}, project_id=project_id,
            permission="memory.write",
        )
        return artifact

    @app.put("/api/v1/artifacts/{artifact_id}")
    def update_artifact(artifact_id: str, request: ArtifactRequest) -> dict:
        try:
            artifact = database.update_artifact(
                artifact_id, request.kind, request.path, request.checksum, request.metadata
            )
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Artefato não encontrado") from error
        database.record_action(
            "Editar artefato autorizado", "memory.artifacts.update", "succeeded",
            parameters={"artifact_id": artifact_id}, project_id=artifact["project_id"],
            permission="memory.write",
        )
        return artifact

    @app.delete("/api/v1/artifacts/{artifact_id}")
    def delete_artifact(artifact_id: str, confirm: bool = False) -> dict:
        if not confirm:
            raise HTTPException(status_code=409, detail="Confirmação explícita obrigatória")
        try:
            artifact = database.get_artifact(artifact_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Artefato não encontrado") from error
        database.delete_memory_item("artifacts", artifact_id)
        database.record_action(
            "Apagar artefato autorizado", "memory.artifacts.delete", "succeeded",
            parameters={"artifact_id": artifact_id}, project_id=artifact["project_id"],
            permission="memory.delete.confirmed",
        )
        return {"deleted": True, "artifact_id": artifact_id}

    @app.get("/api/v1/projects/{project_id}/sources")
    def memory_sources(project_id: str) -> list[dict]:
        try:
            return database.list_memory_sources(project_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Projeto não encontrado") from error

    @app.post("/api/v1/projects/{project_id}/sources", status_code=201)
    def create_memory_source(project_id: str, request: MemorySourceRequest) -> dict:
        try:
            source = database.create_memory_source(
                project_id, request.source_type, request.source_ref, request.title, request.notes,
                request.consent, request.retention, request.scope,
            )
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Projeto não encontrado") from error
        database.record_action(
            "Registrar fonte de memória autorizada", "memory.sources.create", "succeeded",
            parameters={"source_id": source["id"], "consent": source["consent"]},
            project_id=project_id, permission="memory.write",
        )
        return source

    @app.put("/api/v1/sources/{source_id}")
    def update_memory_source(source_id: str, request: MemorySourceRequest) -> dict:
        try:
            source = database.update_memory_source(
                source_id, request.source_type, request.source_ref, request.title, request.notes,
                request.consent, request.retention, request.scope,
            )
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Fonte não encontrada") from error
        database.record_action(
            "Editar fonte de memória autorizada", "memory.sources.update", "succeeded",
            parameters={"source_id": source_id, "consent": source["consent"]},
            project_id=source["project_id"], permission="memory.write",
        )
        return source

    @app.delete("/api/v1/sources/{source_id}")
    def delete_memory_source(source_id: str, confirm: bool = False) -> dict:
        if not confirm:
            raise HTTPException(status_code=409, detail="Confirmação explícita obrigatória")
        try:
            source = database.get_memory_source(source_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Fonte não encontrada") from error
        database.delete_memory_item("memory_sources", source_id)
        database.record_action(
            "Apagar fonte de memória autorizada", "memory.sources.delete", "succeeded",
            parameters={"source_id": source_id}, project_id=source["project_id"],
            permission="memory.delete.confirmed",
        )
        return {"deleted": True, "source_id": source_id}

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

    @app.get("/api/v1/projects/{project_id}/checkpoints")
    def list_checkpoints(project_id: str) -> list[dict]:
        try:
            database.get_project(project_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Projeto não encontrado") from error
        return database.list_checkpoints(project_id)

    @app.post("/api/v1/projects/{project_id}/checkpoints", status_code=201)
    def create_checkpoint(project_id: str) -> dict:
        try:
            database.get_project(project_id)
            snapshot = checkpoints.capture()
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Projeto não encontrado") from error
        except CheckpointError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        checkpoint = database.create_checkpoint(
            project_id,
            snapshot["commit_hash"],
            snapshot["files"],
            snapshot["diff"],
        )
        checkpoint["diff_truncated"] = snapshot["diff_truncated"]
        database.record_action(
            "Criar checkpoint antes de mudança",
            "projects.checkpoints.create",
            "succeeded",
            parameters={"checkpoint_id": checkpoint["id"]},
            result={"commit_hash": checkpoint["commit_hash"], "files": checkpoint["files"]},
            project_id=project_id,
            permission="project.checkpoint",
        )
        return checkpoint

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

    @app.get("/api/v1/memory/search")
    def search_memory(
        q: Annotated[str, Query(min_length=2, max_length=500)],
        project_id: str | None = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
    ) -> list[dict]:
        try:
            return database.search_memory(q, project_id=project_id, limit=limit)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Projeto não encontrado") from error

    @app.get("/api/v1/memory/retention")
    def get_retention_policies() -> list[dict]:
        return database.retention_policies()

    @app.put("/api/v1/memory/retention")
    def set_retention_policy(request: RetentionPolicyRequest) -> dict:
        policy = database.set_retention_policy(request.category, request.retention_days)
        database.record_action(
            "Alterar política de retenção", "memory.retention.update", "succeeded",
            parameters={"category": request.category, "retention_days": request.retention_days},
            permission="memory.retention",
        )
        return policy

    @app.post("/api/v1/memory/purge")
    def purge_memory(request: PurgeMemoryRequest) -> dict:
        if request.confirmation != "APAGAR MEMÓRIA EXPIRADA":
            raise HTTPException(status_code=409, detail="Confirmação textual obrigatória")
        deleted = database.purge_expired_memory()
        database.record_action(
            "Apagar memória expirada", "memory.retention.purge", "succeeded",
            result={"deleted": deleted}, permission="memory.delete.confirmed",
        )
        return {"purged": True, "deleted": deleted}

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


def _bearer_token(authorization: str | None) -> str:
    try:
        return _raw_bearer_token(authorization)
    except AuthenticationError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error


def _raw_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Token Bearer obrigatório")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise AuthenticationError("Token Bearer obrigatório")
    return token
