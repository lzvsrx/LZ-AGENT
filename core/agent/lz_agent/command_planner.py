from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .policies import PolicyEngine, Risk


@dataclass(frozen=True, slots=True)
class CommandProperties:
    intent: str
    risk: Risk
    permission: str
    required_capabilities: tuple[str, ...]
    required_inputs: tuple[str, ...]
    generated_defaults: dict[str, Any]
    requires_approval: bool
    executable: bool
    reason: str
    fallback: str

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["risk"] = self.risk.value
        return value


class CommandPlanner:
    """Creates safe, explicit properties needed to validate a user command."""

    def __init__(self, policy: PolicyEngine | None = None) -> None:
        self.policy = policy or PolicyEngine()

    def prepare(
        self,
        command: str,
        *,
        supplied: dict[str, Any] | None = None,
        approved: bool = False,
        autonomy_level: int = 2,
    ) -> CommandProperties:
        normalized = " ".join(command.strip().casefold().split())
        supplied = supplied or {}
        intent, risk, permission, capabilities, required = self._classify(normalized)
        missing = tuple(item for item in required if not supplied.get(item))
        decision = self.policy.decide(risk, autonomy_level, approved)
        generated = {
            "locale": supplied.get("locale", "pt-BR"),
            "private": bool(supplied.get("private", False)),
            "timeout_seconds": min(max(int(supplied.get("timeout_seconds", 30)), 1), 300),
            "audit": True,
        }
        executable = decision.allowed and not missing
        if missing:
            reason = "Entradas obrigatórias ausentes: " + ", ".join(missing)
        else:
            reason = decision.reason
        return CommandProperties(
            intent=intent,
            risk=risk,
            permission=permission,
            required_capabilities=capabilities,
            required_inputs=missing,
            generated_defaults=generated,
            requires_approval=decision.requires_approval,
            executable=executable,
            reason=reason,
            fallback="Solicitar os dados ou a aprovação que faltam; nunca presumir acesso.",
        )

    @staticmethod
    def _classify(command: str) -> tuple[str, Risk, str, tuple[str, ...], tuple[str, ...]]:
        if any(word in command for word in ("apagar", "deletar", "excluir", "remover")):
            return "delete", Risk.DESTRUCTIVE, "data.delete", ("storage",), ("target",)
        if any(word in command for word in ("pesquisar", "internet", "buscar na web")):
            return "research", Risk.EXTERNAL, "network.research", ("network",), ("query",)
        if any(word in command for word in ("microfone", "ouvir", "gravar voz", "reconhecer voz")):
            return "audio", Risk.SENSITIVE, "microphone.use", ("microphone",), ()
        if any(word in command for word in ("criar", "editar", "alterar", "salvar", "escrever")):
            return "write", Risk.WRITE, "data.write", ("storage",), ("target",)
        return "answer", Risk.READ, "data.read", ("text",), ()
