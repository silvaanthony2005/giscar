"""Esquemas de Despacho e Incidencias."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

# --- Despacho ---


class DeliveryIn(BaseModel):
    fecha_entrega: date
    hora_entrega: str | None = None
    destinatario: str = Field(min_length=1)
    detalle_entregado: str = Field(min_length=1)
    notas: str | None = None


class DeliveryOut(BaseModel):
    id: str
    project_id: str
    fecha_entrega: date | None
    hora_entrega: str | None
    destinatario: str | None
    detalle_entregado: str | None
    notas: str | None
    fecha_registro: datetime


class DenialIn(BaseModel):
    motivo: str = Field(min_length=1)
    detalle: str = Field(min_length=15)


class DenialOut(BaseModel):
    id: str
    project_id: str
    motivo: str
    detalle: str
    fecha: datetime


class DispatchStateRequest(BaseModel):
    target: str


# --- Incidencias ---


class CreateIncidenceRequest(BaseModel):
    titulo: str = Field(min_length=1, max_length=255)
    descripcion: str = Field(min_length=15)
    equipo_afectado: str = Field(min_length=1)
    prioridad: str = Field(pattern="^(baja|media|alta|critica)$")


class IncidenceOut(BaseModel):
    id: str
    codigo: str
    titulo: str
    descripcion: str
    equipo_afectado: str
    departamento_origen: str
    prioridad: str
    estado: str
    orden_llegada: int
    reportado_por: str
    reportado_por_nombre: str | None = None
    asignado_a: str | None
    asignado_a_nombre: str | None = None
    created_at: datetime


class IncidenceStateRequest(BaseModel):
    target: str


class AssignRequest(BaseModel):
    user_id: str


class IncidentReportIn(BaseModel):
    diagnostico: str = Field(min_length=10)
    solucion: str = Field(min_length=10)
    tiempo_resolucion_horas: int = Field(ge=0)


class IncidentReportOut(BaseModel):
    id: str
    incident_id: str
    diagnostico: str
    solucion: str
    tiempo_resolucion_horas: int
    resuelto_por: str
    resuelto_por_nombre: str | None = None
    fecha: datetime
