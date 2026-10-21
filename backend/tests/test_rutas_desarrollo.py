"""Contratos de las rutas de Desarrollo que el frontend pinta tal cual.

Comprueban tres reglas reales, sin BD ni servidor (AGENTS.md):
1. Fases y avances solo existen cuando el proyecto está *en desarrollo*.
   Antes de pulsar «Iniciar desarrollo» el backend no ofrecía acciones de
   fase ni avisaba al intentarlo, y el usuario se perdía el motivo.
2. El alta/baja de miembros y el catálogo de usuarios están declarados:
   sin ellos la sección de equipo no podía asignar a nadie.
3. El catálogo de equipo solo lista usuarios activos de Producción.
"""

from dataclasses import replace
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from fastapi.routing import APIRoute

from app.domain.development.model import Phase
from app.domain.project import service as project_service
from app.domain.project.model import Project
from app.domain.shared.money import Money
from app.domain.user.model import Departamento, EstadoUsuario, User
from app.domain.user.service import change_estado, create_user
from app.infrastructure.api.routes import desarrollo

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _project(desarrollo: str) -> Project:
    r = project_service.create_project(
        id="p1",
        codigo="PRJ-2026-0001",
        titulo="Sistema de inventario",
        descripcion_detallada="Desarrollo de un sistema completo de inventario con reportes.",
        customer_id="c1",
        monto_total=Money.from_amount(100000),
        contacto_nombre="Gerente",
        contacto_telefono="809-555-0001",
        contacto_email=None,
        contacto_direccion=None,
        created_by="u1",
        now=NOW,
    )
    assert r.is_ok(), r
    return replace(r.unwrap(), estado_desarrollo=desarrollo)  # type: ignore[union-attr]


def _phase() -> Phase:
    return Phase(
        id="f1", plan_id="pl1", orden=1, nombre="Fase 1", descripcion="d",
        fecha_inicio=None, fecha_fin_estimada=None, fecha_fin_real=None,
        horas_estimadas=10, horas_reales=0, estado="pendiente",
    )


@pytest.mark.parametrize("estado", ["pendiente", "en_planificacion"])
def test_fases_y_avances_bloqueados_hasta_iniciar(estado: str):
    with pytest.raises(HTTPException) as exc:
        desarrollo._exigir_en_desarrollo(_project(estado))
    assert exc.value.status_code == 422
    assert "Primero inicia la producción" in str(exc.value.detail)


def test_en_desarrollo_se_puede_trabajar():
    desarrollo._exigir_en_desarrollo(_project("en_desarrollo"))  # no lanza


def test_no_se_ofrecen_acciones_de_fase_si_no_esta_en_desarrollo():
    assert desarrollo._phase_out(_phase(), activo=False).acciones == ()
    assert desarrollo._phase_out(_phase(), activo=True).acciones == ("en_curso",)


MIEMBROS = "/api/desarrollo/proyectos/{pid}/miembros"


def _rutas(method: str, path: str) -> list[APIRoute]:
    return [
        r
        for r in desarrollo.router.routes
        if isinstance(r, APIRoute) and r.path == path and method in r.methods
    ]


def test_rutas_de_miembros_y_catalogo_estan_declaradas():
    assert len(_rutas("GET", "/api/desarrollo/catalogo-usuarios")) == 1
    assert len(_rutas("POST", MIEMBROS)) == 1
    assert len(_rutas("DELETE", MIEMBROS + "/{mid}")) == 1


def _usuario(departamento: Departamento, estado: EstadoUsuario) -> User:
    r = create_user(
        id=f"u-{departamento.value}-{estado.value}",
        email=f"{departamento.value}.{estado.value}@giscar.com",
        password_hash="x" * 20,
        nombre="Ana Reyes",
        now=NOW,
        departamento=departamento,
    )
    assert r.is_ok(), r
    return change_estado(r.unwrap(), estado, now=NOW)


def test_el_catalogo_solo_ofrece_usuarios_activos_de_produccion():
    """El equipo de un proyecto de Producción sale solo del propio departamento."""
    assert desarrollo._es_asignable(_usuario(Departamento.DESARROLLO, EstadoUsuario.ACTIVO))
    assert not desarrollo._es_asignable(_usuario(Departamento.VENTAS, EstadoUsuario.ACTIVO))
    assert not desarrollo._es_asignable(_usuario(Departamento.DESARROLLO, EstadoUsuario.BLOQUEADO))
