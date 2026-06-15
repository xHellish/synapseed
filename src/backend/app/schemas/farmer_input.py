"""Entrada del formulario del agricultor (wizard de contexto)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FarmerContextInput(BaseModel):
    """Datos del caso agrícola enviados por el wizard.

    Alineado con ``Recommendation`` ORM y ``Docs/Spec_validada.md``.
    ``humidity`` y ``temperature`` aceptan float o str por discrepancia
    documentación (dropdowns) vs modelo (Numeric).
    """

    crop: str = Field(..., min_length=1, max_length=100)
    crop_stage: str = Field(..., min_length=1, max_length=50)
    problem: str = Field(..., min_length=1, max_length=255)
    problem_category: str = Field(..., min_length=1, max_length=100)
    last_agrochemical_used: str | None = Field(default=None, max_length=255)
    budget_range: str | None = Field(default=None, max_length=50)
    soil_type: str | None = Field(default=None, max_length=50)
    humidity: float | str | None = None
    temperature: float | str | None = None
    water_quality: str | None = Field(default=None, max_length=50)
    zone_id: int | None = None
