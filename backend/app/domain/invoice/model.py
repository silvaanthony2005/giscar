"""Modelo de factura: registro interno del cobro + snapshot del levantamiento."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.shared.money import Money


@dataclass(frozen=True, slots=True)
class InvoiceSnapshot:
    """Copia inmutable de los datos del proyecto al momento de facturar."""

    project_codigo: str
    project_titulo: str
    project_descripcion: str
    cliente_nombre: str
    cliente_documento: str | None
    cliente_telefono: str | None
    cliente_direccion: str | None
    monto_total: Money


@dataclass(frozen=True, slots=True)
class Invoice:
    id: str
    numero: str
    project_id: str
    payment_id: str
    monto: Money
    porcentaje: int
    metodo_pago: str
    descripcion: str
    snapshot: InvoiceSnapshot
    emitida_por: str
    emitida_en: datetime
