"""Servicios de infraestructura y lógica de negocio."""

from app.services.auth_service import (
    AuthError,
    AuthService,
    AuthServiceFactory,
    authenticate_user,
    build_token_response,
    change_user_password,
    register_user,
    reset_user_password,
    resolve_user_from_token,
    update_user_profile,
)
from app.services.auth_strategy import (
    AuthStrategy,
    LocalAuthStrategy,
    SupabaseAuthStrategy,
)
from app.services.llm_client import LLMClient, MockLLMClient, OpenRouterLLMClient
from app.services.recommendation_service import RecommendationService
from app.services.recommendation_stream_service import RecommendationStreamService
from app.services.task_dispatcher import CeleryTaskDispatcher, TaskDispatcher
from app.services.zone_service import (
    HumidityMapper,
    LocationMapper,
    TemperatureMapper,
    ZoneService,
)

__all__ = [
    # Auth — wrappers de compatibilidad hacia atrás
    "AuthError",
    "register_user",
    "reset_user_password",
    "authenticate_user",
    "build_token_response",
    "resolve_user_from_token",
    "update_user_profile",
    "change_user_password",
    # Auth — clases nuevas
    "AuthService",
    "AuthServiceFactory",
    "AuthStrategy",
    "LocalAuthStrategy",
    "SupabaseAuthStrategy",
    # LLM
    "LLMClient",
    "OpenRouterLLMClient",
    "MockLLMClient",
    # Recomendaciones
    "RecommendationService",
    "RecommendationStreamService",
    "TaskDispatcher",
    "CeleryTaskDispatcher",
    # Zonas
    "ZoneService",
    "LocationMapper",
    "HumidityMapper",
    "TemperatureMapper",
]
