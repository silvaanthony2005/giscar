"""Tests de las columnas de los tableros de Desarrollo y Despacho.

Funciones puras: sin BD, sin I/O. Mismo estado -> misma agrupación.
"""

from datetime import UTC, datetime
from itertools import chain

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


def _estado(p: Project, ventas=None, desarrollo=None, despacho=None) -> Project:
    from dataclasses import replace

    return replace(
        p,
        estado_ventas=ventas or p.estado_ventas,
        estado_desarrollo=desarrollo or p.estado_desarrollo,
        estado_despacho=despacho or p.estado_despacho,
    )


# --- Desarrollo ---


def test_desarrollo_excluye_lo_que_aun_no_llego():
    """Un proyecto en Ventas (sin enviar) no aparece en ninguna columna."""
    en_ventas = _estado(_project(), ventas="cobrado_50", desarrollo="pendiente")
    grupos = project_service.agrupar_desarrollo([en_ventas])
    assert all(len(v) == 0 for v in grupos.values())


def test_desarrollo_pendiente_va_a_recibidos():
    p = _estado(_project(), ventas="enviado_desarrollo", desarrollo="pendiente")
    grupos = project_service.agrupar_desarrollo([p])
    assert [x.id for x in grupos["recibidos"]] == ["p1"]
    assert grupos["en_curso"] == () and grupos["historial"] == ()


def test_desarrollo_en_planificacion_y_en_desarrollo_va_a_en_curso():
    for estado in ("en_planificacion", "en_desarrollo"):
        p = _estado(_project(), ventas="enviado_desarrollo", desarrollo=estado)
        grupos = project_service.agrupar_desarrollo([p])
        assert [x.id for x in grupos["en_curso"]] == ["p1"], estado
        assert grupos["recibidos"] == () and grupos["historial"] == ()


def test_desarrollo_finalizados_va_a_historial():
    for estado in ("completado", "cancelado", "enviado_despacho"):
        p = _estado(_project(), ventas="enviado_desarrollo", desarrollo=estado)
        grupos = project_service.agrupar_desarrollo([p])
        assert [x.id for x in grupos["historial"]] == ["p1"], estado


def test_desarrollo_cada_proyecto_cae_en_una_sola_columna():
    proyectos = [
        _estado(_project(id=f"p{i}"), ventas="enviado_desarrollo", desarrollo=des)
        for i, des in enumerate(
            ("pendiente", "en_planificacion", "en_desarrollo", "completado", "cancelado", "enviado_despacho")
        )
    ]
    grupos = project_service.agrupar_desarrollo(proyectos)
    vistos = list(chain.from_iterable(grupos.values()))
    assert len(vistos) == len(proyectos)
    assert len({x.id for x in vistos}) == len(proyectos)


# --- Despacho ---


def test_despacho_abiertos_va_a_pendientes():
    for estado in ("pendiente", "pendiente_entrega"):
        p = _estado(_project(), desarrollo="enviado_despacho", despacho=estado)
        grupos = project_service.agrupar_despacho([p])
        assert [x.id for x in grupos["pendientes"]] == ["p1"], estado
        assert grupos["cerrados"] == ()


def test_despacho_resueltos_va_a_cerrados():
    for estado in ("entregado", "negado"):
        p = _estado(_project(), desarrollo="enviado_despacho", despacho=estado)
        grupos = project_service.agrupar_despacho([p])
        assert [x.id for x in grupos["cerrados"]] == ["p1"], estado
        assert grupos["pendientes"] == ()


def test_despacho_reparte_la_colacion_completa():
    abiertos = _estado(_project(id="a"), despacho="pendiente_entrega")
    cerrados = _estado(_project(id="b"), despacho="entregado")
    grupos = project_service.agrupar_despacho([abiertos, cerrados])
    assert [x.id for x in grupos["pendientes"]] == ["a"]
    assert [x.id for x in grupos["cerrados"]] == ["b"]


# --- Contadores del sidebar ---


def test_ventas_cuenta_lo_que_aun_no_se_envio():
    enviado = _estado(_project(id="a"), ventas="enviado_desarrollo")
    en_venta = _estado(_project(id="b"), ventas="cobrado_50")
    assert project_service.pendientes_ventas([enviado, en_venta]) == 1


def test_ventas_no_cuenta_la_venta_liquidada_en_despacho():
    cerrado = _estado(_project(id="a"), ventas="cerrado")
    en_venta = _estado(_project(id="b"), ventas="cobrado_50")
    assert project_service.pendientes_ventas([cerrado, en_venta]) == 1


def test_venta_cerrada_sigue_visible_en_el_historial_de_desarrollo():
    liquidado = _estado(_project(id="a"), ventas="cerrado", desarrollo="enviado_despacho")
    grupos = project_service.agrupar_desarrollo([liquidado])
    assert [x.id for x in grupos["historial"]] == ["a"]


def test_desarrollo_cuenta_recibidos_y_en_curso_pero_no_historial():
    recibido = _estado(_project(id="a"), ventas="enviado_desarrollo", desarrollo="pendiente")
    en_curso = _estado(_project(id="b"), ventas="enviado_desarrollo", desarrollo="en_desarrollo")
    historial = _estado(_project(id="c"), ventas="enviado_desarrollo", desarrollo="completado")
    cancelado = _estado(_project(id="d"), ventas="enviado_desarrollo", desarrollo="cancelado")
    sin_llegar = _estado(_project(id="e"), ventas="cobrado_50", desarrollo="pendiente")
    activos = [recibido, en_curso, historial, cancelado, sin_llegar]
    assert project_service.activos_desarrollo(activos) == 2


def test_despacho_cuenta_pendientes_y_no_los_cerrados():
    abiertos = _estado(_project(id="a"), desarrollo="enviado_despacho", despacho="pendiente_entrega")
    entregado = _estado(_project(id="b"), desarrollo="enviado_despacho", despacho="entregado")
    negado = _estado(_project(id="c"), desarrollo="enviado_despacho", despacho="negado")
    assert project_service.pendientes_despacho([abiertos, entregado, negado]) == 1
