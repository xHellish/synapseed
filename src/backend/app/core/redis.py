from redis.asyncio import Redis, from_url
from app.config import get_settings

# Cliente Redis unico (singleton): se crea una sola vez y se reutiliza
_redis_client: Redis | None = None

def get_redis_client() -> Redis:
    # Crea la conexion la primera vez que se pide y la cachea para las siguientes
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = from_url(settings.redis_url, decode_responses=True)
    return _redis_client
