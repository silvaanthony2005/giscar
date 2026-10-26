from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

# WAL para concurrencia de lectura en SQLite de un solo PC.
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Importa TODOS los módulos de modelos para que registren sus tablas en
    # Base.metadata; si falta alguno, create_all no crearía esa tabla.
    from app.infrastructure.db import (  # noqa: F401
        models,
        models_audit,
        models_desarrollo,
        models_despacho,
        models_ventas,
    )

    Base.metadata.create_all(bind=engine)

    # create_all no añade columnas a tablas ya existentes: migración mínima de la
    # base local (SQLite) para que las altas nuevas de cliente puedan guardarla.
    with engine.connect() as conn:
        columnas = {row[1] for row in conn.execute(text("PRAGMA table_info(customers)"))}
        if "representante" not in columnas:
            conn.execute(text("ALTER TABLE customers ADD COLUMN representante VARCHAR(255)"))
        # Asignación de técnicos: la columna única pasa a la tabla
        # incident_assignees (varios responsables) y se vacía para no repetir.
        conn.execute(
            text(
                """
                INSERT INTO incident_assignees (id, incident_id, user_id)
                SELECT lower(hex(randomblob(16))), id, asignado_a FROM incidents
                WHERE asignado_a IS NOT NULL
                """
            )
        )
        conn.execute(text("UPDATE incidents SET asignado_a = NULL"))
        # Proyectos en Despacho que aún deben saldo: ahora esperan el cobro.
        conn.execute(
            text(
                """
                UPDATE projects SET estado_despacho = 'pendiente_cobro'
                WHERE estado_despacho = 'pendiente_entrega'
                  AND estado_desarrollo = 'enviado_despacho'
                  AND monto_total > COALESCE(
                        (SELECT SUM(monto) FROM payments WHERE payments.project_id = projects.id),
                        0)
                """
            )
        )
        conn.commit()
