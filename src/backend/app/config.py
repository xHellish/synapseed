"""Configuración de la aplicación, cargada desde variables de entorno.

Usa ``pydantic-settings`` para tipado estricto y validación temprana.
Las variables se leen de ``.env`` o del entorno del sistema.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global de SynapSeed Backend.

    Todas las variables se documentan en ``.env.example`` en la raíz del repo.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Entorno
    app_env: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = True
    log_level: str = "INFO"
    project_name: str = "SynapSeed"
    api_v1_prefix: str = "/api/v1"

    # Base de datos: una URL async (runtime) y una sync (Alembic)
    database_url: str = Field(
        default="postgresql+asyncpg://synapseed:synapseed@localhost:5432/synapseed",
        description="URL asyncpg para SQLAlchemy (Supabase pooler o local).",
    )
    database_url_sync: str = Field(
        default="postgresql+psycopg2://synapseed:synapseed@localhost:5432/synapseed",
        description="URL síncrona para Alembic.",
    )
    supabase_url: str = ""
    supabase_anon_key: str = ""
    db_pool_size: int = 20
    db_max_overflow: int = 10

    # Redis y Celery: broker (cola) y backend (resultados) para tareas async
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_task_time_limit: int = 600
    celery_worker_prefetch_multiplier: int = 1
    celery_worker_concurrency: int = 1

    # Seguridad: clave y parametros del JWT local, mas los origenes permitidos por CORS
    jwt_secret: str = "change-me-in-production"  # noqa: S105
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    backend_cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"],
    )

    # OpenRouter: proveedor del LLM de chat que usan los agentes
    openrouter_api_key: str = "your-openrouter-api-key-here"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_chat_model: str = "openrouter/free"
    openrouter_rpm_limit: int = 20
    openrouter_max_retries: int = 5

    # Google Gemini: genera los embeddings de 768 dims para la busqueda semantica
    gemini_api_key: str = "your-gemini-api-key-here"
    google_embedding_model: str = "models/text-embedding-004"
    embedding_dim: int = 768

    # SSE: intervalos del stream de progreso
    sse_keepalive_interval: int = 15
    sse_heartbeat_timeout: int = 120

    # Observabilidad
    sentry_dsn: str | None = None

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def _parse_cors(cls, value: str | list[str]) -> list[str]:
        """Acepta tanto un JSON serializado como una lista nativa."""
        import json

        if isinstance(value, str):
            value = value.strip()
            if value.startswith("["):
                return json.loads(value)
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_production(self) -> bool:
        """True si estamos en producción."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """True si estamos en desarrollo local."""
        return self.app_env == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton de configuración cacheado en memoria.

    ``lru_cache`` evita releer ``.env`` en cada llamada. Para tests, llamar
    ``get_settings.cache_clear()``.
    """
    return Settings()
