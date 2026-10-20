import os
import sys
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        # Datos en %LOCALAPPDATA%\GCISCAR, fuera de la carpeta de instalación,
        # para que sobrevivan a desinstalaciones y actualizaciones del .exe.
        raiz = os.environ.get("LOCALAPPDATA")
        return Path(raiz) / "GCISCAR" if raiz else Path(sys.executable).resolve().parent
    # backend/app/config.py -> backend/
    return Path(__file__).resolve().parent.parent


BASE_DIR = _base_dir()


class Settings(BaseSettings):
    app_name: str = "GCISCAR"
    database_url: str = f"sqlite:///{BASE_DIR / 'giscar.db'}"
    uploads_dir: Path = BASE_DIR / "uploads"
    jwt_secret: str = "giscar-local-dev-secret-change-me-32bytes-min"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 8
    cors_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]
    max_upload_mb: int = 20

    model_config = {"env_prefix": "GISCAR_", "env_file": BASE_DIR / ".env"}


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    return settings
