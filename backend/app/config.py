from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

# backend/app/config.py -> backend/
BASE_DIR = Path(__file__).resolve().parent.parent


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
