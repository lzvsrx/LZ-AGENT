from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

LOCALE_PATTERN = re.compile(
    r"^[A-Za-z]{2,3}(?:-[A-Za-z]{4})?(?:-(?:[A-Za-z]{2}|[0-9]{3}))?(?:-[A-Za-z0-9]{5,8})*$"
)
RTL_SCRIPTS = frozenset({"Arab", "Hebr", "Adlm", "Nkoo", "Rohg", "Syrc", "Thaa"})
RTL_LANGUAGES = frozenset({"ar", "ckb", "dv", "fa", "he", "ku", "ps", "sd", "ug", "ur", "yi"})


def normalize_locale(value: str) -> str:
    """Normalize a practical BCP 47 language tag without replacing regional identity."""
    raw = value.strip().replace("_", "-")
    if not LOCALE_PATTERN.fullmatch(raw):
        raise ValueError(f"Código de idioma inválido: {value}")
    parts = raw.split("-")
    normalized = [parts[0].lower()]
    for part in parts[1:]:
        if len(part) == 4 and part.isalpha():
            normalized.append(part.title())
        elif (len(part) == 2 and part.isalpha()) or (len(part) == 3 and part.isdigit()):
            normalized.append(part.upper())
        else:
            normalized.append(part.lower())
    return "-".join(normalized)


def locale_fallbacks(locale: str, final_fallback: str = "en") -> tuple[str, ...]:
    normalized = normalize_locale(locale)
    candidates = [normalized]
    language = normalized.split("-", maxsplit=1)[0]
    if language != normalized:
        candidates.append(language)
    fallback = normalize_locale(final_fallback)
    if fallback not in candidates:
        candidates.append(fallback)
    return tuple(candidates)


def writing_direction(locale: str) -> str:
    parts = normalize_locale(locale).split("-")
    return (
        "rtl" if parts[0] in RTL_LANGUAGES or any(part in RTL_SCRIPTS for part in parts) else "ltr"
    )


@dataclass(frozen=True, slots=True)
class AudioCapability:
    locale: str
    stt_available: bool
    tts_available: bool
    voices: tuple[str, ...] = ()
    provider: str = "system"
    verified: bool = False


class Translator:
    def __init__(self, directory: Path, fallback: str = "en") -> None:
        self.directory = directory
        self.fallback = fallback

    def messages(self, locale: str) -> tuple[dict[str, str], str]:
        for candidate in locale_fallbacks(locale, self.fallback):
            path = self.directory / f"{candidate}.json"
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8")), candidate
        return {}, self.fallback

    def text(self, key: str, locale: str) -> str:
        messages, _ = self.messages(locale)
        if key in messages:
            return messages[key]
        fallback, _ = self.messages(self.fallback)
        return fallback.get(key, key)
