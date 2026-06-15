from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", summary="Datos del usuario autenticado")
async def get_me(current_user: dict[str, object] = Depends(get_current_user)) -> dict[str, object]:
    return {
        "id": current_user["id"],
        "identification": current_user.get("identification", "1234567890"),
        "full_name": current_user.get("full_name", "Usuario Demo"),
        "email": current_user.get("email", "demo@synapseed.cr"),
        "phone": current_user.get("phone", "+506-8888-8888"),
        "is_active": True,
    }


@router.put("/me", summary="Actualizar perfil del usuario")
async def update_me(current_user: dict[str, object] = Depends(get_current_user)) -> dict[str, object]:
    return {"message": "Perfil actualizado", "user": current_user}


@router.put("/me/password", summary="Cambiar contraseña")
async def update_password(current_user: dict[str, object] = Depends(get_current_user)) -> dict[str, object]:
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return {"message": "Contraseña actualizada", "user_id": current_user["id"]}
