"""Modelos SQLAlchemy de Desarrollo y adjuntos."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models import new_id, utcnow
from app.infrastructure.db.session import Base


class DevPlanRow(Base):
    __tablename__ = "dev_plans"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(String(32), ForeignKey("projects.id"), index=True)
    resumen: Mapped[str] = mapped_column(Text)
    objetivos: Mapped[str] = mapped_column(Text)
    horas_estimadas: Mapped[int] = mapped_column(Integer)
    created_by: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PhaseRow(Base):
    __tablename__ = "dev_phases"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    plan_id: Mapped[str] = mapped_column(String(32), ForeignKey("dev_plans.id"), index=True)
    orden: Mapped[int] = mapped_column(Integer)
    nombre: Mapped[str] = mapped_column(String(255))
    descripcion: Mapped[str] = mapped_column(Text)
    fecha_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_fin_estimada: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_fin_real: Mapped[date | None] = mapped_column(Date, nullable=True)
    horas_estimadas: Mapped[int] = mapped_column(Integer, default=0)
    horas_reales: Mapped[int] = mapped_column(Integer, default=0)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")


class ProjectMemberRow(Base):
    __tablename__ = "project_members"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(String(32), ForeignKey("projects.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"), index=True)
    rol_proyecto: Mapped[str] = mapped_column(String(100))
    fecha_asignacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProgressUpdateRow(Base):
    __tablename__ = "progress_updates"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(String(32), ForeignKey("projects.id"), index=True)
    phase_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("dev_phases.id"), nullable=True
    )
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"))
    porcentaje: Mapped[int] = mapped_column(Integer)
    notas: Mapped[str] = mapped_column(Text)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CancellationRow(Base):
    __tablename__ = "cancellations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(String(32), ForeignKey("projects.id"), index=True)
    motivo: Mapped[str] = mapped_column(String(255))
    informe: Mapped[str] = mapped_column(Text)
    cancelado_por: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AttachmentRow(Base):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    entidad_tipo: Mapped[str] = mapped_column(String(20), index=True)
    entidad_id: Mapped[str] = mapped_column(String(32), index=True)
    nombre: Mapped[str] = mapped_column(String(255))
    ruta: Mapped[str] = mapped_column(String(500))
    mime: Mapped[str] = mapped_column(String(100))
    tamano: Mapped[int] = mapped_column(Integer)
    subido_por: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
