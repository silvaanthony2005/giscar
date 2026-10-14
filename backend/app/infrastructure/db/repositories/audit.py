"""Repositorio de auditoría + helper para grabar sin romper el flujo."""

from __future__ import annotations

from datetime import UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.audit import service as audit_service
from app.domain.audit.model import AuditLog
from app.infrastructure.db.models import new_id
from app.infrastructure.db.models_audit import AuditLogRow


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_recent(self, limit: int = 200) -> list[AuditLog]:
        stmt = (
            select(AuditLogRow)
            .order_by(AuditLogRow.fecha.desc())
            .limit(limit)
        )
        rows = self._db.execute(stmt).scalars().all()
        return [
            AuditLog(
                id=r.id, user_id=r.user_id, user_email=r.user_email, accion=r.accion,
                entidad_tipo=r.entidad_tipo, entidad_id=r.entidad_id, detalle=r.detalle,
                ip=r.ip, fecha=r.fecha,
            )
            for r in rows
        ]

    def add(self, log: AuditLog) -> AuditLog:
        row = AuditLogRow(
            id=log.id, user_id=log.user_id, user_email=log.user_email, accion=log.accion,
            entidad_tipo=log.entidad_tipo, entidad_id=log.entidad_id, detalle=log.detalle,
            ip=log.ip, fecha=log.fecha,
        )
        self._db.add(row)
        self._db.flush()
        return log


def log_action(
    db: Session,
    *,
    accion: str,
    user_id: str | None = None,
    user_email: str | None = None,
    entidad_tipo: str | None = None,
    entidad_id: str | None = None,
    detalle: str | None = None,
    ip: str | None = None,
) -> None:
    """Registra una acción de auditoría de forma best-effort (no rompe el flujo).

    Si la acción no está en la whitelist, se ignora silenciosamente.
    """
    from datetime import datetime

    result = audit_service.record(
        id=new_id(), user_id=user_id, user_email=user_email, accion=accion,
        fecha=datetime.now(UTC), entidad_tipo=entidad_tipo,
        entidad_id=entidad_id, detalle=detalle, ip=ip,
    )
    if result.is_ok():
        AuditRepository(db).add(result.unwrap())
