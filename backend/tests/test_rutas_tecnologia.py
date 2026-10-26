"""Contratos de acceso a las incidencias (Mesa de Ayuda).

Regla de negocio: todos los departamentos pueden REPORTAR una incidencia,
pero solo enviarla — la cola, el detalle y la resolución son de Tecnología.
Si el listado queda abierto, cualquier módulo podría leer toda la cola
directamente desde la API.

Sin BD ni servidor (AGENTS.md): se leen los permisos declarados en las
rutas, igual que `test_rutas_adjuntos`.
"""

import inspect
from datetime import UTC, datetime

from fastapi.routing import APIRoute

from app.domain.user.model import Departamento, EstadoUsuario, User
from app.infrastructure.api.routes import tecnologia

RUTAS = [
    r for r in tecnologia.router.routes if isinstance(r, APIRoute) and r.path.startswith("/api/tecnologia")
]


def _permitidos(path: str, method: str) -> set[Departamento]:
    """Departamentos que `require_department` acepta en esa ruta."""
    for r in RUTAS:
        if r.path == path and method in r.methods:
            for d in r.dependant.dependencies:
                if getattr(d.call, "__qualname__", "").endswith("checker"):
                    return set(inspect.getclosurevars(d.call).nonlocals["deps"])
    raise AssertionError(f"La ruta {method} {path} no tiene require_department")


def test_cualquier_departamento_puede_reportar_incidencias():
    assert _permitidos("/api/tecnologia/incidencias", "POST") == set(Departamento)


def test_la_cola_y_el_detalle_solo_son_de_tecnologia():
    """El resto de departamentos solo envía la incidencia, nada más."""
    assert _permitidos("/api/tecnologia/incidencias", "GET") == {Departamento.TECNOLOGIA}
    assert _permitidos("/api/tecnologia/incidencias/{iid}", "GET") == {Departamento.TECNOLOGIA}


def test_asignar_transicionar_y_resolver_solo_tecnologia():
    for path in (
        "/api/tecnologia/incidencias/{iid}/asignar",
        "/api/tecnologia/incidencias/{iid}/estado",
        "/api/tecnologia/incidencias/{iid}/reporte",
        "/api/tecnologia/tecnicos",
    ):
        assert _permitidos(path, "POST" if not path.endswith("tecnicos") else "GET") == {
            Departamento.TECNOLOGIA
        }


def _user(uid: str, depto: Departamento) -> User:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return User(
        id=uid, email=f"{uid}@x.com", password_hash="h", nombre=uid, documento=None,
        telefono=None, direccion=None, cargo=None, departamento=depto,
        estado=EstadoUsuario.ACTIVO, created_at=now, updated_at=now,
    )


def test_asignar_solo_acepta_personal_de_tecnologia():
    """La regla se valida en el servidor, no solo filtrando la lista en el frontend."""
    users = {
        "t1": _user("t1", Departamento.TECNOLOGIA),
        "v1": _user("v1", Departamento.VENTAS),
    }
    assert tecnologia._error_asignacion(users, []) is None
    assert tecnologia._error_asignacion(users, ["t1"]) is None
    assert tecnologia._error_asignacion(users, ["nadie"]) == (404, "Usuario no encontrado")
    assert tecnologia._error_asignacion(users, ["t1", "v1"]) == (
        422,
        "Solo se puede asignar personal de Tecnología",
    )
