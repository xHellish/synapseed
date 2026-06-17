"""Sesión asíncrona de base de datos."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings


def create_engine() -> AsyncEngine:
    """Crea el motor asíncrono de SQLAlchemy.

    ``statement_cache_size=0`` es necesario cuando se usa el pooler de
    Supabase (PgBouncer en modo transacción, puerto 6543). Sin esto,
    asyncpg falla con ``DuplicatePreparedStatementError``.
    """
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
        echo=settings.debug,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        },
    )


# Motor global (se inicializa al importar)
async_engine: AsyncEngine = create_engine()

# Factory de sesiones
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia FastAPI para obtener sesión de DB."""
    # Abre una sesion por request; hace rollback si algo falla y siempre la cierra
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager para usar sesión fuera de FastAPI (workers, scripts).

    Crea un engine y session_factory locales para evitar errores de
    'Future attached to a different loop' al usarse en procesos y tareas
    de Celery que levantan loops de asyncio locales.
    """
    local_engine = create_engine()
    local_session_factory = async_sessionmaker(
        local_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with local_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            await local_engine.dispose()