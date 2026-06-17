"""Servicio de lógica de negocio para recomendaciones — SRP + DIP.

Encapsula la orquestación de repositorios, auditoría y despacho de tareas
que antes vivía directamente en los endpoints de ``recommendations.py``.

Cumplimiento SOLID:
- SRP: ``RecommendationService`` solo coordina la creación de tickets y la
  consulta de recomendaciones; no maneja HTTP ni SSE.
- DIP: recibe ``RecommendationRepository``, ``AuditRepository``,
  ``DistributorRepository`` y ``TaskDispatcher`` por constructor.
"""

from __future__ import annotations

import json
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditAction
from app.models.recommendation import RecommendationStatus
from app.repositories import AuditRepository, DistributorRepository, RecommendationRepository
from app.schemas.common import RecommendationRequest
from app.services.task_dispatcher import TaskDispatcher


class RecommendationService:
    """Orquesta las operaciones de negocio sobre recomendaciones."""

    def __init__(
        self,
        recommendation_repo: RecommendationRepository,
        audit_repo: AuditRepository,
        distributor_repo: DistributorRepository,
        dispatcher: TaskDispatcher,
        db: AsyncSession | None = None,
    ) -> None:
        self._recommendations = recommendation_repo
        self._audit = audit_repo
        self._distributors = distributor_repo
        self._dispatcher = dispatcher
        # La sesión DB se recibe explícitamente para crear repositorios adicionales
        # (p. ej. LmrRepository) sin acceder a atributos privados del repo base.
        self._db = db or recommendation_repo._db

    # ------------------------------------------------------------------
    # Solicitar una nueva recomendación
    # ------------------------------------------------------------------

    async def request_recommendation(
        self, user_id: int, payload: RecommendationRequest
    ) -> dict:
        """Crea un ticket de recomendación, registra auditoría y despacha la tarea.

        Returns:
            Dict con ``ticket_id``, ``recommendation_id``, ``status`` y ``message``.
        """
        ticket_id = str(uuid4())

        rec = await self._recommendations.create_recommendation(
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

        await self._audit.log(
            action=AuditAction.RECOMMENDATION_REQUEST,
            user_id=user_id,
            entity_type="recommendation",
            entity_id=rec.id,
        )

        await self._dispatcher.dispatch_recommendation_generation(ticket_id)

        return {
            "ticket_id": ticket_id,
            "recommendation_id": rec.id,
            "status": rec.status.value,
            "message": "Recomendación encolada correctamente",
        }

    # ------------------------------------------------------------------
    # Historial
    # ------------------------------------------------------------------

    async def get_history(
        self,
        user_id: int,
        skip: int,
        limit: int,
        status_filter: RecommendationStatus | None,
    ) -> list[dict]:
        """Retorna el historial de recomendaciones del usuario serializado."""
        items = await self._recommendations.get_by_user_id(
            user_id,
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

    # ------------------------------------------------------------------
    # Detalle de una recomendación
    # ------------------------------------------------------------------

    async def get_detail(
        self, recommendation_id: int, user_id: int
    ) -> dict | None:
        """Retorna el detalle completo de una recomendación con productos.

        Registra un evento de auditoría ``RECOMMENDATION_VIEW``.
        Retorna ``None`` si la recomendación no existe o no pertenece al usuario.
        """
        from app.repositories.lmr_repository import LmrRepository

        rec = await self._recommendations.get_with_products(recommendation_id)
        if not rec or rec.user_id != user_id:
            return None

        await self._audit.log(
            action=AuditAction.RECOMMENDATION_VIEW,
            user_id=user_id,
            entity_type="recommendation",
            entity_id=rec.id,
        )

        # LmrRepository reutiliza la misma sesión DB inyectada en el constructor
        lmr_repo = LmrRepository(self._db)

        products: list[dict] = []
        for p in rec.products:
            product = p.product
            lmr_val = None
            if product and product.ingrediente_activo and rec.crop:
                lmr_val = await lmr_repo.get_lmr_by_active_ingredient_and_crop(
                    product.ingrediente_activo,
                    rec.crop,
                )

            products.append(
                {
                    "rank": p.rank,
                    "product_id": p.product_id,
                    "nombre_comercial": product.nombre_comercial if product else None,
                    "justification": p.justification,
                    "dosis": p.dosis,
                    "precio_estimado": float(p.precio_estimado) if p.precio_estimado else None,
                    "toxicidad": p.toxicidad,
                    "intervalo_seguridad": p.intervalo_seguridad,
                    "lmr": lmr_val,
                    "categoria": (
                        product.categoria.value if product and product.categoria else None
                    ),
                    "cultivo_objetivo": product.cultivo_objetivo if product else None,
                    "problema_objetivo": product.problema_objetivo if product else None,
                    "registrante": product.registrante if product else None,
                    "ventajas": self._parse_json_list(p.ventajas),
                    "riesgos": self._parse_json_list(p.riesgos),
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

    # ------------------------------------------------------------------
    # Distribuidores de una recomendación
    # ------------------------------------------------------------------

    async def get_providers(
        self, recommendation_id: int, user_id: int
    ) -> list[dict] | None:
        """Retorna la lista de distribuidores para los productos de una recomendación.

        Retorna ``None`` si la recomendación no existe o no pertenece al usuario.
        """
        rec = await self._recommendations.get_with_products(recommendation_id)
        if not rec or rec.user_id != user_id:
            return None

        seen_ids: set = set()
        result: list[dict] = []

        for rec_product in rec.products:
            dist_list = await self._distributors.get_by_product(rec_product.product_id)
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

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json_list(raw: str | None) -> list[str]:
        """Parsea una cadena JSON como lista de strings."""
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
