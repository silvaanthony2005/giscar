"""Mapeos fila <-> dominio de la Fase 2. Puros."""

from __future__ import annotations

import json
from datetime import datetime

from app.domain.customer.model import Customer
from app.domain.invoice.model import Invoice, InvoiceSnapshot
from app.domain.payment.model import Payment, TipoPago
from app.domain.project.model import Project
from app.domain.shared.money import Money
from app.infrastructure.db.models_ventas import CustomerRow, InvoiceRow, PaymentRow, ProjectRow


def customer_to_domain(row: CustomerRow) -> Customer:
    return Customer(
        id=row.id,
        nombre=row.nombre,
        documento=row.documento,
        telefono=row.telefono,
        email=row.email,
        direccion=row.direccion,
        notas=row.notas,
        created_by=row.created_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def apply_customer(c: Customer, row: CustomerRow) -> CustomerRow:
    row.nombre = c.nombre
    row.documento = c.documento
    row.telefono = c.telefono
    row.email = c.email
    row.direccion = c.direccion
    row.notas = c.notas
    row.created_by = c.created_by
    row.created_at = c.created_at
    row.updated_at = c.updated_at
    return row


def project_to_domain(row: ProjectRow) -> Project:
    return Project(
        id=row.id,
        codigo=row.codigo,
        titulo=row.titulo,
        descripcion_detallada=row.descripcion_detallada,
        customer_id=row.customer_id,
        monto_total=Money(row.monto_total),
        contacto_nombre=row.contacto_nombre,
        contacto_telefono=row.contacto_telefono,
        contacto_email=row.contacto_email,
        contacto_direccion=row.contacto_direccion,
        estado_ventas=row.estado_ventas,
        estado_desarrollo=row.estado_desarrollo,
        estado_despacho=row.estado_despacho,
        created_by=row.created_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def apply_project(p: Project, row: ProjectRow) -> ProjectRow:
    row.titulo = p.titulo
    row.descripcion_detallada = p.descripcion_detallada
    row.monto_total = p.monto_total.cents
    row.contacto_nombre = p.contacto_nombre
    row.contacto_telefono = p.contacto_telefono
    row.contacto_email = p.contacto_email
    row.contacto_direccion = p.contacto_direccion
    row.estado_ventas = p.estado_ventas
    row.estado_desarrollo = p.estado_desarrollo
    row.estado_despacho = p.estado_despacho
    row.created_by = p.created_by
    row.created_at = p.created_at
    row.updated_at = p.updated_at
    return row


def payment_to_domain(row: PaymentRow) -> Payment:
    return Payment(
        id=row.id,
        project_id=row.project_id,
        monto=Money(row.monto),
        porcentaje=row.porcentaje,
        tipo=TipoPago(row.tipo),
        metodo_pago=row.metodo_pago,
        notas=row.notas,
        registrado_por=row.registrado_por,
        fecha=row.fecha,
    )


def _snapshot_json(s: InvoiceSnapshot) -> str:
    return json.dumps(
        {
            "project_codigo": s.project_codigo,
            "project_titulo": s.project_titulo,
            "project_descripcion": s.project_descripcion,
            "cliente_nombre": s.cliente_nombre,
            "cliente_documento": s.cliente_documento,
            "cliente_telefono": s.cliente_telefono,
            "cliente_direccion": s.cliente_direccion,
            "monto_total": s.monto_total.cents,
        },
        ensure_ascii=False,
    )


def _snapshot_from_json(raw: str) -> InvoiceSnapshot:
    d = json.loads(raw)
    return InvoiceSnapshot(
        project_codigo=d["project_codigo"],
        project_titulo=d["project_titulo"],
        project_descripcion=d["project_descripcion"],
        cliente_nombre=d["cliente_nombre"],
        cliente_documento=d.get("cliente_documento"),
        cliente_telefono=d.get("cliente_telefono"),
        cliente_direccion=d.get("cliente_direccion"),
        monto_total=Money(d["monto_total"]),
    )


def apply_invoice(i: Invoice, row: InvoiceRow) -> InvoiceRow:
    row.numero = i.numero
    row.project_id = i.project_id
    row.payment_id = i.payment_id
    row.monto = i.monto.cents
    row.porcentaje = i.porcentaje
    row.metodo_pago = i.metodo_pago
    row.descripcion = i.descripcion
    row.snapshot = _snapshot_json(i.snapshot)
    row.emitida_por = i.emitida_por
    row.emitida_en = i.emitida_en
    return row


def invoice_to_domain(row: InvoiceRow) -> Invoice:
    return Invoice(
        id=row.id,
        numero=row.numero,
        project_id=row.project_id,
        payment_id=row.payment_id,
        monto=Money(row.monto),
        porcentaje=row.porcentaje,
        metodo_pago=row.metodo_pago,
        descripcion=row.descripcion,
        snapshot=_snapshot_from_json(row.snapshot),
        emitida_por=row.emitida_por,
        emitida_en=row.emitida_en if isinstance(row.emitida_en, datetime) else row.emitida_en,
    )
