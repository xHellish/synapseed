from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


CATALOGS = {
    "crops": [
        {"id": "maize", "name": "Maíz"},
        {"id": "coffee", "name": "Café"},
        {"id": "rice", "name": "Arroz"},
    ],
    "crop_stages": [
        {"id": "germination", "name": "Germinación"},
        {"id": "vegetative", "name": "Vegetativo"},
        {"id": "flowering", "name": "Floración"},
    ],
    "soil_types": [
        {"id": "clay", "name": "Arcilloso"},
        {"id": "loam", "name": "Franco"},
        {"id": "sandy", "name": "Arenoso"},
    ],
    "problems": [
        {"id": "fungus", "name": "Hongos"},
        {"id": "pests", "name": "Plagas"},
        {"id": "drought", "name": "Sequía"},
    ],
    "agrochemicals": [
        {"id": "fungicide-a", "name": "Fungicida A"},
        {"id": "insecticide-b", "name": "Insecticida B"},
    ],
    "budgets": [
        {"id": "low", "name": "Bajo", "min": 0, "max": 10},
        {"id": "medium", "name": "Medio", "min": 10, "max": 25},
    ],
}


@router.get("/crops", summary="Lista de cultivos")
async def list_crops() -> list[dict[str, str]]:
    return CATALOGS["crops"]


@router.get("/crop-stages", summary="Etapas de cultivo")
async def list_crop_stages() -> list[dict[str, str]]:
    return CATALOGS["crop_stages"]


@router.get("/soil-types", summary="Tipos de suelo")
async def list_soil_types() -> list[dict[str, str]]:
    return CATALOGS["soil_types"]


@router.get("/problems", summary="Problemas agrícolas")
async def list_problems() -> list[dict[str, str]]:
    return CATALOGS["problems"]


@router.get("/agrochemicals", summary="Agroquímicos conocidos")
async def list_agrochemicals() -> list[dict[str, str]]:
    return CATALOGS["agrochemicals"]


@router.get("/budgets", summary="Rangos de presupuesto")
async def list_budgets() -> list[dict[str, object]]:
    return CATALOGS["budgets"]
