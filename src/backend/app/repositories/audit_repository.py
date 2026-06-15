from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditAction, AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    # Operaciones de base de datos para AuditLog.
    # Solo crea y lee registros — nunca edita ni borra (inmutabilidad por diseño).

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, AuditLog)

    # ------------------------------------------------------------------
    # Escritura especializada
    # ------------------------------------------------------------------

    async def log(
        self,
        action: AuditAction,
        user_id: int | None = None,
        entity_type: str | None = None,
        entity_id: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        detail: str | None = None,
    ) -> AuditLog:
        # Registra una entrada de auditoría.
        # Ejemplo de uso dentro de un endpoint:
        #   audit = AuditRepository(db)
        #   await audit.log(action=AuditAction.LOGIN, user_id=user.id)
        return await self.create(
            {
                "action": action,
                "user_id": user_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "detail": detail,
            }
        )

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    async def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        action: AuditAction | None = None,
    ) -> Sequence[AuditLog]:
        # Retorna los registros de auditoría de un usuario, ordenados por fecha desc.
        query = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if action is not None:
            query = query.where(AuditLog.action == action)

        result = await self._db.execute(query)
        return result.scalars().all()

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[AuditLog]:
        # Retorna los logs de auditoría asociados a una entidad específica.
        result = await self._db.execute(
            select(AuditLog)
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_recent(self, limit: int = 100) -> Sequence[AuditLog]:
        # Retorna los registros de auditoría más recientes (para admin/dashboard).
        result = await self._db.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        )
        return result.scalars().all()
