"""Esquemas Pydantic de la Fase 2 (Ventas)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class CreateCustomerRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    representante: str = Field(min_length=1, max_length=255)
    documento: str = Field(min_length=1, max_length=50)
    telefono: str = Field(min_length=1, max_length=50)
    direccion: str = Field(min_length=1)
    email: EmailStr | None = None
    notas: str | None = None


class UpdateCustomerRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    representante: str | None = Field(default=None, min_length=1, max_length=255)
    documento: str | None = Field(default=None, max_length=50)
    telefono: str | None = Field(default=None, max_length=50)
    # '' significa "borrar el correo": el formulario reenvía el registro completo.
    email: EmailStr | Literal[""] | None = None
    direccion: str | None = None
    notas: str | None = None


class CustomerOut(BaseModel):
    id: str
    nombre: str
    representante: str | None
    documento: str | None
    telefono: str | None
    email: str | None
    direccion: str | None
    notas: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateProjectRequest(BaseModel):
    customer_id: str
    # El formulario de Ventas ya no lo pide: la ruta deriva uno desde los detalles.
    titulo: str | None = Field(default=None, min_length=1, max_length=255)
    descripcion_detallada: str = Field(min_length=20)
    monto_total: float = Field(gt=0, description="Monto total en pesos")
    contacto_nombre: str = Field(min_length=1)
    contacto_telefono: str | None = None
    contacto_email: EmailStr | None = None
    contacto_direccion: str | None = None


class ProjectOut(BaseModel):
    id: str
    codigo: str
    titulo: str
    descripcion_detallada: str
    customer_id: str
    monto_total: float
    pagado: float = 0.0
    saldo: float = 0.0
    contacto_nombre: str
    contacto_telefono: str | None
    contacto_email: str | None
    contacto_direccion: str | None
    estado_ventas: str
    estado_desarrollo: str
    estado_despacho: str
    acciones: tuple[str, ...] = ()
    created_at: datetime
    updated_at: datetime


class CreatePaymentRequest(BaseModel):
    monto: float = Field(gt=0)
    metodo_pago: str = Field(min_length=1, max_length=50)
    notas: str | None = None


class PaymentOut(BaseModel):
    id: str
    project_id: str
    monto: float
    porcentaje: int
    tipo: str
    metodo_pago: str
    notas: str | None
    fecha: datetime


class InvoiceOut(BaseModel):
    id: str
    numero: str
    project_id: str
    monto: float
    porcentaje: int
    metodo_pago: str
    descripcion: str
    emitida_en: datetime


class TransitionRequest(BaseModel):
    target: str
