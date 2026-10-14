"""Tests de las acciones disponibles que el backend expone al frontend.

Son funciones puras: mismo estado -> mismas acciones, sin BD ni I/O.
"""

from datetime import UTC, datetime

from app.domain.development import service as dev_service
from app.domain.development.model import Phase
from app.domain.project import service as project_service
from app.domain.project.model import Project
from app.domain.shared.money import Money

NOW = datetime(2026, 1, 1, tzinfo=UTC)
TOTAL = 100000


def _project(**kw) -> Project:
    defaults = dict(
        id="p1",
        codigo="PRJ-2026-0001",
        titulo="Sistema de inventario",
        descripcion_detallada="Desarrollo de un sistema completo de inventario con reportes.",
        customer_id="c1",
        monto_total=Money.from_amount(TOTAL),
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


def _estado(p: Project, ventas=None, desarrollo=None, despacho=None) -> Project:
    from dataclasses import replace

    return replace(
        p,
        estado_ventas=ventas or p.estado_ventas,
        estado_desarrollo=desarrollo or p.estado_desarrollo,
        estado_despacho=despacho or p.estado_despacho,
    )


# --- Ventas ---


def test_ventas_sin_pago_solo_permite_registrar_pago():
    assert project_service.acciones_ventas(_project(), Money(0)) == ("registrar_pago",)


def test_ventas_con_50_por_ciento_puede_pasar_a_desarrollo():
    """Con el 50% cobrado el estado ya es cobrado_50 y habilita el paso."""
    p = _estado(_project(), ventas="cobrado_50")
    pagado = Money.from_amount(TOTAL // 2)
    assert project_service.acciones_ventas(p, pagado) == (
        "registrar_pago",
        "pasar_desarrollo",
    )


def test_ventas_pagado_total_no_ofrece_pago():
    p = _estado(_project(), ventas="cobrado_100")
    pagado = Money.from_amount(TOTAL)
    assert project_service.acciones_ventas(p, pagado) == ("pasar_desarrollo",)


def test_ventas_parcial_insuficiente_no_ofrece_pasar_a_desarrollo():
    """Un cobro menor al 50% queda en cobrado_50 pero no habilita Desarrollo."""
    p = _estado(_project(), ventas="cobrado_50")
    pagado = Money.from_amount(TOTAL // 10)
    assert project_service.acciones_ventas(p, pagado) == ("registrar_pago",)


def test_ventas_ya_enviada_no_tiene_acciones():
    p = _estado(_project(), ventas="enviado_desarrollo")
    assert project_service.acciones_ventas(p, Money.from_amount(TOTAL)) == ()


def test_ventas_desde_levantamiento_no_puede_pasar_directo_a_desarrollo():
    """Desde 'levantamiento' no hay arista hacia enviado_desarrollo (hay que cobrar)."""
    assert project_service.acciones_ventas(_project(), Money.from_amount(TOTAL)) == ()


# --- Desarrollo ---


def test_desarrollo_fuera_del_departamento_no_tiene_acciones():
    p = _estado(_project(), ventas="levantamiento")
    assert project_service.acciones_desarrollo(p) == ()


def test_desarrollo_pendiente_ofrece_crear_plan():
    p = _estado(_project(), ventas="enviado_desarrollo")
    assert project_service.acciones_desarrollo(p) == ("crear_plan", "cancelar")


def test_desarrollo_en_desarrollo_ofrece_completar():
    p = _estado(_project(), ventas="enviado_desarrollo", desarrollo="en_desarrollo")
    assert project_service.acciones_desarrollo(p) == ("completar", "cancelar")


def test_desarrollo_oculta_completar_si_hay_fases_pendientes():
    p = _estado(_project(), ventas="enviado_desarrollo", desarrollo="en_desarrollo")
    assert project_service.acciones_desarrollo(p, fases_pendientes=True) == ("cancelar",)


def test_desarrollo_completado_ofrece_pasar_a_despacho():
    p = _estado(_project(), ventas="enviado_desarrollo", desarrollo="completado")
    assert project_service.acciones_desarrollo(p) == ("pasar_despacho",)


def test_desarrollo_cancelado_no_tiene_acciones():
    p = _estado(_project(), ventas="enviado_desarrollo", desarrollo="cancelado")
    assert project_service.acciones_desarrollo(p) == ()


# --- Despacho ---


def test_despacho_antes_de_llegar_no_tiene_acciones():
    p = _estado(_project(), ventas="enviado_desarrollo", desarrollo="en_desarrollo")
    assert project_service.acciones_despacho(p, Money(0)) == ()


def test_despacho_con_saldo_ofrece_liquidar():
    p = _estado(
        _project(), ventas="enviado_desarrollo", desarrollo="enviado_despacho",
        despacho="pendiente_entrega",
    )
    assert project_service.acciones_despacho(p, Money(0)) == ("liquidar", "negar")


def test_despacho_sin_saldo_ofrece_entregar():
    p = _estado(
        _project(), ventas="enviado_desarrollo", desarrollo="enviado_despacho",
        despacho="pendiente_entrega",
    )
    assert project_service.acciones_despacho(p, Money.from_amount(TOTAL)) == (
        "confirmar_entrega",
        "negar",
    )


def test_despacho_negado_ofrece_resolver():
    p = _estado(
        _project(), ventas="enviado_desarrollo", desarrollo="enviado_despacho",
        despacho="negado",
    )
    assert "resolver_negacion" in project_service.acciones_despacho(p, Money.from_amount(TOTAL))


def test_despacho_entregado_no_tiene_acciones():
    p = _estado(
        _project(), ventas="enviado_desarrollo", desarrollo="enviado_despacho",
        despacho="entregado",
    )
    assert project_service.acciones_despacho(p, Money(0)) == ()


# --- Fases ---


def _phase(estado: str) -> Phase:
    return Phase(
        id="f1", plan_id="pl1", orden=1, nombre="Fase 1", descripcion="d",
        fecha_inicio=None, fecha_fin_estimada=None, fecha_fin_real=None,
        horas_estimadas=10, horas_reales=0, estado=estado,
    )


def test_acciones_fase_pendiente_solo_inicia():
    assert dev_service.acciones_fase(_phase("pendiente")) == ("en_curso",)


def test_acciones_fase_en_curso_solo_completa():
    assert dev_service.acciones_fase(_phase("en_curso")) == ("completada",)


def test_acciones_fase_completada_no_tiene_acciones():
    assert dev_service.acciones_fase(_phase("completada")) == ()


def test_fases_pendientes_detecta_fases_abiertas():
    assert dev_service.fases_pendientes([_phase("en_curso")]) is True
    assert dev_service.fases_pendientes([_phase("completada")]) is False
    assert dev_service.fases_pendientes([]) is False


def test_error_fases_pendientes_nomina_las_fases():
    msg = dev_service.error_fases_pendientes([_phase("pendiente"), _phase("completada")])
    assert msg is not None and "Fase 1" in msg
    assert dev_service.error_fases_pendientes([_phase("completada")]) is None
