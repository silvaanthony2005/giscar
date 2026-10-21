"""Router de Ventas: clientes, proyectos, pagos, facturas."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from app.domain.customer import service as customer_service
from app.domain.invoice import service as invoice_service
from app.domain.invoice.pdf import invoice_pdf
from app.domain.payment import service as payment_service
from app.domain.payment.model import TipoPago
from app.domain.project import service as project_service
from app.domain.shared.money import Money
from app.domain.user.model import Departamento, User
from app.infrastructure.api import schemas_ventas as s
from app.infrastructure.db.models import new_id
from app.infrastructure.db.repositories.audit import log_action
from app.infrastructure.db.repositories.ventas import (
    CustomerRepository,
    InvoiceRepository,
    PaymentRepository,
    ProjectRepository,
)
from app.infrastructure.security.deps import DbSession, require_department

router = APIRouter(prefix="/api/ventas", tags=["ventas"])

VentasUser = Annotated[User, Depends(require_department(Departamento.VENTAS))]


def _now() -> datetime:
    return datetime.now(UTC)


def _customer_out(c) -> s.CustomerOut:
    return s.CustomerOut.model_validate(c)


def _project_out(p, pagado: Money | None = None) -> s.ProjectOut:
    # pagado/saldo se calculan aquí: el frontend no suma nada.
    pagado = pagado or Money(0)
    return s.ProjectOut(
        id=p.id,
        codigo=p.codigo,
        titulo=p.titulo,
        descripcion_detallada=p.descripcion_detallada,
        customer_id=p.customer_id,
        monto_total=p.monto_total.amount,
        pagado=pagado.amount,
        saldo=project_service.saldo_restante(p.monto_total, pagado).amount,
        contacto_nombre=p.contacto_nombre,
        contacto_telefono=p.contacto_telefono,
        contacto_email=p.contacto_email,
        contacto_direccion=p.contacto_direccion,
        estado_ventas=p.estado_ventas,
        estado_desarrollo=p.estado_desarrollo,
        estado_despacho=p.estado_despacho,
        acciones=project_service.acciones_ventas(p, pagado),
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _payment_out(p) -> s.PaymentOut:
    return s.PaymentOut(
        id=p.id,
        project_id=p.project_id,
        monto=p.monto.amount,
        porcentaje=p.porcentaje,
        tipo=p.tipo.value,
        metodo_pago=p.metodo_pago,
        notas=p.notas,
        fecha=p.fecha,
    )


def _invoice_out(i) -> s.InvoiceOut:
    return s.InvoiceOut(
        id=i.id,
        numero=i.numero,
        project_id=i.project_id,
        monto=i.monto.amount,
        porcentaje=i.porcentaje,
        metodo_pago=i.metodo_pago,
        descripcion=i.descripcion,
        emitida_en=i.emitida_en,
    )


# --- Clientes --------------------------------------------------------------


@router.get("/clientes", response_model=list[s.CustomerOut])
def list_customers(db: DbSession, _: VentasUser) -> list[s.CustomerOut]:
    return [_customer_out(c) for c in CustomerRepository(db).list_all()]


@router.post("/clientes", response_model=s.CustomerOut, status_code=201)
def create_customer(body: s.CreateCustomerRequest, db: DbSession, user=Depends(require_department(Departamento.VENTAS))):
    now = _now()
    result = customer_service.create_customer(
        id=new_id(),
        nombre=body.nombre,
        representante=body.representante,
        documento=body.documento,
        telefono=body.telefono,
        email=body.email,
        direccion=body.direccion,
        notas=body.notas,
        created_by=user.id,
        now=now,
    )
    if not result.is_ok():
        raise HTTPException(422, result.error.message)
    created = CustomerRepository(db).add(result.unwrap())
    db.commit()
    return _customer_out(created)


@router.patch("/clientes/{cid}", response_model=s.CustomerOut)
def update_customer(cid: str, body: s.UpdateCustomerRequest, db: DbSession, user=Depends(require_department(Departamento.VENTAS))):
    repo = CustomerRepository(db)
    existing = repo.get(cid)
    if existing is None:
        raise HTTPException(404, "Cliente no encontrado")
    result = customer_service.update_customer(
        existing,
        nombre=body.nombre,
        documento=body.documento,
        telefono=body.telefono,
        email=body.email,
        direccion=body.direccion,
        notas=body.notas,
        now=_now(),
    )
    if not result.is_ok():
        raise HTTPException(422, result.error.message)
    saved = repo.update(result.unwrap())
    db.commit()
    return _customer_out(saved)


# --- Proyectos -------------------------------------------------------------


@router.get("/proyectos", response_model=list[s.ProjectOut])
def list_projects(db: DbSession, _: VentasUser) -> list[s.ProjectOut]:
    pagos = PaymentRepository(db).sum_by_project()
    return [
        _project_out(p, Money(pagos.get(p.id, 0)))
        for p in ProjectRepository(db).list_all()
    ]


@router.get("/proyectos/{pid}", response_model=s.ProjectOut)
def get_project(pid: str, db: DbSession, _: VentasUser) -> s.ProjectOut:
    project = ProjectRepository(db).get(pid)
    if project is None:
        raise HTTPException(404, "Proyecto no encontrado")
    pagado = payment_service.sumar_pagos(PaymentRepository(db).list_by_project(pid))
    return _project_out(project, pagado)


def _titulo_desde_detalles(detalles: str) -> str:
    """El formulario ya no pide título: se toman los primeros 80 caracteres de los detalles."""
    return detalles.strip()[:80]


@router.post("/proyectos", response_model=s.ProjectOut, status_code=201)
def create_project(body: s.CreateProjectRequest, db: DbSession, user=Depends(require_department(Departamento.VENTAS))):
    if not CustomerRepository(db).get(body.customer_id):
        raise HTTPException(404, "Cliente no encontrado")
    repo = ProjectRepository(db)
    codigo = _next_codigo(repo)
    result = project_service.create_project(
        id=new_id(),
        codigo=codigo,
        titulo=body.titulo or _titulo_desde_detalles(body.descripcion_detallada),
        descripcion_detallada=body.descripcion_detallada,
        customer_id=body.customer_id,
        monto_total=Money.from_amount(Decimal(str(body.monto_total))),
        contacto_nombre=body.contacto_nombre,
        contacto_telefono=body.contacto_telefono,
        contacto_email=body.contacto_email,
        contacto_direccion=body.contacto_direccion,
        created_by=user.id,
        now=_now(),
    )
    if not result.is_ok():
        raise HTTPException(422, result.error.message)
    created = repo.add(result.unwrap())
    log_action(
        db, accion="proyecto_creado", user_id=user.id, user_email=user.email,
        entidad_tipo="proyecto", entidad_id=created.id, detalle=created.codigo,
    )
    db.commit()
    return _project_out(created)


def _next_codigo(repo: ProjectRepository) -> str:
    """Genera el siguiente código secuencial PRJ-0001 (puro sobre el repo)."""
    year = _now().year
    prefijo = f"PRJ-{year}-"
    existentes = [p.codigo for p in repo.list_all() if p.codigo.startswith(prefijo)]
    numeros = [
        int(c[len(prefijo):]) for c in existentes if c[len(prefijo):].isdigit()
    ]
    siguiente = max(numeros, default=0) + 1
    return f"{prefijo}{siguiente:04d}"


# --- Pagos y facturas -------------------------------------------------------


@router.get("/proyectos/{pid}/pagos", response_model=list[s.PaymentOut])
def list_payments(pid: str, db: DbSession, _: VentasUser) -> list[s.PaymentOut]:
    return [_payment_out(p) for p in PaymentRepository(db).list_by_project(pid)]


@router.get("/proyectos/{pid}/facturas", response_model=list[s.InvoiceOut])
def list_invoices(pid: str, db: DbSession, _: VentasUser) -> list[s.InvoiceOut]:
    return [_invoice_out(i) for i in InvoiceRepository(db).list_by_project(pid)]


@router.post("/proyectos/{pid}/pagos", response_model=s.PaymentOut, status_code=201)
def create_payment(pid: str, body: s.CreatePaymentRequest, db: DbSession, user=Depends(require_department(Departamento.VENTAS))):
    project = ProjectRepository(db).get(pid)
    if project is None:
        raise HTTPException(404, "Proyecto no encontrado")

    pagos_previos = PaymentRepository(db).list_by_project(pid)
    pagado_previo = payment_service.sumar_pagos(pagos_previos)

    monto = Money.from_amount(Decimal(str(body.monto)))
    tipo = _tipo_pago(project.monto_total, pagado_previo, monto)
    result = payment_service.create_payment(
        id=new_id(),
        project_id=pid,
        monto=monto,
        monto_total=project.monto_total,
        pagado_previo=pagado_previo,
        tipo=tipo,
        metodo_pago=body.metodo_pago,
        notas=body.notas,
        registrado_por=user.id,
        fecha=_now(),
    )
    if not result.is_ok():
        raise HTTPException(422, result.error.message)
    payment = result.unwrap()

    # Actualizar estado de ventas según lo cobrado
    pagado = pagado_previo.plus(monto)
    estado = _estado_por_pago(project.monto_total, pagado)
    if estado != project.estado_ventas:
        tr = project_service.set_estado_ventas(project, estado, now=_now())
        if not tr.is_ok():
            raise HTTPException(422, tr.error.message)
        ProjectRepository(db).update(tr.unwrap())

    saved_payment = PaymentRepository(db).add(payment)

    # Emitir factura
    cliente = CustomerRepository(db).get(project.customer_id)
    inv_result = invoice_service.create_invoice(
        id=new_id(),
        numero=_next_factura(InvoiceRepository(db)),
        payment=saved_payment,
        project=project,
        cliente_nombre=cliente.nombre if cliente else "—",
        emitida_por=user.id,
        emitida_en=_now(),
    )
    if inv_result.is_ok():
        InvoiceRepository(db).add(inv_result.unwrap())

    log_action(
        db, accion="pago_registrado", user_id=user.id, user_email=user.email,
        entidad_tipo="proyecto", entidad_id=pid,
        detalle=f"Monto {monto.amount} ({payment.porcentaje}%)",
    )
    if inv_result.is_ok():
        log_action(
            db, accion="factura_emitida", user_id=user.id, user_email=user.email,
            entidad_tipo="factura", entidad_id=inv_result.unwrap().id,
            detalle=inv_result.unwrap().numero,
        )

    db.commit()
    return _payment_out(saved_payment)


def _tipo_pago(total: Money, pagado: Money, monto: Money) -> TipoPago:
    restante = total.cents - pagado.cents
    if pagado.cents == 0 and monto.cents >= total.cents:
        return TipoPago.TOTAL
    if monto.cents >= restante:
        return TipoPago.LIQUIDACION
    return TipoPago.ANTICIPO


def _estado_por_pago(total: Money, pagado: Money) -> str:
    if pagado.cents >= total.cents:
        return "cobrado_100"
    if pagado.cents > 0:
        return "cobrado_50"
    return "levantamiento"


def _next_factura(repo: InvoiceRepository) -> str:
    year = _now().year
    prefijo = f"FAC-{year}-"
    numeros = [
        int(i.numero[len(prefijo):])
        for i in repo.list_all()
        if i.numero.startswith(prefijo) and i.numero[len(prefijo):].isdigit()
    ]
    return f"{prefijo}{max(numeros, default=0) + 1:05d}"


@router.get("/facturas/{iid}/pdf")
def download_invoice(iid: str, db: DbSession, _: VentasUser) -> Response:
    invoice = InvoiceRepository(db).get(iid)
    if invoice is None:
        raise HTTPException(404, "Factura no encontrada")
    data = invoice_pdf(invoice)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{invoice.numero}.pdf"'},
    )


# --- Transiciones -----------------------------------------------------------


@router.post("/proyectos/{pid}/pasar-desarrollo", response_model=s.ProjectOut)
def send_to_desarrollo(pid: str, db: DbSession, user=Depends(require_department(Departamento.VENTAS))):
    repo = ProjectRepository(db)
    project = repo.get(pid)
    if project is None:
        raise HTTPException(404, "Proyecto no encontrado")
    pagado = payment_service.sumar_pagos(PaymentRepository(db).list_by_project(pid))
    result = project_service.puede_pasar_a_desarrollo(project, pagado)
    if not result.is_ok():
        raise HTTPException(422, result.error.message)
    saved = repo.update(result.unwrap())
    db.commit()
    return _project_out(saved)
