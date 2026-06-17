"""Modelo de regulación (normativa MAG/SFE)."""

from __future__ import annotations

import enum

from sqlalchemy import String, Text, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.models.base import Base, TimestampMixin, IDMixin, repr_columns


class RegulationType(str, enum.Enum):
    """Tipo de regulación."""
    DECRETO = "decreto"
    LEY = "ley"
    RESOLUCION = "resolucion"
    LISTA_PROHIBIDA = "lista_prohibida"
    LMR = "lmr"
    OTRO = "otro"


class Regulation(Base, IDMixin, TimestampMixin):
    """Regulación/normativa del MAG o SFE."""

    __tablename__ = "regulations"

    numero: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(500), nullable=False)
    tipo: Mapped[RegulationType] = mapped_column(
        SQLEnum(RegulationType, name="regulationtype", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    fecha_publicacion: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fuente_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resumen: Mapped[str | None] = mapped_column(Text, nullable=True)
    contenido_completo: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Embedding vectorial para búsqueda semántica (768 dims)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(768),
        nullable=True,
    )

    # Entidades/ingredientes afectados (para validación rápida)
    sustancias_afectadas: Mapped[str | None] = mapped_column(Text, nullable=True)
    cultivos_afectados: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_regulations_tipo", "tipo"),
        Index("ix_regulations_sustancias", "sustancias_afectadas"),
    )

    __repr__ = repr_columns("id", "numero", "titulo", "tipo")