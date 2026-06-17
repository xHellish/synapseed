"""Repositorio de productos — capa de datos para API REST y pipeline de agentes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, ProductCategory, ProductStatus, ToxicBand
from app.repositories.base import BaseRepository
from app.schemas.agent_context import ContextAnalysisOutput
from app.schemas.agent_products import ProductCandidate


# Repositorio de productos para la API REST


class ProductRepository(BaseRepository[Product]):
    """Operaciones de base de datos para el modelo Product (API REST)."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Product)

    # Busquedas especificas

    async def get_by_numero_registro(self, numero_registro: str) -> Product | None:
        """Retorna el producto por número de registro SFE."""
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
        """Retorna productos con filtros opcionales y paginación."""
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
        """Cuenta productos con los mismos filtros (para paginación)."""
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
        """Búsqueda por nombre comercial o ingrediente activo (ILIKE)."""
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
        """Retorna solo productos con estado ACTIVO."""
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
        """Retorna productos cuyo cultivo_objetivo contiene el término dado."""
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
        """Retorna productos cuyo problema_objetivo contiene el término dado."""
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
        """Verifica si ya existe un producto con ese número de registro."""
        result = await self._db.execute(
            select(func.count())
            .select_from(Product)
            .where(Product.numero_registro == numero_registro)
        )
        return result.scalar_one() > 0

    # Escritura especializada

    async def create_product(self, data: dict[str, Any]) -> Product:
        """Crea un nuevo producto agroquímico."""
        return await self.create(data)

    async def update_product(self, product: Product, data: dict[str, Any]) -> Product:
        """Actualiza campos de un producto existente."""
        return await self.update(product, data)

    async def update_embedding(
        self, product: Product, embedding: list[float]
    ) -> Product:
        """Actualiza solo el embedding vectorial del producto."""
        return await self.update(product, {"embedding": embedding})


# Abstraccion para el pipeline de agentes, desacoplada del ORM


@dataclass(frozen=True)
class ProductRecord:
    """Vista de producto desacoplada del ORM para el pipeline de agentes."""

    id: int
    numero_registro: str
    nombre_comercial: str
    ingrediente_activo: str
    categoria: str
    cultivo_objetivo: str | None
    problema_objetivo: str | None
    precio_referencia_por_litro: float | None
    banda_toxicologica: str | None
    dosis_recomendada: str | None
    intervalo_seguridad_dias: int | None


class AbstractProductRepository(ABC):
    """Contrato mockeable para búsqueda de productos en el pipeline de agentes."""

    @abstractmethod
    async def search_candidates(
        self,
        context: ContextAnalysisOutput,
        *,
        limit: int = 15,
    ) -> tuple[list[ProductCandidate], str]:
        """Retorna candidatos y el método de búsqueda usado."""


# Helpers de puntuacion y transformacion


def _score_product(product: ProductRecord, context: ContextAnalysisOutput) -> tuple[float, str]:
    """Heurística de relevancia sin inventar datos."""
    score = 0.0
    reasons: list[str] = []

    query_terms = context.resumen_para_rag.lower()
    if product.cultivo_objetivo and product.cultivo_objetivo.lower() in query_terms:
        score += 0.35
        reasons.append(f"cultivo objetivo coincide ({product.cultivo_objetivo})")
    if product.problema_objetivo and product.problema_objetivo.lower() in query_terms:
        score += 0.35
        reasons.append(f"problema objetivo coincide ({product.problema_objetivo})")
    if context.cultivo.lower() in product.nombre_comercial.lower():
        score += 0.1
        reasons.append("nombre comercial relacionado al cultivo")
    if context.problema_detectado.lower()[:20] in product.ingrediente_activo.lower():
        score += 0.1
        reasons.append("ingrediente activo alineado al problema")

    cat = context.categoria_producto_sugerida.lower()
    if cat in product.categoria.lower():
        score += 0.2
        reasons.append(f"categoría {product.categoria}")

    tipo = context.tipo_proteccion_necesaria.lower()
    if product.problema_objetivo and tipo in product.problema_objetivo.lower():
        score += 0.15
        reasons.append("tipo de protección alineado")

    if not reasons:
        reasons.append("coincidencia parcial por filtros activos y texto RAG")
        score = 0.25

    return min(score, 1.0), "; ".join(reasons)


def _to_candidate(product: ProductRecord, score: float, reason: str) -> ProductCandidate:
    return ProductCandidate(
        product_id=product.id,
        nombre_comercial=product.nombre_comercial,
        ingrediente_activo=product.ingrediente_activo,
        categoria=product.categoria,
        cultivo_relacionado=product.cultivo_objetivo,
        problema_relacionado=product.problema_objetivo,
        precio_referencia_por_litro=product.precio_referencia_por_litro,
        toxicidad=product.banda_toxicologica,
        dosis_recomendada=product.dosis_recomendada,
        intervalo_seguridad_dias=product.intervalo_seguridad_dias,
        numero_registro=product.numero_registro,
        score_relevancia=round(score, 3),
        razon_relevancia=reason,
    )


def _orm_to_record(product: Product) -> ProductRecord:
    return ProductRecord(
        id=product.id,
        numero_registro=product.numero_registro,
        nombre_comercial=product.nombre_comercial,
        ingrediente_activo=product.ingrediente_activo,
        categoria=product.categoria.value,
        cultivo_objetivo=product.cultivo_objetivo,
        problema_objetivo=product.problema_objetivo,
        precio_referencia_por_litro=product.precio_referencia_por_litro,
        banda_toxicologica=(
            product.banda_toxicologica.value if product.banda_toxicologica else None
        ),
        dosis_recomendada=product.dosis_recomendada,
        intervalo_seguridad_dias=product.intervalo_seguridad_dias,
    )


# Implementaciones concretas del repositorio abstracto


class SqlAlchemyProductRepository(AbstractProductRepository):
    """Búsqueda real contra PostgreSQL/Supabase vía SQLAlchemy para el pipeline de agentes."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search_candidates(
        self,
        context: ContextAnalysisOutput,
        *,
        limit: int = 15,
    ) -> tuple[list[ProductCandidate], str]:
        categoria_filter = None
        cat = context.categoria_producto_sugerida.lower()
        if cat == "plaguicida":
            categoria_filter = ProductCategory.PLAGUICIDA
        elif cat == "fertilizante":
            categoria_filter = ProductCategory.FERTILIZANTE

        stmt = select(Product).where(Product.estado == ProductStatus.ACTIVO)
        if categoria_filter:
            stmt = stmt.where(Product.categoria == categoria_filter)

        cultivo = context.cultivo
        problema = context.problema_detectado
        text_conditions = or_(
            Product.cultivo_objetivo.ilike(f"%{cultivo}%"),
            Product.problema_objetivo.ilike(f"%{problema}%"),
            Product.nombre_comercial.ilike(f"%{cultivo}%"),
            Product.ingrediente_activo.ilike(f"%{problema[:30]}%"),
        )

        # Try hybrid search (category + text filters) first
        stmt_hibrido = stmt.where(text_conditions).limit(limit * 3)
        result = await self._session.execute(stmt_hibrido)
        products = result.scalars().all()
        method = "hibrido"

        if not products:
            # Fallback: category-only search
            stmt_fallback = stmt.limit(limit * 2)
            result = await self._session.execute(stmt_fallback)
            products = result.scalars().all()
            method = "filtros"

        scored: list[tuple[float, ProductRecord]] = []
        for product in products:
            record = _orm_to_record(product)
            score, _ = _score_product(record, context)
            scored.append((score, record))

        scored.sort(key=lambda x: x[0], reverse=True)
        candidates: list[ProductCandidate] = []
        for score, record in scored[:limit]:
            _, reason = _score_product(record, context)
            candidates.append(_to_candidate(record, score, reason))
        return candidates, method


class FakeProductRepository(AbstractProductRepository):
    """Repositorio en memoria para tests del pipeline de agentes."""

    def __init__(self, products: list[ProductRecord] | None = None) -> None:
        self._products = products or []

    async def search_candidates(
        self,
        context: ContextAnalysisOutput,
        *,
        limit: int = 15,
    ) -> tuple[list[ProductCandidate], str]:
        scored = []
        for product in self._products:
            score, reason = _score_product(product, context)
            scored.append((score, product, reason))
        scored.sort(key=lambda x: x[0], reverse=True)
        candidates = [
            _to_candidate(p, s, r) for s, p, r in scored[:limit]
        ]
        return candidates, "filtros"