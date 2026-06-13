"""Tests del Agente 3 — Validador Legal."""

import pytest

from app.agents.legal_validator_agent import validate_legal
from app.repositories.product_repository import FakeProductRepository, ProductRecord
from app.repositories.regulation_repository import FakeRegulationRepository, RegulationRecord
from app.schemas.agent_context import AgronomicConditions, ContextAnalysisOutput
from app.schemas.agent_products import ProductCandidate, ResearchOutput
from app.services.llm_client import MockLLMClient


def _candidate(pid: int, ingredient: str) -> ProductCandidate:
    return ProductCandidate(
        product_id=pid,
        nombre_comercial=f"Prod {pid}",
        ingrediente_activo=ingredient,
        categoria="plaguicida",
        score_relevancia=0.8,
        razon_relevancia="test",
    )


@pytest.mark.asyncio
async def test_legal_validator_discards_prohibited_substance():
    context = ContextAnalysisOutput(
        cultivo="tomate",
        problema_detectado="plaga",
        condiciones_agronomicas=AgronomicConditions(),
        severidad_estimada="media",
        restricciones_relevantes=[],
        resumen_para_rag="tomate plaga",
        advertencias=[],
        datos_faltantes=[],
        confianza=0.8,
        tipo_proteccion_necesaria="insecticida",
        categoria_producto_sugerida="plaguicida",
    )
    research = ResearchOutput(
        candidatos=[
            _candidate(1, "Imidacloprid"),
            _candidate(2, "Endosulfán"),
        ],
        metodo_busqueda="filtros",
        total_encontrados=2,
    )
    reg_repo = FakeRegulationRepository(
        [
            RegulationRecord(
                id=1,
                numero="LP-2024",
                titulo="Prohibidas",
                tipo="lista_prohibida",
                resumen=None,
                sustancias_afectadas="Endosulfán",
                cultivos_afectados="Todos",
            )
        ]
    )
    llm = MockLLMClient(
        responses={
            "default": {
                "productos_validos_ids": [1],
                "descartes": [],
                "restricciones_detectadas": [],
                "nivel_riesgo_legal": "medio",
                "advertencias_legales": [],
                "confianza": 0.9,
                "normativa_insuficiente": False,
            }
        }
    )
    result = await validate_legal(context, research, reg_repo, llm)
    discarded_ids = {d.producto.product_id for d in result.productos_descartados}
    assert 2 in discarded_ids
    assert any(v.producto.product_id == 1 for v in result.productos_validos)


def _legal_context() -> ContextAnalysisOutput:
    return ContextAnalysisOutput(
        cultivo="tomate",
        problema_detectado="plaga",
        condiciones_agronomicas=AgronomicConditions(),
        severidad_estimada="media",
        restricciones_relevantes=[],
        resumen_para_rag="tomate plaga",
        advertencias=[],
        datos_faltantes=[],
        confianza=0.8,
        tipo_proteccion_necesaria="insecticida",
        categoria_producto_sugerida="plaguicida",
    )


@pytest.mark.asyncio
async def test_legal_validator_without_regulations_marks_insufficient():
    research = ResearchOutput(
        candidatos=[_candidate(1, "Imidacloprid")],
        metodo_busqueda="filtros",
        total_encontrados=1,
    )
    reg_repo = FakeRegulationRepository([])
    llm = MockLLMClient(responses={"default": {"productos_validos_ids": [1]}})

    result = await validate_legal(_legal_context(), research, reg_repo, llm)

    assert result.normativa_insuficiente is True
    assert result.productos_validos == []
    assert len(result.productos_descartados) == 1
    assert "No hay regulaciones" in result.productos_descartados[0].motivo_de_descarte
    assert any("Sin regulaciones" in w for w in result.advertencias_legales)


@pytest.mark.asyncio
async def test_legal_validator_empty_llm_valid_ids_does_not_auto_validate():
    research = ResearchOutput(
        candidatos=[_candidate(1, "Imidacloprid"), _candidate(2, "Abamectina")],
        metodo_busqueda="filtros",
        total_encontrados=2,
    )
    reg_repo = FakeRegulationRepository(
        [
            RegulationRecord(
                id=1,
                numero="REG-001",
                titulo="Normativa general",
                tipo="decreto",
                resumen="Reglas SFE",
                sustancias_afectadas=None,
                cultivos_afectados="tomate",
            )
        ]
    )
    llm = MockLLMClient(
        responses={
            "default": {
                "productos_validos_ids": [],
                "descartes": [],
                "restricciones_detectadas": [],
                "nivel_riesgo_legal": "bajo",
                "advertencias_legales": [],
                "confianza": 0.9,
                "normativa_insuficiente": False,
            }
        }
    )

    result = await validate_legal(_legal_context(), research, reg_repo, llm)

    assert result.productos_validos == []
    assert result.normativa_insuficiente is True
    assert len(result.productos_descartados) == 2
    assert all(
        "No confirmado en revisión normativa LLM" in d.motivo_de_descarte
        for d in result.productos_descartados
    )
    assert any(
        "Ningún producto fue confirmado" in w for w in result.advertencias_legales
    )
