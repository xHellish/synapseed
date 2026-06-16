"""Base de modelos SQLAlchemy - exporta todos los modelos registrados."""

from app.models import (
    User,
    Zone,
    Product,
    Distributor,
    ProductDistributor,
    Recommendation,
    RecommendationProduct,
    Regulation,
    AuditLog,
    Lmr,
)

# Importar Base desde models.base para que todos los modelos se registren
from app.models.base import Base

__all__ = [
    "Base",
    "User",
    "Zone",
    "Product",
    "Distributor",
    "ProductDistributor",
    "Recommendation",
    "RecommendationProduct",
    "Regulation",
    "AuditLog",
    "Lmr",
]