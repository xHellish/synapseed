"""Servicio de streaming SSE para el progreso de recomendaciones — SRP.

Aísla toda la lógica de Redis pub/sub y formateo de Server-Sent Events
en una sola clase, separándola del routing HTTP.

Cumplimiento SOLID:
- SRP: ``RecommendationStreamService`` solo maneja la emisión de eventos SSE.
- DIP: obtiene la sesión de DB y el cliente Redis internamente, pero puede
  recibir una URL de Redis inyectada para facilitar tests.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator


class RecommendationStreamService:
    """Emite eventos SSE del progreso de una recomendación.

    Flujo:
    1. Consulta el estado actual de la recomendación en DB.
    2. Si ya está completada o fallida, emite el estado final y termina.
    3. Si está pendiente/procesando, se suscribe al canal de Redis
       y hace polling hasta recibir el estado terminal.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        """
        Args:
            redis_url: URL de Redis. Si no se provee, se obtiene de ``get_settings()``.
        """
        self._redis_url = redis_url

    def _get_redis_url(self) -> str:
        if self._redis_url:
            return self._redis_url
        from app.config import get_settings
        return get_settings().redis_url

    @staticmethod
    def _format_event(event_name: str, data: dict | str) -> str:
        """Formatea un evento SSE con nombre y datos JSON."""
        if isinstance(data, dict):
            data = json.dumps(data)
        return f"event: {event_name}\ndata: {data}\n\n"

    async def stream_recommendation_progress(
        self, ticket_id: str
    ) -> AsyncGenerator[str, None]:
        """Async generator que emite eventos SSE de progreso.

        Yields:
            Strings con formato SSE (``event: ...\\ndata: ...\\n\\n``).
        """
        from app.db.session import get_db_session
        from app.repositories import RecommendationRepository

        # ------------------------------------------------------------------
        # 1. Verificar estado inicial en DB
        # ------------------------------------------------------------------
        async with get_db_session() as db:
            recommendations = RecommendationRepository(db)
            rec = await recommendations.get_by_ticket_id(ticket_id)

            if not rec:
                yield self._format_event(
                    "status",
                    {"ticket_id": ticket_id, "status": "not_found"},
                )
                return

            yield self._format_event(
                "status",
                {
                    "ticket_id": ticket_id,
                    "status": rec.status.value,
                    "current_step": rec.current_step,
                    "error_message": rec.error_message,
                },
            )

            # Si ya terminó, no hace falta suscribirse a Redis
            if rec.status.value in ("completed", "failed"):
                return

        # ------------------------------------------------------------------
        # 2. Suscribirse a Redis para actualizaciones en tiempo real
        # ------------------------------------------------------------------
        from redis.asyncio import Redis

        redis_client = Redis.from_url(self._get_redis_url(), decode_responses=True)
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
                    yield self._format_event("status", message["data"])
                    try:
                        parsed = json.loads(message["data"])
                        if parsed.get("status") in ("completed", "failed"):
                            break
                    except Exception:
                        pass

                await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            await redis_client.close()
