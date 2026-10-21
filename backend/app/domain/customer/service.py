"""Servicio de cliente. Funciones puras."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from app.domain.customer.model import Customer
from app.domain.shared.types import DomainError, Err, Ok, Result


def _requerido(valor: str | None, codigo: str, mensaje: str) -> DomainError | None:
    """None si el valor viene informado; el error que explica su falta si no."""
    return None if (valor or "").strip() else DomainError(codigo, mensaje)


def create_customer(
    *,
    id: str,
    nombre: str,
    representante: str,
    documento: str,
    telefono: str,
    direccion: str,
    now: datetime,
    created_by: str,
    email: str | None = None,
    notas: str | None = None,
) -> Result[Customer, DomainError]:
    # Todos los datos del levantamiento de cliente son obligatorios.
    faltantes = [
        error
        for error in (
            _requerido(nombre, "customer.nombre_vacio", "El nombre de la empresa es obligatorio"),
            _requerido(
                representante,
                "customer.representante_vacio",
                "El nombre del cliente (representante) es obligatorio",
            ),
            _requerido(
                documento, "customer.documento_vacio", "El documento (RIF o cédula) es obligatorio"
            ),
            _requerido(telefono, "customer.telefono_vacio", "El número telefónico es obligatorio"),
            _requerido(direccion, "customer.direccion_vacia", "La dirección es obligatoria"),
        )
        if error is not None
    ]
    if faltantes:
        return Err(faltantes[0])
    return Ok(
        Customer(
            id=id,
            nombre=nombre.strip(),
            representante=representante.strip(),
            documento=documento.strip(),
            telefono=telefono.strip(),
            email=email,
            direccion=direccion.strip(),
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
