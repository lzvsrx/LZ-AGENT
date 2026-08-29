from __future__ import annotations

import hashlib
import io
from dataclasses import asdict, dataclass

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader

MAX_DOCUMENT_BYTES = 25 * 1024 * 1024
ALLOWED_IMAGE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp", "image/gif"})
ALLOWED_DOCUMENT_TYPES = ALLOWED_IMAGE_TYPES | {"application/pdf", "text/plain"}


class DocumentError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DocumentMetadata:
    filename: str
    media_type: str
    size: int
    sha256: str
    kind: str
    pages: int | None = None
    width: int | None = None
    height: int | None = None
    characters: int | None = None
    retained: bool = False


def inspect_document(filename: str, media_type: str, content: bytes) -> dict:
    if not content:
        raise DocumentError("O arquivo está vazio.")
    if len(content) > MAX_DOCUMENT_BYTES:
        raise DocumentError("O arquivo excede o limite de 25 MiB.")
    normalized_type = media_type.split(";", maxsplit=1)[0].strip().lower()
    if normalized_type not in ALLOWED_DOCUMENT_TYPES:
        raise DocumentError(f"Tipo de arquivo não permitido: {normalized_type}")
    common = {
        "filename": filename,
        "media_type": normalized_type,
        "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }
    if normalized_type in ALLOWED_IMAGE_TYPES:
        try:
            with Image.open(io.BytesIO(content)) as image:
                image.verify()
            with Image.open(io.BytesIO(content)) as image:
                metadata = DocumentMetadata(
                    **common, kind="image", width=image.width, height=image.height
                )
        except (UnidentifiedImageError, OSError) as error:
            raise DocumentError("Imagem inválida ou corrompida.") from error
    elif normalized_type == "application/pdf":
        try:
            reader = PdfReader(io.BytesIO(content))
            characters = sum(len(page.extract_text() or "") for page in reader.pages)
            metadata = DocumentMetadata(
                **common, kind="pdf", pages=len(reader.pages), characters=characters
            )
        except Exception as error:
            raise DocumentError("PDF inválido, corrompido ou não suportado.") from error
    else:
        try:
            characters = len(content.decode("utf-8"))
        except UnicodeDecodeError as error:
            raise DocumentError("Texto deve estar codificado em UTF-8.") from error
        metadata = DocumentMetadata(**common, kind="text", characters=characters)
    return asdict(metadata)
