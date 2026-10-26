from datetime import UTC, datetime

from app.domain.user.model import Departamento, EstadoUsuario
from app.domain.user.service import (
    can_login,
    change_estado,
    change_password,
    create_user,
    normalizar_telefono,
    set_departamento,
    update_profile,
    validar_cambio_usuario,
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
    assert updated.telefono == "8095551234"  # el dominio guarda solo dígitos
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


def test_change_password_inmutable():
    u = _user()
    nuevo = "y" * 60
    changed = change_password(u, password_hash=nuevo, now=NOW).unwrap()
    assert changed.password_hash == nuevo
    assert u.password_hash == HASH  # el original no cambia


def test_change_password_rechaza_hash_corto():
    r = change_password(_user(), password_hash="corto", now=NOW)
    assert not r.is_ok()
    assert r.error.code == "user.hash_corto"


def test_desactivado_no_puede_login_y_no_es_visible():
    u = change_estado(_user(), EstadoUsuario.DESACTIVADO, now=NOW)
    assert not can_login(u).is_ok()
    assert not u.is_visible()


def test_update_profile_cambia_email():
    u = _user()
    updated = update_profile(u, email=" Nuevo@Giscar.com ", now=NOW).unwrap()
    assert updated.email == "nuevo@giscar.com"


def test_update_profile_rechaza_email_invalido():
    r = update_profile(_user(), email="no-es-email", now=NOW)
    assert not r.is_ok()
    assert r.error.code == "user.email_invalido"


def test_normalizar_telefono():
    assert normalizar_telefono("809-555 (0001)") == "8095550001"
    assert normalizar_telefono("  ") is None
    assert normalizar_telefono("abc123") is None
    assert normalizar_telefono(None) is None


def test_update_profile_vacia_campo_con_cadena_vacia():
    u = _user(telefono="809-555-0001", cargo="Analista")
    assert u.telefono == "8095550001"  # create_user normaliza
    updated = update_profile(u, telefono="", cargo="  ", now=NOW).unwrap()
    assert updated.telefono is None
    assert updated.cargo is None
    assert u.telefono == "8095550001"  # el original no cambia


def test_update_profile_none_no_toca_el_campo():
    u = _user(telefono="809-555-0001")
    updated = update_profile(u, nombre="Otro Nombre", now=NOW).unwrap()
    assert updated.telefono == "8095550001"


def test_validar_cambio_no_auto_bloqueo():
    u = _user()
    r = validar_cambio_usuario([u], actor_id=u.id, objetivo=u, estado=EstadoUsuario.BLOQUEADO)
    assert not r.is_ok()
    assert r.error.code == "user.auto_bloqueo"


def test_validar_cambio_protege_ultimo_rrhh():
    rrhh = _user(id="u1", email="r@giscar.com", departamento=Departamento.RRHH)
    r = validar_cambio_usuario([rrhh], actor_id="otro", objetivo=rrhh, estado=EstadoUsuario.DESACTIVADO)
    assert not r.is_ok()
    assert r.error.code == "user.ultimo_rrhh"
    # Cambiarlo de departamento también deja el sistema sin RRHH
    r = validar_cambio_usuario([rrhh], actor_id="otro", objetivo=rrhh, departamento=Departamento.VENTAS)
    assert not r.is_ok()
    # Con otro RRHH activo sí se puede
    otro = _user(id="u2", email="r2@giscar.com", departamento=Departamento.RRHH)
    r = validar_cambio_usuario([rrhh, otro], actor_id="otro", objetivo=rrhh, estado=EstadoUsuario.DESACTIVADO)
    assert r.is_ok()


def test_validar_cambio_sin_rrhh_no_frena_a_ventas():
    v = _user(id="u1", email="v@giscar.com")
    r = validar_cambio_usuario([v], actor_id="otro", objetivo=v, estado=EstadoUsuario.DESACTIVADO)
    assert r.is_ok()
