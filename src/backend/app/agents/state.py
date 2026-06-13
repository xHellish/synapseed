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

    farmer_input: FarmerContextInput
    context_analysis: ContextAnalysisOutput | None = None
    research: ResearchOutput | None = None
    legal_validation: LegalValidationOutput | None = None
    synthesis: SynthesisOutput | None = None
    steps_completed: list[str] = field(default_factory=list)

    def mark_step(self, step: str) -> None:
        self.steps_completed.append(step)
