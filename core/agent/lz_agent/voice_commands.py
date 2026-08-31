from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from .command_planner import CommandPlanner


def _plain(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return " ".join("".join(char for char in normalized if not unicodedata.combining(char)).split())


@dataclass(frozen=True, slots=True)
class VoiceInterpretation:
    transcript: str
    normalized: str
    locale: str
    canonical_command: str
    extracted_properties: dict[str, Any]
    confidence: float
    review_required: bool
    command_properties: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "transcript": self.transcript,
            "normalized": self.normalized,
            "locale": self.locale,
            "canonical_command": self.canonical_command,
            "extracted_properties": self.extracted_properties,
            "confidence": self.confidence,
            "review_required": self.review_required,
            "command_properties": self.command_properties,
        }


class VoiceCommandInterpreter:
    """Normalizes speech into a reviewable command; it never executes the transcript."""

    INTENTS = (
        (
            (
                "pesquisar", "pesquise", "buscar", "busque", "procure", "search", "find",
                "buscar en internet",
            ),
            "Pesquisar na internet",
            "query",
        ),
        (("abrir", "abra", "open", "abre"), "Abrir", "target"),
        (("fechar", "feche", "close", "cierra"), "Fechar", "target"),
        (("criar", "crie", "create", "crear"), "Criar", "target"),
        (("editar", "edite", "edit", "editar"), "Editar", "target"),
        (("salvar", "save", "guardar"), "Salvar", "target"),
        (
            ("apagar", "excluir", "remover", "delete", "remove", "borrar", "eliminar"),
            "Apagar",
            "target",
        ),
        (("ler", "leia", "read", "leer"), "Ler", "target"),
        (("enviar", "mande", "send", "enviar"), "Enviar mensagem", "target"),
        (("ligar", "chamar", "call", "llamar"), "Fazer chamada", "target"),
        (("lembrar", "lembrete", "remind", "recordatorio"), "Criar lembrete", "target"),
        (("aumentar volume", "volume up", "subir volumen"), "Aumentar volume", None),
        (("diminuir volume", "volume down", "bajar volumen"), "Diminuir volume", None),
        (("pausar", "pause", "pausa"), "Pausar mídia", None),
        (("continuar", "reproduzir", "play", "reproducir"), "Reproduzir mídia", None),
        (("ativar leitor", "screen reader", "lector de pantalla"), "Ativar leitor de tela", None),
        (("reduzir animacoes", "reduce motion", "reducir animaciones"), "Reduzir animações", None),
    )

    def __init__(self, planner: CommandPlanner | None = None) -> None:
        self.planner = planner or CommandPlanner()

    def interpret(
        self, transcript: str, *, locale: str = "pt-BR", approved: bool = False
    ) -> VoiceInterpretation:
        normalized = _plain(transcript)
        canonical, key, matched = "Responder", None, ""
        for aliases, candidate, property_key in self.INTENTS:
            found = next((alias for alias in aliases if _plain(alias) in normalized), None)
            if found:
                canonical, key, matched = candidate, property_key, _plain(found)
                break
        extracted: dict[str, Any] = {"locale": locale, "input_mode": "voice"}
        remainder = (
            re.sub(rf"^.*?\b{re.escape(matched)}\b", "", normalized, count=1).strip(" ,:;-")
            if matched
            else ""
        )
        if key and remainder:
            extracted[key] = remainder
        confidence = 0.9 if matched and (not key or remainder) else (0.65 if matched else 0.25)
        command = f"{canonical} {remainder}".strip()
        properties = self.planner.prepare(
            command, supplied=extracted, approved=approved, autonomy_level=2
        ).as_dict()
        return VoiceInterpretation(
            transcript=transcript,
            normalized=normalized,
            locale=locale,
            canonical_command=command,
            extracted_properties=extracted,
            confidence=confidence,
            review_required=confidence < 0.8 or properties["requires_approval"],
            command_properties=properties,
        )
