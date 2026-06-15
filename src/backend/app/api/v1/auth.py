from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.models.audit_log import AuditAction
from app.repositories import AuditRepository, UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserProfile

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"description": "Credenciales inválidas"}},
)


class RegisterResponse(BaseModel):
    id: int
    identification: str
    full_name: str
    email: EmailStr
    phone: str | None = None


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registro de nuevo usuario",
    description=(
        "Crea una cuenta de usuario con cédula, correo y contraseña.\n\n"
        "Retorna los datos del usuario creado (sin contraseña)."
    ),
    responses={
        201: {"description": "Usuario creado exitosamente"},
        409: {"description": "La cédula o el correo ya están registrados"},
    },
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    users = UserRepository(db)

    # Validar unicidad de cédula
    if await users.exists_identification(payload.identification):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El número de cédula ya está registrado",
        )

    # Validar unicidad de correo
    if await users.exists_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo electrónico ya está registrado",
        )

    # Crear usuario
    user = await users.create_user(
        {
            "identification": payload.identification,
            "password_hash": get_password_hash(payload.password),
            "full_name": payload.full_name,
            "email": payload.email,
            "phone": payload.phone,
            "is_active": True,
            "is_verified": False,
        }
    )

    return RegisterResponse(
        id=user.id,
        identification=user.identification,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login con cédula y contraseña",
    description=(
        "Autentica al usuario con su número de cédula y contraseña.\n\n"
        "Retorna un JWT válido por 24 horas."
    ),
    responses={
        200: {"description": "Login exitoso — retorna access_token JWT"},
        401: {"description": "Cédula o contraseña incorrecta"},
    },
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    users = UserRepository(db)
    audit = AuditRepository(db)

    user = await users.get_by_identification(payload.identification)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cédula o contraseña incorrecta",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada",
        )

    token = create_access_token(subject=str(user.id))

    await audit.log(
        action=AuditAction.LOGIN,
        user_id=user.id,
        entity_type="user",
        entity_id=user.id,
    )

    return TokenResponse(
        access_token=token,
        user={
            "id": str(user.id),
            "identification": user.identification,
            "full_name": user.full_name,
            "email": user.email,
        },
    )


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Perfil del usuario autenticado",
)
async def me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    users = UserRepository(db)
    user = await users.get_by_id(int(current_user["id"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return UserProfile.model_validate(user)