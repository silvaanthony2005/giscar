"""Contratos de acceso a las incidencias (Mesa de Ayuda).

Regla de negocio: todos los departamentos pueden REPORTAR una incidencia,
pero solo enviarla — la cola, el detalle y la resolución son de Tecnología.
Si el listado queda abierto, cualquier módulo podría leer toda la cola
directamente desde la API.

Sin BD ni servidor (AGENTS.md): se leen los permisos declarados en las
rutas, igual que `test_rutas_adjuntos`.
"""

import inspect

from fastapi.routing import APIRoute

from app.domain.user.model import Departamento
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
