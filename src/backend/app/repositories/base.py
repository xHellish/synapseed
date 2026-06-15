from __future__ import annotations

from typing import Any, Generic, Sequence, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    # Repository base con operaciones CRUD genéricas.
    # Uso:
    #   class UserRepository(BaseRepository[User]):
    #       def __init__(self, db: AsyncSession) -> None:
    #           super().__init__(db, User)

    def __init__(self, db: AsyncSession, model: Type[ModelT]) -> None:
        self._db = db
        self._model = model

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    async def get_by_id(self, id: int) -> ModelT | None:
        # Retorna el registro por PK o None si no existe.
        result = await self._db.execute(
            select(self._model).where(self._model.id == id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelT]:
        # Retorna todos los registros con paginación simple.
        result = await self._db.execute(
            select(self._model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def count(self) -> int:
        # Cuenta el total de registros en la tabla.
        result = await self._db.execute(
            select(func.count()).select_from(self._model)
        )
        return result.scalar_one()

    async def exists(self, id: int) -> bool:
        # Verifica si existe un registro con ese id.
        result = await self._db.execute(
            select(func.count())
            .select_from(self._model)
            .where(self._model.id == id)  # type: ignore[attr-defined]
        )
        return result.scalar_one() > 0

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------

    async def create(self, data: dict[str, Any]) -> ModelT:
        # Crea y persiste un nuevo registro.
        instance = self._model(**data)
        self._db.add(instance)
        await self._db.commit()
        await self._db.refresh(instance)
        return instance

    async def update(self, instance: ModelT, data: dict[str, Any]) -> ModelT:
        # Actualiza los campos indicados de un registro existente.
        for field, value in data.items():
            setattr(instance, field, value)
        self._db.add(instance)
        await self._db.commit()
        await self._db.refresh(instance)
        return instance

    async def delete(self, instance: ModelT) -> None:
        # Elimina físicamente el registro de la base de datos.
        await self._db.delete(instance)
        await self._db.commit()

    # ------------------------------------------------------------------
    # Helpers de transacción
    # ------------------------------------------------------------------

    async def flush(self) -> None:
        # Envía los cambios al servidor sin hacer commit (útil en transacciones).
        await self._db.flush()

    async def refresh(self, instance: ModelT) -> None:
        # Recarga el estado del objeto desde la base de datos.
        await self._db.refresh(instance)
