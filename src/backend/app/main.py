"""SynapSeed — Application entrypoint (FastAPI app factory).

Este archivo es el esqueleto inicial. La fase 0 solo expone:

* ``/api/v1/health`` → health check (DB + Redis + LLM)
* ``/`` → metadata
* ``/docs`` y ``/redoc`` → OpenAPI auto-generado

Los routers reales (auth, users, zones, recommendations, providers, catalogs)
se agregan en las fases 1, 2 y 3.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings

# Configurar logging antes de cualquier otra cosa
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Ciclo de vida de la app: startup y shutdown.

    En la fase 0 solo logueamos. En fases siguientes conectamos DB/Redis y
    cerramos pools.
    """
    settings = get_settings()
    logger.info(
        "🚀 SynapSeed backend v%s iniciando (env=%s, debug=%s)",
        __version__,
        settings.app_env,
        settings.debug,
    )
    yield
    logger.info("👋 SynapSeed backend detenido")


def create_app() -> FastAPI:
    """App factory principal.

    Devuelve una instancia de ``FastAPI`` lista para servir con uvicorn:
        uvicorn app.main:app --reload
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.project_name,
        version=__version__,
        description=(
            "Plataforma de recomendación de agroquímicos para agricultores "
            "costarricenses. Solo información, sin compras."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # --- CORS: solo orígenes configurados en .env ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Health check (DB + Redis + LLM API) ---
    @app.get(
        f"{settings.api_v1_prefix}/health",
        tags=["health"],
        summary="Health check del sistema",
    )
    async def health() -> dict:
        """Verifica el estado del backend y sus dependencias externas.

        En la fase 0 retorna solo metadata. En la fase 2 agregamos checks
        reales contra PostgreSQL, Redis y Gemini API.
        """
        return {
            "status": "ok",
            "version": __version__,
            "env": settings.app_env,
            "service": "synapseed-backend",
            "checks": {
                "database": "pending",
                "redis": "pending",
                "gemini": "pending",
            },
        }

    # --- Root: metadata simple ---
    @app.get("/", tags=["meta"], include_in_schema=False)
    async def root() -> dict:
        return {
            "name": settings.project_name,
            "version": __version__,
            "docs": "/docs",
            "redoc": "/redoc",
            "api": settings.api_v1_prefix,
        }

    # Aquí en fases siguientes se agregan routers:
    # app.include_router(auth.router, prefix=settings.api_v1_prefix)
    # app.include_router(users.router, prefix=settings.api_v1_prefix)
    # app.include_router(zones.router, prefix=settings.api_v1_prefix)
    # app.include_router(recommendations.router, prefix=settings.api_v1_prefix)
    # app.include_router(providers.router, prefix=settings.api_v1_prefix)
    # app.include_router(catalogs.router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
