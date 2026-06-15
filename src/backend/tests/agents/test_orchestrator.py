"""Tests del orquestador completo."""

import pytest

from app.agents.orchestrator import AgentOrchestrator
from app.schemas.farmer_input import FarmerContextInput


@pytest.mark.asyncio
async def test_orchestrator_full_pipeline_with_mocks(
    sample_farmer_input: FarmerContextInput,
    fake_product_repo,
    fake_regulation_repo,
    pipeline_mock_llm,
):
    orchestrator = AgentOrchestrator(
        llm=pipeline_mock_llm,
        product_repo=fake_product_repo,
        regulation_repo=fake_regulation_repo,
    )
    result = await orchestrator.run(sample_farmer_input)

    assert result.context_analysis.cultivo == "tomate"
    assert len(result.research.candidatos) >= 1
    assert len(result.synthesis.recomendaciones) <= 3
    assert result.processing_steps == [
        "context_analyzer",
        "researcher",
        "legal_validator",
        "synthesizer",
    ]
    # Endosulfán debe descartarse por regla determinística
    discarded = {d.producto.product_id for d in result.legal_validation.productos_descartados}
    assert 4 in discarded
