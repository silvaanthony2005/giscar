"""Modelos de Desarrollo: plan, fases, miembros y avance. Inmutables."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class EstadoFase(StrEnum):
    PENDIENTE = "pendiente"
    EN_CURSO = "en_curso"
    COMPLETADA = "completada"


@dataclass(frozen=True, slots=True)
class DevPlan:
    id: str
    project_id: str
    resumen: str
    objetivos: str
    horas_estimadas: int
    created_by: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Phase:
    id: str
    plan_id: str
    orden: int
    nombre: str
    descripcion: str
    fecha_inicio: date | None
    fecha_fin_estimada: date | None
    fecha_fin_real: date | None
    horas_estimadas: int
    horas_reales: int
    estado: str


@dataclass(frozen=True, slots=True)
class ProjectMember:
    id: str
    project_id: str
    user_id: str
    rol_proyecto: str
    fecha_asignacion: datetime


@dataclass(frozen=True, slots=True)
class ProgressUpdate:
    id: str
    project_id: str
    phase_id: str | None
    user_id: str
    porcentaje: int
    notas: str
    fecha: datetime


@dataclass(frozen=True, slots=True)
class Cancellation:
    id: str
    project_id: str
    motivo: str
    informe: str
    cancelado_por: str
    fecha: datetime
