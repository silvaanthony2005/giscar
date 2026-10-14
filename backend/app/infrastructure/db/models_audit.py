"""Modelo SQLAlchemy de la bitácora."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models import new_id, utcnow
from app.infrastructure.db.session import Base


class AuditLogRow(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    accion: Mapped[str] = mapped_column(String(50), index=True)
    entidad_tipo: Mapped[str | None] = mapped_column(String(30), nullable=True)
    entidad_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
