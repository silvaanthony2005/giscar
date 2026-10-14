"""Esquemas Pydantic de la capa API. El dominio no depende de estos."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field


class DepartamentoSchema(StrEnum):
    ventas = "ventas"
    desarrollo = "desarrollo"
    despacho = "despacho"
    tecnologia = "tecnologia"
    rrhh = "rrhh"


class EstadoUsuarioSchema(StrEnum):
    activo = "activo"
    bloqueado = "bloqueado"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserOut(BaseModel):
    id: str
    email: EmailStr
    nombre: str
    documento: str | None
    telefono: str | None
    direccion: str | None
    cargo: str | None
    departamento: DepartamentoSchema
    estado: EstadoUsuarioSchema
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nombre: str = Field(min_length=1, max_length=255)
    documento: str | None = None
    telefono: str | None = None
    direccion: str | None = None
    cargo: str | None = None
    departamento: DepartamentoSchema = DepartamentoSchema.ventas


class UpdateUserRequest(BaseModel):
    nombre: str | None = None
    documento: str | None = None
    telefono: str | None = None
    direccion: str | None = None
    cargo: str | None = None
    departamento: DepartamentoSchema | None = None
    estado: EstadoUsuarioSchema | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


# --- Búsqueda global ---------------------------------------------------------


class ResultadoBusquedaOut(BaseModel):
    """Una coincidencia. Sin URL: la ruta la decide el frontend según `tipo`."""

    tipo: str
    id: str
    titulo: str
    subtitulo: str | None = None
    codigo: str | None = None


class BusquedaOut(BaseModel):
    consulta: str
    tipos: list[str]
    resultados: dict[str, list[ResultadoBusquedaOut]]
