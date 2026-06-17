from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    # Operaciones de base de datos para el modelo User.

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, User)

    # Busquedas especificas

    async def get_by_email(self, email: str) -> User | None:
        # Retorna el usuario por email (case-insensitive).
        result = await self._db.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_identification(self, identification: str) -> User | None:
        # Retorna el usuario por número de identificación.
        result = await self._db.execute(
            select(User).where(User.identification == identification)
        )
        return result.scalar_one_or_none()

    async def get_all_active(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        # Retorna solo los usuarios activos con paginación.
        result = await self._db.execute(
            select(User)
            .where(User.is_active == True)  # noqa: E712
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_active(self) -> int:
        # Cuenta el total de usuarios activos.
        result = await self._db.execute(
            select(func.count()).select_from(User).where(User.is_active == True)  # noqa: E712
        )
        return result.scalar_one()

    # Verificaciones

    async def exists_email(self, email: str) -> bool:
        # Verifica si ya existe un usuario con ese email.
        result = await self._db.execute(
            select(func.count())
            .select_from(User)
            .where(func.lower(User.email) == email.lower())
        )
        return result.scalar_one() > 0

    async def exists_identification(self, identification: str) -> bool:
        # Verifica si ya existe un usuario con esa cédula.
        result = await self._db.execute(
            select(func.count())
            .select_from(User)
            .where(User.identification == identification)
        )
        return result.scalar_one() > 0

    # Escritura especializada

    async def create_user(self, data: dict[str, Any]) -> User:
        # Crea un usuario nuevo. El campo password_hash ya debe venir hasheado.
        return await self.create(data)

    async def update_user(self, user: User, data: dict[str, Any]) -> User:
        # Actualiza campos del usuario. Excluye automáticamente password_hash.
        data.pop("password_hash", None)
        return await self.update(user, data)

    async def update_password(self, user: User, new_password_hash: str) -> User:
        # Actualiza solo el hash de contraseña.
        return await self.update(user, {"password_hash": new_password_hash})

    async def verify_user(self, user: User) -> User:
        # Marca el usuario como verificado.
        return await self.update(user, {"is_verified": True})

    async def soft_delete(self, user: User) -> User:
        # Desactiva el usuario (borrado lógico) sin eliminarlo de la DB.
        return await self.update(user, {"is_active": False})
