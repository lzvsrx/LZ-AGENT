from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Database:
    def __init__(self, path: Path, migrations: Path) -> None:
        self.path = path
        self.migrations = migrations

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def migrate(self) -> None:
        with self.connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations("
                "version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
            applied = {
                row[0] for row in connection.execute("SELECT version FROM schema_migrations")
            }
            for script in sorted(self.migrations.glob("*.sql")):
                if script.stem in applied:
                    continue
                connection.executescript(script.read_text(encoding="utf-8"))
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (script.stem, utc_now()),
                )

    def record_action(
        self,
        command: str,
        tool: str,
        status: str,
        *,
        parameters: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        project_id: str | None = None,
        permission: str | None = None,
        model: str = "local-policy",
    ) -> dict[str, Any]:
        action_id = str(uuid.uuid4())
        created_at = utc_now()
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO agent_actions
                (id, project_id, command, tool, parameters_json, result_json, error, status,
                 permission, model, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    action_id,
                    project_id,
                    command,
                    tool,
                    json.dumps(parameters or {}),
                    json.dumps(result or {}),
                    error,
                    status,
                    permission,
                    model,
                    created_at,
                    created_at,
                ),
            )
        return self.get_action(action_id)

    def get_action(self, action_id: str) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM agent_actions WHERE id = ?", (action_id,)
            ).fetchone()
        if row is None:
            raise KeyError(action_id)
        return self._decode(row)

    def list_actions(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM agent_actions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._decode(row) for row in rows]

    def stats(self) -> dict[str, int]:
        with self.connect() as connection:
            return {
                "agent_actions": connection.execute(
                    "SELECT COUNT(*) FROM agent_actions"
                ).fetchone()[0],
                "projects": connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0],
                "lessons_learned": connection.execute(
                    "SELECT COUNT(*) FROM lessons_learned"
                ).fetchone()[0],
                "suggestions": connection.execute("SELECT COUNT(*) FROM suggestions").fetchone()[0],
                "artifacts": connection.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0],
            }

    def create_project(self, name: str, objective: str = "") -> dict[str, Any]:
        project_id = str(uuid.uuid4())
        now = utc_now()
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO projects
                (id, name, objective, stack_json, state, created_at, updated_at)
                VALUES (?, ?, ?, '{}', 'active', ?, ?)""",
                (project_id, name, objective, now, now),
            )
        return self.get_project(project_id)

    def get_project(self, project_id: str) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
        if row is None:
            raise KeyError(project_id)
        value = dict(row)
        value["stack"] = json.loads(value.pop("stack_json") or "{}")
        return value

    def list_projects(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT id FROM projects ORDER BY updated_at DESC").fetchall()
        return [self.get_project(row[0]) for row in rows]

    def add_lesson(
        self,
        project_id: str,
        problem: str,
        solution: str,
        confidence: float,
        evidence: str = "",
    ) -> dict[str, Any]:
        self.get_project(project_id)
        lesson_id = str(uuid.uuid4())
        now = utc_now()
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO lessons_learned
                (id, project_id, problem, solution, evidence, confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (lesson_id, project_id, problem, solution, evidence, confidence, now, now),
            )
        return self.get_lesson(lesson_id)

    def get_lesson(self, lesson_id: str) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM lessons_learned WHERE id = ?", (lesson_id,)
            ).fetchone()
        if row is None:
            raise KeyError(lesson_id)
        return dict(row)

    def list_lessons(self, project_id: str | None = None) -> list[dict[str, Any]]:
        with self.connect() as connection:
            if project_id:
                rows = connection.execute(
                    "SELECT * FROM lessons_learned WHERE project_id = ? ORDER BY created_at DESC",
                    (project_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM lessons_learned ORDER BY created_at DESC"
                ).fetchall()
        return [dict(row) for row in rows]

    def create_suggestion(
        self,
        project_id: str,
        title: str,
        description: str,
        priority: str,
        justification: str,
        *,
        impact: str = "",
        source_lesson_id: str | None = None,
    ) -> dict[str, Any]:
        self.get_project(project_id)
        if source_lesson_id:
            lesson = self.get_lesson(source_lesson_id)
            if lesson["project_id"] != project_id:
                raise ValueError("A lição de origem pertence a outro projeto")
        suggestion_id = str(uuid.uuid4())
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO suggestions
                (id, project_id, title, description, priority, impact, justification,
                 source_lesson_id, decision, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
                (
                    suggestion_id,
                    project_id,
                    title,
                    description,
                    priority,
                    impact,
                    justification,
                    source_lesson_id,
                    utc_now(),
                ),
            )
        return self.get_suggestion(suggestion_id)

    def get_suggestion(self, suggestion_id: str) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM suggestions WHERE id = ?", (suggestion_id,)
            ).fetchone()
        if row is None:
            raise KeyError(suggestion_id)
        return dict(row)

    def list_suggestions(self, project_id: str | None = None) -> list[dict[str, Any]]:
        with self.connect() as connection:
            if project_id:
                rows = connection.execute(
                    "SELECT * FROM suggestions WHERE project_id = ? ORDER BY created_at DESC",
                    (project_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM suggestions ORDER BY created_at DESC"
                ).fetchall()
        return [dict(row) for row in rows]

    def decide_suggestion(self, suggestion_id: str, decision: str) -> dict[str, Any]:
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE suggestions SET decision = ? WHERE id = ?",
                (decision, suggestion_id),
            )
        if cursor.rowcount == 0:
            raise KeyError(suggestion_id)
        return self.get_suggestion(suggestion_id)

    def export_memory(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "exported_at": utc_now(),
            "projects": self.list_projects(),
            "lessons_learned": self.list_lessons(),
            "suggestions": self.list_suggestions(),
            "actions": self.list_actions(limit=500),
        }

    def delete_project_memory(self, project_id: str) -> bool:
        with self.connect() as connection:
            cursor = connection.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        return cursor.rowcount > 0

    def create_verified_backup(self, destination_dir: Path) -> dict[str, Any]:
        destination_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        destination = destination_dir / f"lz-agent-{stamp}-{uuid.uuid4().hex[:8]}.db"
        with self.connect() as source, sqlite3.connect(destination) as target:
            source.backup(target)
            integrity = target.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            destination.unlink(missing_ok=True)
            raise RuntimeError(f"Backup SQLite inválido: {integrity}")
        content = destination.read_bytes()
        return {
            "filename": destination.name,
            "size_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "integrity": integrity,
            "created_at": utc_now(),
        }

    def restore_verified_backup(
        self, destination_dir: Path, filename: str, expected_sha256: str
    ) -> dict[str, Any]:
        if Path(filename).name != filename or not filename.endswith(".db"):
            raise ValueError("Nome de backup inválido")
        source_path = destination_dir / filename
        if not source_path.is_file():
            raise FileNotFoundError(filename)
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if digest.lower() != expected_sha256.lower():
            raise ValueError("SHA-256 do backup não confere")

        required_tables = {"schema_migrations", "projects", "agent_actions"}
        with sqlite3.connect(source_path) as source:
            integrity = source.execute("PRAGMA integrity_check").fetchone()[0]
            tables = {
                row[0]
                for row in source.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            if integrity != "ok" or not required_tables.issubset(tables):
                raise ValueError("Backup inválido ou incompatível com o LZ Agent")
            before_restore = self.create_verified_backup(destination_dir)
            with self.connect() as target:
                source.backup(target)
        self.migrate()
        return {
            "restored": True,
            "filename": filename,
            "sha256": digest,
            "integrity": integrity,
            "safety_backup": before_restore["filename"],
            "restored_at": utc_now(),
        }

    def register_plugin(self, plugin_id: str, version: str) -> dict[str, Any]:
        now = utc_now()
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO plugin_states(plugin_id, version, enabled, installed_at, updated_at)
                VALUES (?, ?, 0, ?, ?)
                ON CONFLICT(plugin_id) DO UPDATE SET version=excluded.version,
                updated_at=excluded.updated_at""",
                (plugin_id, version, now, now),
            )
        return self.get_plugin_state(plugin_id)

    def get_plugin_state(self, plugin_id: str) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM plugin_states WHERE plugin_id = ?", (plugin_id,)
            ).fetchone()
            grants = connection.execute(
                "SELECT permission, granted, granted_at FROM plugin_grants WHERE plugin_id = ?",
                (plugin_id,),
            ).fetchall()
        if row is None:
            raise KeyError(plugin_id)
        value = dict(row)
        value["enabled"] = bool(value["enabled"])
        value["grants"] = [
            {**dict(grant), "granted": bool(grant["granted"])} for grant in grants
        ]
        return value

    def set_plugin_enabled(self, plugin_id: str, enabled: bool) -> dict[str, Any]:
        with self.connect() as connection:
            cursor = connection.execute(
                "UPDATE plugin_states SET enabled = ?, updated_at = ? WHERE plugin_id = ?",
                (int(enabled), utc_now(), plugin_id),
            )
        if cursor.rowcount == 0:
            raise KeyError(plugin_id)
        return self.get_plugin_state(plugin_id)

    def set_plugin_grant(self, plugin_id: str, permission: str, granted: bool) -> dict[str, Any]:
        self.get_plugin_state(plugin_id)
        now = utc_now()
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO plugin_grants(plugin_id, permission, granted, granted_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(plugin_id, permission) DO UPDATE SET granted=excluded.granted,
                granted_at=excluded.granted_at""",
                (plugin_id, permission, int(granted), now if granted else None),
            )
        return self.get_plugin_state(plugin_id)

    def create_checkpoint(
        self,
        project_id: str,
        commit_hash: str,
        files: list[str],
        diff: str,
        test_result: str = "not-run",
    ) -> dict[str, Any]:
        self.get_project(project_id)
        checkpoint_id = str(uuid.uuid4())
        with self.connect() as connection:
            connection.execute(
                """INSERT INTO checkpoints
                (id, project_id, commit_hash, files_json, diff, test_result, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    checkpoint_id,
                    project_id,
                    commit_hash,
                    json.dumps(files),
                    diff,
                    test_result,
                    utc_now(),
                ),
            )
        return self.get_checkpoint(checkpoint_id)

    def get_checkpoint(self, checkpoint_id: str) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM checkpoints WHERE id = ?", (checkpoint_id,)
            ).fetchone()
        if row is None:
            raise KeyError(checkpoint_id)
        value = dict(row)
        value["files"] = json.loads(value.pop("files_json") or "[]")
        return value

    def list_checkpoints(self, project_id: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id FROM checkpoints WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            ).fetchall()
        return [self.get_checkpoint(row[0]) for row in rows]

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        value = dict(row)
        for field in ("parameters_json", "result_json"):
            value[field.removesuffix("_json")] = json.loads(value.pop(field) or "{}")
        return value
