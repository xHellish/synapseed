from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.audit_log import AuditAction
from app.models.recommendation import RecommendationStatus
from app.repositories import AuditRepository, RecommendationRepository
from app.schemas.common import RecommendationRequest

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post(
    "/request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Solicitar recomendación",
)
async def request_recommendation(
    payload: RecommendationRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    recommendations = RecommendationRepository(db)
    audit = AuditRepository(db)

    ticket_id = str(uuid4())

    rec = await recommendations.create_recommendation(
        {
            "ticket_id": ticket_id,
            "user_id": int(current_user["id"]),
            "crop": payload.crop,
            "crop_stage": payload.crop_stage,
            "problem": payload.problem_to_solve,
            # Mapear problem_to_solve como problem_category también
            "problem_category": payload.problem_to_solve,
            "soil_type": payload.soil_type,
            "humidity": payload.humidity,
            "temperature": payload.temperature,
            "water_quality": payload.water_quality,
            "budget_range": str(payload.max_budget_per_liter),
            "last_agrochemical_used": payload.last_agrochemical,
            "status": RecommendationStatus.PENDING,
        }
    )

    await audit.log(
        action=AuditAction.RECOMMENDATION_REQUEST,
        user_id=int(current_user["id"]),
        entity_type="recommendation",
        entity_id=rec.id,
    )

    # Encolar la tarea asíncrona en Celery
    from app.workers.tasks import generate_recommendation
    generate_recommendation.delay(ticket_id)

    return {
        "ticket_id": ticket_id,
        "recommendation_id": rec.id,
        "status": rec.status.value,
        "message": "Recomendación encolada correctamente",
    }


@router.get("/history", summary="Historial de recomendaciones del usuario")
async def history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: RecommendationStatus | None = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    recommendations = RecommendationRepository(db)
    items = await recommendations.get_by_user_id(
        int(current_user["id"]),
        skip=skip,
        limit=limit,
        status=status_filter,
    )
    return [
        {
            "id": r.id,
            "ticket_id": r.ticket_id,
            "crop": r.crop,
            "problem": r.problem,
            "status": r.status.value,
            "created_at": r.created_at.isoformat(),
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in items
    ]


@router.get("/{recommendation_id}", summary="Detalle de una recomendación")
async def detail(
    recommendation_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    recommendations = RecommendationRepository(db)
    audit = AuditRepository(db)

    rec = await recommendations.get_with_products(recommendation_id)
    if not rec or rec.user_id != int(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recomendación no encontrada",
        )

    await audit.log(
        action=AuditAction.RECOMMENDATION_VIEW,
        user_id=int(current_user["id"]),
        entity_type="recommendation",
        entity_id=rec.id,
    )

    products = [
        {
            "rank": p.rank,
            "product_id": p.product_id,
            "nombre_comercial": p.product.nombre_comercial if p.product else None,
            "justification": p.justification,
            "dosis": p.dosis,
            "precio_estimado": float(p.precio_estimado) if p.precio_estimado else None,
            "toxicidad": p.toxicidad,
            "intervalo_seguridad": p.intervalo_seguridad,
        }
        for p in rec.products
    ]

    return {
        "id": rec.id,
        "ticket_id": rec.ticket_id,
        "crop": rec.crop,
        "crop_stage": rec.crop_stage,
        "problem": rec.problem,
        "status": rec.status.value,
        "current_step": rec.current_step,
        "error_message": rec.error_message,
        "created_at": rec.created_at.isoformat(),
        "completed_at": rec.completed_at.isoformat() if rec.completed_at else None,
        "products": products,
    }


@router.get("/{recommendation_id}/providers", summary="Distribuidores de la recomendación")
async def providers(
    recommendation_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list:
    from app.repositories import DistributorRepository

    recommendations = RecommendationRepository(db)
    distributors = DistributorRepository(db)

    rec = await recommendations.get_with_products(recommendation_id)
    if not rec or rec.user_id != int(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recomendación no encontrada",
        )

    # Recolectar distribuidores únicos de todos los productos recomendados
    seen_ids: set[int] = set()
    result = []
    for rec_product in rec.products:
        dist_list = await distributors.get_by_product(rec_product.product_id)
        for d in dist_list:
            if d.id not in seen_ids:
                seen_ids.add(d.id)
                result.append(
                    {
                        "id": d.id,
                        "nombre": d.nombre,
                        "correo": d.correo,
                        "telefono": d.telefono,
                        "ubicacion": d.ubicacion,
                        "provincia": d.provincia,
                        "canton": d.canton,
                    }
                )
    return result


@router.get("/stream/{ticket_id}", summary="Stream de progreso (SSE)")
async def stream(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    recommendations = RecommendationRepository(db)
    rec = await recommendations.get_by_ticket_id(ticket_id)

    current_status = rec.status.value if rec else "not_found"

    async def event_stream():
        import json
        data = json.dumps({"ticket_id": ticket_id, "status": current_status})
        yield f"event: status\ndata: {data}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
