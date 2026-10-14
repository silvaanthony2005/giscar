"""Modelo de Incidencia (Tecnología). Cola por llegada + prioridad."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Prioridad(StrEnum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class EstadoIncidencia(StrEnum):
    ABIERTA = "abierta"
    EN_PROCESO = "en_proceso"
    RESUELTA = "resuelta"
    CERRADA = "cerrada"


@dataclass(frozen=True, slots=True)
class Incidence:
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
    asignado_a: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class IncidentReport:
    id: str
    incident_id: str
    diagnostico: str
    solucion: str
    tiempo_resolucion_horas: int
    resuelto_por: str
    fecha: datetime
