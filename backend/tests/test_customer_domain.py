"""Campos obligatorios del formulario de cliente (levantamiento de Ventas).

Dominio puro: se llama la función directamente, sin BD ni servidor.
"""

from datetime import UTC, datetime

from app.domain.customer.service import create_customer

NOW = datetime(2026, 1, 1, tzinfo=UTC)

ALTA = dict(
    id="c1",
    nombre="ACME S.A.",
    representante="Ana Reyes",
    documento="1-3123456-7",
    telefono="809-555-0001",
    direccion="Av. Principal 1",
    created_by="u1",
    now=NOW,
)


def test_alta_con_todos_los_datos():
    r = create_customer(**ALTA)
    assert r.is_ok(), r
    cliente = r.unwrap()
    assert cliente.nombre == "ACME S.A."
    assert cliente.representante == "Ana Reyes"


def test_cada_campo_obligatorio_se_rechaza_vacio():
    for campo in ("nombre", "representante", "documento", "telefono", "direccion"):
        r = create_customer(**{**ALTA, campo: "   "})
        assert not r.is_ok(), campo
        assert r.error.code.startswith("customer."), campo
