from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.audit_log import AuditAction
from app.models.recommendation import RecommendationStatus
from app.repositories import AuditRepository, DistributorRepository, RecommendationRepository
from app.schemas.common import RecommendationRequest

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# Inicia una recomendacion: la guarda como PENDING y dispara el pipeline en segundo plano.
# Responde 202 (aceptado) de inmediato; el resultado llega luego por el stream SSE.
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

    ticket_id = str(uuid4())  # identificador unico para seguir esta solicitud por SSE

    # Crea el registro en estado PENDING con todo el contexto del caso
    rec = await recommendations.create_recommendation(
        {
            "ticket_id": ticket_id,
            "user_id": int(current_user["id"]),
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

    # Deja rastro en la bitacora de auditoria
    await audit.log(
        action=AuditAction.RECOMMENDATION_REQUEST,
        user_id=int(current_user["id"]),
        entity_type="recommendation",
        entity_id=rec.id,
    )

    # Encola la tarea Celery: el LLM (10-50s) corre en el worker, no bloquea la API
    from app.workers.tasks import generate_recommendation
    generate_recommendation.delay(ticket_id)

    return {
        "ticket_id": ticket_id,
        "recommendation_id": rec.id,
        "status": rec.status.value,
        "message": "Recomendación encolada correctamente",
    }


# Lista las recomendaciones del usuario logueado (paginada, con filtro opcional por estado)
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


# Detalle completo de una recomendacion con sus 3 productos y la tabla comparativa
@router.get(
    "/{recommendation_id}",
    summary="Detalle de una recomendación",
)
async def detail(
    recommendation_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    recommendations = RecommendationRepository(db)
    audit = AuditRepository(db)

    # Carga la recomendacion con sus productos; valida que sea del usuario (seguridad)
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

    from app.repositories.lmr_repository import LmrRepository

    lmr_repo = LmrRepository(db)

    # Arma la lista de productos para el frontend, enriqueciendo cada uno con su LMR
    products: list[dict] = []
    for p in rec.products:
        product = p.product
        lmr_val = None
        # LMR (limite maximo de residuos) se busca por ingrediente activo + cultivo
        if product and product.ingrediente_activo and rec.crop:
            lmr_val = await lmr_repo.get_lmr_by_active_ingredient_and_crop(
                product.ingrediente_activo,
                rec.crop,
            )

        def _parse_json_list(raw: str | None) -> list[str]:
            # ventajas/riesgos se guardan como JSON serializado; aqui se reconvierten a lista
            if not raw:
                return []
            try:
                parsed = json.loads(raw)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                return []

        products.append(
            {
                "rank": p.rank,
                "product_id": p.product_id,
                "nombre_comercial": product.nombre_comercial if product else None,
                "justification": p.justification,
                "dosis": p.dosis,
                "precio_estimado": (
                    float(p.precio_estimado) if p.precio_estimado else None
                ),
                "toxicidad": p.toxicidad,
                "intervalo_seguridad": p.intervalo_seguridad,
                "lmr": lmr_val,
                "categoria": (
                    product.categoria.value if product and product.categoria else None
                ),
                "cultivo_objetivo": product.cultivo_objetivo if product else None,
                "problema_objetivo": product.problema_objetivo if product else None,
                "registrante": product.registrante if product else None,
                "ventajas": _parse_json_list(p.ventajas),
                "riesgos": _parse_json_list(p.riesgos),
                "recomendacion_uso_general": p.recomendacion_uso_general,
            }
        )

    try:
        max_budget_per_liter = float(rec.budget_range) if rec.budget_range else None
    except (TypeError, ValueError):
        max_budget_per_liter = None

    return {
        "id": rec.id,
        "ticket_id": rec.ticket_id,
        "crop": rec.crop,
        "crop_stage": rec.crop_stage,
        "problem": rec.problem,
        "budget_range": rec.budget_range,
        "max_budget_per_liter": max_budget_per_liter,
        "status": rec.status.value,
        "current_step": rec.current_step,
        "error_message": rec.error_message,
        "created_at": rec.created_at.isoformat(),
        "completed_at": rec.completed_at.isoformat() if rec.completed_at else None,
        "products": products,
    }


# Distribuidores donde conseguir los productos recomendados (sin repetir)
@router.get("/{recommendation_id}/providers", summary="Distribuidores de la recomendación")
async def providers(
    recommendation_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, object]]:
    recommendation_repo = RecommendationRepository(db)
    distributor_repo = DistributorRepository(db)

    rec = await recommendation_repo.get_with_products(recommendation_id)
    if not rec or rec.user_id != int(current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recomendación no encontrada",
        )

    seen_ids: set[Any] = set()  # evita listar el mismo distribuidor dos veces
    result: list[dict[str, object]] = []
    for rec_product in rec.products:
        dist_list = await distributor_repo.get_by_product(rec_product.product_id)
        if dist_list:
            for d in dist_list:
                if d.id not in seen_ids:
                    seen_ids.add(d.id)
                    result.append(
                        {
                            "id": d.id,
                            "nombre": d.nombre,
                            "product_id": rec_product.product_id,
                            "producto_asociado": (
                                rec_product.product.nombre_comercial
                                if rec_product.product
                                else None
                            ),
                            "correo": d.correo,
                            "telefono": d.telefono,
                            "ubicacion": d.ubicacion,
                            "provincia": d.provincia,
                            "canton": d.canton,
                        }
                    )
        # Si el producto no tiene distribuidores cargados, mostramos al registrante oficial
        elif rec_product.product and rec_product.product.registrante:
            fallback_id = f"reg-{rec_product.product_id}"
            if fallback_id not in seen_ids:
                seen_ids.add(fallback_id)
                result.append(
                    {
                        "id": fallback_id,
                        "nombre": rec_product.product.registrante,
                        "product_id": rec_product.product_id,
                        "producto_asociado": rec_product.product.nombre_comercial,
                        "correo": "No disponible",
                        "telefono": "No disponible",
                        "ubicacion": "Registrante Oficial",
                        "provincia": None,
                        "canton": None,
                    }
                )
    return result


# Stream SSE: el frontend se suscribe y recibe el progreso del pipeline en tiempo real.
# Se eligio SSE (no WebSocket) porque el flujo es unidireccional servidor -> cliente.
@router.get("/stream/{ticket_id}", summary="Stream de progreso (SSE)")
async def stream(
    ticket_id: str,
) -> StreamingResponse:
    from redis.asyncio import Redis

    from app.config import get_settings
    from app.db.session import get_db_session
    from app.repositories import RecommendationRepository

    settings = get_settings()

    # Generador asincrono: cada `yield` envia un evento SSE al navegador
    async def event_stream() -> None:
        # Primer evento: estado actual segun la DB (por si ya termino antes de conectarse)
        async with get_db_session() as db:
            recommendations = RecommendationRepository(db)
            rec = await recommendations.get_by_ticket_id(ticket_id)
            if not rec:
                yield f"event: status\ndata: {json.dumps({'ticket_id': ticket_id, 'status': 'not_found'})}\n\n"
                return

            yield (
                "event: status\n"
                f"data: {json.dumps({'ticket_id': ticket_id, 'status': rec.status.value, 'current_step': rec.current_step, 'error_message': rec.error_message})}\n\n"
            )

            # Si ya estaba terminado, no hay nada que transmitir
            if rec.status.value in ("completed", "failed"):
                return

        # Se suscribe al canal Redis donde el worker publica el avance de cada paso
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        pubsub = redis_client.pubsub()
        channel = f"recommendation_progress:{ticket_id}"
        await pubsub.subscribe(channel)

        try:
            # Bucle: reenvia al navegador cada mensaje que el worker publica
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message:
                    yield f"event: status\ndata: {message['data']}\n\n"
                    try:
                        parsed = json.loads(message["data"])
                        # Cuando llega completed/failed, cerramos el stream
                        if parsed.get("status") in ("completed", "failed"):
                            break
                    except Exception:
                        pass

                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass  # el cliente cerro la conexion
        finally:
            # Siempre liberar la suscripcion y la conexion Redis
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            await redis_client.close()

    # Headers obligatorios para que el navegador y proxies no bufferen el stream SSE
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=headers,
    )