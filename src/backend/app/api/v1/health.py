from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app import __version__
from app.config import get_settings
from app.db.session import get_db

router = APIRouter(tags=["health"])


# Health check: lo usa Docker para saber si el backend esta listo (healthcheck del compose)
@router.get("/health", summary="Health check del backend")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    settings = get_settings()

    # Prueba la conexion a la DB con un SELECT 1 trivial
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "version": __version__,
        "env": settings.app_env,
        "service": "synapseed-backend",
        "checks": {
            "database": db_status,
            "redis": "pending",
            "gemini": "pending",
        },
    }
