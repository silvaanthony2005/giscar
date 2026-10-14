from datetime import UTC, datetime

from app.domain.invoice import service as invoice_service
from app.domain.payment import service as payment_service
from app.domain.payment.model import TipoPago
from app.domain.project import service as project_service
from app.domain.project.model import Project
from app.domain.shared.money import Money

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _project(**kw) -> Project:
    defaults = dict(
        id="p1",
        codigo="PRJ-2026-0001",
        titulo="Sistema de inventario",
        descripcion_detallada="Desarrollo de un sistema completo de inventario con reportes.",
        customer_id="c1",
        monto_total=Money.from_amount(100000),
        contacto_nombre="Gerente",
        contacto_telefono="809-555-0001",
        contacto_email=None,
        contacto_direccion=None,
        created_by="u1",
        now=NOW,
    )
    defaults.update(kw)
    r = project_service.create_project(**defaults)
    assert r.is_ok(), r
    return r.unwrap()  # type: ignore[union-attr]


def _payment(monto, total=100000, previo=0, tipo=TipoPago.ANTICIPO):
    return payment_service.create_payment(
        id="pay1",
        project_id="p1",
        monto=Money.from_amount(monto),
        monto_total=Money.from_amount(total),
        pagado_previo=Money.from_amount(previo),
        tipo=tipo,
        metodo_pago="efectivo",
        registrado_por="u1",
        fecha=NOW,
    )


# --- create_project ---


def test_create_project_ok():
    p = _project()
    assert p.estado_ventas == "levantamiento"
    assert p.estado_desarrollo == "pendiente"


def test_create_rechaza_descripcion_corta():
    r = project_service.create_project(
        id="x", codigo="C", titulo="t", descripcion_detallada="corta",
        customer_id="c", monto_total=Money.from_amount(100),
        contacto_nombre="n", contacto_telefono=None, contacto_email=None,
        contacto_direccion=None, created_by="u", now=NOW,
    )
    assert not r.is_ok()


def test_create_rechaza_monto_cero():
    r = project_service.create_project(
        id="x", codigo="C", titulo="t",
        descripcion_detallada="una descripcion lo suficientemente larga aqui",
        customer_id="c", monto_total=Money(0),
        contacto_nombre="n", contacto_telefono=None, contacto_email=None,
        contacto_direccion=None, created_by="u", now=NOW,
    )
    assert not r.is_ok()


# --- transiciones ---


def test_pasar_a_desarrollo_requiere_50pct():
    p = _project()
    # sin pago -> no puede
    assert not project_service.puede_pasar_a_desarrollo(p, Money(0)).is_ok()


def test_pasar_a_desarrollo_con_50():
    p = _project()
    cobrado = project_service.set_estado_ventas(p, "cobrado_50", now=NOW).unwrap()  # type: ignore[union-attr]
    ok = project_service.puede_pasar_a_desarrollo(cobrado, Money.from_amount(50000))
    assert ok.is_ok() and ok.unwrap().estado_ventas == "enviado_desarrollo"  # type: ignore[union-attr]


def test_pasar_a_desarrollo_menos_de_50_falla():
    p = _project()
    cobrado = project_service.set_estado_ventas(p, "cobrado_50", now=NOW).unwrap()  # type: ignore[union-attr]
    assert not project_service.puede_pasar_a_desarrollo(cobrado, Money.from_amount(49999)).is_ok()


def test_pasar_a_despacho_requiere_completado():
    p = _project()
    assert not project_service.puede_pasar_a_despacho(p).is_ok()


def test_transicion_invalida_estado():
    p = _project()
    # desde levantamiento no puede ir directo a entregado en ventas
    assert not project_service.set_estado_ventas(p, "entregado", now=NOW).is_ok()


def test_estados_inmutables():
    p = _project()
    project_service.set_estado_ventas(p, "cobrado_50", now=NOW)
    assert p.estado_ventas == "levantamiento"  # original intacta


# --- pagos ---


def test_pago_valido():
    r = _payment(50000)
    assert r.is_ok()
    assert r.unwrap().porcentaje == 50  # type: ignore[union-attr]


def test_pago_excede_saldo():
    assert not _payment(150000).is_ok()


def test_pago_monto_cero():
    assert not _payment(0).is_ok()


def test_sumar_pagos_reduce():
    pagos = [
        _payment(30000, previo=0).unwrap(),  # type: ignore[union-attr]
        _payment(20000, previo=30000).unwrap(),  # type: ignore[union-attr]
    ]
    total = payment_service.sumar_pagos(pagos)
    assert total.amount == Money.from_amount(50000).amount


def test_saldo_restante():
    assert project_service.saldo_restante(
        Money.from_amount(100000), Money.from_amount(60000)
    ).amount == Money.from_amount(40000).amount


def test_porcentaje_acumulado():
    # tras pagar 50% + 50% el porcentaje es 100
    r = _payment(50000, previo=50000, tipo=TipoPago.LIQUIDACION)
    assert r.is_ok() and r.unwrap().porcentaje == 100  # type: ignore[union-attr]


# --- factura ---


def test_invoice_snapshot():
    p = _project()
    pay = _payment(50000).unwrap()  # type: ignore[union-attr]
    r = invoice_service.create_invoice(
        id="i1", numero="FAC-001", payment=pay, project=p,
        cliente_nombre="Empresa XYZ", emitida_por="u1", emitida_en=NOW,
    )
    assert r.is_ok()
    inv = r.unwrap()  # type: ignore[union-attr]
    assert inv.snapshot.cliente_nombre == "Empresa XYZ"
    assert inv.snapshot.monto_total.cents == p.monto_total.cents
    assert "50%" in inv.descripcion


def test_entregar_requiere_saldo_cero():
    p = _project()
    saldo = Money.from_amount(50000)
    assert not project_service.puede_entregar(p, Money.from_amount(50000), saldo).is_ok()
