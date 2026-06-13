"""Tests del Agente 1 — Analizador de Contexto."""

import pytest

from app.agents.analyzer_agent import analyze_context
from app.schemas.agent_context import ContextAnalysisOutput
from app.schemas.farmer_input import FarmerContextInput
from app.services.llm_client import MockLLMClient


@pytest.mark.asyncio
async def test_analyzer_returns_structured_context(sample_farmer_input: FarmerContextInput):
    llm = MockLLMClient(
        responses={
            "default": {
                "cultivo": "tomate",
                "problema_detectado": "áfidos",
                "condiciones_agronomicas": {
                    "tipo_suelo": "franco-arcilloso",
                    "humedad": "media",
                    "temperatura": "24",
                    "calidad_agua": "regular",
                },
                "severidad_estimada": "media",
                "restricciones_relevantes": [],
                "resumen_para_rag": "Tomate con áfidos en floración suelo franco humedad media.",
                "advertencias": [],
                "datos_faltantes": [],
                "confianza": 0.8,
                "tipo_proteccion_necesaria": "insecticida",
                "categoria_producto_sugerida": "plaguicida",
            }
        }
    )
    result = await analyze_context(sample_farmer_input, llm)
    assert isinstance(result, ContextAnalysisOutput)
    assert result.cultivo == "tomate"
    assert result.categoria_producto_sugerida == "plaguicida"
    assert len(result.resumen_para_rag) >= 10
