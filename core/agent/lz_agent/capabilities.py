from __future__ import annotations

import os
import platform
import shutil
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

from .localization import AudioCapability, normalize_locale


@dataclass(frozen=True, slots=True)
class RuntimeCapability:
    name: str
    available: bool
    executable: str | None = None
    detail: str | None = None


def executable_capability(name: str) -> RuntimeCapability:
    executable = shutil.which(name)
    return RuntimeCapability(name=name, available=executable is not None, executable=executable)


def runtime_diagnostics(database_path: Path | None = None) -> dict:
    tools = [
        executable_capability(name)
        for name in ("git", "ffmpeg", "dotnet", "java", "adb", "flutter", "cargo", "blender")
    ]
    database_writable = None
    if database_path is not None:
        database_writable = os.access(database_path.parent, os.W_OK)
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "sqlite": sqlite3.sqlite_version,
        "database_writable": database_writable,
        "tools": [asdict(item) for item in tools],
    }


class AudioCapabilityRegistry:
    """Reports verified provider capabilities; absence degrades to text without guessing."""

    def __init__(self) -> None:
        self._capabilities: dict[tuple[str, str], AudioCapability] = {}

    def register(self, capability: AudioCapability) -> None:
        locale = normalize_locale(capability.locale)
        normalized = AudioCapability(
            locale=locale,
            stt_available=capability.stt_available,
            tts_available=capability.tts_available,
            voices=capability.voices,
            provider=capability.provider,
            verified=capability.verified,
        )
        self._capabilities[(normalized.provider, locale)] = normalized

    def list(self, locale: str | None = None) -> list[dict]:
        normalized = normalize_locale(locale) if locale else None
        rows = [
            capability
            for (_, tag), capability in self._capabilities.items()
            if normalized is None or tag == normalized
        ]
        return [asdict(row) for row in sorted(rows, key=lambda item: (item.locale, item.provider))]

    def best(self, locale: str, operation: str) -> AudioCapability | None:
        normalized = normalize_locale(locale)
        candidates = [
            capability
            for (_, tag), capability in self._capabilities.items()
            if tag == normalized and capability.verified
        ]
        attribute = {"stt": "stt_available", "tts": "tts_available"}.get(operation)
        if attribute is None:
            raise ValueError(f"Operação de áudio inválida: {operation}")
        return next((item for item in candidates if getattr(item, attribute)), None)
