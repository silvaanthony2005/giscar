"""Repositorios de la Fase 2: clientes, proyectos, pagos, facturas."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.customer.model import Customer
from app.domain.invoice.model import Invoice
from app.domain.payment.model import Payment
from app.domain.project.model import Project
from app.infrastructure.db.mappers_ventas import (
    apply_customer,
    apply_invoice,
    apply_project,
    customer_to_domain,
    invoice_to_domain,
    payment_to_domain,
    project_to_domain,
)
from app.infrastructure.db.models_ventas import (
    CustomerRow,
    InvoiceRow,
    PaymentRow,
    ProjectRow,
)


class CustomerRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, cid: str) -> Customer | None:
        row = self._db.get(CustomerRow, cid)
        return customer_to_domain(row) if row else None

    def list_all(self) -> list[Customer]:
        rows = self._db.execute(select(CustomerRow).order_by(CustomerRow.nombre)).scalars().all()
        return [customer_to_domain(r) for r in rows]

    def add(self, customer: Customer) -> Customer:
        row = CustomerRow(id=customer.id)
        apply_customer(customer, row)
        self._db.add(row)
        self._db.flush()
        return customer

    def update(self, customer: Customer) -> Customer:
        row = self._db.get(CustomerRow, customer.id)
        if row is None:
            raise KeyError(customer.id)
        apply_customer(customer, row)
        self._db.flush()
        return customer


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, pid: str) -> Project | None:
        row = self._db.get(ProjectRow, pid)
        return project_to_domain(row) if row else None

    def get_by_codigo(self, codigo: str) -> Project | None:
        stmt = select(ProjectRow).where(ProjectRow.codigo == codigo)
        row = self._db.execute(stmt).scalar_one_or_none()
        return project_to_domain(row) if row else None

    def list_all(self) -> list[Project]:
        rows = self._db.execute(select(ProjectRow).order_by(ProjectRow.created_at.desc())).scalars()
        return [project_to_domain(r) for r in rows]

    def codigo_exists(self, codigo: str) -> bool:
        return self.get_by_codigo(codigo) is not None

    def add(self, project: Project) -> Project:
        row = ProjectRow(id=project.id)
        row.codigo = project.codigo
        row.customer_id = project.customer_id
        apply_project(project, row)
        self._db.add(row)
        self._db.flush()
        return project

    def update(self, project: Project) -> Project:
        row = self._db.get(ProjectRow, project.id)
        if row is None:
            raise KeyError(project.id)
        apply_project(project, row)
        self._db.flush()
        return project


class PaymentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_project(self, project_id: str) -> list[Payment]:
        stmt = select(PaymentRow).where(PaymentRow.project_id == project_id)
        rows = self._db.execute(stmt).scalars().all()
        return [payment_to_domain(r) for r in rows]

    def sum_by_project(self) -> dict[str, int]:
        """Total pagado por proyecto en centavos (una sola consulta)."""
        stmt = select(PaymentRow.project_id, func.sum(PaymentRow.monto)).group_by(
            PaymentRow.project_id
        )
        return {pid: int(total or 0) for pid, total in self._db.execute(stmt).all()}

    def add(self, payment: Payment) -> Payment:
        row = PaymentRow(id=payment.id)
        row.project_id = payment.project_id
        row.monto = payment.monto.cents
        row.porcentaje = payment.porcentaje
        row.tipo = payment.tipo.value
        row.metodo_pago = payment.metodo_pago
        row.notas = payment.notas
        row.registrado_por = payment.registrado_por
        row.fecha = payment.fecha
        self._db.add(row)
        self._db.flush()
        return payment


class InvoiceRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, iid: str) -> Invoice | None:
        row = self._db.get(InvoiceRow, iid)
        return invoice_to_domain(row) if row else None

    def list_by_project(self, project_id: str) -> list[Invoice]:
        stmt = select(InvoiceRow).where(InvoiceRow.project_id == project_id)
        rows = self._db.execute(stmt).scalars().all()
        return [invoice_to_domain(r) for r in rows]

    def list_all(self) -> list[Invoice]:
        rows = self._db.execute(select(InvoiceRow).order_by(InvoiceRow.emitida_en.desc())).scalars()
        return [invoice_to_domain(r) for r in rows]

    def add(self, invoice: Invoice) -> Invoice:
        row = InvoiceRow(id=invoice.id)
        apply_invoice(invoice, row)
        self._db.add(row)
        self._db.flush()
        return invoice
