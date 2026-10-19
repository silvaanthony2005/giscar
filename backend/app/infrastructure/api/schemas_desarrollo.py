"""Esquemas de Desarrollo y adjuntos."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class CreatePlanRequest(BaseModel):
    resumen: str = Field(min_length=1)
    objetivos: str = ""
    horas_estimadas: int = Field(gt=0)


class PhaseIn(BaseModel):
    orden: int = Field(ge=1)
    nombre: str = Field(min_length=1)
    descripcion: str = ""
    horas_estimadas: int = Field(ge=0, default=0)
    fecha_inicio: date | None = None
    fecha_fin_estimada: date | None = None


class CreatePlanWithPhasesRequest(BaseModel):
    resumen: str = Field(min_length=1)
    objetivos: str = ""
    horas_estimadas: int = Field(gt=0)
    fases: list[PhaseIn] = Field(default_factory=list)
    miembros: list[str] = Field(default_factory=list)


class PlanOut(BaseModel):
    id: str
    project_id: str
    resumen: str
    objetivos: str
    horas_estimadas: int
    created_at: datetime


class PhaseOut(BaseModel):
    id: str
    orden: int
    nombre: str
    descripcion: str
    fecha_inicio: date | None
    fecha_fin_estimada: date | None
    fecha_fin_real: date | None
    horas_estimadas: int
    horas_reales: int
    estado: str
    acciones: tuple[str, ...] = ()


class MemberOut(BaseModel):
    id: str
    user_id: str
    nombre_usuario: str
    rol_proyecto: str
    fecha_asignacion: datetime


class AddMembersRequest(BaseModel):
    user_ids: list[str] = Field(min_length=1)


class CatalogoUsuarioOut(BaseModel):
    id: str
    nombre: str
    departamento: str


class ProgressIn(BaseModel):
    porcentaje: int = Field(ge=0, le=100)
    notas: str = Field(min_length=1)
    phase_id: str | None = None


class ProgressOut(BaseModel):
    id: str
    phase_id: str | None
    porcentaje: int
    notas: str
    fecha: datetime
    autor: str


class CancellationIn(BaseModel):
    motivo: str = Field(min_length=1)
    informe: str = Field(min_length=30)


class CancellationOut(BaseModel):
    id: str
    project_id: str
    motivo: str
    informe: str
    fecha: datetime


class PhaseStateRequest(BaseModel):
    target: str


class AttachmentOut(BaseModel):
    id: str
    entidad_tipo: str
    entidad_id: str
    nombre: str
    mime: str
    tamano: int
    fecha: datetime
