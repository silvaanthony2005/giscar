"""Servicio de pagos. Puro: valida monto contra el total del proyecto."""

from __future__ import annotations

from datetime import datetime

from app.domain.payment.model import Payment, TipoPago
from app.domain.shared.money import Money
from app.domain.shared.types import DomainError, Err, Ok, Result


def create_payment(
    *,
    id: str,
    project_id: str,
    monto: Money,
    monto_total: Money,
    pagado_previo: Money,
    tipo: TipoPago,
    metodo_pago: str,
    registrado_por: str,
    fecha: datetime,
    notas: str | None = None,
) -> Result[Payment, DomainError]:
    if monto.cents <= 0:
        return Err(DomainError("payment.monto_invalido", "El monto debe ser mayor a cero"))

    saldo = Money(max(0, monto_total.cents - pagado_previo.cents))
    if monto.cents > saldo.cents:
        return Err(
            DomainError(
                "payment.excede_saldo",
                f"El monto ({monto.amount}) excede el saldo pendiente ({saldo.amount})",
            )
        )

    pagado_total = pagado_previo.cents + monto.cents
    if monto_total.cents <= 0:
        return Err(DomainError("payment.total_invalido", "Monto total del proyecto inválido"))
    porcentaje = int(round(pagado_total * 100 / monto_total.cents))

    return Ok(
        Payment(
            id=id,
            project_id=project_id,
            monto=monto,
            porcentaje=porcentaje,
            tipo=tipo,
            metodo_pago=metodo_pago,
            notas=notas,
            registrado_por=registrado_por,
            fecha=fecha,
        )
    )


def sumar_pagos(pagos: list[Payment]) -> Money:
    """Agrega los montos de forma pura (reduce)."""
    from functools import reduce

    return reduce(lambda acc, p: acc.plus(p.monto), pagos, Money(0))
