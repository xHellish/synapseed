"""Modelo de Límite Máximo de Residuos (LMR) nacional."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, IDMixin, repr_columns


class Lmr(Base, IDMixin, TimestampMixin):
    """Límite Máximo de Residuos (LMR) de plaguicidas por cultivo nacional."""

    __tablename__ = "lmrs"

    plaguicida: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    clase: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cultivo: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    lmr_nac: Mapped[str | None] = mapped_column(String(100), nullable=True)

    __repr__ = repr_columns("id", "plaguicida", "cultivo", "lmr_nac")
