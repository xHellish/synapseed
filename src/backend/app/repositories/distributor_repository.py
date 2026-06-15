from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.distributor import Distributor, ProductDistributor
from app.repositories.base import BaseRepository


class DistributorRepository(BaseRepository[Distributor]):
    # Operaciones de base de datos para Distributor y ProductDistributor.

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Distributor)

    # ------------------------------------------------------------------
    # Búsquedas específicas
    # ------------------------------------------------------------------

    async def get_all_filtered(
        self,
        skip: int = 0,
        limit: int = 100,
        provincia: str | None = None,
        canton: str | None = None,
    ) -> Sequence[Distributor]:
        # Retorna distribuidores con filtros geográficos opcionales.
        query = select(Distributor).order_by(Distributor.nombre)

        if provincia is not None:
            query = query.where(func.lower(Distributor.provincia) == provincia.lower())
        if canton is not None:
            query = query.where(func.lower(Distributor.canton) == canton.lower())

        query = query.offset(skip).limit(limit)
        result = await self._db.execute(query)
        return result.scalars().all()

    async def count_filtered(
        self,
        provincia: str | None = None,
        canton: str | None = None,
    ) -> int:
        # Cuenta distribuidores con los mismos filtros geográficos.
        query = select(func.count()).select_from(Distributor)

        if provincia is not None:
            query = query.where(func.lower(Distributor.provincia) == provincia.lower())
        if canton is not None:
            query = query.where(func.lower(Distributor.canton) == canton.lower())

        result = await self._db.execute(query)
        return result.scalar_one()

    async def search_by_name(
        self, name: str, skip: int = 0, limit: int = 50
    ) -> Sequence[Distributor]:
        # Búsqueda por nombre del distribuidor (ILIKE).
        result = await self._db.execute(
            select(Distributor)
            .where(Distributor.nombre.ilike(f"%{name}%"))
            .order_by(Distributor.nombre)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_product(
        self, product_id: int, skip: int = 0, limit: int = 50
    ) -> Sequence[Distributor]:
        # Retorna los distribuidores que venden un producto específico.
        result = await self._db.execute(
            select(Distributor)
            .join(ProductDistributor, ProductDistributor.distributor_id == Distributor.id)
            .where(ProductDistributor.product_id == product_id)
            .order_by(Distributor.nombre)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    # ------------------------------------------------------------------
    # Asociación Product ↔ Distributor
    # ------------------------------------------------------------------

    async def link_product(
        self, product_id: int, distributor_id: int
    ) -> ProductDistributor:
        # Crea la asociación producto-distribuidor si no existe.
        existing = await self._db.execute(
            select(ProductDistributor).where(
                ProductDistributor.product_id == product_id,
                ProductDistributor.distributor_id == distributor_id,
            )
        )
        link = existing.scalar_one_or_none()
        if link:
            return link

        link = ProductDistributor(
            product_id=product_id, distributor_id=distributor_id
        )
        self._db.add(link)
        await self._db.commit()
        await self._db.refresh(link)
        return link

    async def unlink_product(self, product_id: int, distributor_id: int) -> bool:
        # Elimina la asociación producto-distribuidor. Retorna True si existía.
        result = await self._db.execute(
            select(ProductDistributor).where(
                ProductDistributor.product_id == product_id,
                ProductDistributor.distributor_id == distributor_id,
            )
        )
        link = result.scalar_one_or_none()
        if not link:
            return False
        await self._db.delete(link)
        await self._db.commit()
        return True

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------

    async def create_distributor(self, data: dict[str, Any]) -> Distributor:
        # Crea un nuevo distribuidor.
        return await self.create(data)

    async def update_distributor(
        self, distributor: Distributor, data: dict[str, Any]
    ) -> Distributor:
        # Actualiza los campos de un distribuidor.
        return await self.update(distributor, data)
