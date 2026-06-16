"""SynapSeed — Application entrypoint (FastAPI app factory).

Expone los siguientes endpoints:

* ``/api/v1/health``          → health check
* ``/api/v1/auth/register``   → registro de nuevo usuario
* ``/api/v1/auth/login``      → login (JWT)
* ``/api/v1/users/me``        → perfil autenticado
* ``/api/v1/zones``           → CRUD de zonas agrícolas
* ``/api/v1/catalogs``        → catálogos (cultivos, suelos)
* ``/api/v1/recommendations`` → solicitud y consulta de recomendaciones
* ``/docs``                   → Swagger UI (interactivo)
* ``/redoc``                  → ReDoc
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app import __version__
from app.api.v1.router import api_router
from app.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Ciclo de vida de la app: startup y shutdown."""
    settings = get_settings()
    logger.info(
        "🚀 SynapSeed backend v%s iniciando (env=%s, debug=%s)",
        __version__,
        settings.app_env,
        settings.debug,
    )
    yield
    logger.info("👋 SynapSeed backend detenido")


def custom_openapi(app: FastAPI):
    """Genera el schema OpenAPI con el esquema Bearer JWT configurado."""

    def openapi():
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Servers: permite que Swagger UI envíe requests al host correcto
        schema["servers"] = [
            {"url": "http://localhost:8000", "description": "Desarrollo local"},
        ]

        # Esquema de seguridad Bearer JWT
        schema.setdefault("components", {})
        schema["components"]["securitySchemes"] = {
            "HTTPBearer": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": (
                    "Token JWT obtenido en **POST /api/v1/auth/login**.\n\n"
                    "Pegá el token en el botón **🔒 Authorize** (arriba a la derecha)."
                ),
            }
        }

        app.openapi_schema = schema
        return app.openapi_schema

    return openapi


def create_app() -> FastAPI:
    """App factory principal."""
    settings = get_settings()

    app = FastAPI(
        title="SynapSeed API",
        version=__version__,
        description=(
            "## Plataforma de recomendación de agroquímicos 🌱\n\n"
            "Recomienda agroquímicos a agricultores costarricenses basándose en cultivo, "
            "etapa, tipo de suelo y presupuesto.\n\n"
            "### Autenticación\n"
            "1. Ejecuta **POST `/api/v1/auth/login`** con tu cédula y contraseña.\n"
            "2. Copia el `access_token` de la respuesta.\n"
            "3. Hacé clic en **🔒 Authorize** (arriba a la derecha) y pegá el token.\n\n"
            "A partir de ahí todos los endpoints protegidos se autentican automáticamente."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.debug,
        lifespan=lifespan,
        contact={
            "name": "SynapSeed Team",
            "email": "synapseed@tec.ac.cr",
            "url": "https://github.com/xHellish/synapseed",
        },
        license_info={"name": "Proprietary"},
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routers: api_router (auth + users v2 Supabase) + routers legacy ---
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    from app.api.v1 import catalogs, health, recommendations, zones

    app.include_router(health.router, prefix=settings.api_v1_prefix)
    app.include_router(zones.router, prefix=settings.api_v1_prefix)
    app.include_router(catalogs.router, prefix=settings.api_v1_prefix)
    app.include_router(recommendations.router, prefix=settings.api_v1_prefix)

    # --- Root redirect metadata ---
    @app.get("/", tags=["meta"], include_in_schema=False)
    async def root() -> dict:
        return {
            "name": settings.project_name,
            "version": __version__,
            "docs": "/docs",
            "redoc": "/redoc",
            "api": settings.api_v1_prefix,
        }

    # --- Schema OpenAPI personalizado (Bearer JWT) ---
    app.openapi = custom_openapi(app)  # type: ignore[method-assign]

    return app


app = create_app()