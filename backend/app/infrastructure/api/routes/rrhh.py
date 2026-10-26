"""Router de RRHH: visión global de todos los departamentos + bitácora.

RRHH tiene acceso de solo lectura a los datos de todos los departamentos
y gestiona usuarios (CRUD ya cubierto en auth).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.domain.user.model import Departamento, User
from app.infrastructure.db.models import UserRow
from app.infrastructure.db.models_desarrollo import CancellationRow, DevPlanRow, PhaseRow
from app.infrastructure.db.models_despacho import IncidentRow
from app.infrastructure.db.models_ventas import CustomerRow, InvoiceRow, PaymentRow, ProjectRow
from app.infrastructure.db.repositories.audit import AuditRepository
from app.infrastructure.security.deps import DbSession, require_department

router = APIRouter(prefix="/api/rrhh", tags=["rrhh"])

RrhhUser = Annotated[User, Depends(require_department(Departamento.RRHH))]


@router.get("/dashboard")
def dashboard(db: DbSession, _: RrhhUser):
    """KPIs globales agregados por el backend (el frontend solo los muestra)."""

    def count(model, *where) -> int:
        stmt = select(func.count()).select_from(model)
        if where:
            stmt = stmt.where(*where)
        return int(db.execute(stmt).scalar_one())

    def count_by(model, column, *where) -> dict[str, int]:
        stmt = select(column, func.count()).group_by(column)
        if where:
            stmt = stmt.where(*where)
        rows = db.execute(stmt).all()
        return {str(k): int(v) for k, v in rows}

    # Ventas
    proyectos_por_estado_ventas = count_by(ProjectRow, ProjectRow.estado_ventas)
    monto_cobrado = int(
        db.execute(select(func.coalesce(func.sum(PaymentRow.monto), 0))).scalar_one()
    )
    facturas = count(InvoiceRow)
    clientes = count(CustomerRow)

    # Desarrollo
    planes = count(DevPlanRow)
    fases_por_estado = count_by(PhaseRow, PhaseRow.estado)
    cancelaciones = count(CancellationRow)

    # Despacho
    proyectos_por_estado_despacho = count_by(ProjectRow, ProjectRow.estado_despacho)

    # Tecnología
    incidencias_por_estado = count_by(IncidentRow, IncidentRow.estado)
    incidencias_por_prioridad = count_by(IncidentRow, IncidentRow.prioridad)

    # Usuarios
    usuarios_por_departamento = count_by(UserRow, UserRow.departamento)
    usuarios_por_estado = count_by(UserRow, UserRow.estado)

    return {
        "ventas": {
            "clientes": clientes,
            "facturas": facturas,
            "monto_cobrado": monto_cobrado / 100,
            "proyectos_total": count(ProjectRow),
            "proyectos_por_estado": proyectos_por_estado_ventas,
        },
        "desarrollo": {
            "planes": planes,
            "fases_por_estado": fases_por_estado,
            "cancelaciones": cancelaciones,
        },
        "despacho": {
            "proyectos_por_estado": proyectos_por_estado_despacho,
        },
        "tecnologia": {
            "incidencias_por_estado": incidencias_por_estado,
            "incidencias_por_prioridad": incidencias_por_prioridad,
        },
        "usuarios": {
            "por_departamento": usuarios_por_departamento,
            "por_estado": usuarios_por_estado,
            "total": count(UserRow),
        },
    }


@router.get("/actividad")
def actividad(db: DbSession, _: RrhhUser, limit: int = 200):
    """Bitácora reciente de acciones sensibles."""
    logs = AuditRepository(db).list_recent(limit=min(limit, 500))
    return [
        {
            "id": log.id,
            "user_email": log.user_email,
            "accion": log.accion,
            "entidad_tipo": log.entidad_tipo,
            "entidad_id": log.entidad_id,
            "detalle": log.detalle,
            "fecha": log.fecha,
        }
        for log in logs
    ]


@router.get("/proyectos")
def all_projects(db: DbSession, _: RrhhUser):
    """Todos los proyectos con su estado por departamento (solo lectura)."""
    rows = db.execute(select(ProjectRow).order_by(ProjectRow.created_at.desc())).scalars().all()
    return [
        {
            "id": r.id,
            "codigo": r.codigo,
            "titulo": r.titulo,
            "monto_total": r.monto_total / 100,
            "estado_ventas": r.estado_ventas,
            "estado_desarrollo": r.estado_desarrollo,
            "estado_despacho": r.estado_despacho,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.get("/usuarios")
def all_users(db: DbSession, _: RrhhUser, departamento: str | None = None):
    stmt = select(UserRow).order_by(UserRow.nombre)
    if departamento:
        stmt = stmt.where(UserRow.departamento == departamento)
    rows = db.execute(stmt).scalars().all()
    return [
        {
            "id": r.id,
            "email": r.email,
            "nombre": r.nombre,
            "documento": r.documento,
            "telefono": r.telefono,
            "direccion": r.direccion,
            "departamento": r.departamento,
            "cargo": r.cargo,
            "estado": r.estado,
        }
        for r in rows
    ]
