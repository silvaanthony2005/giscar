"""Crea datos iniciales: usuario administrador RRHH y uno por departamento."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.user import service as user_service
from app.domain.user.model import Departamento
from app.infrastructure.db.models import UserRow, new_id
from app.infrastructure.db.session import SessionLocal, init_db
from app.infrastructure.security.password import hash_password

SEED_PASSWORD = "giscar1234"

SEEDS: list[dict] = [
    {"email": "rrhh@giscar.com", "nombre": "Ana Reyes", "departamento": Departamento.RRHH, "cargo": "Directora de RRHH"},
    {"email": "ventas@giscar.com", "nombre": "Luis Pérez", "departamento": Departamento.VENTAS, "cargo": "Ejecutivo de ventas"},
    {"email": "produccion@giscar.com", "nombre": "Marta Gómez", "departamento": Departamento.DESARROLLO, "cargo": "Líder técnico"},
    {"email": "despacho@giscar.com", "nombre": "Carlos Díaz", "departamento": Departamento.DESPACHO, "cargo": "Coordinador de despacho"},
    {"email": "tecnologia@giscar.com", "nombre": "Sofía López", "departamento": Departamento.TECNOLOGIA, "cargo": "Soporte técnico"},
]


def seed() -> list[str]:
    init_db()
    now = datetime.now(UTC)
    created: list[str] = []
    with SessionLocal() as db:
        # Migración mínima: el correo del módulo de Producción cambió de nombre.
        # Se renombra el usuario existente para no duplicar la siembra.
        viejo = db.query(UserRow).filter(UserRow.email == "desarrollo@giscar.com").first()
        nuevo = db.query(UserRow).filter(UserRow.email == "produccion@giscar.com").first()
        if viejo is not None and nuevo is None:
            viejo.email = "produccion@giscar.com"
            # Se fija ya: sin esto la siembra no vería el correo renombrado
            # (autoflush está apagado) e intentaría crear un segundo usuario.
            db.commit()
        for item in SEEDS:
            exists = db.query(UserRow).filter(UserRow.email == item["email"]).first()
            if exists:
                continue
            result = user_service.create_user(
                id=new_id(),
                email=item["email"],
                password_hash=hash_password(SEED_PASSWORD),
                nombre=item["nombre"],
                departamento=item["departamento"],
                cargo=item["cargo"],
                now=now,
            )
            if result.is_ok():
                user = result.unwrap()
                db.add(
                    UserRow(
                        id=user.id,
                        email=user.email,
                        password_hash=user.password_hash,
                        nombre=user.nombre,
                        departamento=user.departamento.value,
                        cargo=user.cargo,
                        estado=user.estado.value,
                    )
                )
                created.append(item["email"])
        db.commit()
    return created


if __name__ == "__main__":
    emails = seed()
    print("Usuarios creados:", emails or "(ya existían)")
    print("Contraseña para todos:", SEED_PASSWORD)
