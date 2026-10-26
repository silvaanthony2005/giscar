"""Búsqueda global. Funciones puras: sin BD, sin I/O, sin reloj.

Quién puede buscar qué es una regla de negocio, así que vive aquí y no en la
ruta. El matching es subcadena insensible a mayúsculas sobre los campos
"identificadores" de cada entidad (código, nombre, título, correo…); nunca
sobre texto largo como descripciones o informes.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.domain.customer.model import Customer
from app.domain.incidence.model import Incidence
from app.domain.project.model import Project
from app.domain.search.model import Resultado
from app.domain.shared.types import DomainError, Err, Ok, Result
from app.domain.user.model import Departamento, User

# Longitud mínima de la consulta: con 1 carácter se devolvería medio sistema.
MINIMA_LONGITUD = 2

# Máximo de coincidencias devueltas por categoría. Es un límite de presentación,
# pero se aplica aquí para que exista una sola copia de la regla.
MAX_POR_TIPO = 8

# Categorías de resultado, en el orden en que se presentan.
TIPOS: tuple[str, ...] = ("proyecto", "cliente", "incidencia", "usuario")

_PROYECTO = "proyecto"
_CLIENTE = "cliente"
_INCIDENCIA = "incidencia"
_USUARIO = "usuario"

# Qué departamento puede buscar cada categoría. Espeja lo que su módulo ya
# puede ver en la interfaz: Ventas ve proyectos y clientes; Desarrollo y
# Despacho solo proyectos; Tecnología solo incidencias; RRHH lo lee todo.
_BUSCABLES: dict[str, tuple[Departamento, ...]] = {
    _PROYECTO: (Departamento.VENTAS, Departamento.DESARROLLO, Departamento.DESPACHO),
    _CLIENTE: (Departamento.VENTAS,),
    _INCIDENCIA: (Departamento.TECNOLOGIA,),
    _USUARIO: (Departamento.RRHH,),
}


def normalizar(texto: str) -> str:
    """Minúsculas y sin espacios sobrantes. Puro y determinista."""
    return " ".join(texto.split()).casefold()


def validar_consulta(consulta: str) -> Result[str, DomainError]:
    limpia = normalizar(consulta)
    if len(limpia) < MINIMA_LONGITUD:
        return Err(
            DomainError(
                "search.consulta_corta",
                f"Escribe al menos {MINIMA_LONGITUD} caracteres para buscar",
            )
        )
    return Ok(limpia)


def coincide(campo: str | None, consulta: str) -> bool:
    """¿Contiene `consulta` (ya normalizada) al `campo`?"""
    if not campo:
        return False
    return consulta in normalizar(campo)


def tipos_buscables(departamento: Departamento) -> tuple[str, ...]:
    """Categorías que este departamento tiene derecho a buscar."""
    if departamento == Departamento.RRHH:
        return TIPOS
    return tuple(t for t in TIPOS if departamento in _BUSCABLES[t])


# --- filtros por entidad -----------------------------------------------------


def buscar_proyectos(proyectos: Iterable[Project], consulta: str) -> tuple[Resultado, ...]:
    return tuple(
        Resultado(
            tipo=_PROYECTO,
            id=p.id,
            titulo=p.titulo,
            subtitulo=p.codigo,
            codigo=p.codigo,
        )
        for p in proyectos
        if coincide(p.titulo, consulta) or coincide(p.codigo, consulta)
    )


def buscar_clientes(clientes: Iterable[Customer], consulta: str) -> tuple[Resultado, ...]:
    return tuple(
        Resultado(
            tipo=_CLIENTE,
            id=c.id,
            titulo=c.nombre,
            subtitulo=c.documento or c.email,
            codigo=c.documento,
        )
        for c in clientes
        if coincide(c.nombre, consulta)
        or coincide(c.documento, consulta)
        or coincide(c.email, consulta)
    )


def buscar_incidencias(incidencias: Iterable[Incidence], consulta: str) -> tuple[Resultado, ...]:
    return tuple(
        Resultado(
            tipo=_INCIDENCIA,
            id=i.id,
            titulo=i.titulo,
            subtitulo=i.equipo_afectado,
            codigo=i.codigo,
        )
        for i in incidencias
        if coincide(i.titulo, consulta)
        or coincide(i.codigo, consulta)
        or coincide(i.equipo_afectado, consulta)
    )


def buscar_usuarios(usuarios: Iterable[User], consulta: str) -> tuple[Resultado, ...]:
    return tuple(
        Resultado(
            tipo=_USUARIO,
            id=u.id,
            titulo=u.nombre,
            subtitulo=u.email,
            codigo=None,
        )
        for u in usuarios
        if u.is_visible()
        and (
            coincide(u.nombre, consulta)
            or coincide(u.email, consulta)
            or coincide(u.cargo, consulta)
        )
    )


def recortar(
    resultados: tuple[Resultado, ...], maximo: int = MAX_POR_TIPO
) -> tuple[Resultado, ...]:
    """Limita las coincidencias de una categoría. Puro: devuelve otra tupla."""
    return resultados[:maximo]


def agrupar(*grupos: tuple[Resultado, ...]) -> dict[str, list[Resultado]]:
    """Une los grupos en un dict por tipo, omitiendo las categorías vacías.

    Cada categoría se recorta a `MAX_POR_TIPO` y se emite en el orden de `TIPOS`.
    """
    por_tipo: dict[str, tuple[Resultado, ...]] = {}
    for grupo in grupos:
        for r in grupo:
            por_tipo[r.tipo] = por_tipo.get(r.tipo, ()) + (r,)
    return {t: list(recortar(por_tipo[t])) for t in TIPOS if por_tipo.get(t)}
