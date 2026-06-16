"""Acceso a Límites Máximos de Residuos (LMR)."""

from __future__ import annotations

import re
import unicodedata
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lmr import Lmr


def remove_accents(input_str: str) -> str:
    """Remueve tildes y caracteres diacríticos de una cadena de texto."""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


class LmrRepository:
    """Operaciones de base de datos para LMRs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_unique_crops(self) -> list[dict[str, str]]:
        """Obtiene la lista única de cultivos con id y nombre limpio, ordenados alfabéticamente."""
        result = await self._session.execute(
            select(Lmr.cultivo).distinct().order_by(Lmr.cultivo)
        )
        raw_crops = result.scalars().all()
        
        crops = []
        seen_names = set()
        for crop_raw in raw_crops:
            # Limpiar nombre, ej. "Brócoli ( Brassica oleracea ... )" -> "Brócoli"
            crop_clean = crop_raw.split("(")[0].strip()
            # Capitalizar pero respetando acentos (capitalize() en python a veces tiene problemas con caracteres no ascii al inicio, pero con tildes va bien)
            crop_clean = crop_clean.capitalize()
            
            # Evitar duplicados después de limpiar
            if crop_clean and crop_clean.lower() not in seen_names:
                seen_names.add(crop_clean.lower())
                crops.append({
                    "id": crop_raw,  # El ID real usado para búsquedas exactas en la DB
                    "name": crop_clean
                })
                
        # Ordenar por el nombre limpio
        crops.sort(key=lambda x: remove_accents(x["name"]))
        return crops

    async def get_lmr_by_active_ingredient_and_crop(self, active_ingredient: str, crop: str) -> str | None:
        """Busca el LMR nacional asociando el cultivo y los ingredientes activos."""
        if not crop or not active_ingredient:
            return None

        crop_clean = remove_accents(crop.lower().strip())
        
        # Obtener todos los LMRs de la DB para hacer cruces inteligentes en memoria
        # (La tabla lmrs tiene ~8500 filas, que carga muy rápido)
        result = await self._session.execute(select(Lmr))
        all_lmrs = result.scalars().all()
        
        # 1. Filtrar LMRs por coincidencia de cultivo
        cultivo_lmrs = []
        for lmr_record in all_lmrs:
            lmr_cultivo_clean = remove_accents(lmr_record.cultivo.lower())
            
            # Si el cultivo de la recomendación está contenido en el cultivo de la norma LMR, o viceversa
            # Ej: "brocoli" en "brocoli ( brassica oleracea... )"
            if crop_clean in lmr_cultivo_clean or lmr_cultivo_clean in crop_clean:
                cultivo_lmrs.append(lmr_record)
                
        if not cultivo_lmrs:
            return None
            
        # 2. Desestructurar el ingrediente activo de la recomendación
        # Ej: "Clorhidrato de Oxitetraciclina, Sulfato de Estreptomicina" -> ["oxitetraciclina", "estreptomicina"]
        ingredients = [remove_accents(i.strip().lower()) for i in re.split(r"[,;/+]", active_ingredient)]
        # Remover palabras vacías o muy cortas
        ingredients = [ing for ing in ingredients if len(ing) > 3]

        # Sinónimos y mapeos comunes (ej: Benomilo/Benomil se norma como Carbendazina)
        synonyms = {
            "benomil": "carbendazina",
            "benomilo": "carbendazina",
            "benomyl": "carbendazina",
            "cobre": "cobre",
        }
        
        expanded_ingredients = []
        for ing in ingredients:
            expanded_ingredients.append(ing)
            # Agregar sinónimo si existe
            for syn_key, syn_val in synonyms.items():
                if syn_key in ing:
                    expanded_ingredients.append(syn_val)
                    
        # 3. Buscar coincidencia de ingrediente activo en los LMRs del cultivo
        for lmr_record in cultivo_lmrs:
            lmr_plaguicida_clean = remove_accents(lmr_record.plaguicida.lower())
            for ing in expanded_ingredients:
                # Si el ingrediente de la recomendación está contenido en el plaguicida de LMR
                # Ej: "carbendazina" en "carbendazina"
                if ing in lmr_plaguicida_clean or lmr_plaguicida_clean in ing:
                    return lmr_record.lmr_nac
                    
        return None
