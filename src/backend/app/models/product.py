"""Modelo de producto (agroquímico del SFE)."""

from __future__ import annotations

import enum

from sqlalchemy import String, Enum as SQLEnum, Index, Text
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.models.base import Base, TimestampMixin, IDMixin, repr_columns


class ProductCategory(str, enum.Enum):
    """Categoría del producto según SFE."""
    PLAGUICIDA = "plaguicida"
    FERTILIZANTE = "fertilizante"


class ToxicBand(str, enum.Enum):
    """Banda toxicológica."""
    ROJA = "roja"
    AMARILLA = "amarilla"
    AZUL = "azul"
    VERDE = "verde"
    NO_APLICA = "no_aplica"


class ProductStatus(str, enum.Enum):
    """Estado del registro en SFE."""
    ACTIVO = "activo"
    CANCELADO = "cancelado"
    EXPIRADO = "expirado"
    SUSPENDIDO = "suspendido"


class Product(Base, IDMixin, TimestampMixin):
    """Producto agroquímico registrado en el SFE."""

    __tablename__ = "products"

    # Identificación SFE
    numero_registro: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nombre_comercial: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    ingrediente_activo: Mapped[str] = mapped_column(Text, nullable=False)
    categoria: Mapped[ProductCategory] = mapped_column(
        SQLEnum(ProductCategory, name="product_category", create_constraint=True),
        nullable=False,
        index=True,
    )
    estado: Mapped[ProductStatus] = mapped_column(
        SQLEnum(ProductStatus, name="product_status", create_constraint=True),
        nullable=False,
        default=ProductStatus.ACTIVO,
        index=True,
    )
    banda_toxicologica: Mapped[ToxicBand] = mapped_column(
        SQLEnum(ToxicBand, name="toxic_band", create_constraint=True),
        nullable=True,
        index=True,
    )
    registrante: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Información adicional para recomendaciones
    dosis_recomendada: Mapped[str | None] = mapped_column(Text, nullable=True)
    intervalo_seguridad_dias: Mapped[int | None] = mapped_column(nullable=True)
    precio_referencia_por_litro: Mapped[float | None] = mapped_column(nullable=True)
    cultivo_objetivo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    problema_objetivo: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Embedding vectorial (768 dims) para la busqueda semantica del agente investigador
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(768),
        nullable=True,
    )

    # Indices para acelerar los filtros mas usados en las consultas
    __table_args__ = (
        Index("ix_products_categoria_estado", "categoria", "estado"),
        Index("ix_products_ingrediente_activo", "ingrediente_activo"),
        Index("ix_products_banda_toxicologica", "banda_toxicologica"),
        # Índice GIN para búsqueda vectorial eficiente (se crea en migración)
    )

    __repr__ = repr_columns("id", "numero_registro", "nombre_comercial", "categoria", "estado")