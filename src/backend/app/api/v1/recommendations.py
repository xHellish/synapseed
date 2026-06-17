from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.recommendation import RecommendationStatus
from app.repositories import (
    AuditRepository,
    DistributorRepository,
    LmrRepository,
    RecommendationRepository,
)
from app.schemas.common import RecommendationRequest
from app.services.recommendation_query_service import (
    RecommendationNotFoundError,
    RecommendationQueryService,
)
from app.services.recommendation_service import RecommendationService
from app.services.recommendation_stream_service import RecommendationStreamService
from app.services.task_dispatcher import CeleryTaskDispatcher, TaskDispatcher

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_task_dispatcher() -> TaskDispatcher:
    return CeleryTaskDispatcher()


def get_recommendation_service(
    db: AsyncSession = Depends(get_db),
    task_dispatcher: TaskDispatcher = Depends(get_task_dispatcher),
) -> RecommendationService:
    return RecommendationService(
        RecommendationRepository(db),
        AuditRepository(db),
        task_dispatcher,
    )


def get_recommendation_stream_service() -> RecommendationStreamService:
    return RecommendationStreamService()


def get_recommendation_query_service(db: AsyncSession = Depends(get_db)) -> RecommendationQueryService:
    return RecommendationQueryService(
        RecommendationRepository(db),
        AuditRepository(db),
        DistributorRepository(db),
        LmrRepository(db),
    )


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
    return await service.request_recommendation(payload, int(current_user["id"]))


@router.get("/history", summary="Historial de recomendaciones del usuario")
async def history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: RecommendationStatus | None = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    query_service: RecommendationQueryService = Depends(get_recommendation_query_service),
) -> list:
    return await query_service.history(
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
    query_service: RecommendationQueryService = Depends(get_recommendation_query_service),
) -> dict:
    try:
        return await query_service.detail(recommendation_id, int(current_user["id"]))
    except RecommendationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recomendación no encontrada",
        ) from exc


@router.get("/{recommendation_id}/providers", summary="Distribuidores de la recomendación")
async def providers(
    recommendation_id: int,
    current_user: dict = Depends(get_current_user),
    query_service: RecommendationQueryService = Depends(get_recommendation_query_service),
) -> list[dict[str, object]]:
    try:
        return await query_service.providers(recommendation_id, int(current_user["id"]))
    except RecommendationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recomendación no encontrada",
        ) from exc


@router.get("/stream/{ticket_id}", summary="Stream de progreso (SSE)")
async def stream(
    ticket_id: str,
    stream_service: RecommendationStreamService = Depends(get_recommendation_stream_service),
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
