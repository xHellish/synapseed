"""Modelo de zona/finca."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, IDMixin, repr_columns

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.recommendation import Recommendation


class Zone(Base, IDMixin, TimestampMixin):
    """Zona o finca del agricultor."""

    __tablename__ = "zones"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    soil_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    humidity: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    temperature: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    water_quality: Mapped[str | None] = mapped_column(String(50), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(11, 8), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="zones")
    recommendations: Mapped[list["Recommendation"]] = relationship("Recommendation", back_populates="zone", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_zones_user_name", "user_id", "name"),
    )

    __repr__ = repr_columns("id", "user_id", "name")
