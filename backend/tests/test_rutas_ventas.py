"""Contratos del alta de proyecto y cliente de Ventas que el frontend pinta tal cual.

Sin BD ni servidor (AGENTS.md): el formulario ya no lleva campo de título y
todos los datos del cliente son obligatorios.
"""

import pytest
from pydantic import ValidationError

from app.infrastructure.api import schemas_ventas as s
from app.infrastructure.api.routes import ventas


def test_el_alta_de_proyecto_no_pide_titulo():
    body = s.CreateProjectRequest(
        customer_id="c1",
        descripcion_detallada="Portal de clientes con facturación y reportes mensuales.",
        monto_total=150000,
        contacto_nombre="Ana Reyes",
    )
    assert body.titulo is None


def test_sin_titulo_el_titulo_sale_de_los_detalles():
    detalles = "  Portal de clientes para la empresa ACME con acceso restringido  "
    assert (
        ventas._titulo_desde_detalles(detalles)
        == "Portal de clientes para la empresa ACME con acceso restringido"
    )
    assert len(ventas._titulo_desde_detalles("x" * 200)) == 80


def test_el_alta_de_cliente_exige_todos_los_datos():
    body = dict(
        nombre="ACME S.A.",
        representante="Ana Reyes",
        documento="1-3123456-7",
        telefono="809-555-0001",
        direccion="Av. Principal 1",
    )
    assert s.CreateCustomerRequest(**body).direccion == "Av. Principal 1"
    # Sin dirección el alta no pasa: el cliente obliga a completar el formulario.
    with pytest.raises(ValidationError):
        s.CreateCustomerRequest(**{**body, "direccion": ""})
