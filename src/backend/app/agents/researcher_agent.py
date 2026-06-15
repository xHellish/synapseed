"""Agente 2 — Investigador RAG."""

from __future__ import annotations

from app.repositories.product_repository import AbstractProductRepository as ProductRepository
from app.schemas.agent_context import ContextAnalysisOutput
from app.schemas.agent_products import ResearchOutput


async def research_products(
    context: ContextAnalysisOutput,
    product_repo: ProductRepository,
    *,
    limit: int = 15,
) -> ResearchOutput:
    """Busca candidatos en DB; nunca inventa productos."""
    candidates, method = await product_repo.search_candidates(context, limit=limit)
    advertencias: list[str] = []
    if not candidates:
        advertencias.append(
            "No se encontraron productos en la base de datos para el contexto dado."
        )
    elif method == "filtros":
        advertencias.append(
            "Búsqueda vectorial no disponible; se usó fallback por filtros SQL."
        )
    return ResearchOutput(
        candidatos=candidates,
        metodo_busqueda=method,
        total_encontrados=len(candidates),
        advertencias=advertencias,
    )
