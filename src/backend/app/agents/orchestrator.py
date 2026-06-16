"""Orquestador secuencial del pipeline de 4 agentes IA."""

from __future__ import annotations

import logging
from typing import Callable, Awaitable

from app.agents.analyzer_agent import analyze_context
from app.agents.legal_validator_agent import validate_legal
from app.agents.researcher_agent import research_products
from app.agents.state import PipelineState
from app.agents.synthesizer_agent import synthesize_recommendations
from app.repositories.product_repository import AbstractProductRepository as ProductRepository
from app.repositories.regulation_repository import RegulationRepository
from app.schemas.agent_recommendations import PipelineResult
from app.schemas.farmer_input import FarmerContextInput
from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Ejecuta los 4 agentes en orden.

    Diseñado para invocarse luego desde Celery, FastAPI o LangGraph.
    Migración futura a LangGraph: cada método privado puede convertirse en nodo.
    """

    def __init__(
        self,
        llm: LLMClient,
        product_repo: ProductRepository,
        regulation_repo: RegulationRepository,
    ) -> None:
        self._llm = llm
        self._product_repo = product_repo
        self._regulation_repo = regulation_repo

    async def run(
        self,
        farmer_input: FarmerContextInput,
        on_step_complete: Callable[[str], Awaitable[None]] | None = None,
    ) -> PipelineResult:
        """Pipeline completo: contexto → RAG → legal → síntesis."""
        state = PipelineState(farmer_input=farmer_input)

        logger.info("Pipeline paso 1/4: Analizador de Contexto")
        state.context_analysis = await analyze_context(farmer_input, self._llm)
        state.mark_step("context_analyzer")
        if on_step_complete:
            await on_step_complete("context_analyzer")

        assert state.context_analysis is not None
        logger.info("Pipeline paso 2/4: Investigador RAG")
        state.research = await research_products(state.context_analysis, self._product_repo)
        state.mark_step("researcher")
        if on_step_complete:
            await on_step_complete("researcher")

        assert state.research is not None
        logger.info("Pipeline paso 3/4: Validador Legal")
        state.legal_validation = await validate_legal(
            state.context_analysis,
            state.research,
            self._regulation_repo,
            self._llm,
        )
        state.mark_step("legal_validator")
        if on_step_complete:
            await on_step_complete("legal_validator")

        assert state.legal_validation is not None
        logger.info("Pipeline paso 4/4: Sintetizador")
        state.synthesis = await synthesize_recommendations(
            state.context_analysis,
            state.legal_validation,
            self._llm,
        )
        state.mark_step("synthesizer")
        if on_step_complete:
            await on_step_complete("synthesizer")

        assert state.synthesis is not None
        return PipelineResult(
            input=farmer_input,
            context_analysis=state.context_analysis,
            research=state.research,
            legal_validation=state.legal_validation,
            synthesis=state.synthesis,
            processing_steps=state.steps_completed,
        )
