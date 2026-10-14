"""Dependencias FastAPI de autenticación y autorización por departamento."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.domain.shared.state_machine import StateMachine  # noqa: F401 (re-export estable)
from app.domain.user.model import Departamento, User
from app.infrastructure.db.repositories.users import UserRepository
from app.infrastructure.db.session import get_db
from app.infrastructure.security.jwt import decode_token, subject_of

_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado"
    )
    if credentials is None:
        raise unauthorized
    payload = decode_token(credentials.credentials)
    if not payload.is_ok():
        raise unauthorized
    user_id = subject_of(payload.unwrap())
    if not user_id:
        raise unauthorized
    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active():
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_department(*deps: Departamento) -> Callable[[User], User]:
    """Factory de dependencias: exige que el usuario pertenezca a alguno de `deps`."""

    def checker(user: CurrentUser) -> User:
        if not user.can_access(*deps):
            allowed = ", ".join(d.value for d in deps)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requiere departamento: {allowed}",
            )
        return user

    return checker
