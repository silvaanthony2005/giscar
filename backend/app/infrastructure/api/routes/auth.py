"""Router de autenticación y gestión de usuarios (RRHH)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.domain.user import service as user_service
from app.domain.user.model import Departamento, EstadoUsuario, User
from app.infrastructure.api import schemas
from app.infrastructure.db.models import new_id
from app.infrastructure.db.repositories.audit import log_action
from app.infrastructure.db.repositories.users import UserRepository
from app.infrastructure.security.deps import CurrentUser, DbSession, require_department
from app.infrastructure.security.jwt import create_access_token
from app.infrastructure.security.password import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

RrhhUser = Annotated[User, Depends(require_department(Departamento.RRHH))]


def _to_out(user) -> schemas.UserOut:
    return schemas.UserOut(
        id=user.id,
        email=user.email,
        nombre=user.nombre,
        documento=user.documento,
        telefono=user.telefono,
        direccion=user.direccion,
        cargo=user.cargo,
        departamento=schemas.DepartamentoSchema(user.departamento.value),
        estado=schemas.EstadoUsuarioSchema(user.estado.value),
        created_at=user.created_at,
    )


@router.post("/login", response_model=schemas.LoginResponse)
def login(body: schemas.LoginRequest, db: DbSession) -> schemas.LoginResponse:
    repo = UserRepository(db)
    user = repo.get_by_email(body.email)
    if user is None or not verify_password(user.password_hash, body.password):
        log_action(db, accion="login_fallido", user_email=body.email, detalle="Credenciales inválidas")
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas"
        )
    active = user_service.can_login(user)
    if not active.is_ok():
        log_action(db, accion="login_fallido", user_id=user.id, user_email=user.email, detalle=active.error.message)
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=active.error.message)
    token = create_access_token(user_id=user.id, departamento=user.departamento)
    log_action(db, accion="login", user_id=user.id, user_email=user.email)
    db.commit()
    return schemas.LoginResponse(access_token=token, user=_to_out(user))


@router.get("/me", response_model=schemas.UserOut)
def me(user: CurrentUser) -> schemas.UserOut:
    return _to_out(user)


@router.get("/usuarios", response_model=list[schemas.UserOut])
def list_users(
    db: DbSession,
    _: RrhhUser,
) -> list[schemas.UserOut]:
    return [_to_out(u) for u in UserRepository(db).list_all()]


@router.post("/usuarios", response_model=schemas.UserOut, status_code=201)
def create_user(
    body: schemas.CreateUserRequest,
    db: DbSession,
    _: RrhhUser,
) -> schemas.UserOut:
    repo = UserRepository(db)
    if repo.email_exists(body.email):
        raise HTTPException(409, "El correo ya está registrado")
    now = datetime.now(UTC)
    result = user_service.create_user(
        id=new_id(),
        email=body.email,
        password_hash=hash_password(body.password),
        nombre=body.nombre,
        documento=body.documento,
        telefono=body.telefono,
        direccion=body.direccion,
        cargo=body.cargo,
        departamento=Departamento(body.departamento.value),
        now=now,
    )
    if not result.is_ok():
        raise HTTPException(422, result.error.message)
    created = repo.add(result.unwrap())
    log_action(
        db, accion="usuario_creado", user_id=created.id, user_email=created.email,
        entidad_tipo="usuario", entidad_id=created.id,
        detalle=f"Departamento: {created.departamento.value}",
    )
    db.commit()
    return _to_out(created)


@router.patch("/usuarios/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: str,
    body: schemas.UpdateUserRequest,
    db: DbSession,
    actor: RrhhUser,
) -> schemas.UserOut:
    repo = UserRepository(db)
    existing = repo.get_by_id(user_id)
    if existing is None:
        raise HTTPException(404, "Usuario no encontrado")
    nuevo_email = body.email.strip().lower() if body.email is not None else None
    if nuevo_email is not None and nuevo_email != existing.email and repo.email_exists(nuevo_email):
        raise HTTPException(409, "El correo ya está registrado")
    if body.estado is not None or body.departamento is not None:
        guardia = user_service.validar_cambio_usuario(
            repo.list_all(),
            actor_id=actor.id,
            objetivo=existing,
            estado=EstadoUsuario(body.estado.value) if body.estado is not None else None,
            departamento=Departamento(body.departamento.value) if body.departamento is not None else None,
        )
        if not guardia.is_ok():
            raise HTTPException(422, guardia.error.message)
    now = datetime.now(UTC)
    updated = user_service.update_profile(
        existing,
        email=body.email,
        nombre=body.nombre,
        documento=body.documento,
        telefono=body.telefono,
        direccion=body.direccion,
        cargo=body.cargo,
        now=now,
    )
    if not updated.is_ok():
        raise HTTPException(422, updated.error.message)
    user = updated.unwrap()
    if body.password is not None:
        changed = user_service.change_password(
            user, password_hash=hash_password(body.password), now=now
        )
        if not changed.is_ok():
            raise HTTPException(422, changed.error.message)
        user = changed.unwrap()
    if body.departamento is not None:
        user = user_service.set_departamento(
            user, Departamento(body.departamento.value), now=now
        )
    if body.estado is not None:
        user = user_service.change_estado(
            user, EstadoUsuario(body.estado.value), now=now
        )
    saved = repo.update(user)
    log_action(
        db, accion="usuario_actualizado", user_id=saved.id, user_email=saved.email,
        entidad_tipo="usuario", entidad_id=saved.id,
        detalle=f"Estado: {saved.estado.value}, Departamento: {saved.departamento.value}",
    )
    if body.password is not None:
        log_action(db, accion="usuario_password_restablecido", user_id=saved.id, user_email=saved.email)
    if body.estado is not None:
        accion = {
            "bloqueado": "usuario_bloqueado",
            "activo": "usuario_desbloqueado",
            "desactivado": "usuario_desactivado",
        }[body.estado.value]
        log_action(db, accion=accion, user_id=saved.id, user_email=saved.email)
    db.commit()
    return _to_out(saved)
