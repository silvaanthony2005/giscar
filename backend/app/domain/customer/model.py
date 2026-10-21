"""Modelo de cliente (datos levantados por Ventas). Inmutable."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Customer:
    id: str
    nombre: str
    representante: str | None
    documento: str | None
    telefono: str | None
    email: str | None
    direccion: str | None
    notas: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
