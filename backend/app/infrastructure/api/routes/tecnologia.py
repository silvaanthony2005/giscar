"""Router de Tecnología: cola de incidencias, asignación, resolución con reporte.

Cualquier departamento puede reportar; Tecnología gestiona la cola.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.domain.incidence import service as incidence_service
from app.domain.user.model import Departamento, User
from app.infrastructure.api import schemas_despacho as s
from app.infrastructure.db.models import new_id
from app.infrastructure.db.repositories.audit import log_action
from app.infrastructure.db.repositories.despacho import (
    IncidentReportRepository,
    IncidentRepository,
)
from app.infrastructure.db.repositories.users import UserRepository
from app.infrastructure.security.deps import DbSession, require_department

router = APIRouter(prefix="/api/tecnologia", tags=["tecnologia"])

# Cualquier departamento puede REPORTAR incidencias
ReportIncidence = Annotated[
    User,
    Depends(
        require_department(
            Departamento.VENTAS,
            Departamento.DESARROLLO,
            Departamento.DESPACHO,
            Departamento.TECNOLOGIA,
            Departamento.RRHH,
        )
    ),
]

# Solo Tecnología gestiona (asignar, transicionar, resolver)
TecnologiaUser = Annotated[User, Depends(require_department(Departamento.TECNOLOGIA))]


def _now() -> datetime:
    return datetime.now(UTC)


def _next_codigo(repo: IncidentRepository) -> str:
    year = _now().year
    prefijo = f"INC-{year}-"
    numeros = [
        int(i.codigo[len(prefijo):])
        for i in repo.list_all()
        if i.codigo.startswith(prefijo) and i.codigo[len(prefijo):].isdigit()
    ]
    return f"{prefijo}{max(numeros, default=0) + 1:04d}"


def _incidence_out(inc, users: dict[str, User]) -> dict:
    return {
        "id": inc.id,
        "codigo": inc.codigo,
        "titulo": inc.titulo,
        "descripcion": inc.descripcion,
        "equipo_afectado": inc.equipo_afectado,
        "departamento_origen": inc.departamento_origen,
        "prioridad": inc.prioridad,
        "estado": inc.estado,
        "orden_llegada": inc.orden_llegada,
        "reportado_por": inc.reportado_por,
        "reportado_por_nombre": users.get(inc.reportado_por).nombre
        if inc.reportado_por in users
        else None,
        "asignados": [
            {
                "user_id": uid,
                "nombre": users[uid].nombre if uid in users else None,
                "cargo": users[uid].cargo if uid in users else None,
            }
            for uid in inc.asignados
        ],
        "created_at": inc.created_at,
    }


@router.post("/incidencias", status_code=201)
def create_incidence(body: s.CreateIncidenceRequest, db: DbSession, user: ReportIncidence):
    repo = IncidentRepository(db)
    result = incidence_service.create_incidence(
        id=new_id(), codigo=_next_codigo(repo), titulo=body.titulo,
        descripcion=body.descripcion, equipo_afectado=body.equipo_afectado,
        departamento_origen=user.departamento.value, prioridad=body.prioridad,
        orden_llegada=repo.next_orden(), reportado_por=user.id, now=_now(),
    )
    if not result.is_ok():
        raise HTTPException(422, result.error.message)
    saved = repo.add(result.unwrap())
    log_action(
        db, accion="incidencia_creada", user_id=user.id, user_email=user.email,
        entidad_tipo="incidencia", entidad_id=saved.id, detalle=saved.codigo,
    )
    db.commit()
    users = {u.id: u for u in UserRepository(db).list_all()}
    return _incidence_out(saved, users)


@router.get("/incidencias")
def list_incidences(db: DbSession, _: TecnologiaUser):
    """Cola ordenada por prioridad (desc) y orden de llegada (asc).

    Solo Tecnología (y RRHH, lectura global) la ve: los demás departamentos
    solo reportan, no consultan.
    """
    users = {u.id: u for u in UserRepository(db).list_all()}
    incidencias = incidence_service.ordenar_cola(IncidentRepository(db).list_all())
    return {
        "incidencias": [_incidence_out(i, users) for i in incidencias],
        "resumen": incidence_service.contar_por_estado(incidencias),
    }


@router.get("/incidencias/{iid}")
def get_incidence(iid: str, db: DbSession, _: TecnologiaUser):
    inc = IncidentRepository(db).get(iid)
    if inc is None:
        raise HTTPException(404, "Incidencia no encontrada")
    users = {u.id: u for u in UserRepository(db).list_all()}
    reportes = IncidentReportRepository(db).list_by_incident(iid)
    return {
        **_incidence_out(inc, users),
        "reportes": [
            {
                "id": r.id,
                "diagnostico": r.diagnostico,
                "solucion": r.solucion,
                "tiempo_resolucion_horas": r.tiempo_resolucion_horas,
                "resuelto_por": r.resuelto_por,
                "resuelto_por_nombre": users.get(r.resuelto_por).nombre
                if r.resuelto_por in users
                else None,
                "fecha": r.fecha,
            }
            for r in reportes
        ],
    }


def _error_asignacion(users: dict[str, User], user_ids: list[str]) -> tuple[int, str] | None:
    """Rechaza técnicos inexistentes o de otro departamento (la regla vive aquí, no en la UI)."""
    if any(uid not in users for uid in user_ids):
        return 404, "Usuario no encontrado"
    if any(users[uid].departamento != Departamento.TECNOLOGIA for uid in user_ids):
        return 422, "Solo se puede asignar personal de Tecnología"
    return None


@router.post("/incidencias/{iid}/asignar")
def assign(iid: str, body: s.AssignRequest, db: DbSession, _: TecnologiaUser):
    repo = IncidentRepository(db)
    inc = repo.get(iid)
    if inc is None:
        raise HTTPException(404, "Incidencia no encontrada")
    users = {u.id: u for u in UserRepository(db).list_all()}
    error = _error_asignacion(users, body.user_ids)
    if error is not None:
        raise HTTPException(*error)
    result = incidence_service.assign_incidence(inc, body.user_ids, now=_now())
    if not result.is_ok():
        raise HTTPException(422, result.error.message)
    saved = repo.update(result.unwrap())
    db.commit()
    return _incidence_out(saved, users)


@router.post("/incidencias/{iid}/estado")
def change_state(iid: str, body: s.IncidenceStateRequest, db: DbSession, _: TecnologiaUser):
    repo = IncidentRepository(db)
    inc = repo.get(iid)
    if inc is None:
        raise HTTPException(404, "Incidencia no encontrada")
    result = incidence_service.transition_incidence(inc, body.target, now=_now())
    if not result.is_ok():
        raise HTTPException(422, result.error.message)
    saved = repo.update(result.unwrap())
    db.commit()
    users = {u.id: u for u in UserRepository(db).list_all()}
    return _incidence_out(saved, users)


@router.post("/incidencias/{iid}/reporte", status_code=201)
def resolve_with_report(iid: str, body: s.IncidentReportIn, db: DbSession, user: TecnologiaUser):
    repo = IncidentRepository(db)
    inc = repo.get(iid)
    if inc is None:
        raise HTTPException(404, "Incidencia no encontrada")

    # La incidencia debe estar en proceso (o abierta -> primero en proceso)
    if inc.estado == "abierta":
        en_proceso = incidence_service.transition_incidence(inc, "en_proceso", now=_now())
        if en_proceso.is_ok():
            inc = repo.update(en_proceso.unwrap())

    result = incidence_service.create_report(
        id=new_id(), incident_id=iid, diagnostico=body.diagnostico,
        solucion=body.solucion, tiempo_resolucion_horas=body.tiempo_resolucion_horas,
        resuelto_por=user.id, fecha=_now(),
    )
    if not result.is_ok():
        raise HTTPException(422, result.error.message)

    # Transicionar a resuelta
    tr = incidence_service.transition_incidence(inc, "resuelta", now=_now())
    if not tr.is_ok():
        raise HTTPException(422, tr.error.message)

    IncidentReportRepository(db).add(result.unwrap())
    saved = repo.update(tr.unwrap())
    log_action(
        db, accion="incidencia_resuelta", user_id=user.id, user_email=user.email,
        entidad_tipo="incidencia", entidad_id=iid, detalle=saved.codigo,
    )
    db.commit()
    users = {u.id: u for u in UserRepository(db).list_all()}
    return {**_incidence_out(saved, users), "reporte_id": result.unwrap().id}


@router.get("/tecnicos", response_model=list[dict])
def list_tecnicos(db: DbSession, _: TecnologiaUser):
    users = UserRepository(db).list_all(Departamento.TECNOLOGIA)
    return [{"id": u.id, "nombre": u.nombre, "cargo": u.cargo} for u in users]
