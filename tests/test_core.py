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
