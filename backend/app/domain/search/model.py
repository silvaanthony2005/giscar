"""Modelos del dominio de búsqueda global."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Resultado:
    """Una coincidencia de la búsqueda global.

    No lleva URL: la ruta es presentación y la decide el frontend a partir de
    `tipo`. El dominio solo expresa *qué* se encontró.
    """

    tipo: str  # proyecto | cliente | incidencia | usuario
    id: str
    titulo: str
    subtitulo: str | None = None
    codigo: str | None = None
