"""Router de Desarrollo: plan, fases, miembros, avance, cancelación, adjuntos."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.domain.attachment import service as attachment_service
from app.domain.development import service as dev_service
from app.domain.development.model import ProjectMember
from app.domain.payment import service as payment_service
from app.domain.project import service as project_service
from app.domain.user.model import Departamento, User
from app.infrastructure.api import schemas_desarrollo as s
from app.infrastructure.api import schemas_ventas as sv
from app.infrastructure.db.models import new_id
from app.infrastructure.db.repositories.audit import log_action
from app.infrastructure.db.repositories.desarrollo import (
    AttachmentRepository,
    CancellationRepository,
    MemberRepository,
    PhaseRepository,
    PlanRepository,
    ProgressRepository,
)
from app.infrastructure.db.repositories.users import UserRepository
from app.infrastructure.db.repositories.ventas import PaymentRepository, ProjectRepository
from app.infrastructure.security.deps import DbSession, require_department
from app.infrastructure.storage.files import read_upload, save_upload

router = APIRouter(prefix="/api/desarrollo", tags=["desarrollo"])

DesarrolloUser = Annotated[User, Depends(require_department(Departamento.DESARROLLO))]

# Quién puede subir, listar y descargar adjuntos. El mismo conjunto en las tres
# rutas: si un departamento sube evidencia, tiene que poder verla y bajarla.
PuedeAdjuntos = Annotated[
    User,
    Depends(
        require_department(
            Departamento.DESARROLLO,
            Departamento.TECNOLOGIA,
            Departamento.DESPACHO,
            Departamento.VENTAS,
        )
    ),
]


def _now() -> datetime:
    return datetime.now(UTC)


def _plan_out(p) -> s.PlanOut:
    return s.PlanOut(
        id=p.id, project_id=p.project_id, resumen=p.resumen, objetivos=p.objetivos,
        horas_estimadas=p.horas_estimadas, created_at=p.created_at,
    )


def _phase_out(p, activo: bool = True) -> s.PhaseOut:
    return s.PhaseOut(
        id=p.id, orden=p.orden, nombre=p.nombre, descripcion=p.descripcion,
        fecha_inicio=p.fecha_inicio, fecha_fin_estimada=p.fecha_fin_estimada,
        fecha_fin_real=p.fecha_fin_real, horas_estimadas=p.horas_estimadas,
        horas_reales=p.horas_reales, estado=p.estado,
        # Las fases solo se pueden mover mientras el desarrollo esté en curso.
        acciones=dev_service.acciones_fase(p) if activo else (),
    )


def _fases_pendientes(db, pid: str) -> bool:
    plan = PlanRepository(db).get_by_project(pid)
    if plan is None:
        return False
    return dev_service.fases_pendientes(PhaseRepository(db).list_by_plan(plan.id))


def _proyecto_out(db, p, pagado) -> sv.ProjectOut:
    """Serializa un proyecto con las acciones que puede ejecutar Desarrollo."""
    return sv.ProjectOut(
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
        acciones=project_service.acciones_desarrollo(
            p, fases_pendientes=_fases_pendientes(db, p.id)
        ),
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _get_project_or_404(db, pid: str):
    project = ProjectRepository(db).get(pid)
    if project is None:
        raise HTTPException(404, "Proyecto no encontrado")
    return project


def _miembros_out(db, pid: str) -> list[dict]:
    repo = MemberRepository(db)
    users = {u.id: u for u in UserRepository(db).list_all()}
    return [
        s.MemberOut(
            id=m.id, user_id=m.user_id,
            nombre_usuario=users[m.user_id].nombre if m.user_id in users else "—",
            rol_proyecto=m.rol_proyecto, fecha_asignacion=m.fecha_asignacion,
        ).model_dump(mode="json")
        for m in repo.list_by_project(pid)
    ]


def _en_desarrollo(project) -> bool:
    """Solo se trabaja en fases/avances cuando el proyecto está en desarrollo."""
    return project.estado_desarrollo == "en_desarrollo"


def _exigir_en_desarrollo(project) -> None:
    if not _en_desarrollo(project):
        raise HTTPException(422, "Primero inicia el desarrollo del proyecto para continuar")


@router.get("/proyectos")
def list_projects(db: DbSession, _: DesarrolloUser):
    """Columnas del tablero de Desarrollo.

    El dominio decide en qué columna cae cada proyecto; el frontend solo las pinta.
    """
    proyectos = ProjectRepository(db).list_all()
    pagos_repo = PaymentRepository(db)

    payload = {
        p.id: _proyecto_out(db, p, payment_service.sumar_pagos(pagos_repo.list_by_project(p.id)))
        for p in proyectos
    }
    return {
        grupo: [payload[p.id] for p in items]
        for grupo, items in project_service.agrupar_desarrollo(proyectos).items()
    }


@router.get("/proyectos/{pid}/acciones", response_model=dict)
def project_actions(pid: str, db: DbSession, _: DesarrolloUser):
    """Acciones disponibles para Desarrollo (el backend decide, el frontend solo las pinta)."""
    project = _get_project_or_404(db, pid)
    return {
        "acciones": project_service.acciones_desarrollo(
            project, fases_pendientes=_fases_pendientes(db, pid)
        ),
        "estado_desarrollo": project.estado_desarrollo,
    }


@router.get("/proyectos/{pid}/plan")
def get_plan(pid: str, db: DbSession, _: DesarrolloUser):
    plan = PlanRepository(db).get_by_project(pid)
    if plan is None:
        raise HTTPException(404, "El proyecto aún no tiene plan")
    project = _get_project_or_404(db, pid)
    activo = _en_desarrollo(project)
    fases = PhaseRepository(db).list_by_plan(plan.id)
    avances = ProgressRepository(db).list_by_project(pid)
    users = {u.id: u for u in UserRepository(db).list_all()}
    return {
        "plan": _plan_out(plan),
        "fases": [_phase_out(f, activo) for f in fases],
        "miembros": _miembros_out(db, pid),
        "avances": [
            s.ProgressOut(
                id=a.id, phase_id=a.phase_id, porcentaje=a.porcentaje, notas=a.notas,
                fecha=a.fecha, autor=users[a.user_id].nombre if a.user_id in users else "—",
            ).model_dump(mode="json")
            for a in avances
        ],
        "horas_totales_fases": dev_service.plan_horas_por_fases(fases),
        "estado_desarrollo": project.estado_desarrollo,
        "puede_registrar_avance": activo,
        "acciones": project_service.acciones_desarrollo(
            project, fases_pendientes=_fases_pendientes(db, pid)
        ),
    }


@router.post("/proyectos/{pid}/plan", status_code=201)
def create_plan(pid: str, body: s.CreatePlanWithPhasesRequest, db: DbSession, user: DesarrolloUser):
    _get_project_or_404(db, pid)
    if PlanRepository(db).get_by_project(pid) is not None:
        raise HTTPException(409, "El proyecto ya tiene un plan")

    plan_result = dev_service.create_plan(
        id=new_id(), project_id=pid, resumen=body.resumen, objetivos=body.objetivos,
        horas_estimadas=body.horas_estimadas, created_by=user.id, now=_now(),
    )
    if not plan_result.is_ok():
        raise HTTPException(422, plan_result.error.message)
    plan = plan_result.unwrap()
    PlanRepository(db).add(plan)

    phase_repo = PhaseRepository(db)
    for f in body.fases:
        pr = dev_service.create_phase(
            id=new_id(), plan_id=plan.id, orden=f.orden, nombre=f.nombre,
            descripcion=f.descripcion, horas_estimadas=f.horas_estimadas,
            fecha_inicio=f.fecha_inicio, fecha_fin_estimada=f.fecha_fin_estimada,
        )
        if not pr.is_ok():
            raise HTTPException(422, f"Fase '{f.nombre}': {pr.error.message}")
        phase_repo.add(pr.unwrap())

    member_repo = MemberRepository(db)
    for uid in body.miembros:
        if UserRepository(db).get_by_id(uid) is None:
            raise HTTPException(404, f"Usuario {uid} no encontrado")
        member_repo.add(
            ProjectMember(
                id=new_id(), project_id=pid, user_id=uid,
                rol_proyecto="Miembro", fecha_asignacion=_now(),
            )
        )

    # Proyecto pasa a en_planificacion
    tr = project_service.set_estado_desarrollo(_get_project_or_404(db, pid), "en_planificacion", now=_now())
    if not tr.is_ok():
        raise HTTPException(422, tr.error.message)
    ProjectRepository(db).update(tr.unwrap())

    db.commit()
    return _plan_out(plan)


@router.get("/proyectos/{pid}/fases/{fid}", response_model=s.PhaseOut)
def get_phase(pid: str, fid: str, db: DbSession, _: DesarrolloUser) -> s.PhaseOut:
    phase = PhaseRepository(db).get(fid)
    if phase is None:
        raise HTTPException(404, "Fase no encontrada")
    return _phase_out(phase)


@router.post("/proyectos/{pid}/fases/{fid}/estado", response_model=s.PhaseOut)
def change_phase_state(pid: str, fid: str, body: s.PhaseStateRequest, db: DbSession, user: DesarrolloUser):
    _exigir_en_desarrollo(_get_project_or_404(db, pid))
    repo = PhaseRepository(db)
    phase = repo.get(fid)
    if phase is None:
        raise HTTPException(404, "Fase no encontrada")
    result = dev_service.set_phase_state(phase, body.target, now=_now())
    if not result.is_ok():
        raise HTTPException(422, result.error.message)
    saved = repo.update(result.unwrap())
    db.commit()
    return _phase_out(saved)


@router.post("/proyectos/{pid}/avance", response_model=s.ProgressOut, status_code=201)
def record_progress(pid: str, body: s.ProgressIn, db: DbSession, user: DesarrolloUser):
    _exigir_en_desarrollo(_get_project_or_404(db, pid))
    result = dev_service.record_progress(
        id=new_id(), project_id=pid, phase_id=body.phase_id, user_id=user.id,
        porcentaje=body.porcentaje, notas=body.notas, fecha=_now(),
    )
    if not result.is_ok():
        raise HTTPException(422, result.error.message)
    saved = ProgressRepository(db).add(result.unwrap())
    db.commit()
    users = {u.id: u for u in UserRepository(db).list_all()}
    return s.ProgressOut(
        id=saved.id, phase_id=saved.phase_id, porcentaje=saved.porcentaje,
        notas=saved.notas, fecha=saved.fecha,
        autor=users.get(saved.user_id).nombre if saved.user_id in users else "—",
    )


@router.post("/proyectos/{pid}/iniciar", response_model=dict)
def start_development(pid: str, db: DbSession, _: DesarrolloUser):
    repo = ProjectRepository(db)
    project = _get_project_or_404(db, pid)
    tr = project_service.set_estado_desarrollo(project, "en_desarrollo", now=_now())
    if not tr.is_ok():
        raise HTTPException(422, tr.error.message)
    saved = repo.update(tr.unwrap())
    db.commit()
    return {"estado_desarrollo": saved.estado_desarrollo}


@router.post("/proyectos/{pid}/completar", response_model=dict)
def complete_development(pid: str, db: DbSession, _: DesarrolloUser):
    repo = ProjectRepository(db)
    project = _get_project_or_404(db, pid)

    # Todas las fases deben estar completadas (regla viva en el dominio)
    plan = PlanRepository(db).get_by_project(pid)
    fases = PhaseRepository(db).list_by_plan(plan.id) if plan is not None else []
    error = dev_service.error_fases_pendientes(fases)
    if error is not None:
        raise HTTPException(422, error)

    tr = project_service.set_estado_desarrollo(project, "completado", now=_now())
    if not tr.is_ok():
        raise HTTPException(422, tr.error.message)
    saved = repo.update(tr.unwrap())
    db.commit()
    return {"estado_desarrollo": saved.estado_desarrollo}


@router.post("/proyectos/{pid}/pasar-despacho", response_model=dict)
def send_to_despacho(pid: str, db: DbSession, _: DesarrolloUser):
    repo = ProjectRepository(db)
    project = _get_project_or_404(db, pid)
    tr = project_service.puede_pasar_a_despacho(project)
    if not tr.is_ok():
        raise HTTPException(422, tr.error.message)
    saved = repo.update(tr.unwrap())
    db.commit()
    return {"estado_desarrollo": saved.estado_desarrollo}


@router.post("/proyectos/{pid}/cancelar", response_model=s.CancellationOut, status_code=201)
def cancel_project(pid: str, body: s.CancellationIn, db: DbSession, user: DesarrolloUser):
    project = _get_project_or_404(db, pid)

    # 1) Validar que la transición a 'cancelado' es permitida (antes de grabar nada)
    tr = project_service.set_estado_desarrollo(project, "cancelado", now=_now())
    if not tr.is_ok():
        raise HTTPException(422, tr.error.message)

    # 2) Crear el informe de cancelación (expediente)
    result = dev_service.create_cancellation(
        id=new_id(), project_id=pid, motivo=body.motivo, informe=body.informe,
        cancelado_por=user.id, fecha=_now(),
    )
    if not result.is_ok():
        raise HTTPException(422, result.error.message)

    CancellationRepository(db).add(result.unwrap())
    ProjectRepository(db).update(tr.unwrap())
    log_action(
        db, accion="proyecto_cancelado", user_id=user.id, user_email=user.email,
        entidad_tipo="proyecto", entidad_id=pid, detalle=body.motivo,
    )
    db.commit()
    c = result.unwrap()
    return s.CancellationOut(
        id=c.id, project_id=c.project_id, motivo=c.motivo, informe=c.informe, fecha=c.fecha,
    )


@router.get("/proyectos/{pid}/cancelacion", response_model=s.CancellationOut | None)
def get_cancellation(pid: str, db: DbSession, _: DesarrolloUser):
    c = CancellationRepository(db).get_by_project(pid)
    if c is None:
        return None
    return s.CancellationOut(
        id=c.id, project_id=c.project_id, motivo=c.motivo, informe=c.informe, fecha=c.fecha,
    )


# --- Miembros del proyecto ---------------------------------------------------


@router.get("/catalogo-usuarios", response_model=list[s.CatalogoUsuarioOut])
def catalogo_usuarios(db: DbSession, _: DesarrolloUser):
    """Usuarios activos que Desarrollo puede asignar a sus proyectos."""
    activos = filter(lambda u: u.estado == "activo", UserRepository(db).list_all())
    return [
        s.CatalogoUsuarioOut(id=u.id, nombre=u.nombre, departamento=u.departamento.value)
        for u in activos
    ]


@router.post("/proyectos/{pid}/miembros", response_model=list[s.MemberOut])
def add_members(pid: str, body: s.AddMembersRequest, db: DbSession, _: DesarrolloUser):
    _get_project_or_404(db, pid)
    member_repo = MemberRepository(db)
    user_repo = UserRepository(db)
    ya_asignados = {m.user_id for m in member_repo.list_by_project(pid)}
    for uid in body.user_ids:
        if uid in ya_asignados:
            continue
        if user_repo.get_by_id(uid) is None:
            raise HTTPException(404, f"Usuario {uid} no encontrado")
        member_repo.add(
            ProjectMember(
                id=new_id(), project_id=pid, user_id=uid,
                rol_proyecto="Miembro", fecha_asignacion=_now(),
            )
        )
        ya_asignados.add(uid)
    db.commit()
    return _miembros_out(db, pid)


@router.delete("/proyectos/{pid}/miembros/{mid}", status_code=204)
def remove_member(pid: str, mid: str, db: DbSession, _: DesarrolloUser):
    miembro = next((m for m in MemberRepository(db).list_by_project(pid) if m.id == mid), None)
    if miembro is None:
        raise HTTPException(404, "Miembro no encontrado")
    MemberRepository(db).delete(mid)
    db.commit()


# --- Adjuntos ---------------------------------------------------------------


@router.post("/adjuntos/{entidad_tipo}/{entidad_id}", response_model=s.AttachmentOut, status_code=201)
async def upload_attachment(
    entidad_tipo: str,
    entidad_id: str,
    db: DbSession,
    user: PuedeAdjuntos,
    file: UploadFile = File(...),
):
    from app.config import get_settings

    tipo = attachment_service.validate_entidad_tipo(entidad_tipo)
    if not tipo.is_ok():
        raise HTTPException(422, tipo.error.message)

    content = await file.read()
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    check = attachment_service.validate_upload(
        nombre=file.filename or "archivo", mime=file.content_type or "", tamano=len(content), max_bytes=max_bytes
    )
    if not check.is_ok():
        raise HTTPException(422, check.error.message)

    att_id = new_id()
    safe = attachment_service.safe_filename(check.unwrap(), att_id)
    save_upload(safe, content)

    from app.domain.attachment.model import Attachment

    att = Attachment(
        id=att_id, entidad_tipo=entidad_tipo, entidad_id=entidad_id, nombre=check.unwrap(),
        ruta=safe, mime=file.content_type or "", tamano=len(content), subido_por=user.id, fecha=_now(),
    )
    AttachmentRepository(db).add(att)
    db.commit()
    return s.AttachmentOut(
        id=att.id, entidad_tipo=att.entidad_tipo, entidad_id=att.entidad_id,
        nombre=att.nombre, mime=att.mime, tamano=att.tamano, fecha=att.fecha,
    )


# OJO: la descarga se declara ANTES que el listado. Si no, /adjuntos/{aid}/descargar
# casa con /adjuntos/{entidad_tipo}/{entidad_id} y se responde [] en vez del binario.

@router.get("/adjuntos/{aid}/descargar")
def download_attachment(aid: str, db: DbSession, _: PuedeAdjuntos):
    att = AttachmentRepository(db).get(aid)
    if att is None:
        raise HTTPException(404, "Archivo no encontrado")
    path = read_upload(att.ruta)
    if path is None:
        raise HTTPException(404, "El archivo físico no existe")
    import tempfile
    from pathlib import Path

    tmp = Path(tempfile.gettempdir()) / att.ruta
    tmp.write_bytes(path)
    return FileResponse(tmp, media_type=att.mime, filename=att.nombre)


@router.get("/adjuntos/{entidad_tipo}/{entidad_id}", response_model=list[s.AttachmentOut])
def list_attachments(entidad_tipo: str, entidad_id: str, db: DbSession, _: PuedeAdjuntos):
    rows = AttachmentRepository(db).list_by_entity(entidad_tipo, entidad_id)
    return [
        s.AttachmentOut(
            id=r.id, entidad_tipo=r.entidad_tipo, entidad_id=r.entidad_id, nombre=r.nombre,
            mime=r.mime, tamano=r.tamano, fecha=r.fecha,
        )
        for r in rows
    ]
