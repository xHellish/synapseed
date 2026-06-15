"""Endpoints de perfil del usuario autenticado."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from app.dependencies import BearerToken, CurrentUser, DbSession
from app.schemas.user import PasswordChange, UserResponse, UserUpdate
from app.services.auth_service import AuthError, change_user_password, update_user_profile

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtener perfil del usuario autenticado",
)
async def get_me(current_user: CurrentUser) -> UserResponse:
    """Retorna los datos del usuario autenticado."""
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Actualizar perfil",
)
async def update_me(
    data: UserUpdate,
    current_user: CurrentUser,
    db: DbSession,
    access_token: BearerToken,
) -> UserResponse:
    """Actualiza nombre, email y/o teléfono."""
    try:
        user = await update_user_profile(
            db,
            current_user,
            data,
            access_token=access_token,
        )
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return UserResponse.model_validate(user)


@router.put(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Cambiar contraseña",
)
async def change_password(
    data: PasswordChange,
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    """Cambia la contraseña validando la contraseña actual."""
    try:
        await change_user_password(db, current_user, data)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
