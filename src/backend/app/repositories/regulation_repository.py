"""Acceso a regulaciones para el Agente Validador Legal."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.regulation import Regulation


@dataclass(frozen=True)
class RegulationRecord:
    """Vista de regulación desacoplada del ORM."""

    id: int
    numero: str
    titulo: str
    tipo: str
    resumen: str | None
    sustancias_afectadas: str | None
    cultivos_afectados: str | None


class RegulationRepository(ABC):
    """Contrato mockeable para lectura de normativa."""

    @abstractmethod
    async def list_active(self) -> list[RegulationRecord]:
        """Regulaciones disponibles para validación."""


def _orm_to_record(regulation: Regulation) -> RegulationRecord:
    return RegulationRecord(
        id=regulation.id,
        numero=regulation.numero,
        titulo=regulation.titulo,
        tipo=regulation.tipo.value,
        resumen=regulation.resumen,
        sustancias_afectadas=regulation.sustancias_afectadas,
        cultivos_afectados=regulation.cultivos_afectados,
    )


class SqlAlchemyRegulationRepository(RegulationRepository):
    """Lee regulaciones desde PostgreSQL/Supabase."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[RegulationRecord]:
        result = await self._session.execute(select(Regulation))
        return [_orm_to_record(r) for r in result.scalars().all()]


class FakeRegulationRepository(RegulationRepository):
    """Regulaciones en memoria para tests."""

    def __init__(self, regulations: list[RegulationRecord] | None = None) -> None:
        self._regulations = regulations or []

    async def list_active(self) -> list[RegulationRecord]:
        return list(self._regulations)
