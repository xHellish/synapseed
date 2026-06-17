"""Endpoints de autenticación: registro y login."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from app.dependencies import DbSession
from app.schemas.user import PasswordResetRequest, TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.auth_service import AuthError, authenticate_user, build_token_response, register_user, reset_user_password

router = APIRouter(prefix="/auth", tags=["auth"])


# Endpoints publicos (no requieren token). Cada uno delega la logica al auth_service
# y traduce los AuthError del servicio a respuestas HTTP.
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


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Restablecer contraseña en modo local/demo",
)
async def reset_password(data: PasswordResetRequest, db: DbSession) -> Response:
    """Restablece contraseña sin sesión activa solo para desarrollo local."""
    try:
        await reset_user_password(db, data)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
