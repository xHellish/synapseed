"""Schemas del Agente 4 — Sintetizador y resultado del pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.agent_context import ContextAnalysisOutput
from app.schemas.agent_legal import LegalValidationOutput
from app.schemas.agent_products import ResearchOutput
from app.schemas.farmer_input import FarmerContextInput


class ProductRecommendation(BaseModel):
    """Una fila de la tabla comparativa final (datos factuales + texto LLM)."""

    ranking: int = Field(..., ge=1, le=3)
    product_id: int
    nombre_producto: str
    ingrediente_activo: str
    dosis: str | None = Field(
        default=None,
        description="null o 'no_disponible' si falta en DB.",
    )
    precio: float | str | None = None
    toxicidad: str | None = None
    intervalo_seguridad: int | str | None = None
    justificacion: str
    ventajas: list[str] = Field(default_factory=list)
    riesgos: list[str] = Field(default_factory=list)
    recomendacion_uso_general: str


class SynthesisOutput(BaseModel):
    """Exactamente hasta 3 recomendaciones rankeadas."""

    recomendaciones: list[ProductRecommendation] = Field(default_factory=list)
    candidatos_validos_totales: int = 0
    advertencias: list[str] = Field(default_factory=list)
    confianza: float = Field(..., ge=0.0, le=1.0)


class PipelineResult(BaseModel):
    """Salida completa del orquestador (listo para integración Celery/FastAPI)."""

    input: FarmerContextInput
    context_analysis: ContextAnalysisOutput
    research: ResearchOutput
    legal_validation: LegalValidationOutput
    synthesis: SynthesisOutput
    processing_steps: list[str] = Field(default_factory=list)
