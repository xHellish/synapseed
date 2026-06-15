"""Modelo de usuario."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import String, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, IDMixin, repr_columns

if TYPE_CHECKING:
    from app.models.zone import Zone
    from app.models.recommendation import Recommendation
    from app.models.audit_log import AuditLog


class User(Base, IDMixin, TimestampMixin):
    """Usuario registrador (agricultor costarricense).

    Credenciales en Supabase Auth (``auth.users``). Este registro guarda el
    perfil de negocio; el login del API usa ``identification`` (cédula) para
    resolver el email y autenticar contra Supabase.
    """

    __tablename__ = "users"

    auth_user_id: Mapped[UUID | None] = mapped_column(Uuid, unique=True, nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    identification: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relaciones
    zones: Mapped[list["Zone"]] = relationship("Zone", back_populates="user", cascade="all, delete-orphan")
    recommendations: Mapped[list["Recommendation"]] = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
    )

    __repr__ = repr_columns("id", "email", "full_name", "identification", "is_active")
