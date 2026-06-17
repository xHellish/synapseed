"""Utilidades de seguridad (helpers locales).

La autenticación principal usa Supabase Auth; ver ``app.core.supabase``.

Helpers heredados para compatibilidad (zones, catalogs, etc.):
- ``get_password_hash`` / ``verify_password`` (bcrypt local)
- ``create_access_token`` / ``decode_access_token`` (JWT local)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

security_scheme = HTTPBearer(auto_error=False)  # lee el header Authorization: Bearer <token>
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # algoritmo de hashing de contrasenas


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Compara la contrasena en texto plano contra su hash bcrypt
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    # Genera el hash bcrypt para guardar (nunca se guarda la contrasena en claro)
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    # Firma un JWT local con el user.id en `sub` y una expiracion
    settings = get_settings()
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.jwt_expire_hours)

    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    # Verifica la firma y la expiracion del JWT local; falla con 401 si no es valido
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        ) from exc


# Dependencia de FastAPI: protege endpoints. Resuelve el usuario a partir del token.
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> dict[str, Any]:
    if credentials is None or not credentials.scheme.lower() == "bearer":
        raise HTTPException(status_code=401, detail="Autenticación requerida")

    from app.db.session import get_db_session
    from app.services.auth_service import resolve_user_from_token, AuthError

    async with get_db_session() as db:
        try:
            user = await resolve_user_from_token(db, credentials.credentials)
            return {
                "id": str(user.id),
                "identification": user.identification,
                "name": user.full_name,
            }
        except AuthError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
            ) from exc