"""Punto de entrada FastAPI. Monta routers, CORS y (en prod) el frontend build."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.infrastructure.api.routes import (
    auth,
    buscar,
    desarrollo,
    despacho,
    health,
    panel,
    rrhh,
    tecnologia,
    ventas,
)
from app.infrastructure.db.seed import seed
from app.infrastructure.db.session import init_db

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(panel.router)
    app.include_router(buscar.router)
    app.include_router(ventas.router)
    app.include_router(desarrollo.router)
    app.include_router(despacho.router)
    app.include_router(tecnologia.router)
    app.include_router(rrhh.router)

    # Sirve el build del frontend en producción (PC local). En el .exe congelado
    # el build viaja dentro del bundle; en dev, en frontend/dist del repo.
    if getattr(sys, "frozen", False):
        dist = Path(sys._MEIPASS) / "frontend" / "dist"
    else:
        dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    if dist.exists():
        assets = dist / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        # Fallback SPA: primero sirve ficheros reales del build (fuentes,
        # favicon...) y solo si no existe devuelve index.html para que la
        # recarga y los deep links funcionen con React Router.
        @app.get("/{full_path:path}", include_in_schema=False)
        def spa_fallback(full_path: str):
            if full_path.startswith("api/"):
                raise HTTPException(404, "No encontrado")
            candidate = (dist / full_path).resolve()
            if full_path and candidate.is_relative_to(dist) and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(dist / "index.html")

    @app.on_event("startup")
    def _startup() -> None:
        init_db()
        # Usuarios iniciales: una instalación nueva debe poder entrar (idempotente).
        seed()

    return app


app = create_app()


def run() -> None:
    import uvicorn

    if getattr(sys, "frozen", False):
        # En el .exe no hay recarga posible; se pasa el objeto app directo.
        uvicorn.run(app, host="127.0.0.1", port=8000)
    else:
        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
