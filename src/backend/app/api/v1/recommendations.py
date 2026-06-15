from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.security import get_current_user
from app.schemas.common import RecommendationRequest

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

RECOMMENDATIONS: list[dict[str, object]] = []


@router.post("/request", status_code=status.HTTP_202_ACCEPTED, summary="Solicitar recomendación")
async def request_recommendation(
    payload: RecommendationRequest,
    current_user: dict[str, object] = Depends(get_current_user),
) -> dict[str, object]:
    ticket_id = str(uuid4())
    recommendation = {
        "id": str(uuid4()),
        "ticket_id": ticket_id,
        "user_id": current_user["id"],
        "status": "queued",
        "crop": payload.crop,
        "crop_stage": payload.crop_stage,
        "problem_to_solve": payload.problem_to_solve,
        "soil_type": payload.soil_type,
        "max_budget_per_liter": payload.max_budget_per_liter,
        "final_recommendation": {
            "summary": "Recomendación generada en modo demo.",
            "products": [
                {"rank": 1, "name": "Producto A", "estimated_cost": 12.5},
                {"rank": 2, "name": "Producto B", "estimated_cost": 10.0},
                {"rank": 3, "name": "Producto C", "estimated_cost": 9.0},
            ],
        },
    }
    RECOMMENDATIONS.append(recommendation)
    return {"ticket_id": ticket_id, "status": "accepted", "message": "Recomendación encolada"}


@router.get("/history", summary="Historial de recomendaciones")
async def history(current_user: dict[str, object] = Depends(get_current_user)) -> list[dict[str, object]]:
    return [item for item in RECOMMENDATIONS if item["user_id"] == current_user["id"]]


@router.get("/{recommendation_id}", summary="Detalle de recomendación")
async def detail(recommendation_id: str, current_user: dict[str, object] = Depends(get_current_user)) -> dict[str, object]:
    for item in RECOMMENDATIONS:
        if item["id"] == recommendation_id and item["user_id"] == current_user["id"]:
            return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recomendación no encontrada")


@router.get("/{recommendation_id}/providers", summary="Proveedores de la recomendación")
async def providers(recommendation_id: str, current_user: dict[str, object] = Depends(get_current_user)) -> list[dict[str, object]]:
    for item in RECOMMENDATIONS:
        if item["id"] == recommendation_id and item["user_id"] == current_user["id"]:
            return [
                {"name": "AgroDistribuidora Norte", "email": "ventas@norte.cr", "phone": "+506-2233-4455", "location": "Heredia"},
                {"name": "Fertilizantes del Valle", "email": "info@valle.cr", "phone": "+506-2244-5566", "location": "Alajuela"},
            ]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recomendación no encontrada")


@router.get("/stream/{ticket_id}", summary="Stream de progreso (SSE)")
async def stream(ticket_id: str) -> StreamingResponse:
    async def event_stream() -> object:
        yield 'event: message\ndata: {"ticket_id": "%s", "status": "queued"}\n\n' % ticket_id

    return StreamingResponse(event_stream(), media_type="text/event-stream")
