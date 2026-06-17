from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import (
    Recommendation,
    RecommendationProduct,
    RecommendationStatus,
)
from app.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    # Operaciones de base de datos para Recommendation y RecommendationProduct.

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Recommendation)

    # Busquedas especificas

    async def get_by_ticket_id(self, ticket_id: str) -> Recommendation | None:
        # Retorna la recomendación por su ticket_id único.
        result = await self._db.execute(
            select(Recommendation).where(Recommendation.ticket_id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        status: RecommendationStatus | None = None,
    ) -> Sequence[Recommendation]:
        # Retorna las recomendaciones de un usuario, con filtro opcional por estado.
        query = (
            select(Recommendation)
            .where(Recommendation.user_id == user_id)
            .order_by(Recommendation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if status is not None:
            query = query.where(Recommendation.status == status)

        result = await self._db.execute(query)
        return result.scalars().all()

    async def get_with_products(self, recommendation_id: int) -> Recommendation | None:
        # Retorna la recomendación con sus productos cargados en eager load.
        result = await self._db.execute(
            select(Recommendation)
            .options(
                selectinload(Recommendation.products).selectinload(
                    RecommendationProduct.product
                )
            )
            .where(Recommendation.id == recommendation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_ticket_with_products(
        self, ticket_id: str
    ) -> Recommendation | None:
        # Retorna la recomendación con productos, buscando por ticket_id.
        result = await self._db.execute(
            select(Recommendation)
            .options(
                selectinload(Recommendation.products).selectinload(
                    RecommendationProduct.product
                )
            )
            .where(Recommendation.ticket_id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def count_by_user(
        self,
        user_id: int,
        status: RecommendationStatus | None = None,
    ) -> int:
        # Cuenta las recomendaciones de un usuario.
        query = (
            select(func.count())
            .select_from(Recommendation)
            .where(Recommendation.user_id == user_id)
        )
        if status is not None:
            query = query.where(Recommendation.status == status)

        result = await self._db.execute(query)
        return result.scalar_one()

    # Escritura especializada

    async def create_recommendation(self, data: dict[str, Any]) -> Recommendation:
        # Crea una nueva recomendación (estado inicial: PENDING).
        data.setdefault("status", RecommendationStatus.PENDING)
        return await self.create(data)

    async def update_status(
        self,
        recommendation: Recommendation,
        status: RecommendationStatus,
        current_step: str | None = None,
        error_message: str | None = None,
    ) -> Recommendation:
        # Actualiza el estado del pipeline de la recomendación.
        patch: dict[str, Any] = {"status": status}
        if current_step is not None:
            patch["current_step"] = current_step
        if error_message is not None:
            patch["error_message"] = error_message
        return await self.update(recommendation, patch)

    async def mark_completed(self, recommendation: Recommendation) -> Recommendation:
        # Marca la recomendación como completada registrando completed_at.
        from datetime import datetime, timezone

        return await self.update(
            recommendation,
            {
                "status": RecommendationStatus.COMPLETED,
                "current_step": None,
                "completed_at": datetime.now(timezone.utc).replace(tzinfo=None),
            },
        )

    async def mark_failed(
        self, recommendation: Recommendation, error_message: str
    ) -> Recommendation:
        # Marca la recomendación como fallida con su mensaje de error.
        return await self.update(
            recommendation,
            {
                "status": RecommendationStatus.FAILED,
                "error_message": error_message,
            },
        )

    # RecommendationProduct

    async def add_product(
        self,
        recommendation_id: int,
        product_id: int,
        rank: int,
        data: dict[str, Any],
    ) -> RecommendationProduct:
        # Agrega un producto recomendado a la recomendación.
        rec_product = RecommendationProduct(
            recommendation_id=recommendation_id,
            product_id=product_id,
            rank=rank,
            **data,
        )
        self._db.add(rec_product)
        await self._db.commit()
        await self._db.refresh(rec_product)
        return rec_product

    async def add_products_bulk(
        self,
        recommendation_id: int,
        products: list[dict[str, Any]],
    ) -> list[RecommendationProduct]:
        # Agrega múltiples productos recomendados en una sola transacción.
        # Cada elemento de `products` debe incluir: product_id, rank, justification.
        instances = [
            RecommendationProduct(recommendation_id=recommendation_id, **p)
            for p in products
        ]
        self._db.add_all(instances)
        await self._db.commit()
        for inst in instances:
            await self._db.refresh(inst)
        return instances

    async def remove_products(self, recommendation_id: int) -> None:
        # Elimina todos los productos de una recomendación (para re-generar).
        result = await self._db.execute(
            select(RecommendationProduct).where(
                RecommendationProduct.recommendation_id == recommendation_id
            )
        )
        for rec_product in result.scalars().all():
            await self._db.delete(rec_product)
        await self._db.commit()
