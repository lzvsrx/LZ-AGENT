from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    text: str
    provider: str
    model: str
    offline: bool


class Provider(Protocol):
    def complete(self, prompt: str) -> ProviderResponse: ...


class LocalFallbackProvider:
    """Deterministic fallback that keeps core flows usable without credentials."""

    def complete(self, prompt: str) -> ProviderResponse:
        normalized = prompt.strip()
        if not normalized:
            text = "Digite ou fale uma tarefa para começar."
        else:
            text = (
                "Estou em modo local e registrei sua solicitação. Para raciocínio com um "
                "modelo de IA, "
                "configure um provedor autorizado nas configurações. Solicitação: " + normalized
            )
        return ProviderResponse(
            text=text, provider="local", model="deterministic-fallback", offline=True
        )
