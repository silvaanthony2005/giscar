"""Servicio de usuario. Funciones puras: reciben datos, devuelven Result.

Sin DB, sin hashing (eso va en infrastructure), sin tiempo propio: `now` y
`password_hash` llegan como argumentos.
"""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import datetime

from app.domain.shared.types import DomainError, Err, Ok, Result
from app.domain.user.model import Departamento, EstadoUsuario, User

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def create_user(
    *,
    id: str,
    email: str,
    password_hash: str,
    nombre: str,
    now: datetime,
    documento: str | None = None,
    telefono: str | None = None,
    direccion: str | None = None,
    cargo: str | None = None,
    departamento: Departamento = Departamento.VENTAS,
) -> Result[User, DomainError]:
    if not nombre.strip():
        return Err(DomainError("user.nombre_vacio", "El nombre es obligatorio"))
    if not _valid_email(email.strip().lower()):
        return Err(DomainError("user.email_invalido", "El correo no es válido"))
    if len(password_hash) < 10:
        return Err(DomainError("user.hash_corto", "Hash de contraseña inválido"))

    return Ok(
        User(
            id=id,
            email=email.strip().lower(),
            password_hash=password_hash,
            nombre=nombre.strip(),
            documento=documento,
            telefono=telefono,
            direccion=direccion,
            cargo=cargo,
            departamento=departamento,
            estado=EstadoUsuario.ACTIVO,
            created_at=now,
            updated_at=now,
        )
    )


def update_profile(
    user: User,
    *,
    nombre: str | None = None,
    documento: str | None = None,
    telefono: str | None = None,
    direccion: str | None = None,
    cargo: str | None = None,
    now: datetime,
) -> Result[User, DomainError]:
    changes: dict[str, object] = {"updated_at": now}
    if nombre is not None:
        if not nombre.strip():
            return Err(DomainError("user.nombre_vacio", "El nombre no puede estar vacío"))
        changes["nombre"] = nombre.strip()
    for field, value in (("documento", documento), ("telefono", telefono), ("direccion", direccion), ("cargo", cargo)):
        if value is not None:
            changes[field] = value
    return Ok(replace(user, **changes))  # type: ignore[arg-type]


def set_departamento(
    user: User, departamento: Departamento, *, now: datetime
) -> User:
    return replace(user, departamento=departamento, updated_at=now)


def change_estado(
    user: User, estado: EstadoUsuario, *, now: datetime
) -> User:
    return replace(user, estado=estado, updated_at=now)


def can_login(user: User) -> Result[User, DomainError]:
    if not user.is_active():
        return Err(DomainError("user.bloqueado", "Usuario bloqueado. Contacte a RRHH."))
    return Ok(user)

def usuarios_bloqueados(users: list[User]) -> int:
    """Usuarios que RRHH debe revisar (contador del sidebar)."""
    return len([u for u in users if u.estado == EstadoUsuario.BLOQUEADO.value])
