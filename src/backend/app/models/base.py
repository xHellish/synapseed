"""Base model y utilidades comunes para SQLAlchemy."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Clase base para todos los modelos."""

    pass


class TimestampMixin:
    """Mixin que agrega created_at y updated_at automáticos."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class IDMixin:
    """Mixin que agrega id autoincremental como PK."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


def repr_columns(*cols: str) -> Any:
    """Helper para generar __repr__ bonito."""
    def _repr(self) -> str:
        items = []
        for c in cols:
            val = getattr(self, c, None)
            items.append(f"{c}={val!r}")
        return f"<{self.__class__.__name__}({', '.join(items)})>"
    return _repr