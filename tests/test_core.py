from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from lz_agent.api import create_app
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
