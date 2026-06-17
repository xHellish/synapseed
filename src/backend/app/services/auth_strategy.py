"""Strategy Pattern para autenticación — SRP + OCP + DIP.

Define la interfaz abstracta ``AuthStrategy`` y sus implementaciones concretas
``LocalAuthStrategy`` (bcrypt, desarrollo/self-hosted) y
``SupabaseAuthStrategy`` (producción).

Agregar un proveedor nuevo (OAuth2, SAML, etc.) solo requiere crear una nueva
subclase de ``AuthStrategy`` sin tocar el código existente (OCP).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.supabase import (
    SupabaseAuthError,
    SupabaseSession,
    SupabaseSignupResult,
    sign_in_with_password,
    sign_up,
    update_user as supabase_update_user,
)
from app.models.user import User
from app.schemas.user import PasswordChange, PasswordResetRequest, UserLogin, UserRegister


# ---------------------------------------------------------------------------
# Excepción de dominio
# ---------------------------------------------------------------------------

class AuthError(Exception):
    """Error de autenticación con código HTTP asociado."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# ---------------------------------------------------------------------------
# Interfaz abstracta
# ---------------------------------------------------------------------------

class AuthStrategy(ABC):
    """Contrato que deben cumplir todas las estrategias de autenticación.

    Cumple DIP: ``AuthService`` depende de esta abstracción, no de implementaciones
    concretas de Supabase o bcrypt.
    """

    @abstractmethod
    async def register(self, db: AsyncSession, data: UserRegister) -> User:
        """Registra un nuevo usuario y retorna la entidad creada."""

    @abstractmethod
    async def authenticate(
        self, db: AsyncSession, data: UserLogin
    ) -> tuple[User, SupabaseSession | None]:
        """Autentica un usuario y retorna (usuario, sesión).

        La sesión puede ser ``None`` si el backend no la genera (p. ej.
        si Supabase requiere confirmación de email).
        """

    @abstractmethod
    async def change_password(
        self, db: AsyncSession, user: User, data: PasswordChange
    ) -> None:
        """Cambia la contraseña verificando la actual."""

    @abstractmethod
    async def reset_password(
        self, db: AsyncSession, data: PasswordResetRequest
    ) -> None:
        """Restablece la contraseña sin conocer la actual (flujo de recuperación)."""

    @abstractmethod
    def build_session(self, user: User) -> SupabaseSession:
        """Construye una sesión local para el usuario dado."""


# ---------------------------------------------------------------------------
# Helpers compartidos (privados al módulo)
# ---------------------------------------------------------------------------

def _is_unconfigured(value: str) -> bool:
    """Detecta valores vacíos o placeholders del .env de ejemplo."""
    normalized = value.strip().lower()
    return not normalized or any(token in normalized for token in ("<", ">", "[", "]", "your-", "tu_"))


async def _get_user_by_identification(db: AsyncSession, identification: str) -> User | None:
    result = await db.execute(select(User).where(User.identification == identification))
    return result.scalar_one_or_none()


async def _get_user_by_auth_id_or_email(
    db: AsyncSession,
    *,
    auth_user_id: UUID,
    email: str,
) -> User | None:
    result = await db.execute(
        select(User).where(
            or_(User.auth_user_id == auth_user_id, User.email == email),
        ),
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Implementación local (bcrypt — desarrollo / self-hosted)
# ---------------------------------------------------------------------------

class LocalAuthStrategy(AuthStrategy):
    """Autenticación local con bcrypt.

    Usada en desarrollo cuando Supabase no está configurado, o en despliegues
    self-hosted que no dependen de Supabase Auth.
    """

    def build_session(self, user: User) -> SupabaseSession:
        from app.config import get_settings
        settings = get_settings()
        return SupabaseSession(
            access_token=create_access_token(subject=str(user.id)),
            refresh_token="",
            expires_in=settings.jwt_expire_hours * 3600,
            auth_user_id=user.auth_user_id if user.auth_user_id is not None else UUID(int=user.id),
            email=user.email,
        )

    def _verify_password(self, user: User, password: str) -> SupabaseSession | None:
        if user.password_hash and verify_password(password, user.password_hash):
            return self.build_session(user)
        return None

    async def register(self, db: AsyncSession, data: UserRegister) -> User:
        existing = await db.execute(
            select(User).where(
                or_(User.email == data.email, User.identification == data.identification),
            ),
        )
        conflict = existing.scalar_one_or_none()
        if conflict is not None:
            if conflict.email == data.email:
                raise AuthError("El correo electrónico ya está registrado", status_code=409)
            raise AuthError("La cédula ya está registrada", status_code=409)

        user = User(
            auth_user_id=None,
            email=data.email,
            password_hash=get_password_hash(data.password),
            full_name=data.full_name,
            identification=data.identification,
            phone=data.phone,
            is_verified=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def authenticate(
        self, db: AsyncSession, data: UserLogin
    ) -> tuple[User, SupabaseSession | None]:
        user = await _get_user_by_identification(db, data.identification)
        if user is None:
            raise AuthError("Cédula o contraseña incorrectos", status_code=401)

        if not user.is_active:
            raise AuthError("Cuenta desactivada", status_code=403)

        session = self._verify_password(user, data.password)
        if session is not None:
            return user, session
        raise AuthError("Cédula o contraseña incorrectos", status_code=401)

    async def change_password(
        self, db: AsyncSession, user: User, data: PasswordChange
    ) -> None:
        if data.current_password == data.new_password:
            raise AuthError("La nueva contraseña debe ser diferente a la actual", status_code=400)

        if not user.password_hash or not verify_password(data.current_password, user.password_hash):
            raise AuthError("La contraseña actual es incorrecta", status_code=400)

        user.password_hash = get_password_hash(data.new_password)
        await db.commit()

    async def reset_password(
        self, db: AsyncSession, data: PasswordResetRequest
    ) -> None:
        generic_error = "No se pudo restablecer la contraseña con los datos ingresados"
        result = await db.execute(
            select(User).where(
                User.identification == data.identification,
                User.email == data.email,
                User.is_active.is_(True),
            ),
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise AuthError(generic_error, status_code=400)

        user.password_hash = get_password_hash(data.new_password)
        await db.commit()


# ---------------------------------------------------------------------------
# Implementación Supabase (producción)
# ---------------------------------------------------------------------------

class SupabaseAuthStrategy(AuthStrategy):
    """Autenticación vía Supabase Auth (producción).

    Delega el almacenamiento de credenciales a Supabase Auth y mantiene
    la entidad ``User`` sincronizada en la base de datos local.
    """

    def build_session(self, user: User) -> SupabaseSession:
        raise NotImplementedError(
            "SupabaseAuthStrategy no construye sesiones locales. "
            "Use la sesión devuelta por sign_in_with_password."
        )

    def _local_fallback_session(self, user: User) -> SupabaseSession | None:
        """Verifica el hash local como fallback de backward-compatibilidad."""
        # Reutilizamos la lógica local para el fallback
        _local = LocalAuthStrategy()
        return None  # El caller pasa la contraseña, no el hash; se delega abajo.

    async def register(self, db: AsyncSession, data: UserRegister) -> User:
        existing = await db.execute(
            select(User).where(
                or_(User.email == data.email, User.identification == data.identification),
            ),
        )
        conflict = existing.scalar_one_or_none()
        if conflict is not None:
            if conflict.email == data.email:
                raise AuthError("El correo electrónico ya está registrado", status_code=409)
            raise AuthError("La cédula ya está registrada", status_code=409)

        try:
            result: SupabaseSignupResult = await sign_up(
                data.email,
                data.password,
                metadata={
                    "full_name": data.full_name,
                    "identification": data.identification,
                    "phone": data.phone,
                },
            )
        except SupabaseAuthError as exc:
            raise AuthError(exc.message, status_code=exc.status_code) from exc

        user = User(
            auth_user_id=result.auth_user_id,
            email=data.email,
            full_name=data.full_name,
            identification=data.identification,
            phone=data.phone,
            is_verified=not result.confirmation_required,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def authenticate(
        self, db: AsyncSession, data: UserLogin
    ) -> tuple[User, SupabaseSession | None]:
        user = await _get_user_by_identification(db, data.identification)
        if user is None:
            raise AuthError("Cédula o contraseña incorrectos", status_code=401)

        if not user.is_active:
            raise AuthError("Cuenta desactivada", status_code=403)

        # Intentar Supabase Auth primero
        try:
            session = await sign_in_with_password(user.email, data.password)
            # Vincular auth_user_id si no estaba seteado
            if user.auth_user_id is None:
                user.auth_user_id = session.auth_user_id
                await db.commit()
                await db.refresh(user)
            return user, session
        except SupabaseAuthError as exc:
            # Si el error no es 401 (credenciales), propagar
            if exc.status_code != 401:
                raise AuthError(exc.message, status_code=exc.status_code) from exc

        # Fallback: verificar contra password_hash local (backward-compatibilidad)
        local_strategy = LocalAuthStrategy()
        if user.password_hash and verify_password(data.password, user.password_hash):
            local_session = local_strategy.build_session(user)
            return user, local_session

        raise AuthError("Cédula o contraseña incorrectos", status_code=401)

    async def change_password(
        self, db: AsyncSession, user: User, data: PasswordChange
    ) -> None:
        if data.current_password == data.new_password:
            raise AuthError("La nueva contraseña debe ser diferente a la actual", status_code=400)

        try:
            session = await sign_in_with_password(user.email, data.current_password)
            await supabase_update_user(session.access_token, password=data.new_password)
        except SupabaseAuthError as exc:
            if exc.status_code == 401:
                raise AuthError("La contraseña actual es incorrecta", status_code=400) from exc
            raise AuthError(exc.message, status_code=exc.status_code) from exc

    async def reset_password(
        self, db: AsyncSession, data: PasswordResetRequest
    ) -> None:
        raise AuthError(
            "La recuperación local de contraseña no está habilitada. Configure Supabase para recuperación por email.",
            status_code=503,
        )
