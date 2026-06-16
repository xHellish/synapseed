"""Endpoints de autenticación: registro y login."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.dependencies import DbSession
from app.schemas.user import TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.auth_service import AuthError, authenticate_user, build_token_response, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
)
async def register(data: UserRegister, db: DbSession) -> UserResponse:
    """Registra un agricultor con email, nombre, cédula, teléfono y contraseña."""
    try:
        user = await register_user(db, data)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión con cédula",
)
async def login(data: UserLogin, db: DbSession) -> TokenResponse:
    """Autentica con cédula + contraseña y retorna JWT de Supabase."""
    try:
        user, session = await authenticate_user(db, data)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return TokenResponse.model_validate(build_token_response(user, session))