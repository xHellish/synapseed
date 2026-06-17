# Sugerencias SOLID — SynapSeed Backend API (Caso #2)

Evaluación de cumplimiento de principios SOLID sobre el código de la capa API del backend. Generado como insumo para el curso Diseño de Software (TEC).

---

## 1. Diagnóstico de Responsabilidades

| Archivo | Responsabilidades actuales | Problemas identificados |
|---|---|---|
| **main.py** | Inicialización de la app, CORS, lifespan, OpenAPI, registro de rutas | Mezcla de concerns: infraestructura (CORS, OpenAPI), bootstrapping, configuración |
| **zones.py** | CRUD de zonas, mapeo de coordenadas, conversión humedad/temperatura, limpieza de payload | Mezcla: routing HTTP, lógica de dominio (conversiones), validación, persistencia |
| **auth.py** | Routing de endpoints de autenticación | Capa delgada — apropiada, delega bien al servicio |
| **recommendations.py** | Endpoints de recomendaciones, streaming Redis SSE, auditoría, generación de ticket | Mezcla: routing, streaming SSE, manejo de Redis, auditoría, coordinación de servicios |
| **auth_service.py** | Registro, login, reset de contraseña, resolución de token, actualización de perfil | Mezcla: lógica de negocio, integración Supabase, hashing, queries DB, construcción de sesión |
| **security.py** | Creación/validación JWT, hashing, extracción Bearer, resolución de usuario actual | Mezcla: utilidades criptográficas, parsing HTTP, validación de tokens, acceso a DB |
| **dependencies.py** | Inyección de dependencias FastAPI (auth, sesión DB) | Apropiado — capa DI delgada con `Depends` |

---

## 2. Matriz de Evaluación SOLID

### `main.py`

| Principio | Estado | Justificación |
|---|---|---|
| S — Single Responsibility | ❌ Viola | `create_app()` maneja: instanciación de FastAPI, CORS, lifespan, OpenAPI, registro de routers, endpoint raíz — 5+ responsabilidades distintas |
| O — Open/Closed | ❌ Viola | El registro de routers es hard-coded (`from app.api.v1 import catalogs, health...`). Agregar un nuevo router obliga a modificar `main.py` |
| L — Liskov Substitution | ✅ Cumple | Sin herencia ni polimorfismo |
| I — Interface Segregation | ✅ Cumple | Sin interfaces gruesas |
| D — Dependency Inversion | ❌ Viola | `get_settings()` se llama directamente; routers se importan y registran como dependencias concretas |

---

### `zones.py`

| Principio | Estado | Justificación |
|---|---|---|
| S — Single Responsibility | ❌ Viola | Un solo archivo maneja: routing HTTP, mapeo de coordenadas, conversión de humedad/temperatura, limpieza de payload, instanciación de repositorios, auditoría |
| O — Open/Closed | ❌ Viola | Funciones como `map_location_to_coords()` usan cascadas de `if` para seleccionar comportamiento. Agregar una nueva provincia requiere modificar la función |
| L — Liskov Substitution | ✅ Cumple | Sin herencia |
| I — Interface Segregation | ❌ Viola | Los handlers reciben dependencias que no siempre usan; sin contrato claro de interfaz |
| D — Dependency Inversion | ❌ Viola | Cada handler instancia repositorios directamente: `zones = ZoneRepository(db)` y `audit = AuditRepository(db)` — no se inyectan |

**Ejemplo de violación DIP:**
```python
# ❌ Actual — instanciación directa dentro del handler
@router.post("")
async def create_zone(payload: dict, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    zones = ZoneRepository(db)   # acoplamiento directo
    audit = AuditRepository(db)  # acoplamiento directo
    ...
```

**Ejemplo de violación OCP:**
```python
# ❌ Actual — cada nueva provincia requiere modificar esta función
def map_location_to_coords(location_str):
    if "cartago" in loc_lower: return 9.86, -83.92
    if "alajuela" in loc_lower: return 10.02, -84.21
    if "heredia" in loc_lower: return 10.00, -84.12
    # ... más ifs
```

---

### `auth.py`

| Principio | Estado | Justificación |
|---|---|---|
| S — Single Responsibility | ✅ Cumple | Una sola responsabilidad: orquestar routing de auth y delegar al servicio |
| O — Open/Closed | ✅ Cumple | Sin condicionales de comportamiento; nuevos flujos se agregan como nuevos endpoints |
| L — Liskov Substitution | ✅ Cumple | Sin herencia |
| I — Interface Segregation | ✅ Cumple | Dependencias granulares; sin interfaces gruesas |
| D — Dependency Inversion | ✅ Cumple | Dependencias inyectadas vía `Depends()` de FastAPI |

**Estado: ARCHIVO LIMPIO** — No requiere refactorización. Es un buen ejemplo de capa de routing.

---

### `recommendations.py`

| Principio | Estado | Justificación |
|---|---|---|
| S — Single Responsibility | ❌ Viola | Mezcla: routing HTTP, coordinación de repositorios, auditoría, streaming Redis pub/sub, dispatch de tareas Celery, generación de UUID, formateo de respuestas |
| O — Open/Closed | ❌ Viola | El dispatch de Celery está hard-coded (`generate_recommendation.delay(ticket_id)`). Cambiar a otro framework requiere modificar el endpoint |
| L — Liskov Substitution | ✅ Cumple | Sin herencia |
| I — Interface Segregation | ❌ Viola | El endpoint `stream()` no declara `current_user` ni `db` en su firma, pero los instancia internamente; sin contrato claro |
| D — Dependency Inversion | ❌ Viola | `RecommendationRepository(db)`, `AuditRepository(db)`, `Redis.from_url()` y `get_db_session()` se instancian directamente dentro de los handlers |

**Ejemplo de violación SRP — endpoint `stream()`:**
```python
# ❌ Actual — 35+ líneas mezclando DB, Redis, SSE, async, cleanup
@router.get("/stream/{ticket_id}")
async def stream(ticket_id: str) -> StreamingResponse:
    async def event_stream():
        async with get_db_session() as db:       # gestión de DB
            recommendations = RecommendationRepository(db)  # instanciación
            rec = await recommendations.get_by_ticket_id(ticket_id)
            ...
        redis_client = Redis.from_url(...)       # gestión de Redis
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(...)
        while True:
            message = await pubsub.get_message(...) # polling
            yield f"event: status\ndata: {data}\n\n"  # formateo SSE
            await asyncio.sleep(0.5)
        # ... finally cleanup
```

---

### `auth_service.py`

| Principio | Estado | Justificación |
|---|---|---|
| S — Single Responsibility | ❌ Viola | Mezcla: autenticación local, integración Supabase, hashing de contraseñas, registro de usuarios, actualización de perfil, construcción de sesión, queries DB directos |
| O — Open/Closed | ❌ Viola | Cada función tiene `if _local_auth_enabled()` para bifurcar entre auth local y Supabase. Agregar OAuth/SAML requiere más condicionales en las mismas funciones |
| L — Liskov Substitution | ✅ Cumple | `AuthError` es apropiado; sin problemas de subtipado |
| I — Interface Segregation | ❌ Viola | El módulo exporta muchas funciones con firmas diferentes; los clientes dependen de funciones que quizás no usan |
| D — Dependency Inversion | ❌ Viola | Llama directamente a `get_settings()`, funciones de Supabase (`sign_up`, `sign_in_with_password`), y ejecuta queries SQLAlchemy sin abstracción de repositorio |

**Ejemplo de violación OCP:**
```python
# ❌ Actual — el mismo patrón se repite en register_user, authenticate_user, change_user_password
async def register_user(db: AsyncSession, data: UserRegister) -> User:
    ...
    if _local_auth_enabled():
        # lógica de registro local
        user = User(auth_user_id=None, password_hash=get_password_hash(...), ...)
        db.add(user)
        return user
    try:
        result = await sign_up(...)  # lógica de registro Supabase
        user = User(auth_user_id=result.auth_user_id, ...)
        ...
```

---

### `security.py`

| Principio | Estado | Justificación |
|---|---|---|
| S — Single Responsibility | ❌ Viola | Mezcla: hashing de contraseñas, creación/validación de JWT, extracción Bearer HTTP, resolución de usuario actual, acceso a DB |
| O — Open/Closed | ❌ Viola | `get_current_user()` tiene lógica de fallback hard-coded (JWT local → Supabase). Agregar otro proveedor requiere modificar la función |
| L — Liskov Substitution | ✅ Cumple | Sin herencia |
| I — Interface Segregation | ❌ Viola | Un endpoint que solo necesita hashear contraseñas importa todo el módulo que también maneja tokens, HTTP y DB |
| D — Dependency Inversion | ❌ Viola | `CryptContext` instanciado globalmente; `get_settings()` llamado directamente; `resolve_user_from_token()` importado directamente |

---

### `dependencies.py`

| Principio | Estado | Justificación |
|---|---|---|
| S — Single Responsibility | ✅ Cumple | Una responsabilidad: definir los patrones de DI de FastAPI |
| O — Open/Closed | ✅ Cumple | Sin condicionales; nuevos tipos de dependencia se agregan sin modificar los existentes |
| L — Liskov Substitution | ✅ Cumple | Sin herencia |
| I — Interface Segregation | ✅ Cumple | `CurrentUser`, `DbSession`, `BearerToken` son granulares; cada cliente toma solo lo que necesita |
| D — Dependency Inversion | ✅ Cumple | Todas las dependencias se inyectan vía `Depends()`; sin instanciación propia |

**Estado: ARCHIVO LIMPIO** — Abstracción correcta sobre el sistema de DI de FastAPI.

---

## 3. Ranking de Prioridades

| Prioridad | Severidad | Archivo(s) | Violación | Impacto |
|---|---|---|---|---|
| 🔴 P0 | CRÍTICA | `recommendations.py` | SRP + DIP en `stream()` | Imposible de testear o mantener: Redis/DB/SSE mezclados |
| 🔴 P0 | CRÍTICA | `zones.py` | SRP + DIP: repositorios instanciados + lógica de mapeo | Cada operación acopla routing a persistencia |
| 🔴 P0 | CRÍTICA | `auth_service.py` | OCP: cascada de condicionales por estrategia de auth | Agregar OAuth/SAML requiere tocar todas las funciones |
| 🟠 P1 | ALTA | `main.py` | OCP + DIP: registro de routers hard-coded | Agregar rutas obliga a modificar `main.py` |
| 🟠 P1 | ALTA | `recommendations.py` | DIP: dispatch directo a Celery | Sin abstracción; imposible cambiar de framework sin modificar el endpoint |
| 🟠 P1 | ALTA | `auth_service.py` | DIP: queries DB directos, sin abstracción de repositorio | Acopla el servicio a SQLAlchemy |
| 🟡 P2 | MEDIA | `security.py` | SRP: crypto + token + HTTP mezclados | Problema de mantenimiento a largo plazo |
| 🟡 P2 | MEDIA | `zones.py` | OCP: mapeo de ubicaciones con `if` hard-coded | Cada nueva provincia requiere modificar código |
| 🟢 P3 | BAJA | `security.py` | DIP: `CryptContext` instanciado globalmente | Podría inyectarse; impacto bajo |

---

## 4. Propuestas de Refactorización

### Refactorización #1 — `auth_service.py`: Strategy Pattern para autenticación

**Problema:** `if _local_auth_enabled()` se repite en cada función de autenticación. Agregar un nuevo proveedor (OAuth, SAML) requiere modificar todas las funciones existentes.

**Solución:** Strategy Pattern con una interfaz abstracta `AuthStrategy` y dos implementaciones concretas.

```
app/services/
├── auth_strategy.py      ← interfaz abstracta + implementaciones
│   ├── AuthStrategy (ABC)
│   ├── LocalAuthStrategy
│   └── SupabaseAuthStrategy
├── auth_service.py       ← AuthService + AuthServiceFactory (refactorizado)
```

```python
# auth_strategy.py — interfaz abstracta
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, PasswordChange, PasswordResetRequest
from app.core.supabase import SupabaseSession

class AuthStrategy(ABC):
    @abstractmethod
    async def register(self, db: AsyncSession, data: UserRegister) -> User: ...

    @abstractmethod
    async def authenticate(self, db: AsyncSession, data: UserLogin) -> tuple[User, SupabaseSession]: ...

    @abstractmethod
    async def change_password(self, db: AsyncSession, user: User, data: PasswordChange) -> None: ...

    @abstractmethod
    async def reset_password(self, db: AsyncSession, data: PasswordResetRequest) -> None: ...

    @abstractmethod
    def build_session(self, user: User) -> SupabaseSession: ...


class LocalAuthStrategy(AuthStrategy):
    """Autenticación local con bcrypt (desarrollo/self-hosted)."""
    async def register(self, db, data): ...
    async def authenticate(self, db, data): ...
    async def change_password(self, db, user, data): ...
    async def reset_password(self, db, data): ...
    def build_session(self, user): ...


class SupabaseAuthStrategy(AuthStrategy):
    """Autenticación vía Supabase Auth (producción)."""
    async def register(self, db, data): ...
    async def authenticate(self, db, data): ...
    async def change_password(self, db, user, data): ...
    async def reset_password(self, db, data):
        raise AuthError("Reset no soportado en Supabase", status_code=503)
    def build_session(self, user):
        raise NotImplementedError("Usar sesión de sign_in_with_password")
```

```python
# auth_service.py — refactorizado
class AuthServiceFactory:
    @staticmethod
    def get_strategy() -> AuthStrategy:
        if AuthServiceFactory._local_auth_enabled():
            return LocalAuthStrategy()
        return SupabaseAuthStrategy()

class AuthService:
    def __init__(self, strategy: AuthStrategy | None = None):
        self.strategy = strategy or AuthServiceFactory.get_strategy()

    async def register_user(self, db, data): return await self.strategy.register(db, data)
    async def authenticate_user(self, db, data): return await self.strategy.authenticate(db, data)
    async def reset_user_password(self, db, data): await self.strategy.reset_password(db, data)
```

**Beneficios:**
- ✅ **OCP:** Agregar OAuth2 = crear `OAuthAuthStrategy`, sin tocar código existente
- ✅ **DIP:** `AuthService` depende de `AuthStrategy` (abstracción), no de implementaciones
- ✅ **SRP:** Cada estrategia tiene una sola responsabilidad de autenticación
- ✅ **Testabilidad:** Se puede inyectar una estrategia mock en tests

---

### Refactorización #2 — `zones.py`: Service Layer + Inyección de Repositorios

**Problema:** Routing, lógica de dominio, repositorios y auditoría conviven en el mismo archivo. Los repositorios se instancian dentro de los handlers.

**Solución:** Extraer `ZoneService`, inyectarlo vía `Depends()`, y separar la lógica de mapeo en clases especializadas.

```
app/services/
└── zone_service.py
    ├── LocationMapper
    ├── HumidityMapper
    ├── TemperatureMapper
    └── ZoneService
```

```python
# zone_service.py
class LocationMapper:
    LOCATION_REGISTRY = {
        "cartago":    LocationCoordinate(9.86, -83.92),
        "alajuela":   LocationCoordinate(10.02, -84.21),
        "heredia":    LocationCoordinate(10.00, -84.12),
        "san_jose":   LocationCoordinate(9.93, -84.09),
        "guanacaste": LocationCoordinate(10.60, -85.40),
        "puntarenas": LocationCoordinate(9.98, -84.83),
        "limon":      LocationCoordinate(10.00, -83.03),
    }

    @classmethod
    def location_string_to_coords(cls, location_str: str | None) -> tuple[float | None, float | None]: ...

    @classmethod
    def coords_to_location_string(cls, lat: float | None, lon: float | None) -> str: ...


class ZoneService:
    def __init__(self, zone_repo: ZoneRepository, audit_repo: AuditRepository):
        self.zone_repo = zone_repo
        self.audit_repo = audit_repo

    async def list_zones(self, user_id: int, skip: int, limit: int) -> list[dict]: ...
    async def create_zone(self, user_id: int, payload: dict) -> dict: ...
    async def update_zone(self, zone_id: int, user_id: int, payload: dict) -> dict: ...
    async def delete_zone(self, zone_id: int, user_id: int) -> dict: ...
```

```python
# zones.py — refactorizado (capa de routing delgada)
def get_zone_service(db: AsyncSession = Depends(get_db)) -> ZoneService:
    return ZoneService(ZoneRepository(db), AuditRepository(db))

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_zone(
    payload: dict,
    current_user: dict = Depends(get_current_user),
    service: ZoneService = Depends(get_zone_service),  # ← inyección
) -> dict:
    try:
        return await service.create_zone(int(current_user["id"]), payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
```

**Beneficios:**
- ✅ **SRP:** Routes son delgadas; `ZoneService` encapsula la lógica; los mappers manejan transformaciones
- ✅ **DIP:** Routes dependen de `ZoneService` (abstracción), no de repositorios concretos
- ✅ **OCP:** Agregar nuevas provincias = actualizar `LOCATION_REGISTRY`, sin modificar funciones
- ✅ **Testabilidad:** `ZoneService` se puede testear con repositorios mock

---

### Refactorización #3 — `recommendations.py`: Abstracción de Task Queue + Service Layer

**Problema:** El endpoint `stream()` mezcla DB, Redis, SSE y polling. El dispatch a Celery es un acoplamiento directo.

**Solución:** Interfaz `TaskDispatcher`, clase `RecommendationStreamService`, clase `RecommendationService`.

```
app/services/
├── task_dispatcher.py              ← abstracción + implementación Celery
├── recommendation_stream_service.py ← lógica SSE aislada
└── recommendation_service.py       ← lógica de negocio
```

```python
# task_dispatcher.py
class TaskDispatcher(ABC):
    @abstractmethod
    async def dispatch_recommendation_generation(self, ticket_id: str) -> None: ...

class CeleryTaskDispatcher(TaskDispatcher):
    async def dispatch_recommendation_generation(self, ticket_id: str) -> None:
        from app.workers.tasks import generate_recommendation
        generate_recommendation.delay(ticket_id)
```

```python
# recommendation_stream_service.py
class RecommendationStreamService:
    async def stream_recommendation_progress(self, ticket_id: str):
        """Async generator que emite eventos SSE de progreso."""
        # Verificar estado inicial en DB
        async with get_db_session() as db:
            rec = await RecommendationRepository(db).get_by_ticket_id(ticket_id)
            if not rec:
                yield self._format_event("status", {"ticket_id": ticket_id, "status": "not_found"})
                return
            yield self._format_event("status", {...})
            if rec.status.value in ("completed", "failed"):
                return

        # Suscribirse a Redis para actualizaciones
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"recommendation_progress:{ticket_id}")
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    yield self._format_event("status", message["data"])
                    if json.loads(message["data"]).get("status") in ("completed", "failed"):
                        break
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe(...)
            await redis_client.close()

    @staticmethod
    def _format_event(event_name: str, data: dict | str) -> str:
        if isinstance(data, dict):
            data = json.dumps(data)
        return f"event: {event_name}\ndata: {data}\n\n"
```

```python
# recommendations.py — refactorizado
def get_recommendation_service(dispatcher: TaskDispatcher = Depends(get_task_dispatcher)):
    return RecommendationService(dispatcher)

@router.get("/stream/{ticket_id}")
async def stream(
    ticket_id: str,
    stream_service: RecommendationStreamService = Depends(get_stream_service),
) -> StreamingResponse:
    return StreamingResponse(
        stream_service.stream_recommendation_progress(ticket_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
```

**Beneficios:**
- ✅ **DIP:** Routes dependen de `TaskDispatcher` (abstracción), no de Celery
- ✅ **SRP:** Streaming aislado en su propio servicio; routing es solo orquestación
- ✅ **OCP:** Cambiar de Celery a Kafka = implementar `KafkaTaskDispatcher`, sin tocar routes
- ✅ **Testabilidad:** Se puede inyectar un `MockTaskDispatcher` en tests

---

## 5. Roadmap de Refactorización

| Paso | Archivo(s) | Acción | Esfuerzo estimado |
|---|---|---|---|
| 1 | `auth_service.py` | Aplicar Strategy Pattern (`AuthStrategy`, `LocalAuthStrategy`, `SupabaseAuthStrategy`) | ~2h |
| 2 | `zones.py` | Crear `ZoneService` + `LocationMapper`/`HumidityMapper`/`TemperatureMapper` | ~1.5h |
| 3 | `recommendations.py` | Crear `TaskDispatcher`, `RecommendationStreamService`, `RecommendationService` | ~2h |
| 4 | `main.py` | Plugin-based router registry para cumplir OCP | ~1h |
| 5 | `security.py` | Separar en `password_service.py` y `token_service.py` | ~1h |

**Total estimado:** ~7.5h de trabajo enfocado.

Los archivos `auth.py` y `dependencies.py` no requieren cambios.
