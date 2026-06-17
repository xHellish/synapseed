"""Estado compartido del pipeline secuencial de agentes."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.agent_context import ContextAnalysisOutput
from app.schemas.agent_legal import LegalValidationOutput
from app.schemas.agent_products import ResearchOutput
from app.schemas.agent_recommendations import SynthesisOutput
from app.schemas.farmer_input import FarmerContextInput


@dataclass
class PipelineState:
    """Estado acumulado entre nodos (compatible con futura migración a LangGraph)."""

    farmer_input: FarmerContextInput  # entrada original del agricultor (no se modifica)
    context_analysis: ContextAnalysisOutput | None = None  # salida del agente 1 (analizador)
    research: ResearchOutput | None = None  # salida del agente 2 (investigador RAG)
    legal_validation: LegalValidationOutput | None = None  # salida del agente 3 (validador legal)
    synthesis: SynthesisOutput | None = None  # salida del agente 4 (sintetizador)
    steps_completed: list[str] = field(default_factory=list)  # nombres de los pasos ya ejecutados

    def mark_step(self, step: str) -> None:
        # Registra que un paso del pipeline termino (sirve para progreso/SSE)
        self.steps_completed.append(step)
