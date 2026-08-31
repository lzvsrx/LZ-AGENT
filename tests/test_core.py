import json
import struct
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from lz_agent.api import create_app
from lz_agent.avatar import AvatarController, AvatarState
from lz_agent.capabilities import AudioCapabilityRegistry
from lz_agent.config import Settings
from lz_agent.localization import (
    AudioCapability,
    locale_fallbacks,
    normalize_locale,
    writing_direction,
)
from lz_agent.plugins import PluginRegistry, PluginValidationError, load_manifest
from lz_agent.policies import PolicyEngine, Risk
from lz_agent.providers import NativeAgentProvider
from lz_agent.web_research import ResearchError, _validate_public_url
from PIL import Image


def test_health_and_private_session(tmp_path: Path) -> None:
    config = Settings.load().config
    settings = Settings(
        root=Settings.load().root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=config,
    )
    with TestClient(create_app(settings)) as client:
        health = client.get("/api/v1/system/health")
        assert health.status_code == 200
        assert health.json()["agent"] == "LZ Agent"
        response = client.post("/api/v1/chat", json={"message": "Olá", "private": True})
        assert response.status_code == 200
        assert response.json()["action_id"] is None
        assert client.get("/api/v1/actions").json() == []


def test_audited_chat(tmp_path: Path) -> None:
    base = Settings.load()
    settings = Settings(
        root=base.root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=base.config,
    )
    with TestClient(create_app(settings)) as client:
        response = client.post("/api/v1/chat", json={"message": "Teste", "private": False})
        action_id = response.json()["action_id"]
        action = client.get(f"/api/v1/actions/{action_id}").json()
        assert action["command"] == "Teste"
        assert action["status"] == "succeeded"


def test_sensitive_actions_always_require_explicit_approval() -> None:
    engine = PolicyEngine()
    assert engine.decide(Risk.DESTRUCTIVE, autonomy_level=4).requires_approval
    assert engine.decide(Risk.DESTRUCTIVE, autonomy_level=4, approved=True).allowed


def test_locale_normalization_fallback_and_direction() -> None:
    assert normalize_locale("pt_br") == "pt-BR"
    assert normalize_locale("zh-hant-tw") == "zh-Hant-TW"
    assert locale_fallbacks("es-MX") == ("es-MX", "es", "en")
    assert writing_direction("ar-SA") == "rtl"
    assert writing_direction("pt-BR") == "ltr"


def test_project_memory_export_and_confirmed_deletion(tmp_path: Path) -> None:
    base = Settings.load()
    settings = Settings(
        root=base.root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=base.config,
    )
    with TestClient(create_app(settings)) as client:
        project = client.post(
            "/api/v1/projects", json={"name": "Projeto", "objective": "Validar memória"}
        ).json()
        lesson = client.post(
            f"/api/v1/projects/{project['id']}/lessons",
            json={"problem": "Falha", "solution": "Teste", "confidence": 0.9},
        )
        assert lesson.status_code == 201
        exported = client.get("/api/v1/memory/export").json()
        assert exported["projects"][0]["id"] == project["id"]
        denied = client.delete(f"/api/v1/projects/{project['id']}/memory")
        assert denied.status_code == 409
        deleted = client.delete(f"/api/v1/projects/{project['id']}/memory?confirm=true")
        assert deleted.status_code == 200


def test_audio_registry_never_selects_unverified_voice() -> None:
    registry = AudioCapabilityRegistry()
    registry.register(
        AudioCapability(
            locale="pt_br",
            stt_available=True,
            tts_available=True,
            voices=("Voz de teste",),
            verified=False,
        )
    )
    assert registry.list("pt-BR")[0]["locale"] == "pt-BR"
    assert registry.best("pt-BR", "tts") is None
    registry.register(
        AudioCapability(
            locale="en",
            stt_available=True,
            tts_available=True,
            voices=("Test voice",),
            verified=True,
        )
    )
    assert registry.best("en", "stt") is not None


def test_all_versioned_plugin_manifests_are_valid() -> None:
    root = Settings.load().root
    registry = PluginRegistry(root / "plugins")
    manifests = registry.discover()
    assert {item["name"] for item in manifests} == {
        "Blender",
        "Desenvolvedor",
        "Mídia",
        "Produtividade",
    }
    assert all(item["permissions"] for item in manifests)


def test_invalid_plugin_is_rejected(tmp_path: Path) -> None:
    manifest = tmp_path / "plugin.json"
    manifest.write_text('{"schema_version": 1, "id": "INVALID"}', encoding="utf-8")
    try:
        load_manifest(manifest)
    except PluginValidationError:
        pass
    else:
        raise AssertionError("Manifesto inválido deveria ser rejeitado")


def test_image_inspection_is_ephemeral_and_audited(tmp_path: Path) -> None:
    base = Settings.load()
    settings = Settings(
        root=base.root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=base.config,
    )
    image = BytesIO()
    Image.new("RGB", (32, 24), "cyan").save(image, format="PNG")
    with TestClient(create_app(settings)) as client:
        response = client.post(
            "/api/v1/documents/inspect",
            files={"file": ("teste.png", image.getvalue(), "image/png")},
        )
        assert response.status_code == 200
        metadata = response.json()
        assert (metadata["width"], metadata["height"], metadata["retained"]) == (
            32,
            24,
            False,
        )
        assert client.get("/api/v1/actions").json()[0]["tool"] == "vision.documents.inspect"


def test_suggestion_has_evidence_and_user_decision(tmp_path: Path) -> None:
    base = Settings.load()
    settings = Settings(
        root=base.root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=base.config,
    )
    with TestClient(create_app(settings)) as client:
        project = client.post("/api/v1/projects", json={"name": "Projeto"}).json()
        lesson = client.post(
            f"/api/v1/projects/{project['id']}/lessons",
            json={"problem": "Build lento", "solution": "Usar cache", "confidence": 0.8},
        ).json()
        created = client.post(
            f"/api/v1/projects/{project['id']}/suggestions",
            json={
                "title": "Ativar cache",
                "description": "Reutilizar saídas verificadas.",
                "priority": "medium",
                "justification": "A lição anterior registrou ganho reproduzível.",
                "source_lesson_id": lesson["id"],
            },
        )
        assert created.status_code == 201
        suggestion = created.json()
        assert suggestion["decision"] == "pending"
        decided = client.patch(
            f"/api/v1/suggestions/{suggestion['id']}", json={"decision": "accepted"}
        )
        assert decided.json()["decision"] == "accepted"
        assert client.get("/api/v1/memory/export").json()["suggestions"][0][
            "source_lesson_id"
        ] == lesson["id"]


def test_memory_backup_is_created_and_verified(tmp_path: Path) -> None:
    base = Settings.load()
    settings = Settings(
        root=base.root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=base.config,
    )
    with TestClient(create_app(settings)) as client:
        client.post("/api/v1/projects", json={"name": "Backup"})
        response = client.post("/api/v1/memory/backup")
        assert response.status_code == 201
        backup = response.json()
        assert backup["integrity"] == "ok"
        assert len(backup["sha256"]) == 64
        assert (tmp_path / "backups" / backup["filename"]).is_file()


def test_plugin_requires_confirmation_and_declared_grant(tmp_path: Path) -> None:
    base = Settings.load()
    settings = Settings(
        root=base.root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=base.config,
    )
    plugin_id = "dev.lzagent.developer"
    with TestClient(create_app(settings)) as client:
        assert client.patch(
            f"/api/v1/plugins/{plugin_id}/state", json={"enabled": True}
        ).status_code == 409
        enabled = client.patch(
            f"/api/v1/plugins/{plugin_id}/state",
            json={"enabled": True, "approved": True},
        )
        assert enabled.json()["enabled"] is True
        invalid = client.put(
            f"/api/v1/plugins/{plugin_id}/grants",
            json={"permission": "system.admin", "granted": True, "approved": True},
        )
        assert invalid.status_code == 400
        granted = client.put(
            f"/api/v1/plugins/{plugin_id}/grants",
            json={"permission": "project.read", "granted": True, "approved": True},
        )
        assert granted.json()["grants"][0]["granted"] is True

        denied = client.post(
            f"/api/v1/plugins/{plugin_id}/execute",
            json={"command": "tests.list", "input": {}, "approved": False},
        )
        assert denied.status_code == 409
        sandbox = client.get("/api/v1/plugins/sandbox/status").json()
        executed = client.post(
            f"/api/v1/plugins/{plugin_id}/execute",
            json={"command": "tests.list", "input": {}, "approved": True},
        )
        if sandbox["available"]:
            assert executed.status_code == 200
            assert "pytest" in executed.json()["result"]["checks"]
            assert executed.json()["isolation"] == "strong-native-sandbox"
        else:
            assert executed.status_code == 503
        action = client.get("/api/v1/actions").json()[0]
        assert action["tool"] == "tests.list"
        expected_permission = (
            "plugins.execute.confirmed" if sandbox["available"] else "plugins.execute.denied"
        )
        assert action["permission"] == expected_permission


def test_plugin_integrity_tampering_is_rejected(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "sample"
    plugin_dir.mkdir()
    runner = plugin_dir / "runner.py"
    runner.write_text("print('safe')", encoding="utf-8")
    manifest = plugin_dir / "plugin.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "id": "dev.lzagent.sample",
                "name": "Sample",
                "version": "1.0.0",
                "description": "Sample",
                "permissions": ["project.read"],
                "commands": ["project.inspect"],
                "entrypoint": "runner.py",
                "integrity_sha256": "0" * 64,
            }
        ),
        encoding="utf-8",
    )
    try:
        load_manifest(manifest)
    except PluginValidationError as error:
        assert "Integridade" in str(error)
    else:
        raise AssertionError("Plugin adulterado deveria ser rejeitado")


def test_memory_restore_requires_hash_confirmation_and_safety_backup(tmp_path: Path) -> None:
    base = Settings.load()
    settings = Settings(
        root=base.root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=base.config,
    )
    with TestClient(create_app(settings)) as client:
        original = client.post("/api/v1/projects", json={"name": "Original"}).json()
        backup = client.post("/api/v1/memory/backup").json()
        temporary = client.post("/api/v1/projects", json={"name": "Temporário"}).json()
        payload = {
            "filename": backup["filename"],
            "sha256": backup["sha256"],
            "confirmation": "RESTAURAR MEMÓRIA",
        }
        assert client.post(
            "/api/v1/memory/restore", json={**payload, "confirmation": "sim"}
        ).status_code == 409
        restored = client.post("/api/v1/memory/restore", json=payload)
        assert restored.status_code == 200
        assert (tmp_path / "backups" / restored.json()["safety_backup"]).is_file()
        project_ids = {item["id"] for item in client.get("/api/v1/projects").json()}
        assert original["id"] in project_ids
        assert temporary["id"] not in project_ids
        assert client.get("/api/v1/actions").json()[0]["tool"] == "memory.backup.restore"


def test_project_checkpoint_captures_git_state(tmp_path: Path) -> None:
    base = Settings.load()
    settings = Settings(
        root=base.root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=base.config,
    )
    with TestClient(create_app(settings)) as client:
        project = client.post("/api/v1/projects", json={"name": "Checkpoint"}).json()
        response = client.post(f"/api/v1/projects/{project['id']}/checkpoints")
        assert response.status_code == 201
        checkpoint = response.json()
        assert len(checkpoint["commit_hash"]) == 40
        assert client.get(
            f"/api/v1/projects/{project['id']}/checkpoints"
        ).json()[0]["id"] == checkpoint["id"]


def test_memory_can_be_edited_searched_and_governed(tmp_path: Path) -> None:
    base = Settings.load()
    settings = Settings(
        root=base.root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=base.config,
    )
    with TestClient(create_app(settings)) as client:
        project = client.post(
            "/api/v1/projects", json={"name": "Rascunho", "objective": "Inicial"}
        ).json()
        changed = client.put(
            f"/api/v1/projects/{project['id']}",
            json={"name": "Projeto acessível", "objective": "Suporte a teclado"},
        )
        assert changed.status_code == 200
        lesson = client.post(
            f"/api/v1/projects/{project['id']}/lessons",
            json={
                "problem": "Foco invisível",
                "solution": "Contraste inicial",
                "confidence": 0.7,
            },
        ).json()
        updated_lesson = client.put(
            f"/api/v1/lessons/{lesson['id']}",
            json={
                "problem": "Foco invisível",
                "solution": "Adicionar indicador de foco com contraste AA",
                "confidence": 0.95,
                "evidence": "Teste por teclado",
            },
        )
        assert updated_lesson.json()["confidence"] == 0.95
        results = client.get(
            "/api/v1/memory/search",
            params={"q": "contraste", "project_id": project["id"]},
        ).json()
        assert {item["kind"] for item in results} == {"lesson"}

        policy = client.put(
            "/api/v1/memory/retention",
            json={"category": "action_ledger", "retention_days": 30},
        )
        assert policy.json()["retention_days"] == 30
        assert client.post(
            "/api/v1/memory/purge", json={"confirmation": "não"}
        ).status_code == 409
        purged = client.post(
            "/api/v1/memory/purge",
            json={"confirmation": "APAGAR MEMÓRIA EXPIRADA"},
        )
        assert purged.status_code == 200
        assert purged.json()["deleted"]["agent_actions"] == 0


def test_local_registration_login_and_logout(tmp_path: Path) -> None:
    base = Settings.load()
    settings = Settings(
        root=base.root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=base.config,
    )
    credentials = {"username": "valentina", "password": "uma-senha-local-segura"}
    with TestClient(create_app(settings)) as client:
        registered = client.post(
            "/api/v1/auth/register",
            json={**credentials, "display_name": "Valentina", "locale": "pt_br"},
        )
        assert registered.status_code == 201
        assert registered.json()["locale"] == "pt-BR"
        assert "password" not in registered.text
        invalid_login = client.post(
            "/api/v1/auth/login", json={**credentials, "password": "errada"}
        )
        assert invalid_login.status_code == 401
        login = client.post("/api/v1/auth/login", json=credentials)
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/v1/auth/me", headers=headers).json()["username"] == "valentina"
        assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_personal_routes_become_private_after_first_account(tmp_path: Path) -> None:
    base = Settings.load()
    settings = Settings(
        root=base.root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=base.config,
    )
    credentials = {"username": "owner", "password": "senha-local-com-12"}
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/v1/projects").status_code == 200
        assert client.post(
            "/api/v1/auth/register",
            json={**credentials, "display_name": "Owner", "locale": "pt-BR"},
        ).status_code == 201
        assert client.get("/api/v1/projects").status_code == 401
        token = client.post("/api/v1/auth/login", json=credentials).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/v1/projects", headers=headers).status_code == 200
        assert client.post(
            "/api/v1/auth/register",
            json={
                "username": "second",
                "display_name": "Second",
                "password": "outra-senha-local-segura",
                "locale": "pt-BR",
            },
        ).status_code == 403


def test_device_detection_is_private_by_default(tmp_path: Path) -> None:
    base = Settings.load()
    settings = Settings(
        root=base.root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=base.config,
    )
    with TestClient(create_app(settings)) as client:
        profile = client.get("/api/v1/system/device").json()
        assert profile["operating_system"]
        assert profile["architecture"]
        assert profile["device_type"] in {"desktop-or-laptop", "mobile-or-tablet", "unknown"}
        assert profile["device_name"] is None
        assert client.get("/api/v1/system/device?include_name=true").json()["device_name"]
        microphones = client.get("/api/v1/audio/devices")
        assert microphones.status_code == 200
        assert "devices" in microphones.json()


def test_native_agent_has_no_external_provider_dependency() -> None:
    response = NativeAgentProvider().complete("organizar a tarefa")
    assert response.provider == "lz-agent"
    assert response.model == "native-core-v1"
    assert response.offline is True


def test_internet_research_requires_explicit_approval(tmp_path: Path) -> None:
    base = Settings.load()
    settings = Settings(
        root=base.root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=base.config,
    )
    with TestClient(create_app(settings)) as client:
        denied = client.post(
            "/api/v1/research/search",
            json={"query": "LZ Agent", "locale": "pt-BR", "approved": False},
        )
        assert denied.status_code == 409


def test_internet_fetch_blocks_local_networks() -> None:
    for url in ("http://127.0.0.1/admin", "http://localhost/", "file:///etc/passwd"):
        try:
            _validate_public_url(url)
        except ResearchError:
            pass
        else:
            raise AssertionError(f"URL local deveria ser bloqueada: {url}")


def test_avatar_states_have_motion_and_accessible_fallbacks() -> None:
    avatar = AvatarController()
    listening = avatar.update(AvatarState.LISTENING)
    assert listening["animation"] == "Listening"
    assert listening["icon"] == "microphone"
    reduced = avatar.update(AvatarState.THINKING, reduced_motion=True)
    assert reduced["animation"] == "Static"
    disabled = avatar.update(AvatarState.PRIVATE, enabled=False)
    assert disabled["fallback"] == "2d-static"


def test_chat_drives_avatar_to_a_terminal_state(tmp_path: Path) -> None:
    base = Settings.load()
    settings = Settings(
        root=base.root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=base.config,
    )
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/v1/avatar/state").json()["state"] == "IDLE"
        assert client.post("/api/v1/chat", json={"message": "Teste"}).status_code == 200
        assert client.get("/api/v1/avatar/state").json()["state"] == "SUCCESS"


def test_avatar_glbs_have_three_lods_and_official_animations() -> None:
    root = Settings.load().root / "assets" / "avatar" / "models"
    expected = {
        "Acting", "Error", "Idle_1", "Idle_2", "Idle_3", "Listening",
        "Needs_Approval", "Offline", "Private", "Speaking", "Success", "Thinking", "Warning",
    }
    triangle_counts = []
    for level in ("Lite", "Standard", "Pro"):
        content = (root / f"LZ_Agent_{level}.glb").read_bytes()
        assert content[:4] == b"glTF"
        json_length = struct.unpack("<I", content[12:16])[0]
        document = json.loads(content[20 : 20 + json_length].decode())
        assert {item["name"] for item in document["animations"]} == expected
        triangles = sum(
            document["accessors"][primitive["indices"]]["count"] // 3
            for mesh in document["meshes"]
            for primitive in mesh["primitives"]
        )
        triangle_counts.append(triangles)
    assert triangle_counts == sorted(triangle_counts)


def test_project_sources_artifacts_are_editable_and_confirmed(tmp_path: Path) -> None:
    base = Settings.load()
    settings = Settings(
        root=base.root,
        data_dir=tmp_path,
        database=tmp_path / "test.db",
        config=base.config,
    )
    with TestClient(create_app(settings)) as client:
        project = client.post("/api/v1/projects", json={"name": "Memória completa"}).json()
        artifact = client.post(
            f"/api/v1/projects/{project['id']}/artifacts",
            json={"kind": "document", "path": "docs/rascunho.md", "checksum": "sha256:teste",
                  "metadata": {"format": "markdown"}},
        )
        assert artifact.status_code == 201
        artifact_id = artifact.json()["id"]
        edited_artifact = client.put(
            f"/api/v1/artifacts/{artifact_id}",
            json={"kind": "document", "path": "docs/final.md", "metadata": {"reviewed": True}},
        )
        assert edited_artifact.json()["metadata"]["reviewed"] is True

        source = client.post(
            f"/api/v1/projects/{project['id']}/sources",
            json={"source_type": "user_document", "source_ref": "docs/final.md",
                  "title": "Documento do usuário", "notes": "Fonte autorizada para contraste",
                  "consent": "explicit"},
        )
        assert source.status_code == 201
        source_id = source.json()["id"]
        edited_source = client.put(
            f"/api/v1/sources/{source_id}",
            json={"source_type": "user_document", "source_ref": "docs/final.md",
                  "title": "Documento revisado", "notes": "Contraste WCAG", "consent": "explicit"},
        )
        assert edited_source.json()["title"] == "Documento revisado"

        results = client.get(
            "/api/v1/memory/search", params={"q": "WCAG", "project_id": project["id"]}
        ).json()
        assert {item["kind"] for item in results} == {"source"}
        exported = client.get("/api/v1/memory/export").json()
        assert exported["artifacts"][0]["id"] == artifact_id
        assert exported["memory_sources"][0]["id"] == source_id
        assert client.delete(f"/api/v1/artifacts/{artifact_id}").status_code == 409
        assert client.delete(f"/api/v1/artifacts/{artifact_id}?confirm=true").status_code == 200
        assert client.delete(f"/api/v1/sources/{source_id}").status_code == 409
        assert client.delete(f"/api/v1/sources/{source_id}?confirm=true").status_code == 200
