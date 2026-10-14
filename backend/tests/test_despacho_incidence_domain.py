from datetime import UTC, date, datetime

from app.domain.dispatch import service as dispatch_service
from app.domain.incidence import service as incidence_service
from app.domain.incidence.model import EstadoIncidencia, Prioridad
from app.domain.project import service as project_service
from app.domain.project.states import DESARROLLO_SM, DESPACHO_SM, VENTAS_SM
from app.domain.shared.money import Money

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _entrega(**kw):
    defaults = dict(
        id="d1", project_id="p1", confirmado_por="u1", fecha_registro=NOW,
        fecha_entrega=date(2026, 3, 1), hora_entrega="10:00", destinatario="Gerente",
        detalle_entregado="Equipo completo", notas=None,
    )
    defaults.update(kw)
    return dispatch_service.confirm_delivery(**defaults)


def _incidencia(**kw):
    defaults = dict(
        id="i1", codigo="INC-2026-0001", titulo="PC no enciende",
        descripcion="El equipo no enciende al presionar el boton de power.",
        equipo_afectado="PC-01", departamento_origen="ventas",
        prioridad=Prioridad.MEDIA.value, orden_llegada=1, reportado_por="u1", now=NOW,
    )
    defaults.update(kw)
    return incidence_service.create_incidence(**defaults)


# --- Despacho: entrega ---


def test_entrega_ok():
    r = _entrega()
    assert r.is_ok()
    assert r.unwrap().destinatario == "Gerente"  # type: ignore[union-attr]


def test_entrega_requiere_destinatario():
    assert not _entrega(destinatario="  ").is_ok()


def test_entrega_requiere_detalle():
    assert not _entrega(detalle_entregado=None).is_ok()


def test_entrega_requiere_fecha():
    assert not _entrega(fecha_entrega=None).is_ok()


# --- Despacho: máquina de estados ---


def test_entregar_requiere_saldo_cero():
    from app.domain.project.model import Project

    p = Project(
        id="p1", codigo="PRJ-1", titulo="t", descripcion_detallada="d" * 25,
        customer_id="c1", monto_total=Money.from_amount(100000),
        contacto_nombre="n", contacto_telefono=None, contacto_email=None,
        contacto_direccion=None, estado_ventas="cobrado_50",
        estado_desarrollo="completado", estado_despacho="pendiente_entrega",
        created_by="u1", created_at=NOW, updated_at=NOW,
    )
    saldo = Money.from_amount(50000)
    assert not project_service.puede_entregar(p, Money.from_amount(50000), saldo).is_ok()
    assert project_service.puede_entregar(p, Money.from_amount(100000), Money(0)).is_ok()


def test_flujo_negado_resolver():
    assert DESPACHO_SM.can_transition("pendiente_entrega", "negado")
    assert DESPACHO_SM.can_transition("negado", "pendiente_entrega")
    assert DESPACHO_SM.can_transition("negado", "entregado")
    assert not DESPACHO_SM.can_transition("pendiente", "entregado")


def test_negacion_ok():
    r = dispatch_service.register_denial(
        id="n1", project_id="p1", motivo="No paga",
        detalle="El cliente rechaza el saldo restante.", registrado_por="u1", fecha=NOW,
    )
    assert r.is_ok()


def test_negacion_detalle_corto():
    assert not dispatch_service.register_denial(
        id="n", project_id="p", motivo="x", detalle="corto", registrado_por="u", fecha=NOW,
    ).is_ok()


# --- Incidencias ---


def test_incidencia_ok():
    r = _incidencia()
    assert r.is_ok()
    assert r.unwrap().estado == EstadoIncidencia.ABIERTA.value  # type: ignore[union-attr]


def test_incidencia_descripcion_corta():
    assert not _incidencia(descripcion="muy corta").is_ok()


def test_incidencia_prioridad_invalida():
    assert not _incidencia(prioridad="urgente").is_ok()


def test_transicion_incidencia():
    inc = _incidencia().unwrap()  # type: ignore[union-attr]
    proceso = incidence_service.transition_incidence(inc, "en_proceso", now=NOW)
    assert proceso.is_ok()
    resuelta = incidence_service.transition_incidence(proceso.unwrap(), "resuelta", now=NOW)  # type: ignore[union-attr]
    assert resuelta.is_ok()
    # no se puede ir de abierta directo a resuelta
    assert not incidence_service.transition_incidence(inc, "resuelta", now=NOW).is_ok()
    # cerrada es terminal
    cerrada = incidence_service.transition_incidence(resuelta.unwrap(), "cerrada", now=NOW)  # type: ignore[union-attr]
    assert cerrada.is_ok()
    assert not incidence_service.transition_incidence(cerrada.unwrap(), "abierta", now=NOW).is_ok()


def test_cola_ordena_por_prioridad_y_llegada():
    a = _incidencia(id="a", codigo="A", prioridad="baja", orden_llegada=1).unwrap()  # type: ignore[union-attr]
    b = _incidencia(id="b", codigo="B", prioridad="critica", orden_llegada=5).unwrap()  # type: ignore[union-attr]
    c = _incidencia(id="c", codigo="C", prioridad="critica", orden_llegada=2).unwrap()  # type: ignore[union-attr]
    cola = incidence_service.ordenar_cola([a, b, c])
    # primero las críticas (por orden de llegada), luego la baja
    assert [i.codigo for i in cola] == ["C", "B", "A"]


def test_cola_no_muta_original():
    a = _incidencia(id="a", codigo="A", prioridad="baja", orden_llegada=1).unwrap()  # type: ignore[union-attr]
    b = _incidencia(id="b", codigo="B", prioridad="critica", orden_llegada=2).unwrap()  # type: ignore[union-attr]
    original = [a, b]
    incidence_service.ordenar_cola(original)
    assert original[0].codigo == "A"  # intacta


def test_contar_por_estado():
    a = _incidencia(id="a", prioridad="baja").unwrap()  # type: ignore[union-attr]
    b = _incidencia(id="b", prioridad="baja").unwrap()  # type: ignore[union-attr]
    conteo = incidence_service.contar_por_estado([a, b])
    assert conteo["abierta"] == 2
    assert conteo["resuelta"] == 0


def test_reporte_validacion():
    ok = incidence_service.create_report(
        id="r", incident_id="i",
        diagnostico="Fuente de poder dañada.", solucion="Se reemplazó la fuente.",
        tiempo_resolucion_horas=2, resuelto_por="u", fecha=NOW,
    )
    assert ok.is_ok()
    assert not incidence_service.create_report(
        id="r", incident_id="i", diagnostico="corto", solucion="corto",
        tiempo_resolucion_horas=2, resuelto_por="u", fecha=NOW,
    ).is_ok()


def test_maquinas_transiciones_basicas():
    assert VENTAS_SM.can_transition("levantamiento", "cobrado_50")
    assert not VENTAS_SM.can_transition("levantamiento", "enviado_desarrollo")
    assert DESARROLLO_SM.can_transition("pendiente", "en_planificacion")
    assert DESARROLLO_SM.can_transition("pendiente", "cancelado")


def test_incidencias_activas_excluye_resueltas_y_cerradas():
    from dataclasses import replace as _replace

    base = _incidencia(id="i1").unwrap()
    abierta = base
    resuelta = _replace(base, estado=EstadoIncidencia.RESUELTA.value)
    cerrada = _replace(base, estado=EstadoIncidencia.CERRADA.value)

    assert incidence_service.incidencias_activas([abierta]) == 1
    assert incidence_service.incidencias_activas([abierta, resuelta]) == 1
    assert incidence_service.incidencias_activas([abierta, resuelta, cerrada]) == 1
    assert incidence_service.incidencias_activas([resuelta, cerrada]) == 0
