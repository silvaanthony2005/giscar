"""Servicio de Despacho. Funciones puras."""

from __future__ import annotations

from datetime import date, datetime

from app.domain.dispatch.model import Denial, Dispatch
from app.domain.shared.types import DomainError, Err, Ok, Result


def confirm_delivery(
    *,
    id: str,
    project_id: str,
    confirmado_por: str,
    fecha_registro: datetime,
    fecha_entrega: date | None = None,
    hora_entrega: str | None = None,
    destinatario: str | None = None,
    detalle_entregado: str | None = None,
    notas: str | None = None,
) -> Result[Dispatch, DomainError]:
    if not destinatario or not destinatario.strip():
        return Err(DomainError("despacho.sin_destinatario", "Indique quién recibe el producto"))
    if not detalle_entregado or not detalle_entregado.strip():
        return Err(
            DomainError("despacho.sin_detalle", "Detalle qué se entregó exactamente")
        )
    if fecha_entrega is None:
        return Err(DomainError("despacho.sin_fecha", "Indique la fecha de entrega"))
    return Ok(
        Dispatch(
            id=id,
            project_id=project_id,
            fecha_entrega=fecha_entrega,
            hora_entrega=hora_entrega,
            destinatario=destinatario.strip(),
            detalle_entregado=detalle_entregado.strip(),
            notas=notas.strip() if notas else None,
            confirmado_por=confirmado_por,
            fecha_registro=fecha_registro,
        )
    )


def register_denial(
    *,
    id: str,
    project_id: str,
    motivo: str,
    detalle: str,
    registrado_por: str,
    fecha: datetime,
) -> Result[Denial, DomainError]:
    if not motivo.strip():
        return Err(DomainError("despacho.motivo_vacio", "Debe indicar el motivo del rechazo"))
    if len(detalle.strip()) < 15:
        return Err(
            DomainError(
                "despacho.detalle_corto",
                "Describa la situación (mínimo 15 caracteres)",
            )
        )
    return Ok(
        Denial(
            id=id,
            project_id=project_id,
            motivo=motivo.strip(),
            detalle=detalle.strip(),
            registrado_por=registrado_por,
            fecha=fecha,
        )
    )
