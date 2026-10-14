"""Modelo de pago (cobro 50/100 y liquidación final)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.shared.money import Money


class TipoPago(StrEnum):
    ANTICIPO = "anticipo"  # 50% o 100% cobrado en Ventas
    LIQUIDACION = "liquidacion"  # resto cobrado en Despacho
    TOTAL = "total"  # pago único


@dataclass(frozen=True, slots=True)
class Payment:
    id: str
    project_id: str
    monto: Money
    porcentaje: int
    tipo: TipoPago
    metodo_pago: str
    notas: str | None
    registrado_por: str
    fecha: datetime
