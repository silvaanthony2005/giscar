"""Repositorio de usuarios: implementa persistencia sobre SQLAlchemy.

El dominio define las operaciones como funciones puras; aquí se orquesta la I/O.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.user.model import Departamento, User
from app.infrastructure.db.mappers import apply_to_row, to_domain
from app.infrastructure.db.models import UserRow


class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: str) -> User | None:
        row = self._db.get(UserRow, user_id)
        return to_domain(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        stmt = select(UserRow).where(UserRow.email == email.strip().lower())
        row = self._db.execute(stmt).scalar_one_or_none()
        return to_domain(row) if row else None

    def list_all(self, departamento: Departamento | None = None) -> list[User]:
        stmt = select(UserRow).order_by(UserRow.nombre)
        if departamento:
            stmt = stmt.where(UserRow.departamento == departamento.value)
        rows = self._db.execute(stmt).scalars().all()
        return [to_domain(r) for r in rows]

    def email_exists(self, email: str) -> bool:
        return self.get_by_email(email) is not None

    def add(self, user: User) -> User:
        row = UserRow(id=user.id)
        apply_to_row(user, row)
        self._db.add(row)
        self._db.flush()
        return user

    def update(self, user: User) -> User:
        row = self._db.get(UserRow, user.id)
        if row is None:
            raise KeyError(user.id)
        apply_to_row(user, row)
        self._db.flush()
        return user
