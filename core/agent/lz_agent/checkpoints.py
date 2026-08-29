from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


class CheckpointError(RuntimeError):
    pass


class GitCheckpointService:
    def __init__(self, repository: Path, max_diff_bytes: int = 2 * 1024 * 1024) -> None:
        self.repository = repository.resolve()
        self.max_diff_bytes = max_diff_bytes
        discovered = shutil.which("git")
        windows_git = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/cmd/git.exe"
        self.git = discovered or (str(windows_git) if windows_git.is_file() else None)

    def capture(self) -> dict:
        if not self.git or not (self.repository / ".git").exists():
            raise CheckpointError("Repositório Git não disponível")
        commit = self._run("rev-parse", "HEAD").strip()
        status = self._run("status", "--porcelain=v1", "-z")
        files = sorted(
            {item[3:] for item in status.split("\0") if len(item) > 3 and item[3:]}
        )
        diff = self._run("diff", "--binary", "--no-ext-diff")
        encoded = diff.encode("utf-8")
        truncated = len(encoded) > self.max_diff_bytes
        if truncated:
            diff = encoded[: self.max_diff_bytes].decode("utf-8", errors="replace")
        return {
            "commit_hash": commit,
            "files": files,
            "diff": diff,
            "diff_truncated": truncated,
        }

    def _run(self, *arguments: str) -> str:
        try:
            result = subprocess.run(  # noqa: S603
                [self.git, *arguments],
                cwd=self.repository,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise CheckpointError(f"Falha ao capturar checkpoint: {error}") from error
        return result.stdout
