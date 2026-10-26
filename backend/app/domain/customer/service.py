"""Servicio de cliente. Funciones puras."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from app.domain.customer.model import Customer
from app.domain.shared.types import DomainError, Err, Ok, Result


def _requerido(valor: str | None, codigo: str, mensaje: str) -> DomainError | None:
    """None si el valor viene informado; el error que explica su falta si no."""
    return None if (valor or "").strip() else DomainError(codigo, mensaje)


def normalizar_telefono(valor: str | None) -> str | None:
    """El teléfono se guarda con dígitos solamente: '809-555 0001' -> '8095550001'.

    None si el dato viene vacío o si contiene letras u otros símbolos.
    """
    if valor is None:
        return None
    limpio = "".join(ch for ch in valor.strip() if ch not in " -()+.")
    return limpio if limpio.isdigit() else None


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
    telefono_limpio = normalizar_telefono(telefono)
    if telefono_limpio is None:
        return Err(
            DomainError(
                "customer.telefono_invalido",
                "El número telefónico solo puede contener números",
            )
        )
    return Ok(
        Customer(
            id=id,
            nombre=nombre.strip(),
            representante=representante.strip(),
            documento=documento.strip(),
            telefono=telefono_limpio,
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
    representante: str | None = None,
    documento: str | None = None,
    telefono: str | None = None,
    email: str | None = None,
    direccion: str | None = None,
    notas: str | None = None,
    now: datetime,
) -> Result[Customer, DomainError]:
    changes: dict[str, object] = {"updated_at": now}
    for field, value, codigo, mensaje in (
        ("nombre", nombre, "customer.nombre_vacio", "El nombre no puede estar vacío"),
        (
            "representante",
            representante,
            "customer.representante_vacio",
            "El representante no puede estar vacío",
        ),
    ):
        if value is not None:
            if not value.strip():
                return Err(DomainError(codigo, mensaje))
            changes[field] = value.strip()
    if telefono is not None:
        limpio = normalizar_telefono(telefono)
        if limpio is None:
            if telefono.strip():
                return Err(
                    DomainError(
                        "customer.telefono_invalido",
                        "El número telefónico solo puede contener números",
                    )
                )
            # Cadena vacía = borrar el dato: el formulario envía el registro completo.
            changes["telefono"] = None
        else:
            changes["telefono"] = limpio
    for field, value in (
        ("documento", documento),
        ("email", email),
        ("direccion", direccion),
        ("notas", notas),
    ):
        if value is not None:
            # Cadena vacía = borrar el dato: el formulario envía el registro completo.
            changes[field] = value.strip() or None
    return Ok(replace(customer, **changes))  # type: ignore[arg-type]


def puede_eliminar(customer: Customer, tiene_proyectos: bool) -> Result[Customer, DomainError]:
    """No se borra un cliente con proyectos: sus expedientes cuelgan de él."""
    if tiene_proyectos:
        return Err(
            DomainError(
                "customer.con_proyectos",
                "El cliente tiene proyectos registrados; no puede eliminarse",
            )
        )
    return Ok(customer)
