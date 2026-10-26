"""Modelo de usuario de dominio. Inmutable, sin dependencias de framework."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Departamento(StrEnum):
    VENTAS = "ventas"
    DESARROLLO = "desarrollo"
    DESPACHO = "despacho"
    TECNOLOGIA = "tecnologia"
    RRHH = "rrhh"


class EstadoUsuario(StrEnum):
    ACTIVO = "activo"
    BLOQUEADO = "bloqueado"
    DESACTIVADO = "desactivado"  # baja lógica: el registro se conserva


@dataclass(frozen=True, slots=True)
class User:
    id: str
    email: str
    password_hash: str
    nombre: str
    documento: str | None
    telefono: str | None
    direccion: str | None
    cargo: str | None
    departamento: Departamento
    estado: EstadoUsuario
    created_at: datetime
    updated_at: datetime

    def is_active(self) -> bool:
        return self.estado == EstadoUsuario.ACTIVO

    def is_visible(self) -> bool:
        """Los desactivados no aparecen en directorios ni búsquedas."""
        return self.estado != EstadoUsuario.DESACTIVADO

    def can_access(self, *deps: Departamento) -> bool:
        return self.departamento in deps or self.departamento == Departamento.RRHH
