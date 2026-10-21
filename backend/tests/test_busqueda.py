"""Tests del dominio de búsqueda global.

Funciones puras: sin BD, sin I/O. Mismo estado -> mismo resultado.
"""

from datetime import UTC, datetime

from app.domain.customer.model import Customer
from app.domain.incidence.model import Incidence
from app.domain.project.model import Project
from app.domain.project.service import create_project
from app.domain.search import service as search
from app.domain.search.model import Resultado
from app.domain.shared.money import Money
from app.domain.shared.types import Err, Ok
from app.domain.user.model import Departamento, EstadoUsuario, User

NOW = datetime(2026, 1, 1, tzinfo=UTC)

# --- normalización y validación ---------------------------------------------


def test_normalizar_quita_mayusculas_y_espacios():
    assert search.normalizar("  Hola   MUNDO ") == "hola mundo"


def test_validar_consulta_rechaza_un_caracter():
    r = search.validar_consulta("p")
    assert isinstance(r, Err)
    assert r.error.code == "search.consulta_corta"


def test_validar_consulta_rechaza_solo_espacios():
    assert isinstance(search.validar_consulta("   "), Err)


def test_validar_consulta_acepta_dos_caracteres():
    r = search.validar_consulta("ab")
    assert isinstance(r, Ok)
    assert r.unwrap() == "ab"


def test_coincide_es_insensible_a_mayusculas():
    assert search.coincide("PRJ-2026-0001", "prj-2026")
    assert search.coincide("ACME S.A.", "acme")
    assert not search.coincide("ACME S.A.", "globex")
    assert not search.coincide(None, "acme")
    assert not search.coincide("", "acme")


# --- RBAC: quién busca qué ---------------------------------------------------


def test_rrhh_busca_las_cuatro_categorias():
    assert search.tipos_buscables(Departamento.RRHH) == search.TIPOS


def test_cada_departamento_busca_lo_de_su_modulo():
    assert search.tipos_buscables(Departamento.VENTAS) == ("proyecto", "cliente")
    assert search.tipos_buscables(Departamento.DESARROLLO) == ("proyecto",)
    assert search.tipos_buscables(Departamento.DESPACHO) == ("proyecto",)
    assert search.tipos_buscables(Departamento.TECNOLOGIA) == ("incidencia",)


def test_tecnologia_no_puede_buscar_proyectos_ni_usuarios():
    tipos = search.tipos_buscables(Departamento.TECNOLOGIA)
    assert "proyecto" not in tipos
    assert "usuario" not in tipos
    assert "cliente" not in tipos


# --- fixtures ----------------------------------------------------------------


def _proyecto(**kw) -> Project:
    defaults = dict(
        id="p1",
        codigo="PRJ-2026-0001",
        titulo="Sistema de inventario",
        descripcion_detallada="Desarrollo de un sistema completo de inventario.",
        customer_id="c1",
        monto_total=Money.from_amount(100000),
        contacto_nombre="Gerente",
        contacto_telefono=None,
        contacto_email=None,
        contacto_direccion=None,
        created_by="u1",
        now=NOW,
    )
    defaults.update(kw)
    r = create_project(**defaults)
    assert r.is_ok(), r
    return r.unwrap()  # type: ignore[union-attr]


def _cliente(**kw) -> Customer:
    defaults = dict(
        id="c1",
        nombre="ACME S.A.",
        representante="Ana Reyes",
        documento="76.492.110-K",
        telefono="809-555-0001",
        email="contacto@acme.cl",
        direccion="Av. Principal 1",
        notas=None,
        created_by="u1",
        created_at=NOW,
        updated_at=NOW,
    )
    defaults.update(kw)
    return Customer(**defaults)


def _incidencia(**kw) -> Incidence:
    defaults = dict(
        id="i1",
        codigo="INC-2026-0001",
        titulo="Monitor sin imagen",
        descripcion="No da imagen tras encender.",
        equipo_afectado="MON-07",
        departamento_origen="ventas",
        prioridad="alta",
        estado="abierta",
        orden_llegada=1,
        reportado_por="u1",
        asignado_a=None,
        created_at=NOW,
        updated_at=NOW,
    )
    defaults.update(kw)
    return Incidence(**defaults)


def _usuario(**kw) -> User:
    defaults = dict(
        id="u1",
        email="ana@giscar.com",
        password_hash="x",
        nombre="Ana Reyes",
        documento=None,
        telefono=None,
        direccion=None,
        cargo="Jefa de RRHH",
        departamento=Departamento.RRHH,
        estado=EstadoUsuario.ACTIVO,
        created_at=NOW,
        updated_at=NOW,
    )
    defaults.update(kw)
    return User(**defaults)


# --- filtros por entidad -----------------------------------------------------


def test_buscar_proyectos_por_titulo_y_por_codigo():
    ps = [_proyecto(), _proyecto(id="p2", codigo="PRJ-2026-0002", titulo="Portal web")]
    assert [r.id for r in search.buscar_proyectos(ps, "inventario")] == ["p1"]
    assert [r.id for r in search.buscar_proyectos(ps, "prj-2026-0002")] == ["p2"]
    assert search.buscar_proyectos(ps, "zzz") == ()


def test_buscar_proyectos_no_mira_descripciones_largas():
    """El matching es sobre campos identificadores, no sobre texto largo."""
    ps = [_proyecto(descripcion_detallada="palabraclave secreta en la descripcion")]
    assert search.buscar_proyectos(ps, "palabraclave") == ()


def test_buscar_clientes_por_nombre_documento_y_correo():
    cs = [_cliente()]
    assert [r.id for r in search.buscar_clientes(cs, "acme")] == ["c1"]
    assert [r.id for r in search.buscar_clientes(cs, "76.492")] == ["c1"]
    assert [r.id for r in search.buscar_clientes(cs, "contacto@acme")] == ["c1"]
    assert search.buscar_clientes(cs, "globex") == ()


def test_buscar_incidencias_por_titulo_codigo_y_equipo():
    incs = [_incidencia()]
    assert [r.id for r in search.buscar_incidencias(incs, "monitor")] == ["i1"]
    assert [r.id for r in search.buscar_incidencias(incs, "inc-2026")] == ["i1"]
    assert [r.id for r in search.buscar_incidencias(incs, "mon-07")] == ["i1"]


def test_buscar_usuarios_por_nombre_correo_y_cargo():
    us = [_usuario()]
    assert [r.id for r in search.buscar_usuarios(us, "ana")] == ["u1"]
    assert [r.id for r in search.buscar_usuarios(us, "ana@giscar")] == ["u1"]
    assert [r.id for r in search.buscar_usuarios(us, "jefa")] == ["u1"]
    assert search.buscar_usuarios(us, "carlos") == ()


# --- agrupación y límite -----------------------------------------------------


def test_agrupar_omite_categorias_vacias():
    rs = search.buscar_proyectos([_proyecto()], "inventario")
    assert search.agrupar(rs, ()) == {"proyecto": list(rs)}


def test_agrupar_respeta_el_orden_de_TIPOS():
    ps = search.buscar_proyectos([_proyecto()], "inventario")
    cs = search.buscar_clientes([_cliente()], "acme")
    incs = search.buscar_incidencias([_incidencia()], "monitor")
    assert list(search.agrupar(ps, cs, incs)) == ["proyecto", "cliente", "incidencia"]


def test_recortar_limita_por_categoria():
    muchos = tuple(
        Resultado(tipo="proyecto", id=f"p{i}", titulo=f"T{i}")
        for i in range(search.MAX_POR_TIPO + 5)
    )
    assert len(search.recortar(muchos)) == search.MAX_POR_TIPO
    assert len(search.recortar(muchos, 3)) == 3
    assert search.recortar(muchos[:2]) == muchos[:2]


def test_agrupar_recorta_cada_categoria():
    muchos = tuple(
        Resultado(tipo="proyecto", id=f"p{i}", titulo=f"T{i}")
        for i in range(search.MAX_POR_TIPO + 5)
    )
    assert len(search.agrupar(muchos)["proyecto"]) == search.MAX_POR_TIPO


def test_resultado_no_lleva_url():
    """La ruta la decide el frontend: el dominio solo expresa qué se encontró."""
    r = Resultado(tipo="proyecto", id="p1", titulo="T")
    assert not hasattr(r, "url")
