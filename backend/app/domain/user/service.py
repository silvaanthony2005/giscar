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


def normalizar_telefono(valor: str | None) -> str | None:
    """El teléfono se guarda solo con dígitos: '809-555 0001' -> '8095550001'.

    None si el dato viene vacío o si contiene letras u otros símbolos.
    """
    if valor is None:
        return None
    limpio = "".join(ch for ch in valor.strip() if ch not in " -()+.")
    return limpio if limpio.isdigit() else None


def _texto(valor: str | None) -> str | None:
    """Recorta espacios; cadena vacía o None quedan como None."""
    return valor.strip() or None if valor is not None else None


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
            documento=_texto(documento),
            telefono=normalizar_telefono(telefono),
            direccion=_texto(direccion),
            cargo=_texto(cargo),
            departamento=departamento,
            estado=EstadoUsuario.ACTIVO,
            created_at=now,
            updated_at=now,
        )
    )


def update_profile(
    user: User,
    *,
    email: str | None = None,
    nombre: str | None = None,
    documento: str | None = None,
    telefono: str | None = None,
    direccion: str | None = None,
    cargo: str | None = None,
    now: datetime,
) -> Result[User, DomainError]:
    changes: dict[str, object] = {"updated_at": now}
    if email is not None:
        if not _valid_email(email.strip().lower()):
            return Err(DomainError("user.email_invalido", "El correo no es válido"))
        changes["email"] = email.strip().lower()
    if nombre is not None:
        if not nombre.strip():
            return Err(DomainError("user.nombre_vacio", "El nombre no puede estar vacío"))
        changes["nombre"] = nombre.strip()
    for field, value in (("documento", documento), ("telefono", telefono), ("direccion", direccion), ("cargo", cargo)):
        if value is not None:
            # '' significa vaciar el campo; los teléfonos solo guardan dígitos.
            changes[field] = normalizar_telefono(value) if field == "telefono" else _texto(value)
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
    if user.estado == EstadoUsuario.DESACTIVADO:
        return Err(DomainError("user.desactivado", "Usuario desactivado. Contacte a RRHH."))
    if not user.is_active():
        return Err(DomainError("user.bloqueado", "Usuario bloqueado. Contacte a RRHH."))
    return Ok(user)


def change_password(
    user: User, *, password_hash: str, now: datetime
) -> Result[User, DomainError]:
    """Restablecimiento de contraseña por RRHH (el hash se genera fuera)."""
    if len(password_hash) < 10:
        return Err(DomainError("user.hash_corto", "Hash de contraseña inválido"))
    return Ok(replace(user, password_hash=password_hash, updated_at=now))


def validar_cambio_usuario(
    users: list[User],
    *,
    actor_id: str,
    objetivo: User,
    estado: EstadoUsuario | None = None,
    departamento: Departamento | None = None,
) -> Result[User, DomainError]:
    """Guardas de RRHH sobre cambios de estado o departamento del `objetivo`.

    - Nadie puede bloquearse ni desactivarse a sí mismo.
    - El sistema no puede quedarse sin ningún usuario activo de RRHH.
    """
    if actor_id == objetivo.id and estado in (EstadoUsuario.BLOQUEADO, EstadoUsuario.DESACTIVADO):
        return Err(DomainError("user.auto_bloqueo", "No puede bloquearse o desactivarse a sí mismo"))
    if objetivo.departamento == Departamento.RRHH:
        queda_en_rrhh = (departamento or objetivo.departamento) == Departamento.RRHH
        sigue_activo = (estado or objetivo.estado) == EstadoUsuario.ACTIVO
        if not (queda_en_rrhh and sigue_activo):
            quedan = [
                u for u in users
                if u.id != objetivo.id
                and u.departamento == Departamento.RRHH
                and u.estado == EstadoUsuario.ACTIVO
            ]
            if not quedan:
                return Err(DomainError(
                    "user.ultimo_rrhh",
                    "Es el último usuario activo de RRHH: no puede bloquearlo, desactivarlo ni cambiarlo de departamento",
                ))
    return Ok(objetivo)

def usuarios_bloqueados(users: list[User]) -> int:
    """Usuarios que RRHH debe revisar (contador del sidebar)."""
    return len([u for u in users if u.estado == EstadoUsuario.BLOQUEADO.value])
