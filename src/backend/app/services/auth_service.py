"""Lógica de negocio de autenticación y perfil (Supabase Auth + tabla users)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.schemas.user import PasswordChange, UserLogin, UserRegister, UserUpdate


class AuthError(Exception):
    """Error de autenticación con código HTTP asociado."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


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


async def authenticate_user(db: AsyncSession, data: UserLogin) -> tuple[User, SupabaseSession]:
    """Login con cédula: resuelve email en ``users`` y autentica en Supabase."""
    user = await _get_user_by_identification(db, data.identification)
    if user is None:
        raise AuthError("Cédula o contraseña incorrectos", status_code=401)

    if not user.is_active:
        raise AuthError("Cuenta desactivada", status_code=403)

    try:
        session = await sign_in_with_password(user.email, data.password)
    except SupabaseAuthError as exc:
        if exc.status_code == 401:
            raise AuthError("Cédula o contraseña incorrectos", status_code=401) from exc
        raise AuthError(exc.message, status_code=exc.status_code) from exc

    if user.auth_user_id is None:
        user.auth_user_id = session.auth_user_id
        await db.commit()
        await db.refresh(user)
    elif user.auth_user_id != session.auth_user_id:
        raise AuthError("Cédula o contraseña incorrectos", status_code=401)

    return user, session


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
    """Valida JWT de Supabase y carga el usuario de la tabla ``users``."""
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

    try:
        session = await sign_in_with_password(user.email, data.current_password)
        await supabase_update_user(session.access_token, password=data.new_password)
    except SupabaseAuthError as exc:
        if exc.status_code == 401:
            raise AuthError("La contraseña actual es incorrecta", status_code=400) from exc
        raise AuthError(exc.message, status_code=exc.status_code) from exc
