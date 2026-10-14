"""Validación de archivos subidos. Puro (sin escribir en disco)."""

from __future__ import annotations

from app.domain.attachment.model import EntidadTipo
from app.domain.shared.types import DomainError, Err, Ok, Result

ALLOWED_MIMES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/gif",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def validate_upload(
    *, nombre: str, mime: str, tamano: int, max_bytes: int
) -> Result[str, DomainError]:
    if not nombre.strip():
        return Err(DomainError("upload.nombre_vacio", "El archivo necesita un nombre"))
    if mime not in ALLOWED_MIMES:
        return Err(DomainError("upload.tipo_no_permitido", f"Tipo de archivo no permitido: {mime}"))
    if tamano <= 0:
        return Err(DomainError("upload.vacio", "El archivo está vacío"))
    if tamano > max_bytes:
        mb = max_bytes // (1024 * 1024)
        return Err(DomainError("upload.demasiado_grande", f"El archivo supera el máximo de {mb} MB"))
    return Ok(nombre.strip())


def validate_entidad_tipo(raw: str) -> Result[EntidadTipo, DomainError]:
    try:
        return Ok(EntidadTipo(raw))
    except ValueError:
        return Err(DomainError("upload.entidad_invalida", f"Entidad no válida: {raw}"))


def safe_filename(nombre: str, id_archivo: str) -> str:
    """Nombre seguro para disco: sin path traversal. Determinista por id."""
    import re

    base = re.sub(r"[^\w.\-]+", "_", nombre).strip("._") or "archivo"
    return f"{id_archivo}_{base[:80]}"
