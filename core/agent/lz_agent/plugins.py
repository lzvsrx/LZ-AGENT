from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

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


class PluginExecutionError(RuntimeError):
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
    entrypoint = data["entrypoint"]
    if Path(entrypoint).name != entrypoint or not entrypoint.endswith(".py"):
        raise PluginValidationError(f"Entrypoint deve ser um arquivo Python local em {path}")
    if not (path.parent / entrypoint).is_file():
        raise PluginValidationError(f"Entrypoint ausente em {path}")
    return PluginManifest(
        schema_version=1,
        id=data["id"],
        name=data["name"],
        version=data["version"],
        description=data["description"],
        permissions=permissions,
        commands=commands,
        entrypoint=entrypoint,
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


class PluginRunner:
    """Runs a bundled plugin behind a constrained JSON subprocess boundary.

    This boundary limits time, payload, environment and working directory. It is not an OS security
    sandbox; untrusted third-party packages remain disabled until a platform sandbox is available.
    """

    def __init__(self, timeout_seconds: float = 5.0, max_output_bytes: int = 1_000_000) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes

    def execute(
        self, manifest: PluginManifest, command: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        if command not in manifest.commands:
            raise PluginExecutionError("Comando não declarado pelo plugin")
        encoded = json.dumps({"command": command, "input": payload}, ensure_ascii=False)
        if len(encoded.encode("utf-8")) > 256_000:
            raise PluginExecutionError("Entrada do plugin excede 256 KB")
        entrypoint = (Path(manifest.path).parent / manifest.entrypoint).resolve()
        started = time.perf_counter()
        environment = {"PYTHONIOENCODING": "utf-8", "LZ_PLUGIN_ID": manifest.id}
        if os.name == "nt":
            environment["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", r"C:\Windows")
        try:
            with tempfile.TemporaryDirectory(prefix="lz-plugin-") as workspace:
                process = subprocess.run(  # noqa: S603 - fixed interpreter and validated local path
                    [sys.executable, "-I", str(entrypoint)],
                    input=encoded,
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    cwd=workspace,
                    env=environment,
                    timeout=self.timeout_seconds,
                    check=False,
                )
        except subprocess.TimeoutExpired as error:
            raise PluginExecutionError("Plugin excedeu o tempo permitido") from error
        duration_ms = round((time.perf_counter() - started) * 1000)
        if len(process.stdout.encode("utf-8")) > self.max_output_bytes:
            raise PluginExecutionError("Saída do plugin excede o limite")
        if process.returncode != 0:
            raise PluginExecutionError("Plugin terminou com erro")
        try:
            response = json.loads(process.stdout)
        except json.JSONDecodeError as error:
            raise PluginExecutionError("Plugin retornou JSON inválido") from error
        if not isinstance(response, dict) or response.get("ok") is not True:
            raise PluginExecutionError(str(response.get("error", "Resposta inválida do plugin")))
        return {
            "result": response.get("result", {}),
            "duration_ms": duration_ms,
            "isolation": "restricted-subprocess",
        }
