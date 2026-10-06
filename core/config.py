from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    entorno: str = "desarrollo"  # "desarrollo" | "produccion"
    frontend_url: str = "http://localhost:5173"

    osrm_base_url: str = "http://router.project-osrm.org"
    solver_time_limit_segundos: int = 5
    nominatim_base_url: str = "https://nominatim.openstreetmap.org"

    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 días

    # Login con Google: sin client_id y client_secret la función queda deshabilitada.
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = ""
    google_timeout_segundos: float = 10

    @property
    def google_habilitado(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @model_validator(mode="after")
    def _redirect_uri_por_defecto(self) -> "Settings":
        # En producción la API comparte origin con el frontend; en desarrollo (API en :8000)
        # hay que configurar GOOGLE_REDIRECT_URI explícitamente.
        if not self.google_redirect_uri:
            self.google_redirect_uri = f"{self.frontend_url}/api/v1/auth/google/callback"
        return self

    @field_validator("database_url")
    @classmethod
    def _usar_driver_psycopg(cls, valor: str) -> str:
        # Railway (y otros hosts) entregan postgresql:// o postgres://; SQLAlchemy necesita el driver explícito.
        for prefijo in ("postgres://", "postgresql://"):
            if valor.startswith(prefijo):
                return "postgresql+psycopg://" + valor.removeprefix(prefijo)
        return valor


@lru_cache
def obtener_settings() -> Settings:
    return Settings()


settings = obtener_settings()
