"""Agente 4 - Sintetizador."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from app.agents.prompts.synthesizer import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.schemas.agent_context import ContextAnalysisOutput
from app.schemas.agent_legal import LegalValidationOutput, ValidatedProduct
from app.schemas.agent_recommendations import ProductRecommendation, SynthesisOutput
from app.services.llm_client import LLMClient

MAX_RECOMMENDATIONS = 3  # el spec pide exactamente 3 recomendaciones como maximo


# Texto generado por el LLM para un producto (justificacion, ventajas, riesgos, estimaciones)
class _SynthesisLLMItem(BaseModel):
    product_id: int
    justificacion: str
    ventajas: list[str] = Field(default_factory=list)
    riesgos: list[str] = Field(default_factory=list)
    recomendacion_uso_general: str
    dosis_estimada: str | None = None  # solo se usa si la DB no trae el dato real
    precio_estimado: float | None = None
    toxicidad_estimada: str | None = None
    intervalo_seguridad_estimado: int | None = None


# Lista de items que devuelve el LLM (uno por producto recomendado)
class _SynthesisLLMResponse(BaseModel):
    items: list[_SynthesisLLMItem]


def _format_price(value: float | None) -> float | str | None:
    # Normaliza precio ausente a la marca "no_disponible" para la tabla comparativa
    if value is None:
        return "no_disponible"
    return value


def _format_interval(days: int | None) -> int | str | None:
    # Igual que el precio: intervalo ausente -> "no_disponible"
    if days is None:
        return "no_disponible"
    return days


def _select_top_valid(validated: list[ValidatedProduct]) -> list[ValidatedProduct]:
    # Ordena los validos por score de relevancia (desc) y toma los 3 mejores
    return sorted(
        validated,
        key=lambda v: v.producto.score_relevancia,
        reverse=True,
    )[:MAX_RECOMMENDATIONS]


async def synthesize_recommendations(
    context: ContextAnalysisOutput,
    legal: LegalValidationOutput,
    llm: LLMClient,
) -> SynthesisOutput:
    """Produce hasta 3 recomendaciones; datos factuales solo desde DB."""
    valid = legal.productos_validos
    total = len(valid)
    advertencias = list(legal.advertencias_legales)

    if total == 0:
        # Sin productos validos no recomendamos nada (no se inventa)
        return SynthesisOutput(
            recomendaciones=[],
            candidatos_validos_totales=0,
            advertencias=advertencias + ["No hay productos válidos para recomendar."],
            confianza=0.0,
        )

    if total < MAX_RECOMMENDATIONS:
        # Avisamos si hay menos de 3 validos (devolvemos los que haya)
        advertencias.append(
            f"Solo {total} producto(s) válido(s); no se alcanzan {MAX_RECOMMENDATIONS} recomendaciones."
        )

    # Arma el payload con los datos REALES de la DB que el LLM va a justificar (no modificar)
    top = _select_top_valid(valid)
    products_payload = []
    for rank, item in enumerate(top, start=1):
        p = item.producto
        products_payload.append(
            {
                "ranking": rank,
                "product_id": p.product_id,
                "nombre_comercial": p.nombre_comercial,
                "ingrediente_activo": p.ingrediente_activo,
                "dosis": p.dosis_recomendada or "no_disponible",
                "precio": _format_price(p.precio_referencia_por_litro),
                "toxicidad": p.toxicidad or "no_disponible",
                "intervalo_seguridad": _format_interval(p.intervalo_seguridad_dias),
                "registrante": getattr(p, "registrante", None) or "no_disponible",
            }
        )

    # El LLM solo genera texto (justificacion, ventajas, riesgos) sobre los datos provistos
    user_prompt = USER_PROMPT_TEMPLATE.format(
        context_summary=context.resumen_para_rag,
        products_json=json.dumps(products_payload, ensure_ascii=False),
    )
    llm_text = await llm.complete_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=_SynthesisLLMResponse,
    )
    text_by_id = {item.product_id: item for item in llm_text.items}  # texto del LLM indexado por id

    # Combina dato real (DB) + texto (LLM) en cada recomendacion final
    recomendaciones: list[ProductRecommendation] = []
    for rank, item in enumerate(top, start=1):
        p = item.producto
        text = text_by_id.get(p.product_id)

        # Prioridad al dato real de la DB; solo si falta se usa la estimacion del LLM
        dosis = p.dosis_recomendada
        if not dosis or dosis == "no_disponible":
            dosis = text.dosis_estimada if text else "no_disponible"

        precio = p.precio_referencia_por_litro
        if precio is None:
            precio = text.precio_estimado if text else None

        toxicidad = p.toxicidad
        if not toxicidad or toxicidad == "no_disponible":
            toxicidad = text.toxicidad_estimada if text else "no_disponible"

        intervalo = p.intervalo_seguridad_dias
        if intervalo is None:
            intervalo = text.intervalo_seguridad_estimado if text else None

        recomendaciones.append(
            ProductRecommendation(
                ranking=rank,
                product_id=p.product_id,
                nombre_producto=p.nombre_comercial,
                ingrediente_activo=p.ingrediente_activo,
                dosis=dosis or "no_disponible",
                precio=_format_price(precio),
                toxicidad=toxicidad or "no_disponible",
                intervalo_seguridad=_format_interval(intervalo),
                justificacion=text.justificacion if text else p.razon_relevancia,
                ventajas=text.ventajas if text else [],
                riesgos=text.riesgos if text else [],
                recomendacion_uso_general=(
                    text.recomendacion_uso_general
                    if text
                    else "Consultar etiqueta SFE y agrónomo certificado."
                ),
            )
        )

    # La confianza final es la del eslabon mas debil entre contexto y validacion legal
    return SynthesisOutput(
        recomendaciones=recomendaciones,
        candidatos_validos_totales=total,
        advertencias=advertencias,
        confianza=min(legal.confianza, context.confianza),
    )
