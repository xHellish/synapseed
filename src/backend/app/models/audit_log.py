"""Modelo de auditoría."""

from __future__ import annotations

import enum

from sqlalchemy import String, ForeignKey, Text, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, IDMixin, repr_columns
from app.models.user import User


class AuditAction(str, enum.Enum):
    """Tipo de acción auditada."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    RECOMMENDATION_REQUEST = "recommendation_request"
    RECOMMENDATION_VIEW = "recommendation_view"


class AuditLog(Base, IDMixin, TimestampMixin):
    """Log de auditoría para trazabilidad."""

    __tablename__ = "audit_logs"

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction, name="audit_action", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    entity_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User | None] = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_user_action", "user_id", "action"),
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    __repr__ = repr_columns("id", "user_id", "action", "entity_type", "entity_id")


# Back-populate
User.audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")