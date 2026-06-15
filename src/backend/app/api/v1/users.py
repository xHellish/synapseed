from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.audit_log import AuditAction
from app.repositories import AuditRepository, UserRepository
from app.schemas.auth import UserProfile

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Datos del usuario autenticado",
)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    users = UserRepository(db)
    user = await users.get_by_id(int(current_user["id"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return UserProfile.model_validate(user)


@router.put(
    "/me",
    response_model=UserProfile,
    summary="Actualizar perfil del usuario",
)
async def update_me(
    payload: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    users = UserRepository(db)
    audit = AuditRepository(db)

    user = await users.get_by_id(int(current_user["id"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    # Verificar email único si se intenta cambiar
    new_email = payload.get("email")
    if new_email and new_email != user.email:
        if await users.exists_email(new_email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email ya está registrado",
            )

    updated = await users.update_user(user, payload)

    await audit.log(
        action=AuditAction.UPDATE,
        user_id=user.id,
        entity_type="user",
        entity_id=user.id,
    )

    return UserProfile.model_validate(updated)


@router.put(
    "/me/password",
    summary="Cambiar contraseña",
)
async def update_password(
    payload: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.core.security import get_password_hash, verify_password

    users = UserRepository(db)
    audit = AuditRepository(db)

    user = await users.get_by_id(int(current_user["id"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    # Verificar contraseña actual antes de permitir el cambio
    current_password = payload.get("current_password", "")
    new_password = payload.get("new_password", "")

    if not verify_password(current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña actual incorrecta",
        )

    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La nueva contraseña debe tener al menos 8 caracteres",
        )

    new_hash = get_password_hash(new_password)
    await users.update_password(user, new_hash)

    await audit.log(
        action=AuditAction.UPDATE,
        user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        detail="password_changed",
    )

    return {"message": "Contraseña actualizada correctamente"}
