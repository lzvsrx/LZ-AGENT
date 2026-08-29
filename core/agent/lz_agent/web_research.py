from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

import httpx


class ResearchError(ValueError):
    pass


def wikipedia_search(query: str, locale: str = "pt") -> list[dict]:
    language = locale.split("-", 1)[0].lower()
    if not language.isalpha() or not 2 <= len(language) <= 3:
        language = "en"
    response = httpx.get(
        f"https://{language}.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": 1,
            "srlimit": 8,
        },
        headers={"User-Agent": "LZ-Agent/0.1 (+https://github.com/lzvsrx/LZ-AGENT)"},
        timeout=15,
    )
    response.raise_for_status()
    rows = response.json().get("query", {}).get("search", [])
    return [
        {
            "title": row["title"],
            "url": f"https://{language}.wikipedia.org/?curid={row['pageid']}",
            "source": "Wikipedia",
        }
        for row in rows
    ]


def fetch_public_text(url: str, max_bytes: int = 1_000_000) -> dict:
    _validate_public_url(url)
    with httpx.stream(
        "GET",
        url,
        follow_redirects=False,
        headers={"User-Agent": "LZ-Agent/0.1 (+https://github.com/lzvsrx/LZ-AGENT)"},
        timeout=20,
    ) as response:
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").split(";", 1)[0]
        if content_type not in {"text/plain", "text/html", "application/json"}:
            raise ResearchError("Tipo de conteúdo remoto não permitido")
        body = bytearray()
        for chunk in response.iter_bytes():
            body.extend(chunk)
            if len(body) > max_bytes:
                raise ResearchError("Conteúdo remoto excede o limite de 1 MB")
    return {"url": url, "content_type": content_type, "text": body.decode("utf-8", "replace")}


def _validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
        raise ResearchError("Somente URLs HTTP(S) públicas são permitidas")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    except OSError as error:
        raise ResearchError("Não foi possível resolver o endereço") from error
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ResearchError("Endereços locais, privados ou reservados são bloqueados")
