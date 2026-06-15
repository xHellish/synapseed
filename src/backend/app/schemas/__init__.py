"""Pydantic DTOs para la API y el pipeline de agentes IA."""

from app.schemas.agent_context import AgronomicConditions, ContextAnalysisOutput
from app.schemas.agent_legal import (
    DiscardedProduct,
    LegalValidationOutput,
    ValidatedProduct,
)
from app.schemas.agent_products import ProductCandidate, ResearchOutput
from app.schemas.agent_recommendations import (
    PipelineResult,
    ProductRecommendation,
    SynthesisOutput,
)
from app.schemas.auth import RegisterRequest
from app.schemas.farmer_input import FarmerContextInput

__all__ = [
    "FarmerContextInput",
    "RegisterRequest",
    "AgronomicConditions",
    "ContextAnalysisOutput",
    "ProductCandidate",
    "ResearchOutput",
    "ValidatedProduct",
    "DiscardedProduct",
    "LegalValidationOutput",
    "ProductRecommendation",
    "SynthesisOutput",
    "PipelineResult",
]