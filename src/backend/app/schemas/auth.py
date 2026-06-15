from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    identification: str = Field(..., min_length=5, max_length=20, description="Número de cédula")
    password: str = Field(..., min_length=6, max_length=128, description="Contraseña (mín. 6 caracteres)")
    full_name: str = Field(..., min_length=3, max_length=255, description="Nombre completo")
    email: EmailStr = Field(..., description="Correo electrónico")
    phone: str | None = Field(None, max_length=30, description="Teléfono (opcional)")


class LoginRequest(BaseModel):
    identification: str = Field(..., min_length=5, max_length=20)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, str]


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    identification: str
    full_name: str
    email: EmailStr
    phone: str | None = None
    is_active: bool = True
    is_verified: bool = False
