from __future__ import annotations

from uuid import uuid4

from app.models.audit_log import AuditAction
from app.models.recommendation import RecommendationStatus
from app.repositories import AuditRepository, RecommendationRepository
from app.schemas.common import RecommendationRequest
from app.services.task_dispatcher import TaskDispatcher


class RecommendationService:
    def __init__(
        self,
        recommendation_repository: RecommendationRepository,
        audit_repository: AuditRepository,
        task_dispatcher: TaskDispatcher,
    ) -> None:
        self.recommendation_repository = recommendation_repository
        self.audit_repository = audit_repository
        self.task_dispatcher = task_dispatcher

    async def request_recommendation(
        self,
        payload: RecommendationRequest,
        user_id: int,
    ) -> dict:
        ticket_id = str(uuid4())
        recommendation = await self.recommendation_repository.create_recommendation(
            {
                "ticket_id": ticket_id,
                "user_id": user_id,
                "crop": payload.crop,
                "crop_stage": payload.crop_stage,
                "problem": payload.problem_to_solve,
                "problem_category": payload.problem_to_solve,
                "soil_type": payload.soil_type,
                "humidity": payload.humidity,
                "temperature": payload.temperature,
                "water_quality": payload.water_quality,
                "budget_range": str(payload.max_budget_per_liter),
                "last_agrochemical_used": payload.last_agrochemical,
                "zone_id": payload.zone_id,
                "status": RecommendationStatus.PENDING,
            }
        )

        await self.audit_repository.log(
            action=AuditAction.RECOMMENDATION_REQUEST,
            user_id=user_id,
            entity_type="recommendation",
            entity_id=recommendation.id,
        )

        await self.task_dispatcher.dispatch_recommendation_generation(ticket_id)

        return {
            "ticket_id": ticket_id,
            "recommendation_id": recommendation.id,
            "status": recommendation.status.value,
            "message": "Recomendación encolada correctamente",
        }
