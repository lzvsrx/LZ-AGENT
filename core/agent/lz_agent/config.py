from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True, slots=True)
class Settings:
    root: Path
    data_dir: Path
    database: Path
    config: dict

    @classmethod
    def load(cls, root: Path = ROOT) -> Settings:
        config = json.loads((root / "config" / "agent.defaults.json").read_text(encoding="utf-8"))
        database = root / config["database"]["local_file"]
        database.parent.mkdir(parents=True, exist_ok=True)
        return cls(root=root, data_dir=database.parent, database=database, config=config)
