"""Emisión y validación de JWT."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

from app.config import get_settings
from app.domain.shared.types import DomainError, Err, Ok, Result
from app.domain.user.model import Departamento


def create_access_token(
    *, user_id: str, departamento: Departamento, expires_minutes: int | None = None
) -> str:
    settings = get_settings()
    minutes = (
        expires_minutes if expires_minutes is not None else settings.access_token_minutes
    )
    payload = {
        "sub": user_id,
        "dep": departamento.value,
        "exp": datetime.now(UTC) + timedelta(minutes=minutes),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Result[dict, DomainError]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return Ok(payload)
    except jwt.PyJWTError:
        return Err(DomainError("auth.token_invalido", "Token inválido o expirado"))


def subject_of(payload: dict) -> str | None:
    sub = payload.get("sub")
    return sub if isinstance(sub, str) else None


def department_of(payload: dict) -> Departamento | None:
    dep = payload.get("dep")
    try:
        return Departamento(dep) if dep else None
    except ValueError:
        return None
