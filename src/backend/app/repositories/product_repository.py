"""Acceso a productos para el Agente Investigador (RAG)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, ProductCategory, ProductStatus
from app.schemas.agent_context import ContextAnalysisOutput
from app.schemas.agent_products import ProductCandidate


@dataclass(frozen=True)
class ProductRecord:
    """Vista de producto desacoplada del ORM."""

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


class ProductRepository(ABC):
    """Contrato mockeable para búsqueda de productos."""

    @abstractmethod
    async def search_candidates(
        self,
        context: ContextAnalysisOutput,
        *,
        limit: int = 15,
    ) -> tuple[list[ProductCandidate], str]:
        """Retorna candidatos y el método de búsqueda usado."""


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


class SqlAlchemyProductRepository(ProductRepository):
    """Búsqueda real contra PostgreSQL/Supabase vía SQLAlchemy."""

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
        stmt = stmt.where(
            or_(
                Product.cultivo_objetivo.ilike(f"%{cultivo}%"),
                Product.problema_objetivo.ilike(f"%{problema}%"),
                Product.nombre_comercial.ilike(f"%{cultivo}%"),
                Product.ingrediente_activo.ilike(f"%{problema[:30]}%"),
            )
        )
        stmt = stmt.limit(limit * 3)

        result = await self._session.execute(stmt)
        products = result.scalars().all()

        if not products:
            stmt_fallback = select(Product).where(Product.estado == ProductStatus.ACTIVO)
            if categoria_filter:
                stmt_fallback = stmt_fallback.where(Product.categoria == categoria_filter)
            stmt_fallback = stmt_fallback.limit(limit * 2)
            result = await self._session.execute(stmt_fallback)
            products = result.scalars().all()
            method = "filtros"
        else:
            method = "hibrido"

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


class FakeProductRepository(ProductRepository):
    """Repositorio en memoria para tests."""

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
