"""Mapeo entre UserRow (SQLAlchemy) y User (dominio inmutable). Puro."""

from __future__ import annotations

from app.domain.user.model import Departamento, EstadoUsuario, User
from app.infrastructure.db.models import UserRow


def to_domain(row: UserRow) -> User:
    return User(
        id=row.id,
        email=row.email,
        password_hash=row.password_hash,
        nombre=row.nombre,
        documento=row.documento,
        telefono=row.telefono,
        direccion=row.direccion,
        cargo=row.cargo,
        departamento=Departamento(row.departamento),
        estado=EstadoUsuario(row.estado),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def apply_to_row(user: User, row: UserRow) -> UserRow:
    row.email = user.email
    row.password_hash = user.password_hash
    row.nombre = user.nombre
    row.documento = user.documento
    row.telefono = user.telefono
    row.direccion = user.direccion
    row.cargo = user.cargo
    row.departamento = user.departamento.value
    row.estado = user.estado.value
    row.updated_at = user.updated_at
    return row
