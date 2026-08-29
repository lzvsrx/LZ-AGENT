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


class NativeAgentProvider:
    """First native LZ reasoning layer, owned and executed entirely by this project."""

    def complete(self, prompt: str) -> ProviderResponse:
        normalized = prompt.strip()
        if not normalized:
            text = "Digite ou fale uma tarefa para começar."
        else:
            text = (
                "O núcleo nativo do LZ Agent registrou sua solicitação. O motor atual organiza, "
                "audita e encaminha tarefas locais, mas ainda não possui pesos generativos "
                "próprios treinados. Solicitação: " + normalized
            )
        return ProviderResponse(
            text=text, provider="lz-agent", model="native-core-v1", offline=True
        )
