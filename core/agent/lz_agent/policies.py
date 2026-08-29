from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Risk(StrEnum):
    READ = "read"
    WRITE = "write"
    DESTRUCTIVE = "destructive"
    EXTERNAL = "external"
    SENSITIVE = "sensitive"


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    requires_approval: bool
    reason: str


class PolicyEngine:
    def decide(self, risk: Risk, autonomy_level: int, approved: bool = False) -> Decision:
        if risk in {Risk.DESTRUCTIVE, Risk.EXTERNAL, Risk.SENSITIVE}:
            return Decision(approved, not approved, "Ação sensível exige consentimento explícito.")
        if risk == Risk.WRITE and autonomy_level < 3:
            return Decision(
                approved, not approved, "Alteração fora do nível de autonomia aprovado."
            )
        return Decision(True, False, "Permitido pela política e pelo escopo atual.")
