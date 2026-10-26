"""Registro de auditoría. Función pura de construcción + validación."""

from __future__ import annotations

from datetime import datetime

from app.domain.audit.model import AuditLog
from app.domain.shared.types import DomainError, Err, Ok, Result

# Acciones permitidas (whitelist)
ACCIONES = {
    "login",
    "login_fallido",
    "logout",
    "usuario_creado",
    "usuario_actualizado",
    "usuario_bloqueado",
    "usuario_desbloqueado",
    "usuario_desactivado",
    "usuario_password_restablecido",
    "departamento_cambiado",
    "cliente_eliminado",
    "proyecto_creado",
    "pago_registrado",
    "factura_emitida",
    "proyecto_cancelado",
    "entrega_confirmada",
    "proyecto_negado",
    "incidencia_creada",
    "incidencia_resuelta",
}


def record(
    *,
    id: str,
    user_id: str | None,
    user_email: str | None,
    accion: str,
    fecha: datetime,
    entidad_tipo: str | None = None,
    entidad_id: str | None = None,
    detalle: str | None = None,
    ip: str | None = None,
) -> Result[AuditLog, DomainError]:
    if accion not in ACCIONES:
        return Err(DomainError("audit.accion_invalida", f"Acción no permitida: {accion}"))
    return Ok(
        AuditLog(
            id=id,
            user_id=user_id,
            user_email=user_email,
            accion=accion,
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
            detalle=detalle,
            ip=ip,
            fecha=fecha,
        )
    )
