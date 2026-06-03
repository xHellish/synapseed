# SynapSeed — Plan de Implementación Integral (Caso 2)

Plan maestro que cubre las 5 etapas de la asignación: prototipado UX, diseño de frontend, diseño de backend + datos, MVP y demo.

## Decisions Resolved ✅

- **TailwindCSS:** v4 (CSS-first, sin `tailwind.config.js`)
- **Cola de tareas MVP:** Celery + Redis
- **Orquestación IA:** LangGraph 1.2 + LangChain 1.x
- **Stripe:** Diseño completo, implementación como mock/stub en MVP
- **Identidad visual:** Paleta verde (a definir sistema de diseño completo)
- **Prototipo UX:** No existe aún en Figma — se creará durante la implementación
- **Datos semilla:** Productos reales del SFE disponibles públicamente
- **Regulaciones SFE/MAG:** Accesibles públicamente, se investigarán
- **Dominio:** URLs de AWS para el MVP (sin dominio propio)



---

## Proposed Changes

La estructura final del repositorio será:

```
SynapSeed/
├── frontend/                # React + Vite + TypeScript
├── backend/                 # FastAPI + Python
├── Docs/                    # Documentación del proyecto
│   ├── Caso2_asignacion_entrega.md
│   ├── Spec_validada.md
│   ├── arquitectura/        # Diagramas y documentos de diseño
│   └── database/            # DBML, ERD, scripts
├── .github/
│   └── workflows/           # CI/CD pipelines
├── docker-compose.yml       # Desarrollo local
├── README.md                # Documentación central
└── .gitignore
```

---

### Etapa 1 — Prototipado y Refinamiento UX (5%)

> [!NOTE]
> Esta etapa requiere trabajo manual del equipo (UX Testing con 4 estudiantes). Aquí se documenta qué debe producirse.

#### Entregables esperados

| Entregable | Formato | Ubicación |
|---|---|---|
| Prototipo interactivo de la ventana principal | Figma / Maze | Link en `Docs/ux/` |
| Tareas definidas para UX Testing | Markdown | `Docs/ux/testing_tasks.md` |
| Resultados del UX Testing (4 participantes) | Markdown + capturas | `Docs/ux/testing_results.md` |
| Problemas detectados y correcciones aplicadas | Markdown | `Docs/ux/corrections.md` |
| Métricas básicas de usabilidad | Tabla | Incluido en `testing_results.md` |

#### Flujo principal a prototipar

El flujo de recomendación de agroquímicos es el flujo principal:
1. **Formulario de plan:** Agricultor ingresa cultivo, hectáreas, etapa fenológica, ubicación
2. **Estado de procesamiento:** Pantalla con progreso en tiempo real (SSE) mostrando cada agente
3. **Resultado:** Recomendación con productos, dosis, costos, alternativas y validación legal

---

### Etapa 2 — Diseño del Frontend (10%)

#### [NEW] `frontend/` — Proyecto React + Vite + TypeScript

##### Tech Stack y Versiones

| Tecnología | Versión | Justificación |
|---|---|---|
| React | 19.x | Última estable, soporte completo de hooks y Suspense |
| TypeScript | 5.8.x | Tipado estático, mejor DX y mantenibilidad |
| Vite | 6.x | Build tool ultra-rápido, HMR instantáneo, mejor que CRA/Webpack |
| Zustand | 5.x | Estado cliente ligero (~1KB), API simple, sin boilerplate |
| TanStack Query | 5.x | Cache de servidor, refetch automático, mutations optimistas |
| TailwindCSS | 4.x | CSS-first config, modern, tree-shaking nativo |
| shadcn/ui | Latest | Componentes copiados al proyecto, control total, basados en Radix |
| React Router | 7.x | Routing declarativo con data loaders |

##### Estructura de carpetas

```
frontend/
├── public/
├── src/
│   ├── app/                        # Setup global
│   │   ├── App.tsx                 # Root con providers
│   │   ├── main.tsx                # Entry point
│   │   ├── router.tsx              # Definición de rutas
│   │   └── providers.tsx           # QueryClient, theme, auth
│   │
│   ├── components/                 # Componentes compartidos
│   │   └── ui/                     # shadcn/ui (generados por CLI)
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── dialog.tsx
│   │       ├── input.tsx
│   │       └── ...
│   │
│   ├── features/                   # Módulos por dominio
│   │   ├── auth/
│   │   │   ├── components/         # LoginForm, RegisterForm
│   │   │   ├── hooks/              # useAuth, useLogin
│   │   │   ├── services/           # authService.ts (API calls)
│   │   │   └── types/              # Auth DTOs
│   │   │
│   │   ├── recommendations/
│   │   │   ├── components/         # PlanForm, ProgressTracker, ResultCard
│   │   │   ├── hooks/              # useCreateRecommendation, useSSEStream
│   │   │   ├── services/           # recommendationService.ts
│   │   │   └── types/
│   │   │
│   │   ├── dashboard/
│   │   │   ├── components/         # StatsOverview, RecentActivity
│   │   │   └── hooks/
│   │   │
│   │   └── products/
│   │       ├── components/         # ProductCatalog, ProductDetail
│   │       └── hooks/
│   │
│   ├── hooks/                      # Hooks globales compartidos
│   │   ├── useSSE.ts               # Hook genérico SSE
│   │   └── useDebounce.ts
│   │
│   ├── lib/                        # Utilidades
│   │   ├── api.ts                  # Axios instance + interceptors
│   │   ├── utils.ts                # Helpers generales
│   │   └── cn.ts                   # clsx + tailwind-merge
│   │
│   ├── stores/                     # Zustand (estado cliente)
│   │   ├── authStore.ts            # Token, user, sesión
│   │   ├── uiStore.ts              # Sidebar, theme, notificaciones
│   │   └── recommendationStore.ts  # Estado local del wizard
│   │
│   ├── types/                      # Tipos globales
│   │   ├── api.ts                  # Tipos de respuesta API
│   │   └── models.ts               # Modelos de dominio
│   │
│   └── styles/
│       └── globals.css             # TailwindCSS v4 imports + tokens
│
├── index.html
├── vite.config.ts
├── tsconfig.json
├── vitest.config.ts
├── components.json                 # shadcn/ui config
├── package.json
└── playwright.config.ts
```

##### Patrones arquitectónicos del frontend

**1. Separación de estado cliente/servidor:**
- **Zustand** → estado de UI, auth tokens, preferencias (client state)
- **TanStack Query** → datos del API, cache, refetch, mutations (server state)
- Regla: **nunca** duplicar datos del API en Zustand

**2. Feature-based modules:**
- Cada feature es auto-contenida (components, hooks, services, types)
- Comunicación entre features solo via stores globales o React Query cache

**3. Compound Components:**
- shadcn/ui ya sigue este patrón (Dialog.Trigger, Dialog.Content, etc.)
- Componentes complejos propios seguirán el mismo patrón

##### Sistema de diseño y tokens CSS

```css
/* globals.css — TailwindCSS v4 */
@import "tailwindcss";

@theme {
  /* Colores primarios — Verdes agrícolas */
  --color-primary-50: #f0fdf4;
  --color-primary-100: #dcfce7;
  --color-primary-500: #22c55e;
  --color-primary-600: #16a34a;
  --color-primary-700: #15803d;
  --color-primary-900: #14532d;

  /* Colores secundarios — Tierra/marrón */
  --color-secondary-50: #fefce8;
  --color-secondary-500: #eab308;
  --color-secondary-700: #a16207;

  /* Colores de estado */
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;

  /* Tipografía */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;

  /* Espaciado base */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;

  /* Border radius */
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
}
```

##### Seguridad del frontend

| Aspecto | Implementación |
|---|---|
| **Autenticación** | JWT via API → access token en Zustand (memoria), refresh token en HttpOnly cookie |
| **Autorización** | Route guards + role-based rendering (farmer, admin, distributor) |
| **Token expiry** | Access token 15 min, refresh token 7 días, auto-refresh via interceptor |
| **Sesiones** | Zustand persist (localStorage) para datos no sensibles; tokens en memoria |
| **OWASP** | CSP headers via CloudFront, XSS sanitization, CSRF con tokens |
| **Input validation** | Zod schemas compartidos con el backend para validación client-side |
| **Data masking** | Datos sensibles (cédula, teléfono) enmascarados en UI por defecto |

##### SSE (Server-Sent Events) — Consumo en React

```typescript
// hooks/useSSE.ts
export function useRecommendationSSE(ticketId: string | null) {
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!ticketId) return
    const es = new EventSource(`${API_URL}/recommendations/${ticketId}/events`)

    es.addEventListener('status_update', (e) => {
      const data = JSON.parse(e.data)
      queryClient.setQueryData(['recommendation', ticketId], (old) => ({
        ...old, status: data.status, message: data.message
      }))
    })

    es.addEventListener('completed', (e) => {
      const data = JSON.parse(e.data)
      queryClient.setQueryData(['recommendation', ticketId], data.result)
      queryClient.invalidateQueries({ queryKey: ['recommendations'] })
      es.close()
    })

    es.onerror = () => { es.close() /* fallback to polling */ }
    return () => es.close()
  }, [ticketId])
}
```

##### Estrategia de testing del frontend

| Tipo | Herramienta | Cobertura mínima | Enfoque |
|---|---|---|---|
| **Unit** | Vitest + React Testing Library | 70% | Hooks, stores, utilidades, lógica |
| **Component** | Vitest + RTL | 70% | Componentes interactivos, formularios |
| **E2E** | Playwright | Flujos críticos | Login, crear recomendación, ver resultado |
| **Visual** | Playwright screenshots | Páginas clave | Regresión visual |

##### Performance y optimización

- **Code splitting:** `React.lazy()` + `Suspense` por ruta
- **Manual chunks:** vendor, query, ui separados en `vite.config.ts`
- **Images:** WebP/AVIF, `loading="lazy"`, optimización via Vite plugin
- **Lists:** `@tanstack/react-virtual` para catálogos de productos largos
- **Cache:** `staleTime: 5min` en React Query para datos que cambian poco
- **Memoization:** `React.memo` en componentes de lista, `useMemo` para cómputos

##### CI/CD del frontend

```mermaid
graph LR
    A[Push a main] --> B[GitHub Actions]
    B --> C[npm ci]
    C --> D[Lint + TypeCheck]
    D --> E[Vitest Unit Tests]
    E --> F[Vite Build]
    F --> G[Deploy S3]
    G --> H[Invalidar CloudFront]
```

Pipeline: lint → typecheck → test → build → sync S3 → invalidate CloudFront cache.

---

### Etapa 3 — Diseño del Backend y Data (20%)

#### [NEW] `backend/` — FastAPI + Python

##### Tech Stack y Versiones

| Tecnología | Versión | Justificación |
|---|---|---|
| Python | 3.12+ | Performance mejorado, better typing, task groups |
| FastAPI | 0.115.x | Framework async moderno, auto-docs OpenAPI, Pydantic nativo |
| SQLAlchemy | 2.0.x | ORM async con asyncpg, type hints, expression language |
| Alembic | 1.14.x | Migraciones versionadas, auto-generate desde modelos |
| Pydantic | 2.10.x | Validación rápida (Rust core), DTOs, settings |
| LangChain | 1.x | Framework base para agentes e integración con LLMs |
| LangGraph | 1.2.x | Orquestación de agentes multi-step con estado (reemplaza SequentialChain) |
| pgvector | 0.8.x | Búsqueda semántica vectorial en PostgreSQL |
| Celery | 5.4.x | Cola de tareas distribuida para procesamiento async |
| Redis | 7.x | Broker para Celery + cache + SSE pub/sub |
| asyncpg | 0.30.x | Driver PostgreSQL async de alto rendimiento |
| pytest | 8.x | Testing framework |

##### Arquitectura en capas

```mermaid
graph TD
    subgraph "API Layer"
        R[Routers / Endpoints]
    end

    subgraph "Service Layer"
        S[Business Services]
        O[Agent Orchestrator]
    end

    subgraph "Data Access Layer"
        RP[Repositories]
        VS[Vector Store]
    end

    subgraph "Infrastructure"
        DB[(PostgreSQL + pgvector)]
        Q[Redis / Celery Queue]
        LLM[Gemini API]
    end

    R --> S
    S --> RP
    S --> O
    O --> A1[Analyzer Agent]
    O --> A2[Researcher Agent]
    O --> A3[Validator Agent]
    O --> A4[Synthesizer Agent]
    A2 --> VS
    A1 & A2 & A3 & A4 --> LLM
    RP --> DB
    VS --> DB
    R --> Q
    Q --> O
```

| Capa | Responsabilidad | Restricciones |
|---|---|---|
| **API (Routers)** | Recibir HTTP, validar input, devolver response | Sin lógica de negocio, sin acceso directo a DB |
| **Services** | Lógica de negocio, coordinación entre repos | Sin conocimiento de HTTP, sin queries directas |
| **Repositories** | Acceso a datos, queries SQL/ORM | Sin lógica de negocio, retorna modelos |
| **Agents** | Orquestación IA, prompts, tools | Aislados, testables con mocks |
| **Workers** | Procesamiento en background | Consume cola, ejecuta pipeline de agentes |

##### Estructura de carpetas del backend

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # App factory, startup/shutdown
│   ├── config.py                   # pydantic-settings
│   ├── dependencies.py             # DI (get_db, get_current_user)
│   │
│   ├── api/v1/                     # Routers
│   │   ├── router.py               # Agrega todos los sub-routers
│   │   ├── auth.py                 # POST /login, /register, /refresh
│   │   ├── recommendations.py      # POST /, GET /{id}, GET /{id}/events (SSE)
│   │   ├── products.py             # GET /, GET /{id}, GET /search
│   │   └── users.py                # GET /me, PUT /me
│   │
│   ├── core/                       # Cross-cutting
│   │   ├── security.py             # JWT, hashing, OAuth2
│   │   ├── exceptions.py           # Custom exceptions + handlers
│   │   ├── middleware.py           # CORS, logging, rate limiting
│   │   └── events.py              # SSE helpers
│   │
│   ├── models/                     # SQLAlchemy ORM
│   │   ├── base.py                 # DeclarativeBase
│   │   ├── user.py
│   │   ├── recommendation.py
│   │   ├── product.py
│   │   ├── distributor.py
│   │   ├── regulation.py
│   │   └── audit.py
│   │
│   ├── schemas/                    # Pydantic DTOs
│   │   ├── user.py                 # UserCreate, UserResponse
│   │   ├── recommendation.py       # FarmerPlan, RecommendationResult
│   │   ├── product.py
│   │   └── common.py              # Pagination, ErrorResponse
│   │
│   ├── services/                   # Lógica de negocio
│   │   ├── auth_service.py
│   │   ├── recommendation_service.py
│   │   ├── product_service.py
│   │   └── notification_service.py
│   │
│   ├── repositories/              # Acceso a datos
│   │   ├── base.py                # GenericRepository[T]
│   │   ├── user_repo.py
│   │   ├── recommendation_repo.py
│   │   └── product_repo.py        # Incluye semantic_search()
│   │
│   ├── agents/                    # Orquestación IA
│   │   ├── orchestrator.py        # Pipeline secuencial
│   │   ├── analyzer_agent.py      # Agente Analizador de Contexto
│   │   ├── researcher_agent.py    # Agente Investigador (RAG)
│   │   ├── validator_agent.py     # Agente Validador Legal
│   │   ├── synthesizer_agent.py   # Agente Sintetizador
│   │   ├── prompts/               # Templates de prompts
│   │   │   ├── analyzer.py
│   │   │   ├── researcher.py
│   │   │   ├── validator.py
│   │   │   └── synthesizer.py
│   │   └── tools/                 # Herramientas de los agentes
│   │       ├── vector_search.py   # Búsqueda semántica
│   │       ├── product_lookup.py  # Consulta de productos
│   │       └── regulation_check.py # Verificación normativa
│   │
│   ├── workers/                   # Background processing
│   │   ├── celery_app.py          # Configuración Celery
│   │   └── recommendation_worker.py
│   │
│   └── db/                        # Database
│       ├── session.py             # Async engine + session factory
│       ├── seed.py                # Datos semilla
│       └── migrations/            # Alembic migrations
│
├── tests/
│   ├── conftest.py                # Fixtures globales
│   ├── unit/                      # Tests unitarios (agents, services)
│   ├── integration/               # Tests con DB real
│   └── api/                       # Tests de endpoints
│
├── alembic.ini
├── pyproject.toml
├── Dockerfile
├── Dockerfile.worker              # Imagen para el worker Celery
└── .env.example
```

##### Orquestación de los 4 Agentes IA (LangGraph)

El pipeline se implementa con **LangGraph** — un grafo de estados donde cada nodo es un agente y el estado se pasa entre nodos:

```mermaid
sequenceDiagram
    participant U as Usuario
    participant API as FastAPI
    participant Q as Redis/Celery
    participant W as Worker
    participant A1 as Agente Analizador
    participant A2 as Agente Investigador
    participant A3 as Agente Validador
    participant A4 as Agente Sintetizador
    participant DB as PostgreSQL
    participant LLM as Gemini API

    U->>API: POST /recommendations (plan)
    API->>DB: Crear ticket (status: pending)
    API->>Q: Encolar tarea
    API-->>U: 202 Accepted {ticket_id}

    Q->>W: Dequeue tarea
    W->>DB: status: processing

    W->>A1: farmer_plan
    A1->>LLM: Analizar contexto
    LLM-->>A1: contexto_estructurado
    W-->>U: SSE: "Analizando plan..."

    W->>A2: contexto_estructurado
    A2->>DB: Búsqueda semántica (pgvector)
    A2->>LLM: Seleccionar productos
    LLM-->>A2: productos_preseleccionados
    W-->>U: SSE: "Consultando catálogos..."

    W->>A3: productos + contexto
    A3->>DB: Consultar regulaciones SFE
    A3->>LLM: Validar legalidad
    LLM-->>A3: productos_validados
    W-->>U: SSE: "Verificando normativas..."

    W->>A4: productos_validados + contexto
    A4->>LLM: Generar recomendación
    LLM-->>A4: recomendación_final
    W-->>U: SSE: "Generando recomendación..."

    W->>DB: Guardar resultado (status: completed)
    W-->>U: SSE: "✅ Completado"
```

##### Detalle de cada agente

**1. Agente Analizador de Contexto (Agrónomo)**
- **Input:** Plan del agricultor (JSON con cultivo, hectáreas, etapa, ubicación)
- **Output:** Necesidades agronómicas estructuradas (tipo de protección necesaria, condiciones ambientales, restricciones)
- **LLM Role:** Extraer y categorizar necesidades con conocimiento agronómico
- **Tools:** Ninguno (solo razonamiento)

**2. Agente Investigador (RAG / Tool Use)**
- **Input:** Necesidades estructuradas del Agente 1
- **Output:** Lista de productos candidatos con justificación técnica
- **LLM Role:** Interpretar resultados de búsqueda, rankear productos
- **Tools:** `vector_search` (pgvector), `get_product_details` (DB lookup)

**3. Agente Validador Legal y de Seguridad**
- **Input:** Productos candidatos + contexto agronómico
- **Output:** Productos filtrados (solo los legalmente válidos)
- **LLM Role:** Cruzar productos con normativas, detectar incompatibilidades
- **Tools:** `check_sfe_registration`, `check_pimpa_eligibility`, `search_regulations`

**4. Agente Sintetizador (Recomendador)**
- **Input:** Productos validados + contexto + precios
- **Output:** Recomendación final estructurada (dosis, costo, alternativas)
- **LLM Role:** Optimizar selección por costo-beneficio, generar texto amigable
- **Tools:** Ninguno (solo razonamiento y formato)

##### Manejo de procesos largos y SSE

El flujo completo sigue el patrón `HTTP 202 Accepted + SSE`:

1. `POST /api/v1/recommendations/` → retorna `202` con `ticket_id`
2. Worker consume de la cola y ejecuta el pipeline
3. El worker publica eventos a Redis pub/sub durante cada paso
4. El endpoint `GET /api/v1/recommendations/{ticket_id}/events` es SSE — el frontend se suscribe
5. Estados posibles: `pending` → `analyzing` → `researching` → `validating` → `synthesizing` → `completed` | `failed`

##### Rate Limiting y Backoff

```python
# Estrategia para Gemini API Free Tier:
# - 15 RPM (requests per minute) para Gemini 1.5 Flash
# - Token bucket rate limiter en el worker
# - Exponential backoff en HTTP 429: 2s → 4s → 8s → 16s → 32s (max 5 retries)
# - La cola actúa como amortiguador natural
```

##### Autenticación y Seguridad del backend

| Aspecto | Implementación |
|---|---|
| **Auth flow** | `POST /auth/login` → JWT access token (15 min) + refresh token (7 días, HttpOnly cookie) |
| **Password hashing** | bcrypt via `passlib` |
| **JWT** | `python-jose` con HS256, claims: sub, role, exp, iat |
| **Authorization** | Dependency injection: `get_current_user`, role-based decorators |
| **CORS** | Middleware con origins específicos (no wildcard en prod) |
| **Rate limiting** | `slowapi` en endpoints públicos |
| **Secrets** | Variables de entorno via `pydantic-settings`, nunca en código |
| **Audit trail** | Tabla `audit_logs` con user, action, entity, IP, timestamp |
| **OWASP** | SQL injection (ORM), XSS (Pydantic validation), CSRF (SameSite cookies) |

##### Configuración de entornos

```python
# Tres entornos con pydantic-settings:
# .env.development  → DEBUG=true,  DB local, Redis local
# .env.staging      → DEBUG=false, RDS staging, ElastiCache
# .env.production   → DEBUG=false, RDS prod, ElastiCache, Stripe live
```

##### Observabilidad y monitoreo

| Aspecto | Herramienta MVP |
|---|---|
| **Logging** | `structlog` (JSON structured logs) |
| **Health check** | `GET /health` → DB connection + Redis connection + LLM API ping |
| **Metrics** | Request count, latency, agent pipeline duration (logs-based para MVP) |
| **Error tracking** | Structured error responses + audit logs |

---

### Base de Datos

#### Motor: PostgreSQL 16 + pgvector 0.8

**Justificación:**
- Relacional para datos transaccionales (users, recommendations, products)
- pgvector para búsqueda semántica de productos sin necesidad de un servicio separado (Pinecone, Weaviate)
- RDS en AWS para hosting gestionado

#### Esquema DBML

```dbml
Project SynapSeed {
  database_type: 'PostgreSQL'
  Note: 'Plataforma de recomendación de agroquímicos para agricultores costarricenses'
}

Table users {
  id uuid [pk, default: `gen_random_uuid()`]
  email varchar(255) [unique, not null]
  password_hash varchar(255) [not null]
  full_name varchar(255) [not null]
  farm_name varchar(255)
  province varchar(100)
  canton varchar(100)
  role varchar(50) [default: 'farmer', note: 'farmer | admin | distributor']
  pimpa_exempt boolean [default: false, note: 'Exención de impuestos PIMPA']
  is_active boolean [default: true]
  created_at timestamptz [default: `now()`]
  updated_at timestamptz [default: `now()`]

  indexes {
    email [unique]
    role
  }
}

Table recommendations {
  id uuid [pk, default: `gen_random_uuid()`]
  ticket_id varchar(100) [unique, not null, note: 'ID público para tracking']
  user_id uuid [ref: > users.id, not null]
  status varchar(50) [default: 'pending', note: 'pending|analyzing|researching|validating|synthesizing|completed|failed']
  crop_type varchar(100) [not null]
  hectares float [not null]
  phenological_stage varchar(100)
  location_province varchar(100)
  location_canton varchar(100)
  farmer_plan jsonb [not null, note: 'Plan original del agricultor']
  agent_context jsonb [note: 'Output del Agente Analizador']
  agent_research jsonb [note: 'Output del Agente Investigador']
  agent_validation jsonb [note: 'Output del Agente Validador']
  final_recommendation jsonb [note: 'Output del Agente Sintetizador']
  total_cost float
  currency varchar(10) [default: 'CRC']
  processing_time_ms int
  error_message text
  created_at timestamptz [default: `now()`]
  completed_at timestamptz

  indexes {
    ticket_id [unique]
    user_id
    status
    (user_id, created_at)
  }
}

Table products {
  id uuid [pk, default: `gen_random_uuid()`]
  name varchar(255) [not null]
  active_ingredient varchar(255)
  description text
  category varchar(100) [not null, note: 'herbicide|fungicide|insecticide|fertilizer|biocontrol']
  formulation varchar(100) [note: 'liquid|granular|powder|emulsion']
  concentration varchar(100)
  dosage_per_hectare varchar(255)
  application_method varchar(255)
  safety_interval_days int [note: 'Días antes de cosecha']
  price float
  currency varchar(10) [default: 'CRC']
  distributor_id uuid [ref: > distributors.id]
  sfe_registration varchar(50) [note: 'Número de registro SFE']
  sfe_status varchar(50) [default: 'active', note: 'active|expired|revoked']
  sfe_expiry_date date
  pimpa_eligible boolean [default: true]
  toxicity_band varchar(20) [note: 'I|II|III|IV - Banda toxicológica']
  embedding "vector(768)" [note: 'pgvector - Gemini embeddings']
  is_active boolean [default: true]
  created_at timestamptz [default: `now()`]
  updated_at timestamptz [default: `now()`]

  indexes {
    category
    sfe_registration
    distributor_id
    sfe_status
  }
}

Table distributors {
  id uuid [pk, default: `gen_random_uuid()`]
  name varchar(255) [not null]
  website varchar(500)
  region varchar(100)
  contact_email varchar(255)
  contact_phone varchar(50)
  is_active boolean [default: true]
  created_at timestamptz [default: `now()`]
}

Table recommendation_products {
  id uuid [pk, default: `gen_random_uuid()`]
  recommendation_id uuid [ref: > recommendations.id, not null]
  product_id uuid [ref: > products.id, not null]
  quantity float [not null]
  unit varchar(50) [not null, note: 'litros|kg|gramos']
  subtotal float
  dosage_applied varchar(255)
  justification text [note: 'Por qué se recomienda este producto']
  alternative_product_id uuid [ref: > products.id, note: 'Alternativa más económica']
  is_group_purchase boolean [default: false, note: 'Si aplica compra conjunta']
  created_at timestamptz [default: `now()`]

  indexes {
    recommendation_id
    product_id
  }
}

Table regulations {
  id uuid [pk, default: `gen_random_uuid()`]
  regulation_code varchar(100) [unique, not null]
  title varchar(500) [not null]
  issuing_body varchar(100) [not null, note: 'SFE|MAG|SENASA']
  description text
  prohibited_substances jsonb [note: 'Lista de sustancias prohibidas']
  restricted_crops jsonb [note: 'Restricciones por cultivo']
  effective_date date
  expiry_date date
  is_active boolean [default: true]
  source_url varchar(500)
  embedding "vector(768)" [note: 'Para búsqueda semántica de regulaciones']
  created_at timestamptz [default: `now()`]
  updated_at timestamptz [default: `now()`]

  indexes {
    regulation_code [unique]
    issuing_body
    is_active
  }
}

Table audit_logs {
  id uuid [pk, default: `gen_random_uuid()`]
  user_id uuid [ref: > users.id]
  action varchar(100) [not null, note: 'login|logout|create_recommendation|view_product|etc']
  entity_type varchar(100)
  entity_id uuid
  details jsonb
  ip_address varchar(45)
  user_agent text
  created_at timestamptz [default: `now()`]

  indexes {
    user_id
    action
    created_at
    (entity_type, entity_id)
  }
}

Table subscriptions {
  id uuid [pk, default: `gen_random_uuid()`]
  user_id uuid [ref: > users.id, not null]
  plan varchar(50) [not null, note: 'free|basic|premium']
  stripe_customer_id varchar(255)
  stripe_subscription_id varchar(255)
  status varchar(50) [default: 'active', note: 'active|cancelled|past_due']
  current_period_start timestamptz
  current_period_end timestamptz
  created_at timestamptz [default: `now()`]

  indexes {
    user_id
    stripe_customer_id
    status
  }
}
```

#### Diagrama Entidad-Relación

```mermaid
erDiagram
    users ||--o{ recommendations : "solicita"
    users ||--o{ audit_logs : "genera"
    users ||--o| subscriptions : "tiene"
    recommendations ||--o{ recommendation_products : "contiene"
    products ||--o{ recommendation_products : "incluido en"
    products }o--|| distributors : "distribuido por"
    recommendation_products }o--o| products : "alternativa"
```

#### Migraciones y versionamiento

- **Alembic** para migraciones versionadas
- Comando: `alembic revision --autogenerate -m "description"`
- Todas las migraciones probadas en ambas direcciones (upgrade + downgrade)
- Migraciones almacenadas en `backend/app/db/migrations/versions/`

#### Seeding

Script de seeding (`backend/app/db/seed.py`) para:
- Productos de ejemplo con embeddings pre-calculados
- Distribuidores de Costa Rica
- Regulaciones del SFE/MAG
- Usuario admin de prueba

#### Seguridad de datos

| Aspecto | Implementación |
|---|---|
| **Cifrado en reposo** | RDS encryption (AES-256) |
| **Cifrado en tránsito** | TLS/SSL en todas las conexiones |
| **Backups** | RDS automated backups (7 días retención) |
| **Audit trail** | Tabla `audit_logs` para trazabilidad |
| **Secretos** | AWS Secrets Manager / `.env` (MVP) |
| **Connection pooling** | asyncpg pool: 20 conexiones, max_overflow 10 |

---

### CI/CD — Pipelines de GitHub Actions

#### [NEW] `.github/workflows/frontend.yml`

```yaml
# Trigger: push a main en frontend/
# Jobs: lint → typecheck → test → build → deploy S3 → invalidate CloudFront
```

#### [NEW] `.github/workflows/backend.yml`

```yaml
# Trigger: push a main en backend/
# Jobs: lint (ruff) → typecheck (mypy) → test (pytest + postgres service) → 
#        build Docker → push ECR → update ECS service
```

#### [NEW] `.github/workflows/db-migrations.yml`

```yaml
# Trigger: push a main en backend/app/db/migrations/
# Jobs: apply Alembic migrations to staging/production RDS
```

---

### Docker Compose — Desarrollo Local

#### [NEW] `docker-compose.yml`

Servicios para desarrollo local:

| Servicio | Imagen | Puerto |
|---|---|---|
| `postgres` | `pgvector/pgvector:pg16` | 5432 |
| `redis` | `redis:7-alpine` | 6379 |
| `backend` | Build from `./backend` | 8000 |
| `worker` | Build from `./backend` (entrypoint: Celery) | — |
| `frontend` | Build from `./frontend` | 5173 |

Un solo `docker-compose up` levanta todo el stack.

---

### Etapa 4 — MVP (10%)

#### Alcance del MVP

El MVP demostrará el **flujo completo end-to-end**:

1. ✅ Login/registro de agricultor
2. ✅ Formulario de plan agrícola (cultivo, hectáreas, etapa fenológica)
3. ✅ Envío asíncrono de solicitud (HTTP 202 + ticket_id)
4. ✅ Pipeline de 4 agentes con Gemini API (free tier)
5. ✅ Progreso en tiempo real vía SSE
6. ✅ Visualización de recomendación (productos, dosis, costos, alternativas)
7. ✅ Historial de recomendaciones del usuario
8. ⬜ Stripe payments (mock/stub)
9. ⬜ Scraping de catálogos (datos seed manuales)

#### Lo que NO incluye el MVP

- Scraping automático de catálogos de distribuidores (se usarán datos semilla)
- Pagos reales (Stripe stub)
- Deployment en AWS (se demostrará local con Docker Compose)
- Multi-idioma
- Mobile app

---

### Etapa 5 — Sales Pitch y Demo (10%)

#### Preparación sugerida

- Demo en vivo del flujo completo corriendo en Docker Compose
- Mostrar el pipeline de agentes en acción con logs en tiempo real
- Preparar 2-3 escenarios de cultivos diferentes
- Slides con la propuesta de valor B2B para distribuidores
- Mostrar la escalabilidad del diseño (colas, workers, rate limiting)

---

## Verification Plan

### Automated Tests

```bash
# Frontend
cd frontend && npm run lint && npm run typecheck && npm run test -- --coverage

# Backend
cd backend && ruff check . && mypy app && pytest --cov=app --cov-report=term-missing

# E2E
cd frontend && npx playwright test

# Docker
docker-compose up -d && curl http://localhost:8000/health
```

### Manual Verification

- Recorrer el flujo completo: registro → login → crear recomendación → ver progreso SSE → ver resultado
- Verificar que el pipeline de 4 agentes se ejecuta correctamente con la API de Gemini
- Verificar rate limiting y backoff con múltiples solicitudes simultáneas
- Revisar respuestas del LLM para detectar alucinaciones en recomendaciones
- Verificar que los datos de productos y regulaciones se consultan correctamente desde pgvector
