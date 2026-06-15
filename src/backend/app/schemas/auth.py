from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    identification: str = Field(..., min_length=5, max_length=20)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, str]


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    identification: str
    full_name: str
    email: EmailStr
    phone: str | None = None
    is_active: bool = True
