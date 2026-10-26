"""Mapeos fila <-> dominio de Despacho e Incidencias. Puros."""

from __future__ import annotations

from app.domain.dispatch.model import Denial, Dispatch
from app.domain.incidence.model import Incidence, IncidentReport
from app.infrastructure.db.models_despacho import (
    DenialRow,
    DispatchRow,
    IncidentAssigneeRow,
    IncidentReportRow,
    IncidentRow,
)


def dispatch_to_domain(r: DispatchRow) -> Dispatch:
    return Dispatch(
        id=r.id, project_id=r.project_id, fecha_entrega=r.fecha_entrega,
        hora_entrega=r.hora_entrega, destinatario=r.destinatario,
        detalle_entregado=r.detalle_entregado, notas=r.notas,
        confirmado_por=r.confirmado_por, fecha_registro=r.fecha_registro,
    )


def apply_dispatch(d: Dispatch, r: DispatchRow) -> DispatchRow:
    r.fecha_entrega = d.fecha_entrega
    r.hora_entrega = d.hora_entrega
    r.destinatario = d.destinatario
    r.detalle_entregado = d.detalle_entregado
    r.notas = d.notas
    r.confirmado_por = d.confirmado_por
    r.fecha_registro = d.fecha_registro
    return r


def denial_to_domain(r: DenialRow) -> Denial:
    return Denial(
        id=r.id, project_id=r.project_id, motivo=r.motivo, detalle=r.detalle,
        registrado_por=r.registrado_por, fecha=r.fecha,
    )


def incident_to_domain(r: IncidentRow) -> Incidence:
    return Incidence(
        id=r.id, codigo=r.codigo, titulo=r.titulo, descripcion=r.descripcion,
        equipo_afectado=r.equipo_afectado, departamento_origen=r.departamento_origen,
        prioridad=r.prioridad, estado=r.estado, orden_llegada=r.orden_llegada,
        reportado_por=r.reportado_por, asignados=tuple(a.user_id for a in r.assignees),
        created_at=r.created_at, updated_at=r.updated_at,
    )


def apply_incidence(i: Incidence, r: IncidentRow) -> IncidentRow:
    r.titulo = i.titulo
    r.descripcion = i.descripcion
    r.equipo_afectado = i.equipo_afectado
    r.departamento_origen = i.departamento_origen
    r.prioridad = i.prioridad
    r.estado = i.estado
    r.assignees = [IncidentAssigneeRow(user_id=uid) for uid in i.asignados]
    r.updated_at = i.updated_at
    return r


def report_to_domain(r: IncidentReportRow) -> IncidentReport:
    return IncidentReport(
        id=r.id, incident_id=r.incident_id, diagnostico=r.diagnostico,
        solucion=r.solucion, tiempo_resolucion_horas=r.tiempo_resolucion_horas,
        resuelto_por=r.resuelto_por, fecha=r.fecha,
    )
