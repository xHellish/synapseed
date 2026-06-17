"""Agente 3 - Validador Legal."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field

from app.agents.prompts.legal_validator import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.repositories.regulation_repository import RegulationRecord, RegulationRepository
from app.schemas.agent_context import ContextAnalysisOutput
from app.schemas.agent_legal import (
    DiscardedProduct,
    LegalValidationOutput,
    ValidatedProduct,
)
from app.schemas.agent_products import ProductCandidate, ResearchOutput
from app.services.llm_client import LLMClient


# Un descarte propuesto por el LLM: que producto y por que
class _LegalDiscardItem(BaseModel):
    product_id: int
    motivo_de_descarte: str
    regulacion_referencia: str | None = None


# Forma esperada de la respuesta JSON del LLM en la revision normativa
class _LegalLLMReview(BaseModel):
    productos_validos_ids: list[int] = Field(default_factory=list)  # IDs que el LLM confirma validos
    descartes: list[_LegalDiscardItem] = Field(default_factory=list)  # IDs que el LLM rechaza
    restricciones_detectadas: list[str] = Field(default_factory=list)
    nivel_riesgo_legal: str = "incierto"
    advertencias_legales: list[str] = Field(default_factory=list)
    confianza: float = Field(default=0.5, ge=0.0, le=1.0)
    normativa_insuficiente: bool = False


def _split_ingredients(ingrediente_activo: str) -> list[str]:
    # Separa "glifosato, 2,4-D / paraquat" en ingredientes sueltos (ignora fragmentos cortos)
    parts = re.split(r"[,;/+]", ingrediente_activo.lower())
    return [p.strip() for p in parts if len(p.strip()) > 2]


def _rule_based_discard(
    candidate: ProductCandidate,
    regulations: list[RegulationRecord],
) -> DiscardedProduct | None:
    """Descarte determinístico por sustancias prohibidas explícitas."""
    # Compara cada ingrediente del producto contra las sustancias prohibidas de cada regulacion
    ingredients = _split_ingredients(candidate.ingrediente_activo)
    for reg in regulations:
        if not reg.sustancias_afectadas:
            continue
        prohibited_blob = reg.sustancias_afectadas.lower()
        for ing in ingredients:
            if ing and ing in prohibited_blob:
                # Coincidencia: el producto se descarta sin necesidad del LLM
                return DiscardedProduct(
                    producto=candidate,
                    motivo_de_descarte=(
                        f"Ingrediente activo '{ing}' aparece en regulación {reg.numero}"
                    ),
                    regulacion_referencia=reg.numero,
                )
    return None


async def validate_legal(
    context: ContextAnalysisOutput,
    research: ResearchOutput,
    regulation_repo: RegulationRepository,
    llm: LLMClient,
) -> LegalValidationOutput:
    """Cruza candidatos con regulaciones; LLM solo interpreta normativa provista."""
    # Carga las regulaciones vigentes del SFE desde la DB
    regulations = await regulation_repo.list_active()
    if not regulations:
        # Sin normativa no se puede validar: por seguridad se descarta todo (politica conservadora)
        return LegalValidationOutput(
            productos_validos=[],
            productos_descartados=[
                DiscardedProduct(
                    producto=c,
                    motivo_de_descarte="No hay regulaciones cargadas en la base de datos",
                )
                for c in research.candidatos
            ],
            restricciones_detectadas=[],
            nivel_riesgo_legal="incierto",
            advertencias_legales=[
                "Sin regulaciones en DB no es posible validar legalmente los productos."
            ],
            confianza=0.0,
            normativa_insuficiente=True,
        )

    # Fase 1 (deterministica): descartar por reglas duras antes de gastar el LLM
    rule_discarded: list[DiscardedProduct] = []
    survivors: list[ProductCandidate] = []
    for candidate in research.candidatos:
        discarded = _rule_based_discard(candidate, regulations)
        if discarded:
            rule_discarded.append(discarded)  # prohibido por sustancia
        else:
            survivors.append(candidate)  # pasa a revision del LLM

    if not survivors:
        # Si las reglas eliminaron todo, no hay nada que mandarle al LLM
        return LegalValidationOutput(
            productos_validos=[],
            productos_descartados=rule_discarded,
            restricciones_detectadas=["Todos los candidatos fueron descartados por reglas SFE"],
            nivel_riesgo_legal="alto",
            advertencias_legales=["Revisar lista de sustancias prohibidas del SFE"],
            confianza=0.85,
            normativa_insuficiente=False,
        )

    # Fase 2 (interpretativa): el LLM revisa los sobrevivientes contra la normativa provista
    # Se le pasan las regulaciones como datos (no inventa nada, solo interpreta lo que recibe)
    reg_payload = [
        {
            "numero": r.numero,
            "titulo": r.titulo,
            "tipo": r.tipo,
            "resumen": r.resumen,
            "sustancias_afectadas": r.sustancias_afectadas,
            "cultivos_afectados": r.cultivos_afectados,
        }
        for r in regulations
    ]
    user_prompt = USER_PROMPT_TEMPLATE.format(
        context_summary=context.resumen_para_rag,
        candidates_json=json.dumps(
            [c.model_dump() for c in survivors],
            ensure_ascii=False,
        ),
        regulations_json=json.dumps(reg_payload, ensure_ascii=False),
        already_discarded=json.dumps(
            [d.model_dump() for d in rule_discarded],
            ensure_ascii=False,
        ),
    )
    review = await llm.complete_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=_LegalLLMReview,
    )

    valid_ids = set(review.productos_validos_ids)
    llm_discarded: list[DiscardedProduct] = []
    valid_products: list[ValidatedProduct] = []

    # Mapa id -> candidato para resolver rapido las referencias que devuelve el LLM
    survivor_map = {c.product_id: c for c in survivors}
    # Procesa los descartes propuestos por el LLM y los saca de la lista de validos
    for discard in review.descartes:
        product = survivor_map.get(discard.product_id)
        if product:
            llm_discarded.append(
                DiscardedProduct(
                    producto=product,
                    motivo_de_descarte=discard.motivo_de_descarte,
                    regulacion_referencia=discard.regulacion_referencia,
                )
            )
            valid_ids.discard(discard.product_id)  # si estaba en validos, lo quitamos

    # Los IDs que el LLM marco explicitamente como validos pasan como ValidatedProduct
    for pid in valid_ids:
        product = survivor_map.get(pid)
        if product:
            valid_products.append(
                ValidatedProduct(
                    producto=product,
                    notas_validacion="Validado por cruce normativo (confirmado por LLM)",
                )
            )

    validated_ids = {v.producto.product_id for v in valid_products}
    discarded_ids = {d.producto.product_id for d in llm_discarded}
    advertencias = list(review.advertencias_legales)

    # Ante duda legal, no validar automáticamente: solo IDs explícitos del LLM.
    # Cualquier sobreviviente que el LLM no menciono (ni valido ni descarto) se descarta por seguridad
    for candidate in survivors:
        if candidate.product_id in validated_ids or candidate.product_id in discarded_ids:
            continue
        llm_discarded.append(
            DiscardedProduct(
                producto=candidate,
                motivo_de_descarte=(
                    "No confirmado en revisión normativa LLM "
                    "(sin evidencia explícita de validez legal)"
                ),
                regulacion_referencia=None,
            )
        )

    # Marca si la normativa no alcanzo para confirmar todo (afecta el nivel de confianza)
    normativa_insuficiente = review.normativa_insuficiente
    if not valid_products:
        normativa_insuficiente = True
        advertencias.append(
            "Ningún producto fue confirmado como legalmente válido por la revisión normativa."
        )
    elif len(validated_ids) < len(survivors):
        normativa_insuficiente = True
        advertencias.append(
            "Al menos un candidato no pudo confirmarse legalmente; "
            "no se asumió validez por omisión."
        )

    # No permitimos "riesgo bajo" si la normativa fue insuficiente (degradamos a incierto)
    nivel_riesgo = review.nivel_riesgo_legal
    if normativa_insuficiente and nivel_riesgo == "bajo":
        nivel_riesgo = "incierto"

    # Sin productos validos, la confianza se capa fuerte
    confianza = review.confianza if valid_products else min(review.confianza, 0.3)

    # Resultado final: descartes por regla + descartes del LLM, mas los validos confirmados
    all_discarded = rule_discarded + llm_discarded
    return LegalValidationOutput(
        productos_validos=valid_products,
        productos_descartados=all_discarded,
        restricciones_detectadas=review.restricciones_detectadas,
        nivel_riesgo_legal=nivel_riesgo,
        advertencias_legales=advertencias,
        confianza=confianza,
        normativa_insuficiente=normativa_insuficiente,
    )
