from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from typing import Any

from redis.asyncio import Redis

from app.config import get_settings
from app.db.session import get_db_session
from app.repositories import RecommendationRepository


class RecommendationStreamService:
    def __init__(
        self,
        redis_url: str | None = None,
        redis_factory: Callable[..., Redis] = Redis.from_url,
    ) -> None:
        settings = get_settings()
        self.redis_url = redis_url or settings.redis_url
        self.redis_factory = redis_factory

    async def stream_recommendation_progress(self, ticket_id: str) -> AsyncIterator[str]:
        async with get_db_session() as db:
            recommendations = RecommendationRepository(db)
            recommendation = await recommendations.get_by_ticket_id(ticket_id)
            if not recommendation:
                yield self._format_event(
                    "status",
                    {"ticket_id": ticket_id, "status": "not_found"},
                )
                return

            yield self._format_event(
                "status",
                {
                    "ticket_id": ticket_id,
                    "status": recommendation.status.value,
                    "current_step": recommendation.current_step,
                    "error_message": recommendation.error_message,
                },
            )

            if recommendation.status.value in ("completed", "failed"):
                return

        redis_client = self.redis_factory(self.redis_url, decode_responses=True)
        pubsub = redis_client.pubsub()
        channel = f"recommendation_progress:{ticket_id}"
        await pubsub.subscribe(channel)

        try:
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message:
                    data = message["data"]
                    yield self._format_event("status", data)
                    if self._is_terminal_status(data):
                        break

                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            await redis_client.close()

    @staticmethod
    def _format_event(event_name: str, data: dict[str, Any] | str) -> str:
        if isinstance(data, dict):
            data = json.dumps(data)
        return f"event: {event_name}\ndata: {data}\n\n"

    @staticmethod
    def _is_terminal_status(data: str) -> bool:
        try:
            parsed = json.loads(data)
        except Exception:
            return False
        return parsed.get("status") in ("completed", "failed")
