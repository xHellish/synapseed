"""Schemas de salida del Agente 1 — Analizador de Contexto."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgronomicConditions(BaseModel):
    """Condiciones ambientales normalizadas para el pipeline."""

    tipo_suelo: str | None = None
    humedad: str | None = None
    temperatura: str | None = None
    calidad_agua: str | None = None


class ContextAnalysisOutput(BaseModel):
    """Resumen agronómico estructurado (Agente 1).

    Futuro: persistir en ``recommendations.agent_context`` (JSONB pendiente).
    """

    cultivo: str
    problema_detectado: str
    condiciones_agronomicas: AgronomicConditions
    severidad_estimada: str = Field(
        ...,
        description="baja | media | alta",
    )
    restricciones_relevantes: list[str] = Field(default_factory=list)
    resumen_para_rag: str = Field(
        ...,
        min_length=10,
        description="Texto denso para búsqueda semántica de productos.",
    )
    advertencias: list[str] = Field(default_factory=list)
    datos_faltantes: list[str] = Field(default_factory=list)
    confianza: float = Field(..., ge=0.0, le=1.0)
    tipo_proteccion_necesaria: str = Field(
        ...,
        description="Ej: insecticida, fungicida, herbicida, fertilizante.",
    )
    categoria_producto_sugerida: str = Field(
        ...,
        description="plaguicida | fertilizante",
    )
