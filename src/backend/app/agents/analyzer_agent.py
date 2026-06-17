"""Agente 1 - Analizador de Contexto."""

from __future__ import annotations

from app.agents.prompts.analyzer import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.schemas.agent_context import ContextAnalysisOutput
from app.schemas.farmer_input import FarmerContextInput
from app.services.llm_client import LLMClient


async def analyze_context(
    farmer_input: FarmerContextInput,
    llm: LLMClient,
) -> ContextAnalysisOutput:
    """Estructura el contexto agronómico sin recomendar productos."""
    # Rellena la plantilla del prompt con los datos del caso (valores por defecto si faltan)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        crop=farmer_input.crop,
        crop_stage=farmer_input.crop_stage,
        problem=farmer_input.problem,
        problem_category=farmer_input.problem_category,
        last_agrochemical_used=farmer_input.last_agrochemical_used or "ninguno",
        budget_range=farmer_input.budget_range or "no especificado",
        soil_type=farmer_input.soil_type or "no especificado",
        humidity=farmer_input.humidity if farmer_input.humidity is not None else "no especificado",
        temperature=(
            farmer_input.temperature if farmer_input.temperature is not None else "no especificado"
        ),
        water_quality=farmer_input.water_quality or "no especificado",
        zone_id=farmer_input.zone_id if farmer_input.zone_id is not None else "ninguna",
    )
    # Pide al LLM una respuesta JSON validada contra el schema ContextAnalysisOutput
    return await llm.complete_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=ContextAnalysisOutput,
    )
