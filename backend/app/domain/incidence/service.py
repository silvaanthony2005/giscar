"""Servicio de Incidencias. Funciones puras: cola, prioridad y transiciones."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from functools import reduce

from app.domain.incidence.model import (
    EstadoIncidencia,
    Incidence,
    IncidentReport,
    Prioridad,
)
from app.domain.shared.types import DomainError, Err, Ok, Result

# Orden numérico para ordenar la cola (mayor = más urgente)
_PRIORIDAD_PESO: dict[str, int] = {
    Prioridad.BAJA.value: 1,
    Prioridad.MEDIA.value: 2,
    Prioridad.ALTA.value: 3,
    Prioridad.CRITICA.value: 4,
}


def create_incidence(
    *,
    id: str,
    codigo: str,
    titulo: str,
    descripcion: str,
    equipo_afectado: str,
    departamento_origen: str,
    prioridad: str,
    orden_llegada: int,
    reportado_por: str,
    now: datetime,
) -> Result[Incidence, DomainError]:
    if not titulo.strip():
        return Err(DomainError("incidencia.titulo_vacio", "La incidencia necesita un título"))
    if len(descripcion.strip()) < 15:
        return Err(
            DomainError(
                "incidencia.descripcion_corta",
                "Describa el problema (mínimo 15 caracteres)",
            )
        )
    if not equipo_afectado.strip():
        return Err(
            DomainError("incidencia.sin_equipo", "Indique el equipo o elemento afectado")
        )
    if prioridad not in _PRIORIDAD_PESO:
        return Err(DomainError("incidencia.prioridad_invalida", f"Prioridad inválida: {prioridad}"))

    return Ok(
        Incidence(
            id=id,
            codigo=codigo,
            titulo=titulo.strip(),
            descripcion=descripcion.strip(),
            equipo_afectado=equipo_afectado.strip(),
            departamento_origen=departamento_origen,
            prioridad=prioridad,
            estado=EstadoIncidencia.ABIERTA.value,
            orden_llegada=orden_llegada,
            reportado_por=reportado_por,
            asignado_a=None,
            created_at=now,
            updated_at=now,
        )
    )


def transition_incidence(
    incidence: Incidence, target: str, *, now: datetime
) -> Result[Incidence, DomainError]:
    allowed: dict[str, set[str]] = {
        EstadoIncidencia.ABIERTA.value: {EstadoIncidencia.EN_PROCESO.value, EstadoIncidencia.CERRADA.value},
        EstadoIncidencia.EN_PROCESO.value: {EstadoIncidencia.RESUELTA.value, EstadoIncidencia.CERRADA.value},
        EstadoIncidencia.RESUELTA.value: {EstadoIncidencia.CERRADA.value},
        EstadoIncidencia.CERRADA.value: set(),
    }
    if target not in {e.value for e in EstadoIncidencia}:
        return Err(DomainError("incidencia.estado_invalido", f"Estado inválido: {target}"))
    if target not in allowed[incidence.estado]:
        return Err(
            DomainError(
                "incidencia.transicion_invalida",
                f"Transición no permitida: {incidence.estado} → {target}",
            )
        )
    return Ok(replace(incidence, estado=target, updated_at=now))


def assign_incidence(
    incidence: Incidence, user_id: str, *, now: datetime
) -> Result[Incidence, DomainError]:
    if incidence.estado == EstadoIncidencia.CERRADA.value:
        return Err(DomainError("incidencia.cerrada", "No se puede asignar una incidencia cerrada"))
    return Ok(replace(incidence, asignado_a=user_id, updated_at=now))


def create_report(
    *,
    id: str,
    incident_id: str,
    diagnostico: str,
    solucion: str,
    tiempo_resolucion_horas: int,
    resuelto_por: str,
    fecha: datetime,
) -> Result[IncidentReport, DomainError]:
    if len(diagnostico.strip()) < 10:
        return Err(
            DomainError("reporte.diagnostico_corto", "Describa el diagnóstico (mínimo 10 caracteres)")
        )
    if len(solucion.strip()) < 10:
        return Err(
            DomainError("reporte.solucion_corta", "Describa la solución aplicada (mínimo 10 caracteres)")
        )
    if tiempo_resolucion_horas < 0:
        return Err(DomainError("reporte.tiempo_invalido", "Tiempo de resolución inválido"))
    return Ok(
        IncidentReport(
            id=id,
            incident_id=incident_id,
            diagnostico=diagnostico.strip(),
            solucion=solucion.strip(),
            tiempo_resolucion_horas=tiempo_resolucion_horas,
            resuelto_por=resuelto_por,
            fecha=fecha,
        )
    )


def prioridad_peso(prioridad: str) -> int:
    return _PRIORIDAD_PESO.get(prioridad, 0)


def ordenar_cola(incidencias: list[Incidence]) -> list[Incidence]:
    """Cola: primero por prioridad (desc), luego por orden de llegada (asc).

    Puro e inmutable (sorted no muta la original).
    """
    return sorted(
        incidencias,
        key=lambda i: (-prioridad_peso(i.prioridad), i.orden_llegada),
    )


def contar_por_estado(incidencias: list[Incidence]) -> dict[str, int]:
    """Agregado puro: conteo por estado (reduce)."""
    estados = [e.value for e in EstadoIncidencia]

    def add(acc: dict[str, int], inc: Incidence) -> dict[str, int]:
        return {**acc, inc.estado: acc.get(inc.estado, 0) + 1}

    base = dict.fromkeys(estados, 0)
    return reduce(add, incidencias, base)

def incidencias_activas(incidencias: list[Incidence]) -> int:
    """Incidencias que aun no se resolvieron ni cerraron (contador del sidebar)."""
    cerradas = (EstadoIncidencia.RESUELTA.value, EstadoIncidencia.CERRADA.value)
    return len([i for i in incidencias if i.estado not in cerradas])
