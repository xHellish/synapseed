# Guía del Desarrollador - SynapSeed

> Documento de referencia técnica. Su objetivo es que cualquier programador que
> entre al proyecto entienda **cómo hacer cada cosa** y, sobre todo, **por qué**
> está hecha así. No reemplaza al [README.md](../README.md) (cómo levantar el
> stack) ni a [Decisiones_de_Diseno.md](Decisiones_de_Diseno.md) (defensa de
> arquitectura); los complementa con el detalle operativo del día a día.

## Tabla de contenidos

1. [Qué es SynapSeed y por qué existe](#1-qué-es-synapseed-y-por-qué-existe)
2. [El flujo completo de una recomendación](#2-el-flujo-completo-de-una-recomendación)
3. [Stack tecnológico y el porqué de cada pieza](#3-stack-tecnológico-y-el-porqué-de-cada-pieza)
4. [Cómo levantar y trabajar el proyecto](#4-cómo-levantar-y-trabajar-el-proyecto)
5. [Estructura de carpetas](#5-estructura-de-carpetas)
6. [Backend: las 4 capas y por qué](#6-backend-las-4-capas-y-por-qué)
7. [Recetas backend: cómo agregar cosas](#7-recetas-backend-cómo-agregar-cosas)
8. [El pipeline de agentes IA](#8-el-pipeline-de-agentes-ia)
9. [Procesamiento asíncrono: Celery + SSE](#9-procesamiento-asíncrono-celery--sse)
10. [Autenticación](#10-autenticación)
11. [Base de datos, migraciones y seeding](#11-base-de-datos-migraciones-y-seeding)
12. [Frontend en profundidad](#12-frontend-en-profundidad)
13. [Recetas frontend: cómo agregar cosas](#13-recetas-frontend-cómo-agregar-cosas)
14. [Testing](#14-testing)
15. [Calidad de código y convenciones](#15-calidad-de-código-y-convenciones)
16. [Recetario rápido](#16-recetario-rápido)
17. [Gotchas: cosas que confunden](#17-gotchas-cosas-que-confunden)

---

## 1. Qué es SynapSeed y por qué existe

SynapSeed es una plataforma que recomienda agroquímicos a agricultores
costarricenses. El agricultor describe su caso (cultivo, etapa, problema, zona,
presupuesto) y el sistema devuelve **exactamente 3 productos** rankeados con una
tabla comparativa y los distribuidores donde conseguirlos. Es **solo
información**: no hay compras.

**El porqué del problema:** elegir un agroquímico es difícil y arriesgado. Hay
miles de productos registrados en el SFE (Servicio Fitosanitario del Estado),
regulaciones que prohíben sustancias, y límites de residuos (LMR) por cultivo.
Un agricultor no puede navegar todo eso. SynapSeed lo hace por él, pero con una
regla de oro: **nunca inventa datos**. Todo dato factual (nombre, precio,
ingrediente, toxicidad) sale de la base de datos; la IA solo redacta el texto
interpretativo.

Es un proyecto académico (TEC, Diseño de Software, Caso #2). Eso explica algunas
decisiones: prioriza claridad y demostrar dominio de patrones por encima de
features.

---

## 2. El flujo completo de una recomendación

Esta es la columna vertebral del sistema. Si entendés este flujo, entendés
SynapSeed. Seguí el recorrido de una sola petición:

```
Usuario (wizard frontend)
   │  1. POST /api/v1/recommendations/request  (crop, problema, presupuesto...)
   ▼
Router recommendations.py
   │  2. Crea fila Recommendation (status=PENDING), encola tarea Celery,
   │     responde 202 con un ticket_id  (NO espera al LLM)
   ▼
Worker Celery (tasks.py)
   │  3. status=PROCESSING. Corre el orquestador de 4 agentes:
   │
   │     Agente 1 Analyzer    -> estructura el contexto (LLM)
   │     Agente 2 Researcher  -> busca productos candidatos en DB (RAG/SQL)
   │     Agente 3 Legal       -> filtra contra regulaciones (reglas + LLM)
   │     Agente 4 Synthesizer -> arma las 3 recomendaciones (LLM solo texto)
   │
   │  4. Tras cada paso publica el progreso en Redis (pub/sub)
   │  5. Guarda los 3 productos en DB, status=COMPLETED
   ▼
Frontend (CaseWizardStep3)
   6. Mientras procesa, refresca el detalle y muestra el avance
   7. Al completarse, pinta la tabla comparativa y los proveedores
```

**Por qué este diseño (asíncrono):** el pipeline tarda 10-50 segundos (varias
llamadas a un LLM). Si el endpoint HTTP esperara a que termine, la petición daría
timeout y bloquearía un worker web. Por eso se parte en dos: el endpoint solo
**encola** y responde al instante; el trabajo pesado corre en un proceso aparte
(Celery) y el progreso vuelve al usuario por streaming.

Archivos clave del flujo:
- [recommendations.py](../src/backend/app/api/v1/recommendations.py) - endpoints
- [tasks.py](../src/backend/app/workers/tasks.py) - la tarea de fondo
- [orchestrator.py](../src/backend/app/agents/orchestrator.py) - los 4 pasos
- [CaseWizardStep3.tsx](../src/frontend/src/features/wizard/CaseWizardStep3.tsx) - la pantalla

---

## 3. Stack tecnológico y el porqué de cada pieza

### Backend

| Pieza | Versión | Por qué |
|---|---|---|
| FastAPI | 0.115 | Async nativo (necesario para I/O de DB + LLM concurrente) y validación automática con Pydantic + Swagger gratis |
| SQLAlchemy 2.0 (async) | 2.0.36 | ORM maduro con soporte async real vía `asyncpg`; separa el modelo de datos de las consultas |
| asyncpg | 0.30 | Driver Postgres async, rápido. Es el de runtime |
| psycopg2 | 2.9 | Driver Postgres **sync**, usado **solo** por Alembic (migraciones) |
| Alembic | 1.14 | Migraciones versionadas de esquema |
| pgvector | 0.3.6 | Tipo `vector` para embeddings de 768 dims (búsqueda semántica) |
| Celery + Redis | 5.4 / 5.2 | Cola de tareas para el pipeline largo; Redis es broker y pub/sub para SSE |
| LangChain / LangGraph | 0.3.x | Cliente de LLM y orquestación; LangGraph deja la puerta abierta a un grafo de agentes |
| Pydantic v2 | 2.10 | Valida la entrada HTTP y, sobre todo, **valida la salida JSON del LLM** contra un schema |
| python-jose + passlib[bcrypt] | - | JWT local y hash de contraseñas para el fallback de auth |
| tenacity | 9.0 | Reintentos con backoff exponencial cuando el LLM devuelve JSON inválido |

### Frontend

| Pieza | Versión | Por qué |
|---|---|---|
| React 19 + Vite 6 | - | UI por componentes; Vite da HMR instantáneo en dev |
| TypeScript 5.7 | - | Tipado estático; contratos claros con la API |
| React Router 7 | - | Ruteo SPA, con rutas protegidas |
| TanStack React Query 5 | - | Maneja el **estado del servidor** (fetching, cache, refetch) |
| Zustand 5 | - | Maneja el **estado del cliente** (auth, datos del wizard) |
| react-hook-form + zod | - | Formularios con validación declarativa y tipada |
| TailwindCSS v4 | - | Estilos utilitarios; v4 es CSS-first (no hay `tailwind.config.js`) |
| shadcn/ui + Radix | - | Componentes accesibles (dialog, select, toast) sin reinventar |
| axios | - | Cliente HTTP |

**El porqué de la separación React Query vs Zustand** es importante y se explica
en [§12](#12-frontend-en-profundidad).

---

## 4. Cómo levantar y trabajar el proyecto

> Detalle completo en el [README.md](../README.md). Aquí va lo operativo del día a día.

**Por qué Docker:** levanta los 4 servicios (redis, backend, worker, frontend) con
una sola orden, todos en la misma red, con las versiones correctas. La base de
datos NO es local: es Supabase (externa), configurada en `.env`.

```bash
docker compose up -d            # levantar todo
docker compose logs -f backend  # ver logs del backend
docker compose logs -f worker   # ver logs del pipeline de agentes
docker compose restart backend  # reiniciar un servicio
docker compose down             # bajar todo
```

**Cambios de código en vivo:** el backend monta `app/` con `--reload` y el
frontend corre Vite con HMR. Editar un archivo se refleja **sin reconstruir la
imagen**. Solo hay que reconstruir (`up -d --build`) si cambian dependencias
(`pyproject.toml`, `package.json`) o un `Dockerfile`.

**Verificaciones rápidas (correr dentro del contenedor):**

```bash
docker compose exec backend ruff check . && docker compose exec backend mypy app
docker compose exec backend pytest
docker compose exec -T frontend npm run typecheck
docker compose exec -T frontend npm run lint
```

Accesos: Frontend `http://localhost:5173`, Swagger `http://localhost:8000/docs`.

---

## 5. Estructura de carpetas

### Backend (`src/backend/app/`)

```
api/v1/         Routers HTTP (entran las peticiones). Uno por recurso.
services/       Lógica de negocio que no es CRUD (auth, cliente LLM)
repositories/   Acceso a datos (todas las queries SQLAlchemy viven aquí)
models/         Modelos ORM (tablas) de SQLAlchemy
schemas/        DTOs Pydantic (entrada/salida HTTP y schemas del LLM)
agents/         El pipeline de 4 agentes + sus prompts + estado
workers/        Celery: la app y las tareas de fondo
core/           Utilidades transversales (security, redis, supabase)
db/             Sesión async, seeding, base declarativa
config.py       Toda la configuración (pydantic-settings, lee .env)
dependencies.py Dependencias inyectables de FastAPI (auth, sesión)
main.py         App factory: CORS, routers, lifespan, OpenAPI
```

**Por qué esta separación:** cada carpeta es una responsabilidad. Un router no
sabe SQL; un repositorio no sabe HTTP. Esto permite testear cada capa por
separado y cambiar una sin tocar las otras (ver [§6](#6-backend-las-4-capas-y-por-qué)).

### Frontend (`src/frontend/src/`)

```
app/            Configuración de rutas (router.tsx) y ProtectedRoute
features/       Módulos por funcionalidad (auth, wizard, zones, account)
components/ui/  Componentes reutilizables (wrappers de shadcn/ui)
stores/         Stores de Zustand (authStore, wizardStore)
lib/            Utilidades (cliente axios implícito, manejo de errores, cn)
main.tsx        Punto de entrada: monta React Query + Router
```

**Por qué "por features":** cada flujo (el wizard, la auth, las zonas) agrupa sus
propios componentes, schemas y lógica. Es más fácil de navegar que separar por
tipo técnico (todos los componentes juntos, todos los hooks juntos).

---

## 6. Backend: las 4 capas y por qué

El backend sigue un flujo estricto de capas:

```
Router (api/v1/)  ->  Service (services/)  ->  Repository (repositories/)  ->  Model (models/)
   HTTP                lógica de negocio        queries a la DB                 tablas ORM
```

**Reglas (qué va en cada capa y qué NO):**

- **Router**: recibe la petición HTTP, valida con Pydantic, llama a un service o
  repository, traduce errores a códigos HTTP. **No** lleva lógica de negocio
  compleja ni SQL.
- **Service**: reglas de negocio que van más allá de CRUD (ej. el login que
  combina Supabase + fallback local en [auth_service.py](../src/backend/app/services/auth_service.py)).
  Para CRUD simple, el router puede llamar directo al repositorio.
- **Repository**: **todas** las consultas a la DB. Hereda de
  [BaseRepository](../src/backend/app/repositories/base.py), que ya trae
  `get_by_id`, `get_all`, `create`, `update`, `delete` genéricos.
- **Model**: la definición de la tabla (columnas, relaciones, índices).

**Por qué el patrón Repository:** centraliza el acceso a datos. Si mañana cambia
una query, se toca un solo lugar. Y permite el truco más importante del proyecto:
el pipeline de agentes depende de una **abstracción** de repositorio, no del ORM,
así que en tests se reemplaza por un repo falso sin tocar la DB (ver
[§8](#8-el-pipeline-de-agentes-ia)).

**Schemas (DTOs) vs Models:** los `schemas/` (Pydantic) son lo que entra y sale
por HTTP; los `models/` (SQLAlchemy) son las tablas. Están **separados a
propósito**: la forma en que guardás datos no tiene por qué ser la forma en que
los exponés. Cambiar una columna interna no rompe el contrato de la API.

**Inyección de dependencias:** FastAPI inyecta la sesión de DB y el usuario
autenticado vía `Depends`. En [dependencies.py](../src/backend/app/dependencies.py)
hay atajos (`CurrentUser`, `DbSession`, `BearerToken`) para no repetir
`Depends(...)` en cada firma.

---

## 7. Recetas backend: cómo agregar cosas

### Cómo agregar un endpoint nuevo

1. Si toca datos, agregá el método de query en el repositorio correspondiente
   (`repositories/x_repository.py`). Si es CRUD simple, ya existe en `BaseRepository`.
2. Definí los schemas de entrada/salida en `schemas/` (Pydantic).
3. En el router de `api/v1/`, agregá la función con su decorador:

```python
@router.get("/mi-ruta", summary="Qué hace")
async def mi_endpoint(
    current_user: dict = Depends(get_current_user),  # exige login
    db: AsyncSession = Depends(get_db),               # inyecta sesión
) -> dict:
    repo = MiRepositorio(db)
    return await repo.mi_metodo()
```

4. Si el router es nuevo (no existe el archivo), registralo en
   [main.py](../src/backend/app/main.py) con `app.include_router(...)`.

**Por qué así:** el decorador define ruta + doc de Swagger; los `Depends`
resuelven auth y DB antes de entrar a tu código; el repositorio aísla el SQL.

### Cómo agregar un modelo y su migración

1. Creá la clase en `models/` heredando de `Base, IDMixin, TimestampMixin` (te dan
   `id`, `created_at`, `updated_at` gratis):

```python
class MiTabla(Base, IDMixin, TimestampMixin):
    __tablename__ = "mi_tabla"
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
```

2. Importá el modelo donde Alembic lo vea (en `db/base.py` o el `models/__init__`).
3. Generá la migración (usa la URL **sync**, por eso existe `DATABASE_URL_SYNC`):

```bash
docker compose exec backend alembic revision --autogenerate -m "agrega mi_tabla"
```

4. Revisá el archivo generado en `alembic/versions/` (autogenerate no es perfecto).
5. Aplicá: `docker compose exec backend alembic upgrade head`.

> El contenedor backend corre `alembic upgrade head` al arrancar, así que las
> migraciones pendientes se aplican solas al hacer `up`.

### Cómo agregar un repositorio

Heredá de `BaseRepository[TuModelo]` y agregá solo los métodos específicos:

```python
class MiRepositorio(BaseRepository[MiTabla]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, MiTabla)

    async def get_by_nombre(self, nombre: str) -> MiTabla | None:
        result = await self._db.execute(
            select(MiTabla).where(MiTabla.nombre == nombre)
        )
        return result.scalar_one_or_none()
```

Exportalo en [repositories/__init__.py](../src/backend/app/repositories/__init__.py).

---

## 8. El pipeline de agentes IA

Es el corazón del sistema. Vive en [agents/](../src/backend/app/agents/).

### Por qué 4 agentes y no uno solo

Un único LLM que "analice + busque + valide + redacte" todo de una excede su
límite lógico y **alucina** (inventa productos, precios, leyes). Separar en 4
pasos acota la responsabilidad de cada uno y, clave, permite meter **validación
determinística entre pasos** (filtros SQL, reglas legales) que un LLM no puede
garantizar.

### Los 4 agentes

| # | Agente | Entrada | Salida | Usa LLM? |
|---|---|---|---|---|
| 1 | [Analyzer](../src/backend/app/agents/analyzer_agent.py) | Contexto del agricultor | Resumen estructurado + texto para RAG | Sí |
| 2 | [Researcher](../src/backend/app/agents/researcher_agent.py) | Resumen del paso 1 | Productos candidatos de la DB | No (solo DB) |
| 3 | [Legal Validator](../src/backend/app/agents/legal_validator_agent.py) | Candidatos + regulaciones | Productos válidos / descartados | Reglas + LLM |
| 4 | [Synthesizer](../src/backend/app/agents/synthesizer_agent.py) | Productos válidos | 3 recomendaciones con texto | Sí (solo texto) |

El [orquestador](../src/backend/app/agents/orchestrator.py) los corre en orden,
acumulando todo en un [PipelineState](../src/backend/app/agents/state.py) y
notificando el progreso con un callback tras cada paso.

### La regla anti-alucinación (lo más importante)

> Los datos factuales (nombre, precio, ingrediente, toxicidad, LMR) **siempre**
> salen de la base de datos. El LLM **solo** genera texto interpretativo
> (justificación, ventajas, riesgos, recomendación de uso).

Se ve en el [synthesizer](../src/backend/app/agents/synthesizer_agent.py): primero
arma el payload con los datos reales de la DB, y solo si un campo viene vacío usa
la estimación del LLM como último recurso. Esto es lo que hace **confiable** un
sistema de recomendación agroquímica.

### El validador legal híbrido (por qué 2 fases)

El agente 3 valida en dos fases:

1. **Determinística (reglas):** compara el ingrediente activo del producto contra
   las sustancias prohibidas de cada regulación. Si coincide, **descarta sin
   gastar LLM**. Es barato, rápido y 100% confiable.
2. **Interpretativa (LLM):** a los sobrevivientes les pasa las regulaciones como
   datos y el LLM interpreta casos que las reglas no cubren.

**Política conservadora:** ante duda, descartar. Si el LLM no confirma
explícitamente que un producto es válido, se descarta. Es un dominio con
responsabilidad legal real, así que se prefiere recomendar de menos que de más.

### El LLMClient (patrón Strategy/Adapter)

Los agentes no hablan con OpenRouter directamente. Dependen de la interfaz
abstracta [LLMClient](../src/backend/app/services/llm_client.py):

- `OpenRouterLLMClient`: implementación real (production).
- `MockLLMClient`: respuestas fijas para tests, sin gastar tokens ni red.

**Por qué:** así se cumple el Principio de Inversión de Dependencias. El pipeline
se testea con el mock, y si mañana se cambia de proveedor de LLM, se escribe otra
implementación sin tocar los agentes.

`complete_json()` hace algo importante: le inyecta al prompt el JSON schema
esperado, limpia la respuesta (a veces viene con markdown), la valida contra un
modelo Pydantic, y **reintenta con backoff** si el JSON no es válido.

### Cómo agregar o modificar un agente

1. El prompt va en `agents/prompts/` (separá `SYSTEM_PROMPT` de
   `USER_PROMPT_TEMPLATE`).
2. El schema de salida del LLM va en `schemas/` (un `BaseModel` de Pydantic).
3. La función del agente recibe sus dependencias por parámetro (LLM, repos) y
   devuelve su schema. Ejemplo mínimo:

```python
async def mi_agente(context, llm: LLMClient) -> MiSalida:
    prompt = USER_PROMPT_TEMPLATE.format(...)
    return await llm.complete_json(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt,
        response_model=MiSalida,   # Pydantic valida la respuesta
    )
```

4. Enganchalo en el [orquestador](../src/backend/app/agents/orchestrator.py) como
   un paso más, marcando el step y llamando el callback de progreso.

---

## 9. Procesamiento asíncrono: Celery + SSE

### Por qué Celery

El pipeline tarda demasiado para una petición HTTP. Celery corre la tarea en un
**worker separado** ([tasks.py](../src/backend/app/workers/tasks.py)). El endpoint
solo encola (`generate_recommendation.delay(ticket_id)`) y responde 202.

Detalle técnico: la tarea Celery es **síncrona**, pero el pipeline es **async**.
Por eso la tarea hace `asyncio.run(...)` para abrir un event loop dentro del
worker. Y por eso `get_db_session()` crea un engine local: evita el error
"Future attached to a different loop" entre el loop de Celery y el global.

Config del worker en [celery_app.py](../src/backend/app/workers/celery_app.py):
`prefetch_multiplier=1` (una tarea a la vez, porque son largas) y
`max_tasks_per_child=50` (recicla el proceso para evitar fugas de memoria).

### Por qué SSE y no WebSockets

El progreso fluye en **una sola dirección**: del servidor al cliente. WebSocket es
bidireccional y gastaría recursos sin necesidad. Server-Sent Events (SSE) es la
herramienta correcta para streaming unidireccional. Fue una decisión explícita de
diseño (WebSockets fue rechazado).

### El flujo del progreso

```
Worker (tasks.py)                Redis              Backend (recommendations.py)      Frontend
   publish_progress()  ---->  canal pub/sub  ---->  endpoint /stream (SSE)     ---->  EventSource
```

El worker publica cada cambio de paso en un canal Redis
(`recommendation_progress:{ticket_id}`). El endpoint
`/recommendations/stream/{ticket_id}` se suscribe a ese canal y reenvía cada
mensaje al navegador como evento SSE.

> **Gap conocido (importante):** el backend expone SSE, pero la pantalla actual
> [CaseWizardStep3.tsx](../src/frontend/src/features/wizard/CaseWizardStep3.tsx)
> consume el progreso por **polling** (un `GET` al detalle cada segundo), no por
> el stream SSE. Ambos caminos funcionan; el polling es el que está cableado en la
> UI. Si vas a tocar esto, tenelo presente.

---

## 10. Autenticación

### Por qué Supabase + fallback local

La auth primaria es **Supabase Auth** (gestiona credenciales, tokens, confirmación
de email). Pero hay un **fallback local** (JWT firmado con `JWT_SECRET` + bcrypt)
para desarrollo cuando Supabase no está configurado, o para usuarios viejos
migrados. Toda esa lógica vive en
[auth_service.py](../src/backend/app/services/auth_service.py).

### El flujo de login (es por cédula, no por email)

1. El usuario ingresa **cédula + contraseña**.
2. El backend resuelve el email asociado a esa cédula en la tabla `users`.
3. Intenta autenticar en Supabase con ese email.
4. Si Supabase falla con 401, prueba el hash bcrypt local (compatibilidad).
5. Devuelve un JWT (de Supabase o local).

El perfil de negocio (nombre, cédula, teléfono) vive en **nuestra** tabla `users`,
ligado a Supabase por `auth_user_id`. Supabase guarda solo las credenciales.

### Cómo proteger un endpoint

Agregá la dependencia `get_current_user` (o el atajo `CurrentUser`):

```python
@router.get("/privado")
async def privado(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user["id"]}
```

La validación del token (local o Supabase) está en
[security.py](../src/backend/app/core/security.py) y
[auth_service.py](../src/backend/app/services/auth_service.py). En el frontend, la
ruta se protege con [ProtectedRoute](../src/frontend/src/app/ProtectedRoute.tsx),
que exige `isAuthenticated` **y** `token`.

---

## 11. Base de datos, migraciones y seeding

### Por qué dos DATABASE_URL

- `DATABASE_URL` (asyncpg): la usa la app en runtime (async).
- `DATABASE_URL_SYNC` (psycopg2): la usa **solo** Alembic, porque las migraciones
  son síncronas.

Es la misma base (Supabase), con dos drivers distintos.

### Tablas clave

`users`, `zones`, `products` (con embedding de 768 dims), `distributors`,
`recommendations` + `recommendation_products`, `regulations`, `lmrs`
(~8.500 límites de residuos), `audit_log`. Ver
[models/](../src/backend/app/models/) y el diseño en
[database/schema.dbml](database/schema.dbml).

### Migraciones (Alembic)

```bash
alembic revision --autogenerate -m "descripción"   # generar
alembic upgrade head                                # aplicar
alembic downgrade -1                                # revertir una
```

**Por qué:** versionan el esquema. Cada cambio de modelo se acompaña de su
migración para que todos los entornos converjan al mismo estado.

### Seeding y embeddings

[seed.py](../src/backend/app/db/seed.py) carga productos, distribuidores y
regulaciones. Genera los embeddings con Gemini (`text-embedding-004`,
`task_type="RETRIEVAL_DOCUMENT"`), truncados a 768 dims, que es lo que espera la
columna `Vector(768)`.

```bash
docker compose exec backend python -m app.db.seed
```

**Por qué pgvector:** permite búsqueda por similitud semántica (no solo por texto
exacto), que es lo que usa el agente investigador para encontrar productos
relevantes al caso.

---

## 12. Frontend en profundidad

### Estado: React Query vs Zustand (por qué dos)

Esta es la decisión clave del frontend:

- **React Query** maneja el **estado del servidor**: todo lo que viene de la API
  (zonas, recomendaciones, catálogos). Se encarga de fetching, cache, refetch y
  estados de carga/error. No guardás esos datos a mano.
- **Zustand** maneja el **estado del cliente**: lo que no vive en el servidor
  (token de sesión en [authStore](../src/frontend/src/stores/authStore.ts), datos
  del wizard en [wizardStore](../src/frontend/src/stores/wizardStore.ts)).

**Por qué no usar uno solo:** mezclar datos del servidor en un store global obliga
a sincronizar a mano (cuándo refrescar, invalidar, etc.), que es justo lo que
React Query resuelve. Cada herramienta hace lo que mejor sabe.

Ambos stores usan `persist` (localStorage) para sobrevivir recargas. Por eso, al
cerrar sesión, [AppLayout](../src/frontend/src/features/layout/AppLayout.tsx) llama
`queryClient.clear()` además de limpiar el store: si no, datos del usuario anterior
quedarían cacheados.

### Routing y rutas protegidas

[router.tsx](../src/frontend/src/app/router.tsx) define las rutas. Las privadas
cuelgan de [ProtectedRoute](../src/frontend/src/app/ProtectedRoute.tsx), que
redirige a `/login` si no hay sesión válida. Las públicas son `/login` y
`/register`.

### Consumo de API y manejo de errores

Las peticiones usan `axios` con el header `Authorization: Bearer ${token}`. Los
errores de la API (que vienen con formato de FastAPI) se traducen a mensajes
legibles con [getApiErrorMessage](../src/frontend/src/lib/apiError.ts).

### Formularios

react-hook-form + zod. El schema zod (ej.
[wizard/schemas.ts](../src/frontend/src/features/wizard/schemas.ts)) valida y a la
vez **tipa** el formulario. `zodResolver` conecta ambos.

### El wizard de 4 pasos

Es el flujo principal ([features/wizard/](../src/frontend/src/features/wizard/)):

1. **Step1**: datos del caso (cultivo, finca/zona, problema, presupuesto).
2. **Confirm**: resumen antes de enviar; aquí se hace el `POST /request`.
3. **Step3**: muestra el progreso y luego la tabla comparativa.
4. **Step4**: distribuidores.

El [recommendationMapper.ts](../src/frontend/src/features/wizard/recommendationMapper.ts)
transforma la respuesta cruda del backend en las filas de la tabla comparativa.
Es solo transformación de datos, sin red, así que es fácil de testear (ver su
`.test.ts`).

---

## 13. Recetas frontend: cómo agregar cosas

### Cómo agregar una página nueva

1. Creá el componente en `features/<mi-feature>/MiPagina.tsx`.
2. Registrá la ruta en [router.tsx](../src/frontend/src/app/router.tsx). Si es
   privada, ponela dentro del bloque de `ProtectedRoute`.
3. Si aparece en el menú, agregá el item en
   [AppLayout](../src/frontend/src/features/layout/AppLayout.tsx).

### Cómo consumir un endpoint (lectura)

```tsx
const { data, isLoading } = useQuery({
  queryKey: ['mi-recurso', id],            // identifica el cache
  queryFn: async () => {
    const res = await axios.get(`/api/v1/mi-recurso/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    return res.data
  },
  enabled: !!token,                         // no dispara sin sesión
})
```

### Cómo enviar datos (escritura)

```tsx
const mutation = useMutation({
  mutationFn: (payload) => axios.post('/api/v1/mi-recurso', payload, {
    headers: { Authorization: `Bearer ${token}` },
  }),
  onSuccess: () => queryClient.invalidateQueries({ queryKey: ['mi-recurso'] }),
})
```

**Por qué `invalidateQueries`:** tras un cambio, le dice a React Query que los
datos cacheados quedaron viejos y los vuelva a pedir. Así la UI refleja el cambio
sin recargar.

### Cómo agregar un formulario

```tsx
const schema = z.object({ nombre: z.string().min(1, 'Requerido') })
const { register, handleSubmit, formState: { errors } } =
  useForm({ resolver: zodResolver(schema) })
```

---

## 14. Testing

### Backend (pytest)

```bash
docker compose exec backend pytest                      # todo
docker compose exec backend pytest ruta/test_x.py::test_y  # uno
docker compose exec backend pytest --cov=app            # con cobertura
```

`asyncio_mode = "auto"` permite tests async sin decorador. La cobertura mínima
configurada es 80% ([pyproject.toml](../src/backend/pyproject.toml)).

**Cómo testear el pipeline sin gastar tokens:** usá `MockLLMClient` y
`FakeProductRepository`. Como los agentes dependen de abstracciones, les inyectás
los falsos y testeás la lógica sin red ni DB.

### Frontend (vitest)

```bash
docker compose exec -T frontend npm run test           # correr
docker compose exec -T frontend npm run test:coverage  # cobertura
```

Lo más fácil de testear es la lógica pura como
[recommendationMapper.ts](../src/frontend/src/features/wizard/recommendationMapper.ts),
que no toca red.

---

## 15. Calidad de código y convenciones

### Herramientas

| Área | Comando | Para qué |
|---|---|---|
| Backend lint+format | `ruff check . && ruff format .` | Estilo y bugs comunes |
| Backend tipos | `mypy app` | Type checking |
| Frontend lint | `npm run lint` | ESLint |
| Frontend tipos | `npm run typecheck` | `tsc --noEmit` |

### Convenciones de comentarios

> Convención del proyecto (importante, se aplica siempre):
> - Comentarios de **una línea**, concisos.
> - `#` en Python, `//` en TypeScript. Nada de `"""..."""` como comentario interno
>   (los docstrings son solo para describir funciones/clases).
> - **No** usar separadores decorativos (`# ====`, `# ----`).
> - Usar solo `-`, **nunca** el guion largo.
> - El comentario explica el **porqué**, no repite el qué.

### Nomenclatura

- Backend: campos en **español** alineados con los datos del SFE
  (`nombre_comercial`, `ingrediente_activo`). PKs enteras autoincrementales.
- Frontend: componentes en PascalCase, hooks/utilidades en camelCase.

---

## 16. Recetario rápido

| Quiero... | Dónde / cómo |
|---|---|
| Levantar todo | `docker compose up -d` |
| Ver por qué falla el pipeline | `docker compose logs -f worker` |
| Agregar un endpoint | [§7](#7-recetas-backend-cómo-agregar-cosas) -> router + repo |
| Agregar una tabla | [§7](#7-recetas-backend-cómo-agregar-cosas) -> model + migración |
| Cambiar un prompt de un agente | [agents/prompts/](../src/backend/app/agents/prompts/) |
| Cambiar la regla de precios | [prompts/synthesizer.py](../src/backend/app/agents/prompts/synthesizer.py) |
| Agregar una página | [§13](#13-recetas-frontend-cómo-agregar-cosas) -> componente + router |
| Cambiar la tabla comparativa | [recommendationMapper.ts](../src/frontend/src/features/wizard/recommendationMapper.ts) |
| Proteger un endpoint | `Depends(get_current_user)` |
| Recargar datos de seed | `docker compose exec backend python -m app.db.seed` |
| Crear migración | `alembic revision --autogenerate -m "..."` |
| Ver la API | `http://localhost:8000/docs` |

---

## 17. Gotchas: cosas que confunden

- **Dos `DATABASE_URL`:** una async (runtime) y una sync (Alembic). No es un error,
  es a propósito ([§11](#11-base-de-datos-migraciones-y-seeding)).
- **`statement_cache_size=0`** en [session.py](../src/backend/app/db/session.py):
  necesario por el pooler de Supabase (PgBouncer en modo transacción), sin esto
  asyncpg falla con `DuplicatePreparedStatementError`.
- **bcrypt fijado en 4.0.1:** passlib es incompatible con bcrypt >= 4.1. No lo
  subas sin verificar.
- **SSE vs polling:** el backend tiene SSE pero la UI usa polling
  ([§9](#9-procesamiento-asíncrono-celery--sse)). No te confunda ver ambos.
- **`docker-compose.yml` no debe sobrescribir `DATABASE_URL`:** la DB es Supabase
  (viene del `.env`). Apuntarla a un `postgres` local rompe el arranque (la DB
  local ya no existe).
- **El `queryClient.clear()` en logout** es necesario: sin él, datos del usuario
  anterior quedan en cache tras cerrar sesión.
- **El dropdown de cultivos** sale de la tabla `lmrs` (columna `cultivo`), no está
  hardcodeado; se precarga en memoria al arrancar el backend
  ([catalogs.py](../src/backend/app/api/v1/catalogs.py)).

---

> ¿Falta algo o un "cómo hago X" no está cubierto? Agregalo aquí mismo: este
> documento debe mantenerse alineado con `/src`. Si el código y esta guía
> difieren, gana el código y hay que actualizar la guía.
