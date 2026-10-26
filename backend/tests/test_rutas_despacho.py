"""La liquidación de Despacho debe emitir factura y su PDF debe ser descargable.

Test de integración con SQLite en memoria y la app real: override de `get_db`.
No usa el `giscar.db` del repositorio ni ejecuta el startup (seed/init_db).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.db import (  # noqa: F401 - registran las tablas en Base.metadata
    models,
    models_audit,
    models_desarrollo,
    models_despacho,
    models_ventas,
)
from app.infrastructure.db.models import UserRow
from app.infrastructure.db.models_audit import AuditLogRow
from app.infrastructure.db.models_ventas import CustomerRow, InvoiceRow, PaymentRow, ProjectRow
from app.infrastructure.db.session import Base, get_db
from app.infrastructure.security.password import hash_password
from app.main import app

PASSWORD = "prueba1234"


@pytest.fixture()
def api():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app), TestSession
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _seed(Session) -> None:
    now = datetime.now(UTC)
    with Session() as db:
        db.add_all(
            [
                UserRow(
                    id="u-desp", email="despacho@test.com", password_hash=hash_password(PASSWORD),
                    nombre="Despacho", departamento="despacho", estado="activo",
                ),
                UserRow(
                    id="u-vend", email="ventas@test.com", password_hash=hash_password(PASSWORD),
                    nombre="Ventas", departamento="ventas", estado="activo",
                ),
            ]
        )
        db.add(
            CustomerRow(
                id="c1", nombre="ACME S.A.", representante="Ana", documento="1-1",
                telefono="8095550000", direccion="Calle 1", created_by="u-vend",
                created_at=now, updated_at=now,
            )
        )
        db.add(
            ProjectRow(
                id="p1", codigo="PRJ-2026-0001", titulo="Portal ACME",
                descripcion_detallada="Portal de clientes con facturación y reportes.",
                customer_id="c1", monto_total=100_000, contacto_nombre="Ana",
                estado_ventas="enviado_desarrollo", estado_desarrollo="enviado_despacho",
                estado_despacho="pendiente_cobro", created_by="u-vend",
                created_at=now, updated_at=now,
            )
        )
        db.add(
            PaymentRow(
                id="pay1", project_id="p1", monto=50_000, porcentaje=50, tipo="anticipo",
                metodo_pago="efectivo", registrado_por="u-vend", fecha=now,
            )
        )
        db.commit()


def test_liquidar_emite_factura_y_despacho_puede_bajar_el_pdf(api):
    client, Session = api
    _seed(Session)

    login = client.post(
        "/api/auth/login", json={"email": "despacho@test.com", "password": PASSWORD}
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    year = datetime.now(UTC).year
    liquidar = client.post(
        "/api/despacho/proyectos/p1/liquidar",
        json={"metodo_pago": "transferencia"},
        headers=headers,
    )
    assert liquidar.status_code == 201, liquidar.text
    numero = f"FAC-{year}-00001"
    assert liquidar.json()["factura"]["numero"] == numero

    detalle = client.get("/api/despacho/proyectos/p1", headers=headers)
    assert detalle.status_code == 200
    assert [f["numero"] for f in detalle.json()["facturas"]] == [numero]

    pdf = client.get(f"/api/ventas/facturas/{liquidar.json()['factura']['id']}/pdf", headers=headers)
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")

    with Session() as db:
        assert db.execute(select(func.count()).select_from(InvoiceRow)).scalar_one() == 1
        assert db.execute(
            select(func.count()).select_from(AuditLogRow).where(
                AuditLogRow.accion == "factura_emitida"
            )
        ).scalar_one() == 1
