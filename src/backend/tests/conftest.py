"""Fixtures compartidas para tests del pipeline de agentes."""

from __future__ import annotations

import pytest

from app.repositories.product_repository import FakeProductRepository, ProductRecord
from app.repositories.regulation_repository import FakeRegulationRepository, RegulationRecord
from app.schemas.agent_context import AgronomicConditions, ContextAnalysisOutput
from app.schemas.agent_products import ProductCandidate
from app.schemas.farmer_input import FarmerContextInput
from app.services.llm_client import MockLLMClient


@pytest.fixture
def sample_farmer_input() -> FarmerContextInput:
    return FarmerContextInput(
        crop="tomate",
        crop_stage="floración",
        problem="áfidos en hojas jóvenes",
        problem_category="plaga",
        last_agrochemical_used="ninguno",
        budget_range="medio",
        soil_type="franco-arcilloso",
        humidity="media",
        temperature="24",
        water_quality="regular",
        zone_id=None,
    )


@pytest.fixture
def sample_context() -> ContextAnalysisOutput:
    return ContextAnalysisOutput(
        cultivo="tomate",
        problema_detectado="infestación de áfidos en floración",
        condiciones_agronomicas=AgronomicConditions(
            tipo_suelo="franco-arcilloso",
            humedad="media",
            temperatura="24°C",
            calidad_agua="regular",
        ),
        severidad_estimada="media",
        restricciones_relevantes=["presupuesto medio", "etapa de floración"],
        resumen_para_rag=(
            "Cultivo de tomate en floración con plaga de áfidos, suelo franco-arcilloso, "
            "humedad media, agua regular, sin agroquímico reciente, presupuesto medio."
        ),
        advertencias=[],
        datos_faltantes=[],
        confianza=0.85,
        tipo_proteccion_necesaria="insecticida",
        categoria_producto_sugerida="plaguicida",
    )


@pytest.fixture
def sample_products() -> list[ProductRecord]:
    return [
        ProductRecord(
            id=1,
            numero_registro="SFE-001",
            nombre_comercial="Insecticida Alpha",
            ingrediente_activo="Imidacloprid",
            categoria="plaguicida",
            cultivo_objetivo="tomate",
            problema_objetivo="áfidos",
            precio_referencia_por_litro=12000.0,
            banda_toxicologica="amarilla",
            dosis_recomendada="1.5 L/ha",
            intervalo_seguridad_dias=14,
        ),
        ProductRecord(
            id=2,
            numero_registro="SFE-002",
            nombre_comercial="Insecticida Beta",
            ingrediente_activo="Lambda-cihalotrina",
            categoria="plaguicida",
            cultivo_objetivo="tomate",
            problema_objetivo="insectos",
            precio_referencia_por_litro=9500.0,
            banda_toxicologica="roja",
            dosis_recomendada="0.8 L/ha",
            intervalo_seguridad_dias=7,
        ),
        ProductRecord(
            id=3,
            numero_registro="SFE-003",
            nombre_comercial="Insecticida Gamma",
            ingrediente_activo="Abamectina",
            categoria="plaguicida",
            cultivo_objetivo="tomate",
            problema_objetivo="ácaros",
            precio_referencia_por_litro=15000.0,
            banda_toxicologica="amarilla",
            dosis_recomendada="1.0 L/ha",
            intervalo_seguridad_dias=10,
        ),
        ProductRecord(
            id=4,
            numero_registro="SFE-004",
            nombre_comercial="Prohibido X",
            ingrediente_activo="Endosulfán",
            categoria="plaguicida",
            cultivo_objetivo="tomate",
            problema_objetivo="plaga",
            precio_referencia_por_litro=8000.0,
            banda_toxicologica="roja",
            dosis_recomendada=None,
            intervalo_seguridad_dias=None,
        ),
    ]


@pytest.fixture
def sample_regulations() -> list[RegulationRecord]:
    return [
        RegulationRecord(
            id=1,
            numero="Lista Prohibida SFE 2024",
            titulo="Sustancias prohibidas",
            tipo="lista_prohibida",
            resumen="Lista de sustancias prohibidas",
            sustancias_afectadas="Endosulfán, DDT, Aldrín",
            cultivos_afectados="Todos",
        ),
    ]


@pytest.fixture
def fake_product_repo(sample_products: list[ProductRecord]) -> FakeProductRepository:
    return FakeProductRepository(sample_products)


@pytest.fixture
def fake_regulation_repo(sample_regulations: list[RegulationRecord]) -> FakeRegulationRepository:
    return FakeRegulationRepository(sample_regulations)


@pytest.fixture
def analyzer_mock_llm() -> MockLLMClient:
    llm = MockLLMClient()
    llm.register(
        "default",
        {
            "cultivo": "tomate",
            "problema_detectado": "infestación de áfidos",
            "condiciones_agronomicas": {
                "tipo_suelo": "franco-arcilloso",
                "humedad": "media",
                "temperatura": "24°C",
                "calidad_agua": "regular",
            },
            "severidad_estimada": "media",
            "restricciones_relevantes": ["presupuesto medio"],
            "resumen_para_rag": (
                "Tomate en floración con áfidos en suelo franco-arcilloso humedad media."
            ),
            "advertencias": [],
            "datos_faltantes": [],
            "confianza": 0.9,
            "tipo_proteccion_necesaria": "insecticida",
            "categoria_producto_sugerida": "plaguicida",
        },
    )
    return llm


@pytest.fixture
def legal_mock_llm() -> MockLLMClient:
    llm = MockLLMClient()
    llm.register(
        "default",
        {
            "productos_validos_ids": [1, 2, 3],
            "descartes": [],
            "restricciones_detectadas": [],
            "nivel_riesgo_legal": "bajo",
            "advertencias_legales": [],
            "confianza": 0.88,
            "normativa_insuficiente": False,
        },
    )
    return llm


@pytest.fixture
def synthesizer_mock_llm() -> MockLLMClient:
    llm = MockLLMClient()
    llm.register(
        "default",
        {
            "items": [
                {
                    "product_id": 1,
                    "justificacion": "Alta relevancia para áfidos en tomate.",
                    "ventajas": ["Buen perfil para el cultivo"],
                    "riesgos": ["Respetar intervalo de seguridad"],
                    "recomendacion_uso_general": "Aplicar según etiqueta SFE.",
                },
                {
                    "product_id": 2,
                    "justificacion": "Alternativa de costo moderado.",
                    "ventajas": ["Precio accesible"],
                    "riesgos": ["Banda toxicológica roja"],
                    "recomendacion_uso_general": "Usar EPP completo.",
                },
                {
                    "product_id": 3,
                    "justificacion": "Tercera opción balanceada.",
                    "ventajas": ["Amplio espectro"],
                    "riesgos": ["Verificar compatibilidad"],
                    "recomendacion_uso_general": "Consultar agrónomo.",
                },
            ],
        },
    )
    return llm


@pytest.fixture
def pipeline_mock_llm(
    analyzer_mock_llm: MockLLMClient,
    legal_mock_llm: MockLLMClient,
    synthesizer_mock_llm: MockLLMClient,
) -> MockLLMClient:
    """LLM unificado que responde según palabras clave del prompt."""

    class CombinedMockLLM(MockLLMClient):
        async def complete_json(self, *, system_prompt, user_prompt, response_model):
            if "agrónomo experto" in system_prompt or "Analiza el siguiente caso" in user_prompt:
                return await analyzer_mock_llm.complete_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_model=response_model,
                )
            if "normativa fitosanitaria" in system_prompt:
                return await legal_mock_llm.complete_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_model=response_model,
                )
            if "consultor agronómico" in system_prompt:
                return await synthesizer_mock_llm.complete_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_model=response_model,
                )
            return await analyzer_mock_llm.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=response_model,
            )

    return CombinedMockLLM()
