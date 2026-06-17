"""Servicio de autenticación refactorizado con Strategy Pattern.

``AuthServiceFactory`` selecciona la estrategia correcta según el entorno.
``AuthService`` delega toda la lógica de autenticación a la estrategia activa.

Las funciones del módulo (``register_user``, ``authenticate_user``, etc.) se
mantienen como wrappers de compatibilidad para no romper importaciones existentes
en ``auth.py`` y otros consumidores.

Cumplimiento SOLID:
- SRP: cada estrategia tiene una sola responsabilidad de autenticación.
- OCP: agregar OAuth2/SAML = crear nueva subclase, sin modificar este archivo.
- DIP: ``AuthService`` depende de ``AuthStrategy`` (abstracción), no de bcrypt/Supabase directamente.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.supabase import (
    SupabaseAuthError,
    SupabaseSession,
    get_user as supabase_get_user,
    update_user as supabase_update_user,
)
from app.models.user import User
from app.schemas.user import (
    PasswordChange,
    PasswordResetRequest,
    UserLogin,
    UserRegister,
    UserUpdate,
)
from app.services.auth_strategy import (
    AuthError,
    AuthStrategy,
    LocalAuthStrategy,
    SupabaseAuthStrategy,
    _get_user_by_auth_id_or_email,
    _is_unconfigured,
)

# Re-exportar AuthError para que los importadores existentes no se rompan
__all__ = [
    "AuthError",
    "AuthService",
    "AuthServiceFactory",
    "register_user",
    "authenticate_user",
    "build_token_response",
    "resolve_user_from_token",
    "update_user_profile",
    "change_user_password",
    "reset_user_password",
]


# ---------------------------------------------------------------------------
# Factory — selección de estrategia
# ---------------------------------------------------------------------------

class AuthServiceFactory:
    """Selecciona la estrategia de autenticación según la configuración del entorno.

    Centraliza la lógica de decisión en un único punto (OCP): agregar un nuevo
    proveedor solo requiere añadir una condición aquí y crear la estrategia.
    """

    @staticmethod
    def _local_auth_enabled() -> bool:
        """True cuando Supabase no está configurado y estamos en desarrollo."""
        settings = get_settings()
        return settings.is_development and (
            _is_unconfigured(settings.supabase_url)
            or _is_unconfigured(settings.supabase_anon_key)
        )

    @staticmethod
    def get_strategy() -> AuthStrategy:
        """Retorna la estrategia activa para el entorno actual."""
        if AuthServiceFactory._local_auth_enabled():
            return LocalAuthStrategy()
        return SupabaseAuthStrategy()


# ---------------------------------------------------------------------------
# Servicio principal — delega a la estrategia inyectada (DIP)
# ---------------------------------------------------------------------------

class AuthService:
    """Orquestador de autenticación que delega a la estrategia configurada.

    Acepta inyección de una estrategia externa para facilitar tests
    (inyectar un mock) sin modificar este archivo (DIP + OCP).
    """

    def __init__(self, strategy: AuthStrategy | None = None) -> None:
        self.strategy: AuthStrategy = strategy or AuthServiceFactory.get_strategy()

    async def register_user(self, db: AsyncSession, data: UserRegister) -> User:
        """Registra un nuevo usuario delegando a la estrategia activa."""
        return await self.strategy.register(db, data)

    async def authenticate_user(
        self, db: AsyncSession, data: UserLogin
    ) -> tuple[User, SupabaseSession | None]:
        """Autentica un usuario delegando a la estrategia activa."""
        return await self.strategy.authenticate(db, data)

    async def change_user_password(
        self, db: AsyncSession, user: User, data: PasswordChange
    ) -> None:
        """Cambia la contraseña delegando a la estrategia activa."""
        await self.strategy.change_password(db, user, data)

    async def reset_user_password(
        self, db: AsyncSession, data: PasswordResetRequest
    ) -> None:
        """Restablece la contraseña delegando a la estrategia activa."""
        await self.strategy.reset_password(db, data)

    def build_token_response(self, user: User, session: SupabaseSession) -> dict:
        """Construye respuesta de login con los tokens de sesión."""
        return build_token_response(user, session)

    async def resolve_user_from_token(
        self, db: AsyncSession, access_token: str
    ) -> User:
        """Valida JWT y carga el usuario de la tabla ``users``."""
        return await resolve_user_from_token(db, access_token)

    async def update_user_profile(
        self,
        db: AsyncSession,
        user: User,
        data: UserUpdate,
        *,
        access_token: str,
    ) -> User:
        """Actualiza perfil en DB y email en Supabase si cambió."""
        return await update_user_profile(db, user, data, access_token=access_token)


# ---------------------------------------------------------------------------
# Funciones de módulo — wrappers de compatibilidad hacia atrás
# ---------------------------------------------------------------------------
# Mantienen la API pública que consume auth.py y services/__init__.py
# sin necesidad de modificar esos archivos.

def build_token_response(user: User, session: SupabaseSession) -> dict:
    """Construye respuesta de login con JWT de Supabase."""
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_in": session.expires_in,
        "token_type": "bearer",
        "user": user,
    }


async def resolve_user_from_token(db: AsyncSession, access_token: str) -> User:
    """Valida JWT y carga el usuario de la tabla ``users``.

    Soporta dos tipos de token:
    1. **JWT local** (firmado con ``JWT_SECRET``): sub contiene el ``user.id``.
    2. **JWT de Supabase**: se valida contra la API de Supabase ``/auth/v1/user``.
    """
    from app.core.security import decode_access_token as _local_decode

    # --- Intentar decodificar como JWT local primero ---
    try:
        payload = _local_decode(access_token)
        sub = payload.get("sub", "")
        if sub.isdigit():
            result = await db.execute(select(User).where(User.id == int(sub)))
            user = result.scalar_one_or_none()
            if user is None:
                raise AuthError("Usuario no encontrado", status_code=401)
            if not user.is_active:
                raise AuthError("Cuenta desactivada", status_code=403)
            return user
    except AuthError:
        raise
    except Exception:
        pass

    # --- Intentar validar como JWT de Supabase ---
    try:
        auth_user = await supabase_get_user(access_token)
    except SupabaseAuthError as exc:
        raise AuthError(exc.message, status_code=exc.status_code) from exc

    user = await _get_user_by_auth_id_or_email(
        db,
        auth_user_id=auth_user.auth_user_id,
        email=auth_user.email,
    )
    if user is None:
        raise AuthError("Usuario no encontrado", status_code=401)

    if not user.is_active:
        raise AuthError("Cuenta desactivada", status_code=403)

    if user.auth_user_id is None:
        user.auth_user_id = auth_user.auth_user_id
        await db.commit()
        await db.refresh(user)

    return user


async def update_user_profile(
    db: AsyncSession,
    user: User,
    data: UserUpdate,
    *,
    access_token: str,
) -> User:
    """Actualiza perfil en DB y email en Supabase si cambió."""
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return user

    new_email = updates.get("email")
    if new_email is not None and new_email != user.email:
        result = await db.execute(select(User).where(User.email == new_email))
        if result.scalar_one_or_none() is not None:
            raise AuthError("El correo electrónico ya está en uso", status_code=409)

        if not AuthServiceFactory._local_auth_enabled():
            try:
                await supabase_update_user(access_token, email=new_email)
            except SupabaseAuthError as exc:
                raise AuthError(exc.message, status_code=exc.status_code) from exc

    for field, value in updates.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Instancia por defecto (para los wrappers de funciones de módulo)
# ---------------------------------------------------------------------------

def _default_service() -> AuthService:
    """Crea una instancia de ``AuthService`` con la estrategia del entorno."""
    return AuthService()


async def register_user(db: AsyncSession, data: UserRegister) -> User:
    """Wrapper de compatibilidad — delega a ``AuthService.register_user``."""
    return await _default_service().register_user(db, data)


async def authenticate_user(
    db: AsyncSession, data: UserLogin
) -> tuple[User, SupabaseSession | None]:
    """Wrapper de compatibilidad — delega a ``AuthService.authenticate_user``."""
    return await _default_service().authenticate_user(db, data)


async def change_user_password(
    db: AsyncSession,
    user: User,
    data: PasswordChange,
) -> None:
    """Wrapper de compatibilidad — delega a ``AuthService.change_user_password``."""
    await _default_service().change_user_password(db, user, data)


async def reset_user_password(db: AsyncSession, data: PasswordResetRequest) -> None:
    """Wrapper de compatibilidad — delega a ``AuthService.reset_user_password``."""
    await _default_service().reset_user_password(db, data)
