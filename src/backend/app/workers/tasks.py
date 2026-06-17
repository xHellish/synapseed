"""Tareas en segundo plano de Celery para SynapSeed."""

from __future__ import annotations

import asyncio
from celery.utils.log import get_task_logger

from app.workers.celery_app import celery_app
from app.db.session import get_db_session
from app.repositories import RecommendationRepository
from app.repositories.product_repository import SqlAlchemyProductRepository
from app.repositories.regulation_repository import SqlAlchemyRegulationRepository
from app.agents.orchestrator import AgentOrchestrator
from app.services.llm_client import OpenRouterLLMClient
from app.schemas.farmer_input import FarmerContextInput
from app.models.recommendation import RecommendationStatus

logger = get_task_logger(__name__)


async def publish_progress(
    ticket_id: str,
    status: str,
    current_step: str | None = None,
    error_message: str | None = None,
) -> None:
    """Publica el progreso del ticket en un canal de Redis pub/sub."""
    try:
        from app.core.redis import get_redis_client
        import json
        redis_client = get_redis_client()
        payload = {
            "ticket_id": ticket_id,
            "status": status,
            "current_step": current_step,
            "error_message": error_message,
        }
        await redis_client.publish(f"recommendation_progress:{ticket_id}", json.dumps(payload))
    except Exception as exc:
        logger.error(f"Error al publicar progreso en Redis: {exc}")


async def async_run_recommendation_pipeline(ticket_id: str) -> None:
    """Procesa una recomendación asíncronamente en el motor SQLAlchemy."""
    async with get_db_session() as db:
        recommendations = RecommendationRepository(db)
        rec = await recommendations.get_by_ticket_id(ticket_id)
        if not rec:
            logger.error(f"Recomendación no encontrada para el ticket: {ticket_id}")
            return

        logger.info(f"Actualizando estado a PROCESSING para ticket {ticket_id}")
        await recommendations.update_status(
            recommendation=rec,
            status=RecommendationStatus.PROCESSING,
            current_step="context_analyzer",
        )
        await publish_progress(ticket_id, "processing", "context_analyzer")

        try:
            # Construir el context input a partir de la recomendación de la DB
            farmer_input = FarmerContextInput(
                crop=rec.crop,
                crop_stage=rec.crop_stage,
                problem=rec.problem,
                problem_category=rec.problem_category,
                last_agrochemical_used=rec.last_agrochemical_used,
                budget_range=rec.budget_range,
                soil_type=rec.soil_type,
                humidity=float(rec.humidity) if rec.humidity is not None else None,
                temperature=float(rec.temperature) if rec.temperature is not None else None,
                water_quality=rec.water_quality,
            )

            logger.info("Instanciando cliente LLM y repositorios...")
            llm = OpenRouterLLMClient()
            product_repo = SqlAlchemyProductRepository(db)
            regulation_repo = SqlAlchemyRegulationRepository(db)

            orchestrator = AgentOrchestrator(
                llm=llm,
                product_repo=product_repo,
                regulation_repo=regulation_repo,
            )

            async def progress_callback(step: str) -> None:
                await recommendations.update_status(
                    recommendation=rec,
                    status=RecommendationStatus.PROCESSING,
                    current_step=step,
                )
                await publish_progress(ticket_id, "processing", step)

            logger.info(f"Ejecutando el pipeline de agentes para ticket {ticket_id}")
            result = await orchestrator.run(farmer_input, on_step_complete=progress_callback)

            # Limpiar recomendaciones de productos previas (por si acaso se re-ejecuta)
            await recommendations.remove_products(rec.id)

            # Insertar nuevos productos recomendados mapeando tipos
            import json as _json
            products_to_add = []
            for item in result.synthesis.recomendaciones:
                # Tratar valores que vengan como 'no_disponible' o incompatibles con base de datos
                precio_estimado = None
                if item.precio is not None and item.precio != "no_disponible":
                    try:
                        precio_estimado = float(item.precio)
                    except (ValueError, TypeError):
                        pass

                intervalo_seguridad = None
                if item.intervalo_seguridad is not None and item.intervalo_seguridad != "no_disponible":
                    try:
                        intervalo_seguridad = int(item.intervalo_seguridad)
                    except (ValueError, TypeError):
                        pass

                products_to_add.append({
                    "product_id": item.product_id,
                    "rank": item.ranking,
                    "justification": item.justificacion,
                    "dosis": item.dosis if item.dosis != "no_disponible" else None,
                    "precio_estimado": precio_estimado,
                    "toxicidad": item.toxicidad if item.toxicidad != "no_disponible" else None,
                    "intervalo_seguridad": intervalo_seguridad,
                    "ventajas": _json.dumps(item.ventajas, ensure_ascii=False) if item.ventajas else None,
                    "riesgos": _json.dumps(item.riesgos, ensure_ascii=False) if item.riesgos else None,
                    "recomendacion_uso_general": item.recomendacion_uso_general or None,
                })

            if products_to_add:
                logger.info(f"Guardando {len(products_to_add)} productos recomendados en base de datos...")
                await recommendations.add_products_bulk(rec.id, products_to_add)

            # Marcar la recomendación como completada
            logger.info(f"Marcando ticket {ticket_id} como COMPLETED")
            await recommendations.mark_completed(rec)
            await publish_progress(ticket_id, "completed")

        except Exception as exc:
            logger.exception(f"Error procesando el ticket {ticket_id}: {exc}")
            logger.info(f"Marcando ticket {ticket_id} como FAILED")
            try:
                await db.rollback()
            except Exception:
                pass
            await recommendations.mark_failed(rec, str(exc))
            await publish_progress(ticket_id, "failed", error_message=str(exc))


@celery_app.task(name="app.workers.tasks.generate_recommendation")
def generate_recommendation(ticket_id: str) -> None:
    """Punto de entrada síncrono para Celery que levanta el event loop asíncrono."""
    logger.info(f"Tarea Celery recibida: procesar recomendación para ticket {ticket_id}")
    try:
        asyncio.run(async_run_recommendation_pipeline(ticket_id))
    except Exception as exc:
        logger.exception(f"Fallo crítico ejecutando la tarea de Celery para ticket {ticket_id}: {exc}")
        raise
