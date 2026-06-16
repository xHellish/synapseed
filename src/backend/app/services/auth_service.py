"""Lógica de negocio de autenticación y perfil (Supabase Auth + tabla users)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.supabase import (
    SupabaseAuthError,
    SupabaseSession,
    SupabaseSignupResult,
    get_user as supabase_get_user,
    sign_in_with_password,
    sign_up,
    update_user as supabase_update_user,
)
from app.models.user import User
from app.schemas.user import PasswordChange, PasswordResetRequest, UserLogin, UserRegister, UserUpdate


class AuthError(Exception):
    """Error de autenticación con código HTTP asociado."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _is_unconfigured(value: str) -> bool:
    """Detecta valores vacíos o placeholders del .env de ejemplo."""
    normalized = value.strip().lower()
    return not normalized or any(token in normalized for token in ("<", ">", "[", "]", "your-", "tu_"))


def _local_auth_enabled() -> bool:
    """Permite auth local solo para desarrollo cuando Supabase no está configurado."""
    settings = get_settings()
    return settings.is_development and (
        _is_unconfigured(settings.supabase_url)
        or _is_unconfigured(settings.supabase_anon_key)
    )


def _build_local_session(user: User) -> SupabaseSession:
    settings = get_settings()
    return SupabaseSession(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token="",
        expires_in=settings.jwt_expire_hours * 3600,
        auth_user_id=user.auth_user_id if user.auth_user_id is not None else UUID(int=user.id),
        email=user.email,
    )


def _verify_local_password(user: User, password: str) -> SupabaseSession | None:
    if user.password_hash and verify_password(password, user.password_hash):
        return _build_local_session(user)
    return None


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


async def register_user(db: AsyncSession, data: UserRegister) -> User:
    """Registra perfil en DB y credenciales en Supabase Auth.

    Funciona tanto si Supabase tiene confirmación de email habilitada como deshabilitada.
    Si está habilitada, el usuario se guarda en la DB con ``is_verified=False`` y sin sesión.
    """
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

    if _local_auth_enabled():
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


async def authenticate_user(db: AsyncSession, data: UserLogin) -> tuple[User, SupabaseSession | None]:
    """Login con cédula: resuelve email en ``users`` y autentica en Supabase.

    Soporta backward-compatibility:
    - Usuarios registrados con bcrypt local (password_hash) intentan Supabase;
      si Supabase no los tiene, se verifica contra el hash local.
    - Usuarios registrados via Supabase Auth se autentican normalmente.
    """
    user = await _get_user_by_identification(db, data.identification)
    if user is None:
        raise AuthError("Cédula o contraseña incorrectos", status_code=401)

    if not user.is_active:
        raise AuthError("Cuenta desactivada", status_code=403)

    if _local_auth_enabled():
        local_session = _verify_local_password(user, data.password)
        if local_session is not None:
            return user, local_session
        raise AuthError("Cédula o contraseña incorrectos", status_code=401)

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
    local_session = _verify_local_password(user, data.password)
    if local_session is not None:
        return user, local_session

    raise AuthError("Cédula o contraseña incorrectos", status_code=401)


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
    1. **JWT local** (firmado con ``JWT_SECRET``): emitido por el fallback de bcrypt.
       El campo ``sub`` contiene el ``user.id`` como string numérico.
    2. **JWT de Supabase**: emitido por Supabase Auth.
       Se valida contra la API de Supabase ``/auth/v1/user``.
    """
    # --- Intentar decodificar como JWT local primero ---
    from app.core.security import decode_access_token as _local_decode

    try:
        payload = _local_decode(access_token)
        sub = payload.get("sub", "")
        # Token local: sub es el user.id (entero serializado como str)
        if sub.isdigit():
            result = await db.execute(select(User).where(User.id == int(sub)))
            user = result.scalar_one_or_none()
            if user is None:
                raise AuthError("Usuario no encontrado", status_code=401)
            if not user.is_active:
                raise AuthError("Cuenta desactivada", status_code=403)
            return user
        # sub no es numérico → podría ser un token de Supabase con formato UUID;
        # caemos al path de Supabase abajo.
    except AuthError:
        raise
    except Exception:
        # No es un JWT local válido → intentar con Supabase
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

        if not _local_auth_enabled():
            try:
                await supabase_update_user(access_token, email=new_email)
            except SupabaseAuthError as exc:
                raise AuthError(exc.message, status_code=exc.status_code) from exc

    for field, value in updates.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


async def change_user_password(
    db: AsyncSession,
    user: User,
    data: PasswordChange,
) -> None:
    """Cambia contraseña verificando la actual vía Supabase."""
    if data.current_password == data.new_password:
        raise AuthError("La nueva contraseña debe ser diferente a la actual", status_code=400)

    if _local_auth_enabled():
        if not user.password_hash or not verify_password(data.current_password, user.password_hash):
            raise AuthError("La contraseña actual es incorrecta", status_code=400)
        user.password_hash = get_password_hash(data.new_password)
        await db.commit()
        return

    try:
        session = await sign_in_with_password(user.email, data.current_password)
        await supabase_update_user(session.access_token, password=data.new_password)
    except SupabaseAuthError as exc:
        if exc.status_code == 401:
            raise AuthError("La contraseña actual es incorrecta", status_code=400) from exc
        raise AuthError(exc.message, status_code=exc.status_code) from exc


async def reset_user_password(db: AsyncSession, data: PasswordResetRequest) -> None:
    """Restablece contraseña en modo local de desarrollo/demo."""
    if not _local_auth_enabled():
        raise AuthError(
            "La recuperación local de contraseña no está habilitada. Configure Supabase para recuperación por email.",
            status_code=503,
        )

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
