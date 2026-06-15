"""Schemas del Agente 3 — Validador Legal."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.agent_products import ProductCandidate


class ValidatedProduct(BaseModel):
    """Producto que pasó validación normativa."""

    producto: ProductCandidate
    notas_validacion: str | None = None


class DiscardedProduct(BaseModel):
    """Producto descartado con motivo trazable."""

    producto: ProductCandidate
    motivo_de_descarte: str
    regulacion_referencia: str | None = None


class LegalValidationOutput(BaseModel):
    """Resultado de cruce productos × regulaciones."""

    productos_validos: list[ValidatedProduct] = Field(default_factory=list)
    productos_descartados: list[DiscardedProduct] = Field(default_factory=list)
    restricciones_detectadas: list[str] = Field(default_factory=list)
    nivel_riesgo_legal: str = Field(
        ...,
        description="bajo | medio | alto | incierto",
    )
    advertencias_legales: list[str] = Field(default_factory=list)
    confianza: float = Field(..., ge=0.0, le=1.0)
    normativa_insuficiente: bool = Field(
        default=False,
        description="True si no hay regulaciones suficientes para validar con certeza.",
    )
