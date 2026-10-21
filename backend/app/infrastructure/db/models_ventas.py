"""Modelos SQLAlchemy de la Fase 2: clientes, proyectos, pagos, facturas."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.models import new_id, utcnow
from app.infrastructure.db.session import Base


class CustomerRow(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    nombre: Mapped[str] = mapped_column(String(255))
    # Nullable solo por registros antiguos; en altas nuevas es obligatorio.
    representante: Mapped[str | None] = mapped_column(String(255), nullable=True)
    documento: Mapped[str | None] = mapped_column(String(50), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    direccion: Mapped[str | None] = mapped_column(Text, nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ProjectRow(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    titulo: Mapped[str] = mapped_column(String(255))
    descripcion_detallada: Mapped[str] = mapped_column(Text)
    customer_id: Mapped[str] = mapped_column(String(32), ForeignKey("customers.id"))
    monto_total: Mapped[int] = mapped_column(Integer)  # centavos
    contacto_nombre: Mapped[str] = mapped_column(String(255))
    contacto_telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contacto_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contacto_direccion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado_ventas: Mapped[str] = mapped_column(String(30), default="levantamiento")
    estado_desarrollo: Mapped[str] = mapped_column(String(30), default="pendiente")
    estado_despacho: Mapped[str] = mapped_column(String(30), default="pendiente")
    created_by: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PaymentRow(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(String(32), ForeignKey("projects.id"), index=True)
    monto: Mapped[int] = mapped_column(Integer)
    porcentaje: Mapped[int] = mapped_column(Integer)
    tipo: Mapped[str] = mapped_column(String(20))
    metodo_pago: Mapped[str] = mapped_column(String(50))
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    registrado_por: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class InvoiceRow(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    numero: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    project_id: Mapped[str] = mapped_column(String(32), ForeignKey("projects.id"), index=True)
    payment_id: Mapped[str] = mapped_column(String(32), ForeignKey("payments.id"))
    monto: Mapped[int] = mapped_column(Integer)
    porcentaje: Mapped[int] = mapped_column(Integer)
    metodo_pago: Mapped[str] = mapped_column(String(50))
    descripcion: Mapped[str] = mapped_column(Text)
    snapshot: Mapped[str] = mapped_column(Text)  # JSON inmutable
    emitida_por: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"))
    emitida_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
