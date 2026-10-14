"""Modelos SQLAlchemy de Despacho e Incidencias."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models import new_id, utcnow
from app.infrastructure.db.session import Base


class DispatchRow(Base):
    __tablename__ = "dispatches"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(String(32), ForeignKey("projects.id"), index=True)
    fecha_entrega: Mapped[date | None] = mapped_column(Date, nullable=True)
    hora_entrega: Mapped[str | None] = mapped_column(String(10), nullable=True)
    destinatario: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detalle_entregado: Mapped[str | None] = mapped_column(Text, nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmado_por: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"))
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DenialRow(Base):
    __tablename__ = "denials"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(String(32), ForeignKey("projects.id"), index=True)
    motivo: Mapped[str] = mapped_column(String(255))
    detalle: Mapped[str] = mapped_column(Text)
    registrado_por: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IncidentRow(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    titulo: Mapped[str] = mapped_column(String(255))
    descripcion: Mapped[str] = mapped_column(Text)
    equipo_afectado: Mapped[str] = mapped_column(String(255))
    departamento_origen: Mapped[str] = mapped_column(String(20))
    prioridad: Mapped[str] = mapped_column(String(20))
    estado: Mapped[str] = mapped_column(String(20), default="abierta")
    orden_llegada: Mapped[int] = mapped_column(Integer)
    reportado_por: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"))
    asignado_a: Mapped[str | None] = mapped_column(String(32), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IncidentReportRow(Base):
    __tablename__ = "incident_reports"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    incident_id: Mapped[str] = mapped_column(String(32), ForeignKey("incidents.id"), index=True)
    diagnostico: Mapped[str] = mapped_column(Text)
    solucion: Mapped[str] = mapped_column(Text)
    tiempo_resolucion_horas: Mapped[int] = mapped_column(Integer)
    resuelto_por: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
