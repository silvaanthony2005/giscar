"""Mapeos fila <-> dominio de Desarrollo. Puros."""

from __future__ import annotations

from app.domain.attachment.model import Attachment
from app.domain.development.model import (
    Cancellation,
    DevPlan,
    Phase,
    ProgressUpdate,
    ProjectMember,
)
from app.infrastructure.db.models_desarrollo import (
    AttachmentRow,
    CancellationRow,
    DevPlanRow,
    PhaseRow,
    ProgressUpdateRow,
    ProjectMemberRow,
)


def plan_to_domain(r: DevPlanRow) -> DevPlan:
    return DevPlan(
        id=r.id, project_id=r.project_id, resumen=r.resumen, objetivos=r.objetivos,
        horas_estimadas=r.horas_estimadas, created_by=r.created_by,
        created_at=r.created_at, updated_at=r.updated_at,
    )


def apply_plan(p: DevPlan, r: DevPlanRow) -> DevPlanRow:
    r.resumen = p.resumen
    r.objetivos = p.objetivos
    r.horas_estimadas = p.horas_estimadas
    r.created_by = p.created_by
    r.created_at = p.created_at
    r.updated_at = p.updated_at
    return r


def phase_to_domain(r: PhaseRow) -> Phase:
    return Phase(
        id=r.id, plan_id=r.plan_id, orden=r.orden, nombre=r.nombre,
        descripcion=r.descripcion, fecha_inicio=r.fecha_inicio,
        fecha_fin_estimada=r.fecha_fin_estimada, fecha_fin_real=r.fecha_fin_real,
        horas_estimadas=r.horas_estimadas, horas_reales=r.horas_reales, estado=r.estado,
    )


def apply_phase(p: Phase, r: PhaseRow) -> PhaseRow:
    r.orden = p.orden
    r.nombre = p.nombre
    r.descripcion = p.descripcion
    r.fecha_inicio = p.fecha_inicio
    r.fecha_fin_estimada = p.fecha_fin_estimada
    r.fecha_fin_real = p.fecha_fin_real
    r.horas_estimadas = p.horas_estimadas
    r.horas_reales = p.horas_reales
    r.estado = p.estado
    return r


def member_to_domain(r: ProjectMemberRow) -> ProjectMember:
    return ProjectMember(
        id=r.id, project_id=r.project_id, user_id=r.user_id,
        rol_proyecto=r.rol_proyecto, fecha_asignacion=r.fecha_asignacion,
    )


def progress_to_domain(r: ProgressUpdateRow) -> ProgressUpdate:
    return ProgressUpdate(
        id=r.id, project_id=r.project_id, phase_id=r.phase_id, user_id=r.user_id,
        porcentaje=r.porcentaje, notas=r.notas, fecha=r.fecha,
    )


def cancellation_to_domain(r: CancellationRow) -> Cancellation:
    return Cancellation(
        id=r.id, project_id=r.project_id, motivo=r.motivo, informe=r.informe,
        cancelado_por=r.cancelado_por, fecha=r.fecha,
    )


def apply_cancellation(c: Cancellation, r: CancellationRow) -> CancellationRow:
    r.motivo = c.motivo
    r.informe = c.informe
    r.cancelado_por = c.cancelado_por
    r.fecha = c.fecha
    return r


def attachment_to_domain(r: AttachmentRow) -> Attachment:
    return Attachment(
        id=r.id, entidad_tipo=r.entidad_tipo, entidad_id=r.entidad_id, nombre=r.nombre,
        ruta=r.ruta, mime=r.mime, tamano=r.tamano, subido_por=r.subido_por, fecha=r.fecha,
    )
