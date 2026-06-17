"""Routing de recomendaciones — capa delgada que delega a servicios inyectados.

Los handlers solo se ocupan de:
1. Recibir la request HTTP.
2. Extraer dependencias via ``Depends()``.
3. Llamar al servicio correspondiente.
4. Devolver la respuesta o lanzar una HTTPException.

La lógica de negocio vive en ``RecommendationService``.
La lógica de streaming SSE vive en ``RecommendationStreamService``.
El despacho de tareas se abstrae detrás de ``TaskDispatcher``.

Cumplimiento SOLID:
- SRP: el router solo maneja routing HTTP.
- DIP: los endpoints dependen de abstracciones (TaskDispatcher), no de Celery.
- OCP: cambiar de Celery a otro broker = crear nueva implementación de
  TaskDispatcher sin tocar este archivo.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.recommendation import RecommendationStatus
from app.repositories import AuditRepository, DistributorRepository, RecommendationRepository
from app.schemas.common import RecommendationRequest
from app.services.recommendation_service import RecommendationService
from app.services.recommendation_stream_service import RecommendationStreamService
from app.services.task_dispatcher import CeleryTaskDispatcher, TaskDispatcher

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# ---------------------------------------------------------------------------
# Proveedores de dependencia
# ---------------------------------------------------------------------------

def get_task_dispatcher() -> TaskDispatcher:
    """Retorna la implementación de ``TaskDispatcher`` activa (Celery por defecto)."""
    return CeleryTaskDispatcher()


def get_recommendation_service(
    db: AsyncSession = Depends(get_db),
    dispatcher: TaskDispatcher = Depends(get_task_dispatcher),
) -> RecommendationService:
    """Fabrica una instancia de ``RecommendationService`` con sus dependencias."""
    return RecommendationService(
        recommendation_repo=RecommendationRepository(db),
        audit_repo=AuditRepository(db),
        distributor_repo=DistributorRepository(db),
        dispatcher=dispatcher,
        db=db,
    )


def get_stream_service() -> RecommendationStreamService:
    """Fabrica una instancia de ``RecommendationStreamService``."""
    return RecommendationStreamService()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Solicitar recomendación",
)
async def request_recommendation(
    payload: RecommendationRequest,
    current_user: dict = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
) -> dict:
    return await service.request_recommendation(int(current_user["id"]), payload)


@router.get("/history", summary="Historial de recomendaciones del usuario")
async def history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: RecommendationStatus | None = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
) -> list:
    return await service.get_history(
        int(current_user["id"]),
        skip=skip,
        limit=limit,
        status_filter=status_filter,
    )


@router.get(
    "/{recommendation_id}",
    summary="Detalle de una recomendación",
)
async def detail(
    recommendation_id: int,
    current_user: dict = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
) -> dict:
    result = await service.get_detail(recommendation_id, int(current_user["id"]))
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recomendación no encontrada",
        )
    return result


@router.get("/{recommendation_id}/providers", summary="Distribuidores de la recomendación")
async def providers(
    recommendation_id: int,
    current_user: dict = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
) -> list[dict]:
    result = await service.get_providers(recommendation_id, int(current_user["id"]))
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recomendación no encontrada",
        )
    return result


@router.get("/stream/{ticket_id}", summary="Stream de progreso (SSE)")
async def stream(
    ticket_id: str,
    stream_service: RecommendationStreamService = Depends(get_stream_service),
) -> StreamingResponse:
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        stream_service.stream_recommendation_progress(ticket_id),
        media_type="text/event-stream",
        headers=headers,
    )
