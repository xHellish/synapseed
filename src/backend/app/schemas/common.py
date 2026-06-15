from __future__ import annotations

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str


class RecommendationRequest(BaseModel):
    crop: str = Field(..., min_length=2)
    crop_stage: str = Field(..., min_length=2)
    problem_to_solve: str = Field(..., min_length=2)
    soil_type: str = Field(..., min_length=2)
    humidity: float = Field(..., ge=0)
    temperature: float = Field(..., ge=-50, le=100)
    water_quality: str = Field(..., min_length=2)
    max_budget_per_liter: float = Field(..., ge=0)
    last_agrochemical: str | None = None
    affected_area: float | None = None
