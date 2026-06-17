"""Modelos de recomendación."""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, ForeignKey, Enum as SQLEnum, Numeric, Text, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, IDMixin, repr_columns
from app.models.user import User
from app.models.zone import Zone
from app.models.product import Product


class RecommendationStatus(str, PyEnum):
    """Estado de la recomendación."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Recommendation(Base, IDMixin, TimestampMixin):
    """Recomendación generada por el pipeline de IA."""

    __tablename__ = "recommendations"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("zones.id", ondelete="SET NULL"), nullable=True, index=True)
    ticket_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    # Contexto del caso
    crop: Mapped[str] = mapped_column(String(100), nullable=False)
    crop_stage: Mapped[str] = mapped_column(String(50), nullable=False)
    problem: Mapped[str] = mapped_column(String(255), nullable=False)
    problem_category: Mapped[str] = mapped_column(String(100), nullable=False)
    last_agrochemical_used: Mapped[str | None] = mapped_column(String(255), nullable=True)
    budget_range: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Contexto ambiental (si no hay zona)
    soil_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    humidity: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    temperature: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    water_quality: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Estado del pipeline
    status: Mapped[RecommendationStatus] = mapped_column(
        SQLEnum(RecommendationStatus, name="recommendation_status", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=RecommendationStatus.PENDING,
        index=True,
    )
    current_step: Mapped[str | None] = mapped_column(String(50), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    user: Mapped[User] = relationship("User", back_populates="recommendations")
    zone: Mapped[Zone | None] = relationship("Zone", back_populates="recommendations")
    products: Mapped[list["RecommendationProduct"]] = relationship(
        "RecommendationProduct",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        order_by="RecommendationProduct.rank",
    )

    __table_args__ = (
        Index("ix_recommendations_user_status", "user_id", "status"),
        Index("ix_recommendations_ticket_id", "ticket_id", unique=True),
    )

    __repr__ = repr_columns("id", "ticket_id", "user_id", "crop", "problem", "status")


class RecommendationProduct(Base, IDMixin, TimestampMixin):
    """Producto recomendado dentro de una recomendación."""

    __tablename__ = "recommendation_products"

    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rank: Mapped[int] = mapped_column(nullable=False)  # 1, 2, 3

    # Justificación específica para este producto en este caso
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    dosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    precio_estimado: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    toxicidad: Mapped[str | None] = mapped_column(String(20), nullable=True)
    intervalo_seguridad: Mapped[int | None] = mapped_column(nullable=True)

    # Contenido generado por el LLM (texto enriquecido por el sintetizador)
    ventajas: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list serializado
    riesgos: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON list serializado
    recomendacion_uso_general: Mapped[str | None] = mapped_column(Text, nullable=True)

    recommendation: Mapped[Recommendation] = relationship("Recommendation", back_populates="products")
    product: Mapped[Product] = relationship("Product")

    __table_args__ = (
        UniqueConstraint("recommendation_id", "rank", name="uq_recommendation_rank"),
        UniqueConstraint("recommendation_id", "product_id", name="uq_recommendation_product"),
    )

    __repr__ = repr_columns("id", "recommendation_id", "product_id", "rank")


# Back-populates
User.recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
Zone.recommendations = relationship("Recommendation", back_populates="zone", cascade="all, delete-orphan")