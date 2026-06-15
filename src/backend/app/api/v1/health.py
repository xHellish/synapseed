from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check del backend")
async def health() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "env": settings.app_env,
        "service": "synapseed-backend",
        "checks": {"database": "pending", "redis": "pending", "gemini": "pending"},
    }
