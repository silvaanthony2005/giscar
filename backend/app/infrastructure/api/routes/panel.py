"""Panel: contadores globales que pinta el sidebar.

Los calcula el dominio; el frontend solo los muestra (AGENTS.md).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.domain.incidence import service as incidence_service
from app.domain.project import service as project_service
from app.domain.user import service as user_service
from app.domain.user.model import Departamento
from app.infrastructure.db.repositories.despacho import IncidentRepository
from app.infrastructure.db.repositories.users import UserRepository
from app.infrastructure.db.repositories.ventas import ProjectRepository
from app.infrastructure.security.deps import CurrentUser, DbSession

router = APIRouter(prefix="/api/panel", tags=["panel"])

_CON_PROYECTOS = (Departamento.VENTAS, Departamento.DESARROLLO, Departamento.DESPACHO)


@router.get("/contadores")
def contadores(db: DbSession, user: CurrentUser) -> dict[str, int]:
    """Contadores por departamento, solo de los que el usuario puede ver.

    RRHH (lectura global) recibe todos; el resto, únicamente el suyo.
    """
    visibles = set(Departamento) if user.departamento == Departamento.RRHH else {user.departamento}

    out: dict[str, int] = {}

    if any(d in visibles for d in _CON_PROYECTOS):
        proyectos = ProjectRepository(db).list_all()
        if Departamento.VENTAS in visibles:
            out["ventas"] = project_service.pendientes_ventas(proyectos)
        if Departamento.DESARROLLO in visibles:
            out["desarrollo"] = project_service.activos_desarrollo(proyectos)
        if Departamento.DESPACHO in visibles:
            out["despacho"] = project_service.pendientes_despacho(proyectos)

    if Departamento.TECNOLOGIA in visibles:
        incidencias = IncidentRepository(db).list_all()
        out["tecnologia"] = incidence_service.incidencias_activas(incidencias)

    if Departamento.RRHH in visibles:
        out["rrhh"] = user_service.usuarios_bloqueados(UserRepository(db).list_all())

    return out
