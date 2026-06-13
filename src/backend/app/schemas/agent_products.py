"""Schemas del Agente 2 — Investigador RAG."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProductCandidate(BaseModel):
    """Producto candidato proveniente exclusivamente de la base de datos."""

    product_id: int
    nombre_comercial: str
    ingrediente_activo: str
    categoria: str
    cultivo_relacionado: str | None = None
    problema_relacionado: str | None = None
    precio_referencia_por_litro: float | None = None
    toxicidad: str | None = None
    dosis_recomendada: str | None = None
    intervalo_seguridad_dias: int | None = None
    numero_registro: str | None = None
    score_relevancia: float = Field(..., ge=0.0, le=1.0)
    razon_relevancia: str


class ResearchOutput(BaseModel):
    """Salida del investigador con metadatos de búsqueda."""

    candidatos: list[ProductCandidate] = Field(default_factory=list)
    metodo_busqueda: str = Field(
        ...,
        description="vector | filtros | hibrido",
    )
    total_encontrados: int = 0
    advertencias: list[str] = Field(default_factory=list)
