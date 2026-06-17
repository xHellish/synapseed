"""Tests del Agente 4 — Sintetizador."""

import pytest

from app.agents.synthesizer_agent import synthesize_recommendations
from app.schemas.agent_context import AgronomicConditions, ContextAnalysisOutput
from app.schemas.agent_legal import LegalValidationOutput, ValidatedProduct
from app.schemas.agent_products import ProductCandidate
from app.services.llm_client import MockLLMClient


def _validated(pid: int, score: float = 0.9) -> ValidatedProduct:
    return ValidatedProduct(
        producto=ProductCandidate(
            product_id=pid,
            nombre_comercial=f"Producto {pid}",
            ingrediente_activo=f"Ing {pid}",
            categoria="plaguicida",
            precio_referencia_por_litro=10000.0,
            toxicidad="amarilla",
            dosis_recomendada="1 L/ha",
            intervalo_seguridad_dias=7,
            score_relevancia=score,
            razon_relevancia="test",
        )
    )


@pytest.mark.asyncio
async def test_synthesizer_returns_exactly_three_when_enough_valid():
    context = ContextAnalysisOutput(
        cultivo="tomate",
        problema_detectado="plaga",
        condiciones_agronomicas=AgronomicConditions(),
        severidad_estimada="media",
        restricciones_relevantes=[],
        resumen_para_rag="tomate plaga insecticida",
        advertencias=[],
        datos_faltantes=[],
        confianza=0.9,
        tipo_proteccion_necesaria="insecticida",
        categoria_producto_sugerida="plaguicida",
    )
    legal = LegalValidationOutput(
        productos_validos=[_validated(i, 1 - i * 0.1) for i in range(1, 5)],
        productos_descartados=[],
        restricciones_detectadas=[],
        nivel_riesgo_legal="bajo",
        advertencias_legales=[],
        confianza=0.9,
    )
    llm = MockLLMClient(
        responses={
            "default": {
                "items": [
                    {
                        "product_id": i,
                        "justificacion": f"Just {i}",
                        "ventajas": ["v"],
                        "riesgos": ["r"],
                        "recomendacion_uso_general": "uso seguro",
                    }
                    for i in range(1, 4)
                ]
            }
        }
    )
    result = await synthesize_recommendations(context, legal, llm)
    assert len(result.recomendaciones) == 3
    assert result.recomendaciones[0].ranking == 1
    assert result.recomendaciones[0].precio == 10000.0


@pytest.mark.asyncio
async def test_synthesizer_does_not_invent_third_when_only_two_valid():
    context = ContextAnalysisOutput(
        cultivo="tomate",
        problema_detectado="plaga",
        condiciones_agronomicas=AgronomicConditions(),
        severidad_estimada="media",
        restricciones_relevantes=[],
        resumen_para_rag="tomate plaga",
        advertencias=[],
        datos_faltantes=[],
        confianza=0.9,
        tipo_proteccion_necesaria="insecticida",
        categoria_producto_sugerida="plaguicida",
    )
    legal = LegalValidationOutput(
        productos_validos=[_validated(1), _validated(2, 0.8)],
        productos_descartados=[],
        restricciones_detectadas=[],
        nivel_riesgo_legal="bajo",
        advertencias_legales=[],
        confianza=0.9,
    )
    llm = MockLLMClient(
        responses={
            "default": {
                "items": [
                    {
                        "product_id": 1,
                        "justificacion": "J1",
                        "ventajas": [],
                        "riesgos": [],
                        "recomendacion_uso_general": "U1",
                    },
                    {
                        "product_id": 2,
                        "justificacion": "J2",
                        "ventajas": [],
                        "riesgos": [],
                        "recomendacion_uso_general": "U2",
                    },
                ]
            }
        }
    )
    result = await synthesize_recommendations(context, legal, llm)
    assert len(result.recomendaciones) == 2
    assert any("Solo 2 producto" in w for w in result.advertencias)


@pytest.mark.asyncio
async def test_synthesizer_populates_ventajas_riesgos_recomendacion():
    """ventajas, riesgos y recomendacion_uso_general deben incluirse en la salida."""
    context = ContextAnalysisOutput(
        cultivo="tomate",
        problema_detectado="plaga",
        condiciones_agronomicas=AgronomicConditions(),
        severidad_estimada="media",
        restricciones_relevantes=[],
        resumen_para_rag="tomate plaga insecticida",
        advertencias=[],
        datos_faltantes=[],
        confianza=0.9,
        tipo_proteccion_necesaria="insecticida",
        categoria_producto_sugerida="plaguicida",
    )
    legal = LegalValidationOutput(
        productos_validos=[_validated(1)],
        productos_descartados=[],
        restricciones_detectadas=[],
        nivel_riesgo_legal="bajo",
        advertencias_legales=[],
        confianza=0.9,
    )
    llm = MockLLMClient(
        responses={
            "default": {
                "items": [
                    {
                        "product_id": 1,
                        "justificacion": "Producto ideal para este caso.",
                        "ventajas": ["Amplio espectro", "Registrado SFE"],
                        "riesgos": ["Respetar intervalo de seguridad", "Usar EPP"],
                        "recomendacion_uso_general": "Aplicar en las horas de menor temperatura.",
                    }
                ]
            }
        }
    )
    result = await synthesize_recommendations(context, legal, llm)
    rec = result.recomendaciones[0]

    assert rec.ventajas == ["Amplio espectro", "Registrado SFE"]
    assert rec.riesgos == ["Respetar intervalo de seguridad", "Usar EPP"]
    assert rec.recomendacion_uso_general == "Aplicar en las horas de menor temperatura."


@pytest.mark.asyncio
async def test_synthesizer_empty_ventajas_riesgos_when_llm_omits():
    """Si el LLM no devuelve ventajas/riesgos, deben ser listas vacías (no None)."""
    context = ContextAnalysisOutput(
        cultivo="café",
        problema_detectado="roya",
        condiciones_agronomicas=AgronomicConditions(),
        severidad_estimada="alta",
        restricciones_relevantes=[],
        resumen_para_rag="café roya fungicida",
        advertencias=[],
        datos_faltantes=[],
        confianza=0.8,
        tipo_proteccion_necesaria="fungicida",
        categoria_producto_sugerida="plaguicida",
    )
    legal = LegalValidationOutput(
        productos_validos=[_validated(2)],
        productos_descartados=[],
        restricciones_detectadas=[],
        nivel_riesgo_legal="bajo",
        advertencias_legales=[],
        confianza=0.8,
    )
    llm = MockLLMClient(
        responses={
            "default": {
                "items": [
                    {
                        "product_id": 2,
                        "justificacion": "Fungicida con buena cobertura.",
                        # Sin ventajas ni riesgos explícitos → defaults vacíos
                        "recomendacion_uso_general": "Consultar etiqueta SFE.",
                    }
                ]
            }
        }
    )
    result = await synthesize_recommendations(context, legal, llm)
    rec = result.recomendaciones[0]

    assert isinstance(rec.ventajas, list)
    assert isinstance(rec.riesgos, list)
    assert rec.recomendacion_uso_general == "Consultar etiqueta SFE."


@pytest.mark.asyncio
async def test_synthesizer_does_not_invent_missing_factual_fields():
    context = ContextAnalysisOutput(
        cultivo="tomate",
        problema_detectado="plaga",
        condiciones_agronomicas=AgronomicConditions(),
        severidad_estimada="media",
        restricciones_relevantes=[],
        resumen_para_rag="tomate plaga",
        advertencias=[],
        datos_faltantes=[],
        confianza=0.9,
        tipo_proteccion_necesaria="insecticida",
        categoria_producto_sugerida="plaguicida",
    )
    legal = LegalValidationOutput(
        productos_validos=[
            ValidatedProduct(
                producto=ProductCandidate(
                    product_id=99,
                    nombre_comercial="Producto sin datos",
                    ingrediente_activo="Ing X",
                    categoria="plaguicida",
                    precio_referencia_por_litro=None,
                    toxicidad=None,
                    dosis_recomendada=None,
                    intervalo_seguridad_dias=None,
                    score_relevancia=0.9,
                    razon_relevancia="coincidencia parcial",
                )
            )
        ],
        productos_descartados=[],
        restricciones_detectadas=[],
        nivel_riesgo_legal="bajo",
        advertencias_legales=[],
        confianza=0.9,
    )
    llm = MockLLMClient(
        responses={
            "default": {
                "items": [
                    {
                        "product_id": 99,
                        "justificacion": "Opción agronómica con datos incompletos en catálogo.",
                        "ventajas": ["Relevancia parcial"],
                        "riesgos": ["Verificar etiqueta SFE"],
                        "recomendacion_uso_general": "Consultar agrónomo certificado.",
                    }
                ]
            }
        }
    )

    result = await synthesize_recommendations(context, legal, llm)
    rec = result.recomendaciones[0]

    assert rec.dosis == "no_disponible"
    assert rec.precio == "no_disponible"
    assert rec.toxicidad == "no_disponible"
    assert rec.intervalo_seguridad == "no_disponible"
    assert "L/ha" not in rec.justificacion
    assert rec.precio != 10000.0
