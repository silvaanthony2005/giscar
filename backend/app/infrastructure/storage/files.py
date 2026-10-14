"""Almacenamiento de archivos en disco (uploads/). I/O puro de infraestructura."""

from __future__ import annotations

from pathlib import Path

from app.config import get_settings


def save_upload(filename: str, content: bytes) -> str:
    """Escribe el archivo en uploads/ y devuelve la ruta relativa segura."""
    settings = get_settings()
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    destino = settings.uploads_dir / filename
    destino.write_bytes(content)
    return filename


def read_upload(ruta: str) -> bytes | None:
    settings = get_settings()
    destino = settings.uploads_dir / ruta
    if not destino.is_file():
        return None
    return destino.read_bytes()


def upload_path(ruta: str) -> Path:
    return get_settings().uploads_dir / ruta
