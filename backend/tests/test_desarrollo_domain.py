from datetime import UTC, date, datetime

from app.domain.development import service as dev_service
from app.domain.development.model import EstadoFase, Phase

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _plan(**kw):
    defaults = dict(
        id="pl1", project_id="p1", resumen="Plan del proyecto", objetivos="Entregar a tiempo",
        horas_estimadas=100, created_by="u1", now=NOW,
    )
    defaults.update(kw)
    r = dev_service.create_plan(**defaults)
    assert r.is_ok(), r
    return r.unwrap()  # type: ignore[union-attr]


def _phase(**kw) -> Phase:
    defaults = dict(
        id="f1", plan_id="pl1", orden=1, nombre="Diseño", descripcion="UI",
        horas_estimadas=40, fecha_inicio=None, fecha_fin_estimada=None,
    )
    defaults.update(kw)
    r = dev_service.create_phase(**defaults)
    assert r.is_ok(), r
    return r.unwrap()  # type: ignore[union-attr]


# --- plan ---


def test_create_plan_ok():
    assert _plan().horas_estimadas == 100


def test_plan_rechaza_resumen_vacio():
    r = dev_service.create_plan(
        id="x", project_id="p", resumen="  ", objetivos="", horas_estimadas=10,
        created_by="u", now=NOW,
    )
    assert not r.is_ok()


def test_plan_rechaza_horas_cero():
    r = dev_service.create_plan(
        id="x", project_id="p", resumen="ok", objetivos="", horas_estimadas=0,
        created_by="u", now=NOW,
    )
    assert not r.is_ok()


# --- fases ---


def test_create_phase_ok():
    assert _phase().estado == EstadoFase.PENDIENTE.value


def test_fase_fechas_invalidas():
    r = dev_service.create_phase(
        id="f", plan_id="p", orden=1, nombre="X", descripcion="", horas_estimadas=10,
        fecha_inicio=date(2026, 5, 1), fecha_fin_estimada=date(2026, 4, 1),
    )
    assert not r.is_ok()
    assert r.error.code == "fase.fechas_invalidas"  # type: ignore[union-attr]


def test_fase_transicion_correcta():
    f = _phase()
    en_curso = dev_service.set_phase_state(f, "en_curso", now=NOW).unwrap()  # type: ignore[union-attr]
    assert en_curso.estado == "en_curso"
    completada = dev_service.set_phase_state(en_curso, "completada", now=NOW).unwrap()  # type: ignore[union-attr]
    assert completada.estado == "completada"
    assert completada.fecha_fin_real == NOW.date()


def test_fase_transicion_saltando_falla():
    f = _phase()
    assert not dev_service.set_phase_state(f, "completada", now=NOW).is_ok()


def test_fase_no_reabre():
    f = _phase()
    en_curso = dev_service.set_phase_state(f, "en_curso", now=NOW).unwrap()  # type: ignore[union-attr]
    completada = dev_service.set_phase_state(en_curso, "completada", now=NOW).unwrap()  # type: ignore[union-attr]
    assert not dev_service.set_phase_state(completada, "en_curso", now=NOW).is_ok()


def test_fase_inmutable():
    f = _phase()
    dev_service.set_phase_state(f, "en_curso", now=NOW)
    assert f.estado == EstadoFase.PENDIENTE.value


# --- avance ---


def test_record_progress_rango():
    ok = dev_service.record_progress(
        id="a", project_id="p", phase_id=None, user_id="u", porcentaje=50,
        notas="media etapa", fecha=NOW,
    )
    assert ok.is_ok()
    assert not dev_service.record_progress(
        id="a", project_id="p", phase_id=None, user_id="u", porcentaje=101,
        notas="x", fecha=NOW,
    ).is_ok()
    assert not dev_service.record_progress(
        id="a", project_id="p", phase_id=None, user_id="u", porcentaje=50,
        notas="   ", fecha=NOW,
    ).is_ok()


# --- cancelación ---


def test_cancelacion_requiere_informe_largo():
    r = dev_service.create_cancellation(
        id="c", project_id="p", motivo="tiempo", informe="corto", cancelado_por="u", fecha=NOW,
    )
    assert not r.is_ok()


def test_cancelacion_ok():
    r = dev_service.create_cancellation(
        id="c", project_id="p", motivo="tiempo",
        informe="El proyecto excede el tiempo estimado por complejidad no prevista.",
        cancelado_por="u", fecha=NOW,
    )
    assert r.is_ok()


def test_suma_horas_fases():
    fases = [_phase(orden=1, horas_estimadas=40), _phase(orden=2, horas_estimadas=60)]
    assert dev_service.plan_horas_por_fases(fases) == 100
