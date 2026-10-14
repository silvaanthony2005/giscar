"""Contratos de la superficie HTTP de adjuntos.

Comprueban dos regresiones reales:
1. La descarga debe declararse ANTES que el listado; si no, la ruta
   /adjuntos/{aid}/descargar casa con /adjuntos/{entidad_tipo}/{entidad_id}
   y se responde ``[]`` en lugar del binario.
2. Subir, listar y descargar deben usar el MISMO permiso de departamento:
   si un departamento puede subir evidencia, tiene que poder verla y bajarla.

Usan la lista de rutas del router (declaración), no una petición HTTP:
no hay BD ni servidor, como exige AGENTS.md para los tests.
"""

from fastapi.routing import APIRoute

from app.infrastructure.api.routes import desarrollo

RAIZ = "/api/desarrollo/adjuntos"
SUBIDA = f"{RAIZ}/{{entidad_tipo}}/{{entidad_id}}"
LISTADO = f"{RAIZ}/{{entidad_tipo}}/{{entidad_id}}"
DESCARGA = f"{RAIZ}/{{aid}}/descargar"

ADJUNTOS = [
    r
    for r in desarrollo.router.routes
    if isinstance(r, APIRoute) and r.path.startswith(RAIZ)
]


def _rutas(method: str, path: str) -> list[APIRoute]:
    return [r for r in ADJUNTOS if r.path == path and method in r.methods]


def _checker(route: APIRoute):
    for d in route.dependant.dependencies:
        if getattr(d.call, "__qualname__", "").endswith("checker"):
            return d.call
    raise AssertionError(f"La ruta {route.path} no tiene require_department")


def test_se_declaran_exactamente_tres_rutas_de_adjuntos():
    assert len(ADJUNTOS) == 3, [(sorted(r.methods), r.path) for r in ADJUNTOS]


def test_subir_listar_y_descargar_estan_presentes():
    assert len(_rutas("POST", SUBIDA)) == 1
    assert len(_rutas("GET", LISTADO)) == 1
    assert len(_rutas("GET", DESCARGA)) == 1


def test_descarga_se_declara_antes_que_el_listado():
    """Invertir el orden hace que la descarga devuelva [] (JSON) y no el binario."""
    assert ADJUNTOS.index(_rutas("GET", DESCARGA)[0]) < ADJUNTOS.index(
        _rutas("GET", LISTADO)[0]
    ), "Mueve la ruta de descarga por encima del listado"


def test_los_tres_adjuntos_comparten_el_mismo_permiso():
    """Regresión: el listado y la descarga exigían únicamente Desarrollo,
    con lo que Tecnología subía evidencia pero no podía verla ni bajarla."""
    checkers = {_checker(r) for r in ADJUNTOS}
    assert len(checkers) == 1, "Las tres rutas deben usar el mismo require_department"
