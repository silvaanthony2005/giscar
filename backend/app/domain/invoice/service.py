"""Servicio de facturas. Puro: arma la factura a partir del pago y el proyecto."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from app.domain.invoice.model import Invoice, InvoiceSnapshot
from app.domain.payment.model import Payment
from app.domain.project.model import Project
from app.domain.shared.types import DomainError, Err, Ok, Result


def next_numero(existing: Iterable[str], *, year: int, prefix: str = "FAC") -> str:
    """Siguiente número secuencial `FAC-YYYY-NNNNN` (ignora otros años/formatos)."""
    year_prefix = f"{prefix}-{year}-"
    numeros = [
        int(n[len(year_prefix):])
        for n in existing
        if n.startswith(year_prefix) and n[len(year_prefix):].isdigit()
    ]
    return f"{year_prefix}{max(numeros, default=0) + 1:05d}"


def snapshot_from_project(project: Project, cliente_nombre: str) -> InvoiceSnapshot:
    return InvoiceSnapshot(
        project_codigo=project.codigo,
        project_titulo=project.titulo,
        project_descripcion=project.descripcion_detallada,
        cliente_nombre=cliente_nombre,
        cliente_documento=None,
        cliente_telefono=project.contacto_telefono,
        cliente_direccion=project.contacto_direccion,
        monto_total=project.monto_total,
    )


def create_invoice(
    *,
    id: str,
    numero: str,
    payment: Payment,
    project: Project,
    cliente_nombre: str,
    emitida_por: str,
    emitida_en: datetime,
) -> Result[Invoice, DomainError]:
    if payment.project_id != project.id:
        return Err(DomainError("invoice.proyecto_distinto", "El pago no pertenece al proyecto"))
    if payment.monto.cents <= 0:
        return Err(DomainError("invoice.monto_invalido", "Monto de factura inválido"))

    descripcion = (
        f"Cobro de proyecto {project.codigo} — {project.titulo} "
        f"({payment.porcentaje}% del total)"
    )
    return Ok(
        Invoice(
            id=id,
            numero=numero,
            project_id=project.id,
            payment_id=payment.id,
            monto=payment.monto,
            porcentaje=payment.porcentaje,
            metodo_pago=payment.metodo_pago,
            descripcion=descripcion,
            snapshot=snapshot_from_project(project, cliente_nombre),
            emitida_por=emitida_por,
            emitida_en=emitida_en,
        )
    )
