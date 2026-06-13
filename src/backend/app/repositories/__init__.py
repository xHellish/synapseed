"""Repositorios de lectura para el pipeline de agentes."""

from app.repositories.product_repository import (
    FakeProductRepository,
    ProductRepository,
    SqlAlchemyProductRepository,
)
from app.repositories.regulation_repository import (
    FakeRegulationRepository,
    RegulationRecord,
    RegulationRepository,
    SqlAlchemyRegulationRepository,
)

__all__ = [
    "ProductRepository",
    "SqlAlchemyProductRepository",
    "FakeProductRepository",
    "RegulationRepository",
    "RegulationRecord",
    "SqlAlchemyRegulationRepository",
    "FakeRegulationRepository",
]
