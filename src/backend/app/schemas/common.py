from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class MessageResponse(BaseModel):
    message: str


# ── Lookup tables live outside the model so validators can reference them ─────
_HUMIDITY_MAP: dict[str, float] = {
    "muy baja": 20.0,
    "baja": 40.0,
    "media": 60.0,
    "alta": 80.0,
    "muy alta": 95.0,
}

_TEMP_MAP: dict[str, float] = {
    "menos de 10°c": 8.0,
    "menos de 10c": 8.0,
    "10°c - 15°c": 12.5,
    "10c - 15c": 12.5,
    "15°c - 20°c": 17.5,
    "15c - 20c": 17.5,
    "20°c - 25°c": 22.5,
    "20c - 25c": 22.5,
    "25°c - 30°c": 27.5,
    "25c - 30c": 27.5,
    "más de 30°c": 35.0,
    "mas de 30c": 35.0,
}


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
    zone_id: int | None = None

    @field_validator("humidity", mode="before")
    @classmethod
    def coerce_humidity(cls, v: object) -> float:
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            mapped = _HUMIDITY_MAP.get(v.lower().strip())
            if mapped is not None:
                return mapped
            try:
                return float(v)
            except ValueError:
                pass
        return 60.0  # safe default: Media

    @field_validator("temperature", mode="before")
    @classmethod
    def coerce_temperature(cls, v: object) -> float:
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            key = v.lower().strip()
            mapped = _TEMP_MAP.get(key)
            if mapped is not None:
                return mapped
            # Loose match ignoring spaces
            for k, val in _TEMP_MAP.items():
                if k.replace(" ", "") == key.replace(" ", ""):
                    return val
            try:
                return float(v)
            except ValueError:
                pass
        return 22.0  # safe default
