"""Cliente HTTP para Supabase Auth (login, registro, validación de JWT)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx

from app.config import get_settings


class SupabaseAuthError(Exception):
    """Error devuelto por la API de Supabase Auth."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class SupabaseSession:
    """Tokens y datos mínimos tras login o registro."""

    access_token: str
    refresh_token: str
    expires_in: int
    auth_user_id: UUID
    email: str


@dataclass(frozen=True, slots=True)
class SupabaseSignupResult:
    """Resultado de un registro — puede tener sesión o estar pendiente de confirmación de email."""

    auth_user_id: UUID
    email: str
    session: SupabaseSession | None
    confirmation_required: bool


@dataclass(frozen=True, slots=True)
class SupabaseAuthUser:
    """Usuario autenticado según Supabase."""

    auth_user_id: UUID
    email: str


def _auth_base_url() -> str:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_anon_key:
        msg = "SUPABASE_URL y SUPABASE_ANON_KEY deben estar configurados"
        raise SupabaseAuthError(msg, status_code=503)
    return settings.supabase_url.rstrip("/") + "/auth/v1"


def _default_headers() -> dict[str, str]:
    settings = get_settings()
    return {
        "apikey": settings.supabase_anon_key,
        "Content-Type": "application/json",
    }


def _parse_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or "Error de autenticación con Supabase"

    if isinstance(payload, dict):
        return (
            payload.get("msg")
            or payload.get("error_description")
            or payload.get("message")
            or payload.get("error")
            or "Error de autenticación con Supabase"
        )
    return "Error de autenticación con Supabase"


def _session_from_payload(payload: dict[str, Any]) -> SupabaseSession:
    """Parsea una respuesta con sesión activa (login). Falla si falta el token."""
    user = payload.get("user") or {}
    user_id = user.get("id")
    email = user.get("email")
    access_token = payload.get("access_token")
    refresh_token = payload.get("refresh_token")
    expires_in = payload.get("expires_in", 3600)

    if not user_id or not email or not access_token:
        raise SupabaseAuthError("Respuesta incompleta de Supabase Auth", status_code=502)

    return SupabaseSession(
        access_token=access_token,
        refresh_token=refresh_token or "",
        expires_in=int(expires_in),
        auth_user_id=UUID(str(user_id)),
        email=str(email),
    )


def _signup_result_from_payload(payload: dict[str, Any]) -> SupabaseSignupResult:
    """Parsea la respuesta de /signup, que puede o no incluir sesión."""
    user = payload.get("user") or {}
    user_id = user.get("id")
    email = user.get("email")

    if not user_id or not email:
        raise SupabaseAuthError("Respuesta incompleta de Supabase Auth", status_code=502)

    access_token = payload.get("access_token")
    confirmation_required = not access_token

    session: SupabaseSession | None = None
    if not confirmation_required:
        session = SupabaseSession(
            access_token=access_token,
            refresh_token=payload.get("refresh_token") or "",
            expires_in=int(payload.get("expires_in", 3600)),
            auth_user_id=UUID(str(user_id)),
            email=str(email),
        )

    return SupabaseSignupResult(
        auth_user_id=UUID(str(user_id)),
        email=str(email),
        session=session,
        confirmation_required=confirmation_required,
    )


async def sign_up(
    email: str,
    password: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> SupabaseSignupResult:
    """Crea usuario en Supabase Auth (email + contraseña).

    Si Supabase tiene confirmación de email habilitada, retorna un resultado con
    ``confirmation_required=True`` y ``session=None``.
    """
    body: dict[str, Any] = {"email": email, "password": password}
    if metadata:
        body["data"] = metadata

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{_auth_base_url()}/signup",
            headers=_default_headers(),
            json=body,
        )

    if response.status_code >= 400:
        raise SupabaseAuthError(_parse_error(response), status_code=response.status_code)

    return _signup_result_from_payload(response.json())


async def sign_in_with_password(email: str, password: str) -> SupabaseSession:
    """Autentica en Supabase con email + contraseña."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{_auth_base_url()}/token?grant_type=password",
            headers=_default_headers(),
            json={"email": email, "password": password},
        )

    if response.status_code >= 400:
        status = 401 if response.status_code in {400, 401, 422} else response.status_code
        raise SupabaseAuthError(_parse_error(response), status_code=status)

    return _session_from_payload(response.json())


async def get_user(access_token: str) -> SupabaseAuthUser:
    """Valida el JWT de Supabase y retorna el usuario autenticado."""
    headers = {
        **_default_headers(),
        "Authorization": f"Bearer {access_token}",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(f"{_auth_base_url()}/user", headers=headers)

    if response.status_code >= 400:
        print(f"[DEBUG] Supabase /user validation failed: {response.status_code} - {response.text}")
        raise SupabaseAuthError(
            "Token inválido o expirado",
            status_code=401,
        )

    payload = response.json()
    user_id = payload.get("id")
    email = payload.get("email")
    if not user_id or not email:
        raise SupabaseAuthError("Token inválido o expirado", status_code=401)

    return SupabaseAuthUser(auth_user_id=UUID(str(user_id)), email=str(email))


async def update_user(
    access_token: str,
    *,
    email: str | None = None,
    password: str | None = None,
) -> None:
    """Actualiza email y/o contraseña en Supabase Auth."""
    body: dict[str, str] = {}
    if email is not None:
        body["email"] = email
    if password is not None:
        body["password"] = password
    if not body:
        return

    headers = {
        **_default_headers(),
        "Authorization": f"Bearer {access_token}",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.put(
            f"{_auth_base_url()}/user",
            headers=headers,
            json=body,
        )

    if response.status_code >= 400:
        raise SupabaseAuthError(_parse_error(response), status_code=response.status_code)
