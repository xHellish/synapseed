from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.zone import Zone
from app.repositories.base import BaseRepository


class ZoneRepository(BaseRepository[Zone]):
    # Operaciones de base de datos para el modelo Zone.

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Zone)

    # ------------------------------------------------------------------
    # Búsquedas específicas
    # ------------------------------------------------------------------

    async def get_by_user_id(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[Zone]:
        # Retorna todas las zonas pertenecientes a un usuario.
        result = await self._db.execute(
            select(Zone)
            .where(Zone.user_id == user_id)
            .order_by(Zone.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_id_and_user(self, zone_id: int, user_id: int) -> Zone | None:
        # Retorna una zona solo si pertenece al usuario indicado.
        # Usado para validar ownership antes de operar sobre la zona.
        result = await self._db.execute(
            select(Zone).where(Zone.id == zone_id, Zone.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def count_by_user(self, user_id: int) -> int:
        # Cuenta las zonas que tiene un usuario.
        result = await self._db.execute(
            select(func.count()).select_from(Zone).where(Zone.user_id == user_id)
        )
        return result.scalar_one()

    async def exists_name_for_user(self, user_id: int, name: str) -> bool:
        # Verifica si el usuario ya tiene una zona con ese nombre.
        result = await self._db.execute(
            select(func.count())
            .select_from(Zone)
            .where(Zone.user_id == user_id, func.lower(Zone.name) == name.lower())
        )
        return result.scalar_one() > 0

    # ------------------------------------------------------------------
    # Escritura especializada
    # ------------------------------------------------------------------

    async def create_zone(self, user_id: int, data: dict[str, Any]) -> Zone:
        # Crea una zona asociada al usuario dado.
        return await self.create({**data, "user_id": user_id})

    async def update_zone(self, zone: Zone, data: dict[str, Any]) -> Zone:
        # Actualiza los campos de una zona existente.
        # Evita que se cambie el owner por error.
        data.pop("user_id", None)
        return await self.update(zone, data)

    async def delete_zone(self, zone: Zone) -> None:
        # Elimina físicamente una zona y sus recomendaciones en cascada.
        await self.delete(zone)
