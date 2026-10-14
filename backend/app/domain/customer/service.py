"""Servicio de cliente. Funciones puras."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from app.domain.customer.model import Customer
from app.domain.shared.types import DomainError, Err, Ok, Result


def create_customer(
    *,
    id: str,
    nombre: str,
    now: datetime,
    created_by: str,
    documento: str | None = None,
    telefono: str | None = None,
    email: str | None = None,
    direccion: str | None = None,
    notas: str | None = None,
) -> Result[Customer, DomainError]:
    if not nombre.strip():
        return Err(DomainError("customer.nombre_vacio", "El nombre del cliente es obligatorio"))
    return Ok(
        Customer(
            id=id,
            nombre=nombre.strip(),
            documento=documento,
            telefono=telefono,
            email=email,
            direccion=direccion,
            notas=notas,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
    )


def update_customer(
    customer: Customer,
    *,
    nombre: str | None = None,
    documento: str | None = None,
    telefono: str | None = None,
    email: str | None = None,
    direccion: str | None = None,
    notas: str | None = None,
    now: datetime,
) -> Result[Customer, DomainError]:
    changes: dict[str, object] = {"updated_at": now}
    if nombre is not None:
        if not nombre.strip():
            return Err(DomainError("customer.nombre_vacio", "El nombre no puede estar vacío"))
        changes["nombre"] = nombre.strip()
    for field, value in (
        ("documento", documento),
        ("telefono", telefono),
        ("email", email),
        ("direccion", direccion),
        ("notas", notas),
    ):
        if value is not None:
            changes[field] = value
    return Ok(replace(customer, **changes))  # type: ignore[arg-type]
