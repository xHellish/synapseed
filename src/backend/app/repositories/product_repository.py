from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, ProductCategory, ProductStatus, ToxicBand
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    # Operaciones de base de datos para el modelo Product.

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Product)

    # ------------------------------------------------------------------
    # Búsquedas específicas
    # ------------------------------------------------------------------

    async def get_by_numero_registro(self, numero_registro: str) -> Product | None:
        # Retorna el producto por número de registro SFE.
        result = await self._db.execute(
            select(Product).where(Product.numero_registro == numero_registro)
        )
        return result.scalar_one_or_none()

    async def get_filtered(
        self,
        skip: int = 0,
        limit: int = 100,
        categoria: ProductCategory | None = None,
        estado: ProductStatus | None = None,
        banda_toxicologica: ToxicBand | None = None,
        cultivo_objetivo: str | None = None,
    ) -> Sequence[Product]:
        # Retorna productos con filtros opcionales y paginación.
        query = select(Product)

        if categoria is not None:
            query = query.where(Product.categoria == categoria)
        if estado is not None:
            query = query.where(Product.estado == estado)
        if banda_toxicologica is not None:
            query = query.where(Product.banda_toxicologica == banda_toxicologica)
        if cultivo_objetivo is not None:
            query = query.where(
                func.lower(Product.cultivo_objetivo).contains(cultivo_objetivo.lower())
            )

        query = query.order_by(Product.nombre_comercial).offset(skip).limit(limit)
        result = await self._db.execute(query)
        return result.scalars().all()

    async def count_filtered(
        self,
        categoria: ProductCategory | None = None,
        estado: ProductStatus | None = None,
        banda_toxicologica: ToxicBand | None = None,
    ) -> int:
        # Cuenta productos con los mismos filtros (para paginación).
        query = select(func.count()).select_from(Product)

        if categoria is not None:
            query = query.where(Product.categoria == categoria)
        if estado is not None:
            query = query.where(Product.estado == estado)
        if banda_toxicologica is not None:
            query = query.where(Product.banda_toxicologica == banda_toxicologica)

        result = await self._db.execute(query)
        return result.scalar_one()

    async def search_by_text(
        self, query_text: str, skip: int = 0, limit: int = 50
    ) -> Sequence[Product]:
        # Búsqueda por nombre comercial o ingrediente activo (ILIKE).
        pattern = f"%{query_text}%"
        result = await self._db.execute(
            select(Product)
            .where(
                or_(
                    Product.nombre_comercial.ilike(pattern),
                    Product.ingrediente_activo.ilike(pattern),
                )
            )
            .order_by(Product.nombre_comercial)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_activos(self, skip: int = 0, limit: int = 100) -> Sequence[Product]:
        # Retorna solo productos con estado ACTIVO.
        result = await self._db.execute(
            select(Product)
            .where(Product.estado == ProductStatus.ACTIVO)
            .order_by(Product.nombre_comercial)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_cultivo(
        self, cultivo: str, skip: int = 0, limit: int = 50
    ) -> Sequence[Product]:
        # Retorna productos cuyo cultivo_objetivo contiene el término dado.
        result = await self._db.execute(
            select(Product)
            .where(Product.cultivo_objetivo.ilike(f"%{cultivo}%"))
            .where(Product.estado == ProductStatus.ACTIVO)
            .order_by(Product.nombre_comercial)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_problema(
        self, problema: str, skip: int = 0, limit: int = 50
    ) -> Sequence[Product]:
        # Retorna productos cuyo problema_objetivo contiene el término dado.
        result = await self._db.execute(
            select(Product)
            .where(Product.problema_objetivo.ilike(f"%{problema}%"))
            .where(Product.estado == ProductStatus.ACTIVO)
            .order_by(Product.nombre_comercial)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def exists_numero_registro(self, numero_registro: str) -> bool:
        # Verifica si ya existe un producto con ese número de registro.
        result = await self._db.execute(
            select(func.count())
            .select_from(Product)
            .where(Product.numero_registro == numero_registro)
        )
        return result.scalar_one() > 0

    # ------------------------------------------------------------------
    # Escritura especializada
    # ------------------------------------------------------------------

    async def create_product(self, data: dict[str, Any]) -> Product:
        # Crea un nuevo producto agroquímico.
        return await self.create(data)

    async def update_product(self, product: Product, data: dict[str, Any]) -> Product:
        # Actualiza campos de un producto existente.
        return await self.update(product, data)

    async def update_embedding(
        self, product: Product, embedding: list[float]
    ) -> Product:
        # Actualiza solo el embedding vectorial del producto.
        return await self.update(product, {"embedding": embedding})
