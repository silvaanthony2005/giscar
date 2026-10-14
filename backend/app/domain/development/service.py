"""Servicio de Desarrollo. Funciones puras sobre el plan, fases y avance."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import date, datetime

from app.domain.development.model import (
    Cancellation,
    DevPlan,
    EstadoFase,
    Phase,
    ProgressUpdate,
)
from app.domain.shared.functions import sum_by
from app.domain.shared.types import DomainError, Err, Ok, Result


def create_plan(
    *,
    id: str,
    project_id: str,
    resumen: str,
    objetivos: str,
    horas_estimadas: int,
    created_by: str,
    now: datetime,
) -> Result[DevPlan, DomainError]:
    if not resumen.strip():
        return Err(DomainError("plan.resumen_vacio", "El resumen del plan es obligatorio"))
    if horas_estimadas <= 0:
        return Err(DomainError("plan.horas_invalidas", "Las horas estimadas deben ser > 0"))
    return Ok(
        DevPlan(
            id=id,
            project_id=project_id,
            resumen=resumen.strip(),
            objetivos=objetivos.strip(),
            horas_estimadas=horas_estimadas,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
    )


def create_phase(
    *,
    id: str,
    plan_id: str,
    orden: int,
    nombre: str,
    descripcion: str,
    horas_estimadas: int,
    fecha_inicio: date | None = None,
    fecha_fin_estimada: date | None = None,
) -> Result[Phase, DomainError]:
    if not nombre.strip():
        return Err(DomainError("fase.nombre_vacia", "La fase necesita un nombre"))
    if orden < 1:
        return Err(DomainError("fase.orden_invalido", "El orden debe ser >= 1"))
    if horas_estimadas < 0:
        return Err(DomainError("fase.horas_invalidas", "Horas inválidas"))
    if fecha_inicio and fecha_fin_estimada and fecha_fin_estimada < fecha_inicio:
        return Err(
            DomainError("fase.fechas_invalidas", "La fecha fin no puede ser anterior al inicio")
        )
    return Ok(
        Phase(
            id=id,
            plan_id=plan_id,
            orden=orden,
            nombre=nombre.strip(),
            descripcion=descripcion.strip(),
            fecha_inicio=fecha_inicio,
            fecha_fin_estimada=fecha_fin_estimada,
            fecha_fin_real=None,
            horas_estimadas=horas_estimadas,
            horas_reales=0,
            estado=EstadoFase.PENDIENTE.value,
        )
    )


def set_phase_state(
    phase: Phase, target: str, *, now: datetime | None = None
) -> Result[Phase, DomainError]:
    valid = {e.value for e in EstadoFase}
    if target not in valid:
        return Err(DomainError("fase.estado_invalido", f"Estado inválido: {target}"))
    allowed = {
        EstadoFase.PENDIENTE.value: {EstadoFase.EN_CURSO.value},
        EstadoFase.EN_CURSO.value: {EstadoFase.COMPLETADA.value},
        EstadoFase.COMPLETADA.value: set(),
    }
    if target not in allowed[phase.estado]:
        return Err(
            DomainError(
                "fase.transicion_invalida",
                f"Transición no permitida: {phase.estado} → {target}",
            )
        )
    fecha_fin_real = phase.fecha_fin_real
    if target == EstadoFase.COMPLETADA.value and now is not None:
        fecha_fin_real = now.date()
    return Ok(
        replace(
            phase,
            estado=target,
            fecha_fin_real=fecha_fin_real,
        )
    )


def update_phase_progress(
    phase: Phase, *, horas_reales: int, fecha_fin_real: date | None
) -> Result[Phase, DomainError]:
    if horas_reales < 0:
        return Err(DomainError("fase.horas_invalidas", "Horas reales inválidas"))
    return Ok(replace(phase, horas_reales=horas_reales, fecha_fin_real=fecha_fin_real))


def record_progress(
    *,
    id: str,
    project_id: str,
    phase_id: str | None,
    user_id: str,
    porcentaje: int,
    notas: str,
    fecha: datetime,
) -> Result[ProgressUpdate, DomainError]:
    if porcentaje < 0 or porcentaje > 100:
        return Err(DomainError("avance.rango_invalido", "El porcentaje debe estar entre 0 y 100"))
    if not notas.strip():
        return Err(DomainError("avance.notas_vacias", "Describe el avance realizado"))
    return Ok(
        ProgressUpdate(
            id=id,
            project_id=project_id,
            phase_id=phase_id,
            user_id=user_id,
            porcentaje=porcentaje,
            notas=notas.strip(),
            fecha=fecha,
        )
    )


def create_cancellation(
    *,
    id: str,
    project_id: str,
    motivo: str,
    informe: str,
    cancelado_por: str,
    fecha: datetime,
) -> Result[Cancellation, DomainError]:
    if not motivo.strip():
        return Err(DomainError("cancelacion.motivo_vacio", "Debe indicar el motivo de cancelación"))
    if len(informe.strip()) < 30:
        return Err(
            DomainError(
                "cancelacion.informe_corto",
                "El informe de cancelación debe detallar el porqué (mínimo 30 caracteres)",
            )
        )
    return Ok(
        Cancellation(
            id=id,
            project_id=project_id,
            motivo=motivo.strip(),
            informe=informe.strip(),
            cancelado_por=cancelado_por,
            fecha=fecha,
        )
    )


def plan_horas_por_fases(phases: list[Phase]) -> int:
    """Suma pura de horas estimadas de las fases (reduce/sum_by)."""
    return int(sum_by(lambda p: p.horas_estimadas)(phases))


def acciones_fase(phase: Phase) -> tuple[str, ...]:
    """Estados destino válidos para la fase según su estado actual."""
    allowed = {
        EstadoFase.PENDIENTE.value: (EstadoFase.EN_CURSO.value,),
        EstadoFase.EN_CURSO.value: (EstadoFase.COMPLETADA.value,),
        EstadoFase.COMPLETADA.value: (),
    }
    return allowed.get(phase.estado, ())


def fases_pendientes(fases: Sequence[Phase]) -> bool:
    """True si queda alguna fase sin completar (regla del dominio)."""
    return any(f.estado != EstadoFase.COMPLETADA.value for f in fases)


def error_fases_pendientes(fases: Sequence[Phase]) -> str | None:
    """Mensaje de error si no se puede completar el proyecto por fases abiertas."""
    pendientes = [f.nombre for f in fases if f.estado != EstadoFase.COMPLETADA.value]
    if pendientes:
        return f"Fases pendientes: {', '.join(pendientes)}"
    return None
