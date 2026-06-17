from __future__ import annotations

import json
from typing import Any

from app.models.audit_log import AuditAction
from app.models.recommendation import RecommendationStatus
from app.repositories import (
    AuditRepository,
    DistributorRepository,
    LmrRepository,
    RecommendationRepository,
)


class RecommendationNotFoundError(ValueError):
    """Error cuando una recomendación no existe o no pertenece al usuario."""


class RecommendationQueryService:
    def __init__(
        self,
        recommendation_repository: RecommendationRepository,
        audit_repository: AuditRepository,
        distributor_repository: DistributorRepository,
        lmr_repository: LmrRepository,
    ) -> None:
        self.recommendation_repository = recommendation_repository
        self.audit_repository = audit_repository
        self.distributor_repository = distributor_repository
        self.lmr_repository = lmr_repository

    async def history(
        self,
        user_id: int,
        skip: int,
        limit: int,
        status_filter: RecommendationStatus | None,
    ) -> list[dict[str, Any]]:
        items = await self.recommendation_repository.get_by_user_id(
            user_id,
            skip=skip,
            limit=limit,
            status=status_filter,
        )
        return [
            {
                "id": recommendation.id,
                "ticket_id": recommendation.ticket_id,
                "crop": recommendation.crop,
                "problem": recommendation.problem,
                "status": recommendation.status.value,
                "created_at": recommendation.created_at.isoformat(),
                "completed_at": (
                    recommendation.completed_at.isoformat()
                    if recommendation.completed_at
                    else None
                ),
            }
            for recommendation in items
        ]

    async def detail(self, recommendation_id: int, user_id: int) -> dict[str, Any]:
        recommendation = await self.recommendation_repository.get_with_products(
            recommendation_id
        )
        if not recommendation or recommendation.user_id != user_id:
            raise RecommendationNotFoundError("Recomendación no encontrada")

        await self.audit_repository.log(
            action=AuditAction.RECOMMENDATION_VIEW,
            user_id=user_id,
            entity_type="recommendation",
            entity_id=recommendation.id,
        )

        products = []
        for recommendation_product in recommendation.products:
            product = recommendation_product.product
            lmr_value = None
            if product and product.ingrediente_activo and recommendation.crop:
                lmr_value = await self.lmr_repository.get_lmr_by_active_ingredient_and_crop(
                    product.ingrediente_activo,
                    recommendation.crop,
                )

            products.append(
                {
                    "rank": recommendation_product.rank,
                    "product_id": recommendation_product.product_id,
                    "nombre_comercial": product.nombre_comercial if product else None,
                    "justification": recommendation_product.justification,
                    "dosis": recommendation_product.dosis,
                    "precio_estimado": (
                        float(recommendation_product.precio_estimado)
                        if recommendation_product.precio_estimado
                        else None
                    ),
                    "toxicidad": recommendation_product.toxicidad,
                    "intervalo_seguridad": recommendation_product.intervalo_seguridad,
                    "lmr": lmr_value,
                    "categoria": (
                        product.categoria.value if product and product.categoria else None
                    ),
                    "cultivo_objetivo": product.cultivo_objetivo if product else None,
                    "problema_objetivo": product.problema_objetivo if product else None,
                    "registrante": product.registrante if product else None,
                    "ventajas": self._parse_json_list(recommendation_product.ventajas),
                    "riesgos": self._parse_json_list(recommendation_product.riesgos),
                    "recomendacion_uso_general": (
                        recommendation_product.recomendacion_uso_general
                    ),
                }
            )

        try:
            max_budget_per_liter = (
                float(recommendation.budget_range)
                if recommendation.budget_range
                else None
            )
        except (TypeError, ValueError):
            max_budget_per_liter = None

        return {
            "id": recommendation.id,
            "ticket_id": recommendation.ticket_id,
            "crop": recommendation.crop,
            "crop_stage": recommendation.crop_stage,
            "problem": recommendation.problem,
            "budget_range": recommendation.budget_range,
            "max_budget_per_liter": max_budget_per_liter,
            "status": recommendation.status.value,
            "current_step": recommendation.current_step,
            "error_message": recommendation.error_message,
            "created_at": recommendation.created_at.isoformat(),
            "completed_at": (
                recommendation.completed_at.isoformat()
                if recommendation.completed_at
                else None
            ),
            "products": products,
        }

    async def providers(
        self,
        recommendation_id: int,
        user_id: int,
    ) -> list[dict[str, object]]:
        recommendation = await self.recommendation_repository.get_with_products(
            recommendation_id
        )
        if not recommendation or recommendation.user_id != user_id:
            raise RecommendationNotFoundError("Recomendación no encontrada")

        seen_ids: set[Any] = set()
        result: list[dict[str, object]] = []
        for recommendation_product in recommendation.products:
            distributors = await self.distributor_repository.get_by_product(
                recommendation_product.product_id
            )
            if distributors:
                for distributor in distributors:
                    if distributor.id in seen_ids:
                        continue
                    seen_ids.add(distributor.id)
                    result.append(
                        {
                            "id": distributor.id,
                            "nombre": distributor.nombre,
                            "product_id": recommendation_product.product_id,
                            "producto_asociado": (
                                recommendation_product.product.nombre_comercial
                                if recommendation_product.product
                                else None
                            ),
                            "correo": distributor.correo,
                            "telefono": distributor.telefono,
                            "ubicacion": distributor.ubicacion,
                            "provincia": distributor.provincia,
                            "canton": distributor.canton,
                        }
                    )
            elif recommendation_product.product and recommendation_product.product.registrante:
                fallback_id = f"reg-{recommendation_product.product_id}"
                if fallback_id in seen_ids:
                    continue
                seen_ids.add(fallback_id)
                result.append(
                    {
                        "id": fallback_id,
                        "nombre": recommendation_product.product.registrante,
                        "product_id": recommendation_product.product_id,
                        "producto_asociado": (
                            recommendation_product.product.nombre_comercial
                        ),
                        "correo": "No disponible",
                        "telefono": "No disponible",
                        "ubicacion": "Registrante Oficial",
                        "provincia": None,
                        "canton": None,
                    }
                )
        return result

    @staticmethod
    def _parse_json_list(raw: str | None) -> list[str]:
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
