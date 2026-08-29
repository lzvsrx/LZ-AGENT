from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

PLUGIN_ID = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)+$")
PERMISSION = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z0-9]+)+$")


@dataclass(frozen=True, slots=True)
class PluginManifest:
    schema_version: int
    id: str
    name: str
    version: str
    description: str
    permissions: tuple[str, ...]
    commands: tuple[str, ...]
    entrypoint: str
    path: str


class PluginValidationError(ValueError):
    pass


def load_manifest(path: Path) -> PluginManifest:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PluginValidationError(f"Manifesto inválido em {path}: {error}") from error
    required = {
        "schema_version",
        "id",
        "name",
        "version",
        "description",
        "permissions",
        "commands",
        "entrypoint",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise PluginValidationError(f"Campos ausentes em {path}: {', '.join(missing)}")
    if data["schema_version"] != 1 or not PLUGIN_ID.fullmatch(data["id"]):
        raise PluginValidationError(f"Versão ou ID inválido em {path}")
    permissions = tuple(data["permissions"])
    commands = tuple(data["commands"])
    if any(not PERMISSION.fullmatch(item) for item in (*permissions, *commands)):
        raise PluginValidationError(f"Permissão ou comando inválido em {path}")
    if len(set(commands)) != len(commands) or len(set(permissions)) != len(permissions):
        raise PluginValidationError(f"Permissões ou comandos duplicados em {path}")
    return PluginManifest(
        schema_version=1,
        id=data["id"],
        name=data["name"],
        version=data["version"],
        description=data["description"],
        permissions=permissions,
        commands=commands,
        entrypoint=data["entrypoint"],
        path=str(path),
    )


class PluginRegistry:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self._plugins: dict[str, PluginManifest] = {}

    def discover(self) -> list[dict]:
        plugins: dict[str, PluginManifest] = {}
        for path in sorted(self.directory.glob("*/plugin.json")):
            manifest = load_manifest(path)
            if manifest.id in plugins:
                raise PluginValidationError(f"ID de plugin duplicado: {manifest.id}")
            plugins[manifest.id] = manifest
        self._plugins = plugins
        return [asdict(item) for item in plugins.values()]

    def get(self, plugin_id: str) -> PluginManifest:
        if not self._plugins:
            self.discover()
        try:
            return self._plugins[plugin_id]
        except KeyError as error:
            raise KeyError(plugin_id) from error
