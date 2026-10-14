from datetime import UTC, datetime

from app.domain.user.model import Departamento, EstadoUsuario
from app.domain.user.service import (
    can_login,
    change_estado,
    create_user,
    set_departamento,
    update_profile,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)
HASH = "x" * 20  # hash simulado largo


def _user(**kw):
    defaults = dict(
        id="u1",
        email="  Persona@Giscar.COM ",
        password_hash=HASH,
        nombre="  Ana Reyes  ",
        now=NOW,
        departamento=Departamento.VENTAS,
    )
    defaults.update(kw)
    result = create_user(**defaults)
    assert result.is_ok(), result
    return result.unwrap()


def test_create_normaliza_email_y_nombre():
    u = _user()
    assert u.email == "persona@giscar.com"
    assert u.nombre == "Ana Reyes"
    assert u.estado == EstadoUsuario.ACTIVO


def test_create_rechaza_email_invalido():
    r = create_user(id="u", email="no-es-email", password_hash=HASH, nombre="X", now=NOW)
    assert not r.is_ok()
    assert r.error.code == "user.email_invalido"


def test_create_rechaza_nombre_vacio():
    r = create_user(id="u", email="a@b.com", password_hash=HASH, nombre="   ", now=NOW)
    assert not r.is_ok()


def test_update_profile_inmutable():
    u = _user()
    updated = update_profile(u, telefono="809-555-1234", now=NOW).unwrap()
    assert updated.telefono == "809-555-1234"
    assert u.telefono is None  # original sin cambios


def test_update_profile_rechaza_nombre_vacio():
    u = _user()
    r = update_profile(u, nombre="  ", now=NOW)
    assert not r.is_ok()


def test_set_departamento_inmutable():
    u = _user()
    moved = set_departamento(u, Departamento.DESPACHO, now=NOW)
    assert moved.departamento == Departamento.DESPACHO
    assert u.departamento == Departamento.VENTAS


def test_cambiar_estado():
    u = _user()
    blocked = change_estado(u, EstadoUsuario.BLOQUEADO, now=NOW)
    assert not can_login(blocked).is_ok()
    assert can_login(u).is_ok()


def test_rrhh_ve_todo():
    u = _user(departamento=Departamento.RRHH)
    for dep in Departamento:
        assert u.can_access(dep)


def test_ventas_no_ve_otros():
    u = _user(departamento=Departamento.VENTAS)
    assert u.can_access(Departamento.VENTAS)
    assert not u.can_access(Departamento.DESARROLLO)


def test_usuarios_bloqueados():
    activo = _user(id="u1", email="a@giscar.com")
    bloqueado = change_estado(
        _user(id="u2", email="b@giscar.com"), EstadoUsuario.BLOQUEADO, now=NOW
    )
    from app.domain.user.service import usuarios_bloqueados

    assert usuarios_bloqueados([activo, bloqueado]) == 1
