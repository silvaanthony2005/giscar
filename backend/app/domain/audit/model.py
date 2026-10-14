"""Modelo de bitácora de auditoría. Registro de acciones sensibles."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AuditLog:
    id: str
    user_id: str | None
    user_email: str | None
    accion: str
    entidad_tipo: str | None
    entidad_id: str | None
    detalle: str | None
    ip: str | None
    fecha: datetime
