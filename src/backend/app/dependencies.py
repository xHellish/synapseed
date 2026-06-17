"""Dependencias inyectables de FastAPI."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthError, resolve_user_from_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Obtiene el usuario autenticado validando el JWT de Supabase."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticación no provistas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return await resolve_user_from_token(db, credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_bearer_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> str:
    """Extrae el token Bearer para operaciones que lo reenvían a Supabase."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de autenticación no provistas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


# Atajos para inyectar en los endpoints: en vez de repetir Depends(...) en cada firma,
# se anota el parametro con estos tipos (ej. `current_user: CurrentUser`).
CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
BearerToken = Annotated[str, Depends(get_bearer_token)]
