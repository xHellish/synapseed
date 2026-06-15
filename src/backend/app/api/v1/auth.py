from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.security import create_access_token, get_password_hash, verify_password
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

DEMO_USERS = {
    "1234567890": {
        "id": "demo-user-1",
        "identification": "1234567890",
        "full_name": "Usuario Demo",
        "email": "demo@synapseed.cr",
        "phone": "+506-8888-8888",
        "password_hash": get_password_hash("secret123"),
        "is_active": True,
    }
}


@router.post("/login", response_model=TokenResponse, summary="Login con cédula y contraseña")
async def login(payload: LoginRequest) -> TokenResponse:
    try:
        user = DEMO_USERS.get(payload.identification)
        if not user or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

        token = create_access_token(subject=user["id"])
        return TokenResponse(
            access_token=token,
            user={
                "id": user["id"],
                "identification": user["identification"],
                "full_name": user["full_name"],
                "email": user["email"],
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
