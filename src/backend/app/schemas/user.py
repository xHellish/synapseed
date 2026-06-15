"""Esquemas de usuario para auth y perfil."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize_identification(value: str) -> str:
    """Elimina guiones y espacios de la cédula."""
    return re.sub(r"[\s\-]", "", value.strip())


def _validate_identification(value: str) -> str:
    """Valida formato básico de cédula costarricense (9–12 dígitos)."""
    normalized = _normalize_identification(value)
    if not re.fullmatch(r"\d{9,12}", normalized):
        msg = "La cédula debe contener entre 9 y 12 dígitos"
        raise ValueError(msg)
    return normalized


def _validate_email(value: str) -> str:
    """Valida formato básico de email (simple regex, no DNS checks)."""
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, value.strip()):
        msg = "Email address format is invalid"
        raise ValueError(msg)
    return value.strip().lower()


class UserRegister(BaseModel):
    """Datos para registro de un nuevo agricultor."""

    email: str = Field(min_length=5, max_length=255)
    full_name: str = Field(min_length=2, max_length=255)
    identification: str = Field(min_length=9, max_length=20)
    phone: str = Field(min_length=8, max_length=30)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)

    @field_validator("identification")
    @classmethod
    def validate_identification(cls, value: str) -> str:
        return _validate_identification(value)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        return value.strip()


class UserLogin(BaseModel):
    """Login con cédula + contraseña (no email)."""

    identification: str = Field(min_length=9, max_length=20)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("identification")
    @classmethod
    def validate_identification(cls, value: str) -> str:
        return _validate_identification(value)


class UserUpdate(BaseModel):
    """Actualización parcial del perfil."""

    email: str | None = Field(default=None, min_length=5, max_length=255)
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    phone: str | None = Field(default=None, min_length=8, max_length=30)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_email(value)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()


class PasswordChange(BaseModel):
    """Cambio de contraseña con verificación de la actual."""

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Usuario serializado para respuestas de la API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    identification: str
    phone: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    """Respuesta de login con JWT de Supabase."""

    access_token: str
    refresh_token: str | None = None
    expires_in: int | None = None
    token_type: str = "bearer"
    user: UserResponse
