"""Búsqueda global del TopBar.

El frontend no filtra (AGENTS.md: filtrar es lógica de negocio), así que la
consulta, el matching y el RBAC viven en `domain/search`. La ruta solo
orchestra: leer filas, pasarlas al dominio y devolver lo que el dominio decide.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, HTTPException, Query

from app.domain.search import service as search_service
from app.domain.search.model import Resultado
from app.infrastructure.api import schemas as s
from app.infrastructure.db.repositories.despacho import IncidentRepository
from app.infrastructure.db.repositories.users import UserRepository
from app.infrastructure.db.repositories.ventas import CustomerRepository, ProjectRepository
from app.infrastructure.security.deps import CurrentUser, DbSession

router = APIRouter(prefix="/api/buscar", tags=["buscar"])


def _out(r: Resultado) -> s.ResultadoBusquedaOut:
    return s.ResultadoBusquedaOut(
        tipo=r.tipo, id=r.id, titulo=r.titulo, subtitulo=r.subtitulo, codigo=r.codigo
    )


@router.get("", response_model=s.BusquedaOut)
def buscar(
    db: DbSession,
    user: CurrentUser,
    q: str = Query(min_length=1, max_length=100),
):
    """Coincidencias de proyectos, clientes, incidencias y usuarios.

    Devuelve solo las categorías que este departamento puede buscar; RRHH
    busca las cuatro. Corto: 422 si la consulta tiene menos de 2 caracteres.
    """
    consulta = search_service.validar_consulta(q)
    if not consulta.is_ok():
        raise HTTPException(status_code=422, detail=consulta.error.message)
    termino = consulta.unwrap()

    tipos = search_service.tipos_buscables(user.departamento)

    # Cada fuente se consulta solo si el departamento puede buscar esa categoría.
    fuentes: dict[str, Callable[[], tuple[Resultado, ...]]] = {
        "proyecto": lambda: search_service.buscar_proyectos(
            ProjectRepository(db).list_all(), termino
        ),
        "cliente": lambda: search_service.buscar_clientes(
            CustomerRepository(db).list_all(), termino
        ),
        "incidencia": lambda: search_service.buscar_incidencias(
            IncidentRepository(db).list_all(), termino
        ),
        "usuario": lambda: search_service.buscar_usuarios(UserRepository(db).list_all(), termino),
    }

    grupos = [fuentes[t]() for t in tipos]
    return s.BusquedaOut(
        consulta=q,
        tipos=list(tipos),
        resultados={
            tipo: [_out(r) for r in rs] for tipo, rs in search_service.agrupar(*grupos).items()
        },
    )
