"""Servicio del agregado Project. Funciones puras: estado + pagos -> Result."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from datetime import datetime

from app.domain.project.model import Project
from app.domain.project.states import DESARROLLO_SM, DESPACHO_SM, VENTAS_SM
from app.domain.shared.money import Money
from app.domain.shared.state_machine import StateMachine
from app.domain.shared.types import DomainError, Err, Ok, Result

# Estados de Ventas en los que el proyecto ya salió del departamento.
_SALIO_VENTAS = frozenset({"enviado_desarrollo", "cerrado"})


def create_project(
    *,
    id: str,
    codigo: str,
    titulo: str,
    descripcion_detallada: str,
    customer_id: str,
    monto_total: Money,
    contacto_nombre: str,
    contacto_telefono: str | None,
    contacto_email: str | None,
    contacto_direccion: str | None,
    created_by: str,
    now: datetime,
) -> Result[Project, DomainError]:
    if not titulo.strip():
        return Err(DomainError("project.titulo_vacio", "El título es obligatorio"))
    if len(descripcion_detallada.strip()) < 20:
        return Err(
            DomainError(
                "project.descripcion_corta",
                "El levantamiento debe detallar el proyecto (mínimo 20 caracteres)",
            )
        )
    if monto_total.cents <= 0:
        return Err(DomainError("project.monto_invalido", "El monto total debe ser mayor a cero"))

    states = Project.new_state_fields()
    return Ok(
        Project(
            id=id,
            codigo=codigo,
            titulo=titulo.strip(),
            descripcion_detallada=descripcion_detallada.strip(),
            customer_id=customer_id,
            monto_total=monto_total,
            contacto_nombre=contacto_nombre,
            contacto_telefono=contacto_telefono,
            contacto_email=contacto_email,
            contacto_direccion=contacto_direccion,
            estado_ventas=states["estado_ventas"],
            estado_desarrollo=states["estado_desarrollo"],
            estado_despacho=states["estado_despacho"],
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
    )


def _transition(
    project: Project,
    sm: StateMachine[str],
    field: str,
    target: str,
    now: datetime,
) -> Result[Project, DomainError]:
    current = getattr(project, field)
    next_state = sm.next(current, target)
    if not next_state.is_ok():
        return next_state  # type: ignore[return-value]
    return Ok(replace(project, **{field: next_state.unwrap(), "updated_at": now}))  # type: ignore[arg-type]


def set_estado_ventas(project: Project, target: str, *, now: datetime) -> Result[Project, DomainError]:
    return _transition(project, VENTAS_SM, "estado_ventas", target, now)


def set_estado_desarrollo(project: Project, target: str, *, now: datetime) -> Result[Project, DomainError]:
    return _transition(project, DESARROLLO_SM, "estado_desarrollo", target, now)


def set_estado_despacho(project: Project, target: str, *, now: datetime) -> Result[Project, DomainError]:
    return _transition(project, DESPACHO_SM, "estado_despacho", target, now)


# --- Reglas de negocio de Ventas sobre pagos -------------------------------


def saldo_restante(monto_total: Money, pagado: Money) -> Money:
    return Money(max(0, monto_total.cents - pagado.cents))


def puede_pasar_a_desarrollo(project: Project, pagado: Money) -> Result[Project, DomainError]:
    """Se pasa a desarrollo solo si el cliente pagó al menos el 50%."""
    if pagado.cents < project.monto_total.cents // 2:
        return Err(
            DomainError(
                "project.pago_insuficiente",
                "Debe cobrarse al menos el 50% antes de pasar a Desarrollo",
            )
        )
    return set_estado_ventas(project, "enviado_desarrollo", now=project.updated_at)


def puede_pasar_a_despacho(project: Project) -> Result[Project, DomainError]:
    if project.estado_desarrollo != "completado":
        return Err(
            DomainError(
                "project.desarrollo_incompleto",
                "El proyecto debe estar completado antes de pasar a Despacho",
            )
        )
    result = set_estado_desarrollo(project, "enviado_despacho", now=project.updated_at)
    if not result.is_ok():
        return result
    # Al llegar a Despacho entra directamente en 'pendiente_entrega'
    arrived = result.unwrap()  # type: ignore[union-attr]
    tr = set_estado_despacho(arrived, "pendiente_entrega", now=arrived.updated_at)
    if not tr.is_ok():
        return tr
    return Ok(replace(arrived, estado_despacho=tr.unwrap().estado_despacho))  # type: ignore[arg-type]


def puede_entregar(project: Project, pagado: Money, saldo: Money) -> Result[Project, DomainError]:
    """Entrega solo con saldo en cero (se liquidó el resto del proyecto).

    Al entregar, la venta también queda cerrada en Ventas: no hay nada más
    que cobrar ni gestionar desde ese departamento.
    """
    if saldo.cents > 0:
        return Err(
            DomainError(
                "project.saldo_pendiente",
                f"Queda un saldo de {saldo.amount} pendiente antes de entregar",
            )
        )
    entregado = set_estado_despacho(project, "entregado", now=project.updated_at)
    if not entregado.is_ok():
        return entregado
    if entregado.unwrap().estado_ventas != "enviado_desarrollo":
        return entregado
    return set_estado_ventas(entregado.unwrap(), "cerrado", now=entregado.unwrap().updated_at)


# --- Acciones disponibles (las calcula el backend; el frontend solo las pinta) ---

_ACCIONES_DESARROLLO: dict[str, str] = {
    "en_planificacion": "crear_plan",
    "en_desarrollo": "iniciar",
    "completado": "completar",
    "enviado_despacho": "pasar_despacho",
    "cancelado": "cancelar",
}


def acciones_ventas(project: Project, pagado: Money) -> tuple[str, ...]:
    """Acciones que Ventas puede ejecutar ahora mismo sobre el proyecto."""
    if project.estado_ventas in _SALIO_VENTAS:
        return ()
    saldo = saldo_restante(project.monto_total, pagado)
    pago = ("registrar_pago",) if saldo.cents > 0 else ()
    paso = ("pasar_desarrollo",) if puede_pasar_a_desarrollo(project, pagado).is_ok() else ()
    return (*pago, *paso)


def acciones_desarrollo(project: Project, *, fases_pendientes: bool = False) -> tuple[str, ...]:
    """Acciones que Desarrollo puede ejecutar ahora mismo sobre el proyecto.

    `fases_pendientes` refleja la regla de negocio: el proyecto solo se marca
    como completado cuando todas sus fases están completadas.
    """
    if project.estado_ventas not in _SALIO_VENTAS:
        return ()
    acciones = tuple(
        _ACCIONES_DESARROLLO[target]
        for target in DESARROLLO_SM.allowed_targets(project.estado_desarrollo)
        if target in _ACCIONES_DESARROLLO
    )
    if fases_pendientes:
        acciones = tuple(a for a in acciones if a != "completar")
    return acciones


def acciones_despacho(project: Project, pagado: Money) -> tuple[str, ...]:
    """Acciones que Despacho puede ejecutar ahora mismo sobre el proyecto."""
    if project.estado_desarrollo != "enviado_despacho":
        return ()
    saldo = saldo_restante(project.monto_total, pagado)
    objetivos = DESPACHO_SM.allowed_targets(project.estado_despacho)
    acciones: list[str] = []
    if project.estado_despacho != "entregado" and saldo.cents > 0:
        acciones.append("liquidar")
    if "entregado" in objetivos and puede_entregar(project, pagado, saldo).is_ok():
        acciones.append("confirmar_entrega")
    if "negado" in objetivos:
        acciones.append("negar")
    if "pendiente_entrega" in objetivos and project.estado_despacho == "negado":
        acciones.append("resolver_negacion")
    return tuple(acciones)


# --- Columnas de los tableros (las agrupa el backend; el frontend solo pinta) ---

GRUPOS_DESARROLLO: tuple[str, ...] = ("recibidos", "en_curso", "historial")
GRUPOS_DESPACHO: tuple[str, ...] = ("pendientes", "cerrados")

_EN_CURSO_DESARROLLO = frozenset({"en_planificacion", "en_desarrollo"})
_HISTORIAL_DESARROLLO = frozenset({"completado", "cancelado", "enviado_despacho"})
_CERRADOS_DESPACHO = frozenset({"entregado", "negado"})


def grupo_desarrollo(project: Project) -> str:
    """Columna del tablero de Desarrollo en la que cae el proyecto."""
    if project.estado_desarrollo in _EN_CURSO_DESARROLLO:
        return "en_curso"
    if project.estado_desarrollo in _HISTORIAL_DESARROLLO:
        return "historial"
    return "recibidos"


def agrupar_desarrollo(projects: Iterable[Project]) -> dict[str, tuple[Project, ...]]:
    """Agrupa los proyectos que ya llegaron a Desarrollo en sus tres columnas."""
    llegados = tuple(filter(lambda p: p.estado_ventas in _SALIO_VENTAS, projects))
    return {
        grupo: tuple(filter(lambda p: grupo_desarrollo(p) == grupo, llegados))
        for grupo in GRUPOS_DESARROLLO
    }


def grupo_despacho(project: Project) -> str:
    """Columna del tablero de Despacho: abierto o ya resuelto."""
    return "cerrados" if project.estado_despacho in _CERRADOS_DESPACHO else "pendientes"


def agrupar_despacho(projects: Iterable[Project]) -> dict[str, tuple[Project, ...]]:
    """Agrupa los proyectos en alcance de Despacho en sus dos columnas."""
    alcance = tuple(projects)
    return {
        grupo: tuple(filter(lambda p: grupo_despacho(p) == grupo, alcance))
        for grupo in GRUPOS_DESPACHO
    }


# --- Contadores del sidebar (los calcula el backend; el frontend solo pinta) ---


def pendientes_ventas(projects: Iterable[Project]) -> int:
    """Proyectos que Ventas aún gestiona (no se han enviado a Desarrollo)."""
    return len(tuple(filter(lambda p: p.estado_ventas not in _SALIO_VENTAS, projects)))


def activos_desarrollo(projects: Iterable[Project]) -> int:
    """Proyectos recibidos o en curso en Desarrollo (sin cerrar ni cancelar)."""
    return len(
        tuple(
            filter(
                lambda p: p.estado_ventas in _SALIO_VENTAS
                and grupo_desarrollo(p) in ("recibidos", "en_curso"),
                projects,
            )
        )
    )


def pendientes_despacho(projects: Iterable[Project]) -> int:
    """Proyectos en Desarrollo pendientes de entregar o resolver."""
    alcance = tuple(
        filter(
            lambda p: p.estado_desarrollo == "enviado_despacho"
            or p.estado_despacho in {"pendiente_entrega", "negado", "entregado"},
            projects,
        )
    )
    return len(agrupar_despacho(alcance)["pendientes"])

