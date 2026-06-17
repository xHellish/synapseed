from __future__ import annotations

from abc import ABC, abstractmethod


class TaskDispatcher(ABC):
    @abstractmethod
    async def dispatch_recommendation_generation(self, ticket_id: str) -> None:
        """Encola la generación de una recomendación."""


class CeleryTaskDispatcher(TaskDispatcher):
    async def dispatch_recommendation_generation(self, ticket_id: str) -> None:
        from app.workers.tasks import generate_recommendation

        generate_recommendation.delay(ticket_id)
