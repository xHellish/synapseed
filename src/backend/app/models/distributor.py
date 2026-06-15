"""Modelo de distribuidor."""

from __future__ import annotations

from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, IDMixin, repr_columns


class Distributor(Base, IDMixin, TimestampMixin):
    """Distribuidor/proveedor de agroquímicos."""

    __tablename__ = "distributors"

    nombre: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    correo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ubicacion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provincia: Mapped[str | None] = mapped_column(String(50), nullable=True)
    canton: Mapped[str | None] = mapped_column(String(50), nullable=True)
    distrito: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Productos que distribuye (many-to-many via ProductDistributor)
    # products: Mapped[list["Product"]] = relationship(secondary="product_distributors", back_populates="distributors")

    __table_args__ = (
        Index("ix_distributors_nombre", "nombre"),
        Index("ix_distributors_ubicacion", "provincia", "canton"),
    )

    __repr__ = repr_columns("id", "nombre", "correo", "telefono")


# Tabla de asociación Product <-> Distributor (many-to-many)
from app.models.product import Product  # noqa: E402

class ProductDistributor(Base):
    """Asociación producto-distribuidor."""

    __tablename__ = "product_distributors"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    distributor_id: Mapped[int] = mapped_column(
        ForeignKey("distributors.id", ondelete="CASCADE"), primary_key=True
    )

    product: Mapped[Product] = relationship("Product", back_populates="distributors")
    distributor: Mapped[Distributor] = relationship("Distributor", back_populates="products")

    __repr__ = repr_columns("product_id", "distributor_id")


# Agregar los back-populates a Product y Distributor
Product.distributors = relationship(
    "ProductDistributor", back_populates="product", cascade="all, delete-orphan"
)
Distributor.products = relationship(
    "ProductDistributor", back_populates="distributor", cascade="all, delete-orphan"
)