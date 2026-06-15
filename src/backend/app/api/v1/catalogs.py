from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.product import ProductCategory, ProductStatus, ToxicBand
from app.repositories import ProductRepository

router = APIRouter(prefix="/catalogs", tags=["catalogs"])

# Catálogos estáticos — no requieren DB
_CROPS = [
    {"id": "maize", "name": "Maíz"},
    {"id": "coffee", "name": "Café"},
    {"id": "rice", "name": "Arroz"},
    {"id": "banana", "name": "Banano"},
    {"id": "pineapple", "name": "Piña"},
    {"id": "potato", "name": "Papa"},
    {"id": "tomato", "name": "Tomate"},
    {"id": "bean", "name": "Frijol"},
]

_CROP_STAGES = [
    {"id": "germination", "name": "Germinación"},
    {"id": "vegetative", "name": "Vegetativo"},
    {"id": "flowering", "name": "Floración"},
    {"id": "fruiting", "name": "Fructificación"},
    {"id": "harvest", "name": "Cosecha"},
]

_SOIL_TYPES = [
    {"id": "clay", "name": "Arcilloso"},
    {"id": "loam", "name": "Franco"},
    {"id": "sandy", "name": "Arenoso"},
    {"id": "silty", "name": "Limoso"},
    {"id": "peaty", "name": "Turboso"},
]

_PROBLEMS = [
    {"id": "fungus", "name": "Hongos"},
    {"id": "pests", "name": "Plagas"},
    {"id": "drought", "name": "Sequía"},
    {"id": "weeds", "name": "Malezas"},
    {"id": "bacteria", "name": "Bacterias"},
    {"id": "nematodes", "name": "Nematodos"},
]

_BUDGETS = [
    {"id": "low", "name": "Bajo", "min": 0, "max": 10},
    {"id": "medium", "name": "Medio", "min": 10, "max": 25},
    {"id": "high", "name": "Alto", "min": 25, "max": 100},
]


@router.get("/crops", summary="Lista de cultivos")
async def list_crops() -> list[dict]:
    return _CROPS


@router.get("/crop-stages", summary="Etapas de cultivo")
async def list_crop_stages() -> list[dict]:
    return _CROP_STAGES


@router.get("/soil-types", summary="Tipos de suelo")
async def list_soil_types() -> list[dict]:
    return _SOIL_TYPES


@router.get("/problems", summary="Problemas agrícolas")
async def list_problems() -> list[dict]:
    return _PROBLEMS


@router.get("/budgets", summary="Rangos de presupuesto")
async def list_budgets() -> list[dict]:
    return _BUDGETS


# Endpoints de productos dinámicos — consultan Supabase

@router.get("/products", summary="Productos agroquímicos registrados (SFE)")
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    categoria: ProductCategory | None = None,
    estado: ProductStatus | None = Query(ProductStatus.ACTIVO),
    banda_toxicologica: ToxicBand | None = None,
    cultivo: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    products = ProductRepository(db)
    items = await products.get_filtered(
        skip=skip,
        limit=limit,
        categoria=categoria,
        estado=estado,
        banda_toxicologica=banda_toxicologica,
        cultivo_objetivo=cultivo,
    )
    total = await products.count_filtered(
        categoria=categoria,
        estado=estado,
        banda_toxicologica=banda_toxicologica,
    )
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "id": p.id,
                "numero_registro": p.numero_registro,
                "nombre_comercial": p.nombre_comercial,
                "ingrediente_activo": p.ingrediente_activo,
                "categoria": p.categoria.value,
                "estado": p.estado.value,
                "banda_toxicologica": p.banda_toxicologica.value if p.banda_toxicologica else None,
                "registrante": p.registrante,
                "cultivo_objetivo": p.cultivo_objetivo,
                "problema_objetivo": p.problema_objetivo,
                "dosis_recomendada": p.dosis_recomendada,
                "precio_referencia_por_litro": p.precio_referencia_por_litro,
            }
            for p in items
        ],
    }


@router.get("/products/search", summary="Búsqueda de productos por nombre o ingrediente activo")
async def search_products(
    q: str = Query(..., min_length=2, description="Texto a buscar"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    products = ProductRepository(db)
    items = await products.search_by_text(q, skip=skip, limit=limit)
    return [
        {
            "id": p.id,
            "numero_registro": p.numero_registro,
            "nombre_comercial": p.nombre_comercial,
            "ingrediente_activo": p.ingrediente_activo,
            "categoria": p.categoria.value,
            "estado": p.estado.value,
            "banda_toxicologica": p.banda_toxicologica.value if p.banda_toxicologica else None,
        }
        for p in items
    ]
