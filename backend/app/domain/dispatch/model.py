"""Modelo de Despacho: confirmación interna de entrega. Inmutable."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class EstadoEntrega(StrEnum):
    PENDIENTE_ENTREGA = "pendiente_entrega"
    ENTREGADO = "entregado"
    NEGADO = "negado"


@dataclass(frozen=True, slots=True)
class Dispatch:
    """Formulario interno de confirmación de datos de entrega."""

    id: str
    project_id: str
    fecha_entrega: date | None
    hora_entrega: str | None
    destinatario: str | None
    detalle_entregado: str | None
    notas: str | None
    confirmado_por: str
    fecha_registro: datetime


@dataclass(frozen=True, slots=True)
class Denial:
    """Motivo de rechazo (proyecto 'negado')."""

    id: str
    project_id: str
    motivo: str
    detalle: str
    registrado_por: str
    fecha: datetime
