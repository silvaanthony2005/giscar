"""Adjuntos polimórficos: documentos/imágenes/evidencia de cualquier entidad."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class EntidadTipo(StrEnum):
    PROYECTO = "proyecto"
    PLAN = "plan"
    FASE = "fase"
    CANCELACION = "cancelacion"
    DESPACHO = "despacho"
    INCIDENCIA = "incidencia"
    FACTURA = "factura"


@dataclass(frozen=True, slots=True)
class Attachment:
    id: str
    entidad_tipo: str
    entidad_id: str
    nombre: str
    ruta: str
    mime: str
    tamano: int
    subido_por: str
    fecha: datetime
