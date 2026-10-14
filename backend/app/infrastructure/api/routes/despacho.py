"""Router de Despacho: entrega, estados, pago restante, negación."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.domain.dispatch import service as dispatch_service
from app.domain.payment import service as payment_service
from app.domain.payment.model import TipoPago
from app.domain.project import service as project_service
from app.domain.user.model import Departamento, User
from app.infrastructure.api import schemas_despacho as s
from app.infrastructure.db.models import new_id
from app.infrastructure.db.repositories.audit import log_action
from app.infrastructure.db.repositories.despacho import DenialRepository, DispatchRepository
from app.infrastructure.db.repositories.ventas import (
    CustomerRepository,
    PaymentRepository,
    ProjectRepository,
)
from app.infrastructure.security.deps import DbSession, require_department

router = APIRouter(prefix="/api/despacho", tags=["despacho"])

DespachoUser = Annotated[User, Depends(require_department(Departamento.DESPACHO))]


def _now() -> datetime:
    return datetime.now(UTC)


def _project_out(p, pagado) -> dict:
    return {
        "id": p.id,
        "codigo": p.codigo,
        "titulo": p.titulo,
        "customer_id": p.customer_id,
        "contacto_nombre": p.contacto_nombre,
        "contacto_telefono": p.contacto_telefono,
        "contacto_email": p.contacto_email,
        "contacto_direccion": p.contacto_direccion,
        "monto_total": p.monto_total.amount,
        "estado_ventas": p.estado_ventas,
        "estado_desarrollo": p.estado_desarrollo,
        "estado_despacho": p.estado_despacho,
        "acciones": project_service.acciones_despacho(p, pagado),
        "created_at": p.created_at,
        "updated_at": p.updated_at,
    }


def _get_project(db, pid: str):
    p = ProjectRepository(db).get(pid)
    if p is None:
        raise HTTPException(404, "Proyecto no encontrado")
    return p


@router.get("/proyectos")
def list_projects(db: DbSession, _: DespachoUser):
    """Columnas del tablero: `pendientes` y `cerrados`.

    El criterio lo decide el dominio; el frontend solo las pinta.
    """
    proyectos = [
        p for p in ProjectRepository(db).list_all()
        if p.estado_desarrollo == "enviado_despacho"
        or p.estado_despacho in {"pendiente_entrega", "negado", "entregado"}
    ]
    pagos_repo = PaymentRepository(db)
    customers = {c.id: c for c in CustomerRepository(db).list_all()}

    payload: dict[str, dict] = {}
    for p in proyectos:
        pagado = payment_service.sumar_pagos(pagos_repo.list_by_project(p.id))
        saldo = project_service.saldo_restante(p.monto_total, pagado)
        dispatch = DispatchRepository(db).get_by_project(p.id)
        denial = DenialRepository(db).get_by_project(p.id)
        payload[p.id] = {
            **_project_out(p, pagado),
            "cliente": customers[p.customer_id].nombre if p.customer_id in customers else "—",
            "pagado": pagado.amount,
            "saldo": saldo.amount,
            "entrega": dispatch,
            "negacion": denial,
        }

    return {
        grupo: [payload[p.id] for p in items]
        for grupo, items in project_service.agrupar_despacho(proyectos).items()
    }


@router.get("/proyectos/{pid}")
def get_project(pid: str, db: DbSession, _: DespachoUser):
    p = _get_project(db, pid)
    pagos = PaymentRepository(db).list_by_project(pid)
    pagado = payment_service.sumar_pagos(pagos)
    saldo = project_service.saldo_restante(p.monto_total, pagado)
    customer = CustomerRepository(db).get(p.customer_id)
    return {
        **_project_out(p, pagado),
        "cliente": customer,
        "pagado": pagado.amount,
        "saldo": saldo.amount,
        "por_pagado": int(pagado.cents * 100 / p.monto_total.cents) if p.monto_total.cents else 0,
        "pagos": pagos,
        "entrega": DispatchRepository(db).get_by_project(pid),
        "negacion": DenialRepository(db).get_by_project(pid),
    }


def _register_remaining_payment(db, pid: str, user: User, metodo_pago: str, notas: str | None):
    project = _get_project(db, pid)
    pagos_previos = PaymentRepository(db).list_by_project(pid)
    pagado_previo = payment_service.sumar_pagos(pagos_previos)
    saldo = project_service.saldo_restante(project.monto_total, pagado_previo)

    if saldo.cents <= 0:
        raise HTTPException(422, "El proyecto no tiene saldo pendiente")

    result = payment_service.create_payment(
        id=new_id(), project_id=pid, monto=saldo, monto_total=project.monto_total,
        pagado_previo=pagado_previo, tipo=TipoPago.LIQUIDACION, metodo_pago=metodo_pago,
        notas=notas, registrado_por=user.id, fecha=_now(),
    )
    if not result.is_ok():
        raise HTTPException(422, result.error.message)

    # Proyecto pasa a cobrado_100 en ventas
    if project.estado_ventas != "cobrado_100":
        tr = project_service.set_estado_ventas(project, "cobrado_100", now=_now())
        if tr.is_ok():
            ProjectRepository(db).update(tr.unwrap())

    saved = PaymentRepository(db).add(result.unwrap())
    db.commit()
    return saved


class RemainingPaymentIn(BaseModel):
    metodo_pago: str
    notas: str | None = None


@router.post("/proyectos/{pid}/liquidar", status_code=201)
def liquidate(pid: str, body: RemainingPaymentIn, db: DbSession, user: DespachoUser):
    payment = _register_remaining_payment(db, pid, user, body.metodo_pago, body.notas)
    return {
        "id": payment.id,
        "monto": payment.monto.amount,
        "porcentaje": payment.porcentaje,
        "tipo": payment.tipo.value,
    }


@router.post("/proyectos/{pid}/confirmar-entrega", response_model=s.DeliveryOut, status_code=201)
def confirm_delivery(pid: str, body: s.DeliveryIn, db: DbSession, user: DespachoUser):
    project = _get_project(db, pid)
    pagado = payment_service.sumar_pagos(PaymentRepository(db).list_by_project(pid))
    saldo = project_service.saldo_restante(project.monto_total, pagado)

    # Validar transición a 'entregado' (incluye validación de saldo en dominio)
    tr = project_service.puede_entregar(project, pagado, saldo)
    if not tr.is_ok():
        raise HTTPException(422, tr.error.message)

    result = dispatch_service.confirm_delivery(
        id=new_id(), project_id=pid, confirmado_por=user.id, fecha_registro=_now(),
        fecha_entrega=body.fecha_entrega, hora_entrega=body.hora_entrega,
        destinatario=body.destinatario, detalle_entregado=body.detalle_entregado,
        notas=body.notas,
    )
    if not result.is_ok():
        raise HTTPException(422, result.error.message)

    repo = DispatchRepository(db)
    existing = repo.get_by_project(pid)
    saved = repo.update(result.unwrap()) if existing else repo.add(result.unwrap())

    ProjectRepository(db).update(tr.unwrap())
    log_action(
        db, accion="entrega_confirmada", user_id=user.id, user_email=user.email,
        entidad_tipo="proyecto", entidad_id=pid,
        detalle=f"Entregado a {saved.destinatario}",
    )
    db.commit()
    return s.DeliveryOut(
        id=saved.id, project_id=saved.project_id, fecha_entrega=saved.fecha_entrega,
        hora_entrega=saved.hora_entrega, destinatario=saved.destinatario,
        detalle_entregado=saved.detalle_entregado, notas=saved.notas,
        fecha_registro=saved.fecha_registro,
    )


@router.post("/proyectos/{pid}/negar", response_model=s.DenialOut, status_code=201)
def deny(pid: str, body: s.DenialIn, db: DbSession, user: DespachoUser):
    project = _get_project(db, pid)
    tr = project_service.set_estado_despacho(project, "negado", now=_now())
    if not tr.is_ok():
        raise HTTPException(422, tr.error.message)

    result = dispatch_service.register_denial(
        id=new_id(), project_id=pid, motivo=body.motivo, detalle=body.detalle,
        registrado_por=user.id, fecha=_now(),
    )
    if not result.is_ok():
        raise HTTPException(422, result.error.message)

    DenialRepository(db).add(result.unwrap())
    ProjectRepository(db).update(tr.unwrap())
    log_action(
        db, accion="proyecto_negado", user_id=user.id, user_email=user.email,
        entidad_tipo="proyecto", entidad_id=pid, detalle=body.motivo,
    )
    db.commit()
    d = result.unwrap()
    return s.DenialOut(
        id=d.id, project_id=d.project_id, motivo=d.motivo, detalle=d.detalle, fecha=d.fecha,
    )


@router.post("/proyectos/{pid}/resolver-negacion", response_model=dict)
def resolve_denial(pid: str, db: DbSession, _: DespachoUser):
    project = _get_project(db, pid)
    tr = project_service.set_estado_despacho(project, "pendiente_entrega", now=_now())
    if not tr.is_ok():
        raise HTTPException(422, tr.error.message)
    saved = ProjectRepository(db).update(tr.unwrap())
    db.commit()
    return {"estado_despacho": saved.estado_despacho}


@router.post("/proyectos/{pid}/estado", response_model=dict)
def set_state(pid: str, body: s.DispatchStateRequest, db: DbSession, _: DespachoUser):
    project = _get_project(db, pid)
    tr = project_service.set_estado_despacho(project, body.target, now=_now())
    if not tr.is_ok():
        raise HTTPException(422, tr.error.message)
    saved = ProjectRepository(db).update(tr.unwrap())
    db.commit()
    return {"estado_despacho": saved.estado_despacho}
