"""Campos obligatorios del formulario de cliente (levantamiento de Ventas).

Dominio puro: se llama la función directamente, sin BD ni servidor.
"""

from datetime import UTC, datetime

from app.domain.customer.model import Customer
from app.domain.customer.service import create_customer, puede_eliminar, update_customer

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


# --- edición y borrado ---


def _cliente() -> Customer:
    return create_customer(**ALTA).unwrap()  # type: ignore[union-attr]


def test_editar_cambia_los_datos_y_recorta_espacios():
    r = update_customer(
        _cliente(), nombre="  ACME Dominicana ", representante="Luis Pérez", now=NOW
    )
    assert r.is_ok(), r
    assert (r.unwrap().nombre, r.unwrap().representante) == ("ACME Dominicana", "Luis Pérez")


def test_editar_representante_vacio_se_rechaza():
    assert not update_customer(_cliente(), representante="  ", now=NOW).is_ok()


def test_editar_con_cadena_vacia_borra_el_dato():
    r = update_customer(_cliente(), email="", direccion="   ", now=NOW)
    assert r.is_ok(), r
    assert r.unwrap().email is None and r.unwrap().direccion is None


# --- teléfono: solo números ---


def test_el_telefono_se_guarda_solo_con_digitos():
    r = create_customer(**{**ALTA, "telefono": "+1 (809) 555.0001"})
    assert r.is_ok(), r
    assert r.unwrap().telefono == "18095550001"


def test_el_telefono_con_letras_se_rechaza_en_el_alta():
    r = create_customer(**{**ALTA, "telefono": "809-VENTA"})
    assert not r.is_ok() and r.error.code == "customer.telefono_invalido"


def test_editar_telefono_invalido_se_rechaza_y_el_vacio_lo_borra():
    cliente = _cliente()
    assert not update_customer(cliente, telefono="llamar al gerente", now=NOW).is_ok()
    r = update_customer(cliente, telefono="   ", now=NOW)
    assert r.is_ok() and r.unwrap().telefono is None


def test_no_se_puede_eliminar_un_cliente_con_proyectos():
    r = puede_eliminar(_cliente(), tiene_proyectos=True)
    assert not r.is_ok() and r.error.code == "customer.con_proyectos"


def test_eliminar_un_cliente_sin_proyectos_esta_permitido():
    r = puede_eliminar(_cliente(), tiene_proyectos=False)
    assert r.is_ok() and r.unwrap().id == "c1"
