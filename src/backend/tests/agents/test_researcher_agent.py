"""Tests del Agente 2 — Investigador RAG."""

import pytest

from app.agents.researcher_agent import research_products
from app.repositories.product_repository import FakeProductRepository, ProductRecord
from app.schemas.agent_context import AgronomicConditions, ContextAnalysisOutput


@pytest.mark.asyncio
async def test_researcher_returns_candidates_from_fake_repo(sample_context: ContextAnalysisOutput):
    repo = FakeProductRepository(
        [
            ProductRecord(
                id=10,
                numero_registro="X",
                nombre_comercial="Prod Tomate",
                ingrediente_activo="Ing A",
                categoria="plaguicida",
                cultivo_objetivo="tomate",
                problema_objetivo="áfidos",
                precio_referencia_por_litro=1000.0,
                banda_toxicologica="amarilla",
                dosis_recomendada="1 L/ha",
                intervalo_seguridad_dias=5,
            )
        ]
    )
    result = await research_products(sample_context, repo)
    assert len(result.candidatos) >= 1
    assert result.candidatos[0].product_id == 10
    assert result.metodo_busqueda in {"filtros", "hibrido", "vector"}


@pytest.mark.asyncio
async def test_researcher_empty_when_no_products(sample_context: ContextAnalysisOutput):
    repo = FakeProductRepository([])
    result = await research_products(sample_context, repo)
    assert result.candidatos == []
    assert result.advertencias
