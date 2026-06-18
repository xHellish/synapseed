# SynapSeed

> Plataforma de recomendacion de agroquimicos para agricultores costarricenses.
> Solo informacion — **nada de compras**.

SynapSeed es un proyecto del curso **Diseno de Software — TEC** (Caso #2). Dado el cultivo, condiciones de zona y presupuesto de un agricultor, recomienda agroquimicos apropiados a traves de un pipeline de **4 agentes IA (LangGraph + OpenRouter)**. El motor analiza el contexto agronomico, busca productos con busqueda semantica (RAG + pgvector), valida contra regulaciones del SFE/MAG y sintetiza exactamente **3 recomendaciones rankeadas** con tabla comparativa.

---

## Tabla de contenidos

1. [Prototipado y refinamiento UX](#1-prototipado-y-refinamiento-ux)
2. [Diseno del frontend](#2-diseno-del-frontend)
3. [Diseno del backend y data](#3-diseno-del-backend-y-data)
4. [MVP](#4-mvp)

---

# 1. Prototipado y refinamiento UX

## 1.1 Problem Statement

Los agricultores costarricenses no tienen acceso facil a recomendaciones tecnicas de agroquimicos adaptadas a su cultivo, zona y presupuesto especifico. Recurren a distribuidores que priorizan ventas sobre idoneidad tecnica, o a informacion generica que no considera sus condiciones reales.

**Solucion:** asistente digital que — dado el contexto del agricultor — recomienda exactamente que producto comprar, a que dosis, donde conseguirlo y por que, respaldado por regulaciones del SFE.

## 1.2 Prototipo interactivo

El prototipo cubre el flujo principal: ingreso de contexto agricola → espera del pipeline de agentes → visualizacion de 3 recomendaciones rankeadas.

**Herramienta:** Figma
**Enlace:** _(agregar enlace al prototipo Figma aqui)_

Pantallas incluidas en el prototipo:
- Login con cedula
- Wizard paso 1 — cultivo, finca y etapa
- Wizard paso 2 — confirmacion del caso
- Pantalla de carga con progreso de agentes
- Resultado con 3 productos y tabla comparativa
- Listado de proveedores por producto

## 1.3 UX Testing

**Participantes:** 4 estudiantes del grupo de Diseno de Software que no pertenecen al equipo.

**Tareas definidas para los participantes:**
1. Registrarse con una cedula ficticia
2. Completar el wizard para "tomate con hongo en las hojas, presupuesto medio"
3. Interpretar cual de los 3 productos recomendados elegirian y por que
4. Encontrar el contacto de un proveedor de un producto especifico

**Resultados del UX Testing:**

| Problema detectado | Participantes afectados | Severidad |
|---|---|---|
| No era claro que "finca" es opcional | 3/4 | Alta |
| El boton "Iniciar analisis" no comunicaba que el proceso tarda 30s | 4/4 | Alta |
| La tabla comparativa se cortaba en movil | 2/4 | Media |
| El campo cedula no indicaba el formato esperado | 2/4 | Baja |

## 1.4 Correcciones aplicadas al prototipo

| Problema | Correccion | Criterio |
|---|---|---|
| Finca obligatoria sin opcion de omitir | Se agrego opcion "Sin finca (ingresar datos manualmente)" como primera opcion del dropdown | Reducir friccion en el flujo principal |
| Usuario no sabe que el proceso tarda | Se agrego pantalla de carga con barra de progreso por agente y mensajes descriptivos por paso | Comunicar estado activo del sistema |
| Tabla comparativa sin scroll horizontal | Se envolvio en contenedor con `overflow-x-auto` | Responsive en pantallas angostas |
| Campo cedula sin indicacion de formato | Se agrego placeholder "Ej: 123456789" y validacion con mensaje claro | Reducir error de entrada |

---

# 2. Diseno del frontend

## 2.1 Stack tecnologico

| Tecnologia | Version | Justificacion |
|---|---|---|
| React | 19 | Ecosistema maduro, Concurrent Mode, compatibilidad con todas las librerias usadas |
| TypeScript | 5.7 | Tipado estatico previene errores en tiempo de compilacion; fundamental para contratos con la API |
| Vite | 6 | Build tool extremadamente rapido; HMR instantaneo en desarrollo |
| TailwindCSS | 4 | CSS-first (sin `tailwind.config.js`), utilidades directamente en JSX, reduccion de CSS custom |
| shadcn/ui | latest | Componentes accesibles (Radix UI) con estilos Tailwind; no es una dependencia de paquete, el codigo vive en `/src` |
| Zustand | 5 | Estado cliente ligero y sin boilerplate; `persist` middleware para persistir token en localStorage |
| TanStack React Query | 5 | Manejo de estado servidor: cache, revalidacion, loading/error states automaticos |
| React Router | 7 | Enrutamiento declarativo con rutas protegidas via `Outlet` |
| react-hook-form + zod | 7 + 3 | Validacion de formularios con schema tipado; evita re-renders innecesarios |
| axios | 1.7 | Cliente HTTP con interceptores; mas ergonomico que `fetch` para manejar headers globales |
| Vitest | 2 | Compatible con Vite, rapido, API identica a Jest |
| Playwright | 1.49 | Tests E2E contra el navegador real |

**Hosting:** el frontend corre en un contenedor Docker con Vite. En produccion se serviria como bundle estatico desde un CDN (Cloudflare Pages o Vercel). Actualmente solo ambiente local.

## 2.2 Estructura de carpetas

```
src/frontend/src/
├── app/
│   ├── router.tsx          # definicion de todas las rutas
│   └── ProtectedRoute.tsx  # guard que redirige a /login si no hay sesion
├── features/               # modulos por dominio (feature-based architecture)
│   ├── auth/               # login, registro, recuperacion de contrasena
│   ├── wizard/             # flujo principal de 4 pasos + resultado
│   ├── zones/              # gestion de fincas del agricultor
│   ├── account/            # perfil de usuario
│   ├── dashboard/          # pantalla de inicio post-login
│   └── layout/             # AppLayout con navbar y logout
├── components/
│   └── ui/                 # componentes reutilizables (shadcn/ui wrappers)
├── stores/                 # estado global con Zustand
│   ├── authStore.ts        # token, usuario, isAuthenticated
│   └── wizardStore.ts      # estado del wizard entre pasos
├── lib/
│   ├── cn.ts               # helper clsx + tailwind-merge
│   └── apiError.ts         # extrae mensajes de error de respuestas axios
└── main.tsx                # entry point: QueryClient, RouterProvider, store
```

Referencia: [`src/frontend/src/app/router.tsx`](src/frontend/src/app/router.tsx)

## 2.3 Convenciones de nomenclatura

| Elemento | Convencion | Ejemplo |
|---|---|---|
| Componentes React | PascalCase | `LoginPage.tsx`, `CaseWizardStep1.tsx` |
| Hooks | camelCase con prefijo `use` | `useAuthStore`, `useWizardStore` |
| Stores Zustand | camelCase con sufijo `Store` | `authStore.ts` |
| Archivos de utilidades | camelCase | `apiError.ts`, `recommendationMapper.ts` |
| Carpetas de features | kebab-case | `features/auth/`, `features/wizard/` |
| Interfaces/tipos | PascalCase | `AuthUser`, `RecommendationData` |
| Variables/funciones | camelCase | `handleLogout`, `buildComparisonRows` |
| Constantes | SCREAMING_SNAKE o camelCase segun scope | `NO_FINCA`, `DEMO_RECOMMENDATION` |

## 2.4 Lineamientos CSS y branding

El proyecto usa **TailwindCSS v4 CSS-first** — no hay `tailwind.config.js`. Los tokens de diseno se definen como variables CSS en el HTML raiz.

**Paleta de colores:**

| Token | Valor | Uso |
|---|---|---|
| Verde primario | `#16A34A` | Botones principales, iconos de estado OK, acentos |
| Indigo | `#4F46E5` | Badges de ranking |
| Amber | `#F59E0B` | Advertencias, badges intermedios |
| Rojo | `#DC2626` | Errores, estados FAILED |
| Gris texto | `#111827` | Texto principal |
| Gris secundario | `#6B7280` | Labels, subtitulos |
| Fondo panel | `#FFFFFF` | Cards y paneles |
| Borde | `#E5E7EB` | Divisores y bordes de tabla |

**Tipografia:** Inter (sistema) — `font-sans` de Tailwind.

**Iconografia:** Lucide React (`lucide-react`) — iconos SVG consistentes con la paleta.

**Responsive design:** breakpoints estandar de Tailwind (`sm`, `lg`). La grid de 3 columnas del resultado colapsa a 1 columna en movil. La tabla comparativa tiene `overflow-x-auto` para scroll horizontal.

**Componentes reutilizables:** `Panel`, `SynapButton`, `CaseStepper`, `PageHeader` definidos en [`src/frontend/src/components/ui/prototype.tsx`](src/frontend/src/components/ui/prototype.tsx).

## 2.5 Patrones arquitectonicos del frontend

### Feature-based architecture

Cada dominio de negocio (auth, wizard, zones, account) es un modulo independiente en `features/`. Ninguna feature importa de otra directamente — comparten solo stores y componentes de `components/ui/`.

### Presentational vs Container

- **Container:** componentes de pagina (`LoginPage`, `CaseWizardStep3`) — manejan estado, queries y logica
- **Presentational:** componentes de UI (`ProductCard`, `Panel`, `SynapButton`) — solo reciben props y renderizan

### Separacion de estado servidor vs cliente

- **React Query** (estado servidor): datos que vienen de la API — recomendaciones, zonas, catalogs. Se cachean automaticamente, se revalidan en focus, tienen loading/error states declarativos
- **Zustand** (estado cliente): estado que no necesita ir al servidor — token JWT, paso actual del wizard, preferencias de UI

Esta separacion evita el patron anti-recomendado de guardar respuestas de API en Zustand o Redux.

Referencias: [`src/frontend/src/stores/authStore.ts`](src/frontend/src/stores/authStore.ts), [`src/frontend/src/stores/wizardStore.ts`](src/frontend/src/stores/wizardStore.ts)

## 2.6 Patrones de componentes

**Compound components:** los componentes de shadcn/ui (Dialog, Select) usan el patron Compound donde el padre controla el estado y los hijos son slots con responsabilidades atomicas.

`ProtectedRoute` usa el patron `Outlet` de React Router para componer rutas protegidas sin prop drilling.

Referencia: [`src/frontend/src/app/ProtectedRoute.tsx`](src/frontend/src/app/ProtectedRoute.tsx)

```tsx
// ProtectedRoute verifica AMBAS condiciones: flag y token real
export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const token = useAuthStore((state) => state.token)
  if (!isAuthenticated || !token) return <Navigate to="/login" replace />
  return <Outlet />
}
```

## 2.7 Seguridad frontend

### Autenticacion y sesion

- El token JWT (emitido por Supabase Auth) se persiste en `localStorage` via Zustand `persist` middleware con clave `synapseed-auth`
- `ProtectedRoute` verifica `isAuthenticated && token` — dos condiciones para evitar que un flag stale permita acceso sin token real
- Al cerrar sesion: `queryClient.clear()` borra todo el cache de React Query (previene que datos de sesion anterior aparezcan si otro usuario inicia sesion en el mismo navegador) y `navigate('/login', { replace: true })` elimina la ruta del historial

Referencia: [`src/frontend/src/features/layout/AppLayout.tsx`](src/frontend/src/features/layout/AppLayout.tsx)

### Expiracion de tokens

Los JWT de Supabase expiran segun la configuracion del proyecto Supabase (default 1 hora). El frontend no implementa refresh automatico actualmente; al expirar, la siguiente peticion falla con 401 y el usuario debe re-autenticarse.

### Validacion de permisos

Todas las rutas dentro de `ProtectedRoute` requieren token valido. El backend valida el token en cada request — el frontend no implementa logica de autorizacion por roles.

### OWASP aplicable

| Riesgo OWASP | Mitigacion |
|---|---|
| A01 Broken Access Control | `ProtectedRoute` en cliente + validacion JWT en backend |
| A02 Cryptographic Failures | JWT firmado por Supabase; contrasenas hasheadas con bcrypt en backend |
| A03 Injection | Todas las entradas pasan por validacion Zod antes de enviarse a la API |
| A07 Auth Failures | Token verificado en cada endpoint; logout limpia cache y redirige |

## 2.8 Comunicacion asincrona y manejo de estado

### Consumo de API

Todas las llamadas HTTP usan `axios` directamente desde los componentes o funciones `queryFn` de React Query. El baseURL se configura con la variable de entorno `VITE_API_URL`.

```tsx
// Patron estandar de query en un componente
const { data, isLoading, isError } = useQuery({
  queryKey: ['recommendation', id],
  queryFn: () =>
    axios.get(`/api/v1/recommendations/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    }).then(r => r.data),
  enabled: !!token && !!id,
})
```

### Procesos largos — Polling del pipeline

El pipeline de agentes tarda entre 10 y 50 segundos. El frontend usa **polling** para detectar cuando la recomendacion cambia de `pending`/`processing` a `completed`:

```tsx
// CaseWizardStep3.tsx — polling cada 1 segundo mientras el pipeline esta activo
useEffect(() => {
  if (recommendation?.status !== 'pending' && recommendation?.status !== 'processing') return
  const interval = setInterval(() => {
    axios.get(`/api/v1/recommendations/${id}`, { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => queryClient.setQueryData(['recommendation', id], response.data))
  }, 1000)
  return () => clearInterval(interval)
}, [id, token, recommendation, queryClient])
```

El backend publica progreso via SSE (Redis pub/sub → `GET /recommendations/stream/{ticket_id}`), pero el cliente actual usa polling del endpoint REST en lugar del stream SSE. Ambas estrategias son validas; el polling es mas simple y suficiente para este caso de uso.

Referencia: [`src/frontend/src/features/wizard/CaseWizardStep3.tsx`](src/frontend/src/features/wizard/CaseWizardStep3.tsx)

### Manejo de errores

El hook `useQuery` expone `isError` y `error`. Los errores de red o 4xx/5xx muestran un panel con `AlertTriangle`. Los errores de validacion de formulario se muestran inline bajo cada campo con `react-hook-form`.

```ts
// lib/apiError.ts — extrae el mensaje legible del error de axios
export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? error.message
  }
  return 'Error desconocido'
}
```

### Caching y retries

React Query cachea respuestas por `queryKey`. Por defecto reintenta 3 veces en error de red. Las queries de catalogs (cultivos, suelos) se consideran datos estables y no se revalidan en focus.

### Storage

| Dato | Donde | Por que |
|---|---|---|
| JWT token, usuario | `localStorage` via Zustand persist | Sobrevive recargas de pagina |
| Paso del wizard, datos del formulario | Zustand en memoria | Se limpia al terminar el flujo |
| Cache de recomendaciones, zonas | React Query en memoria | Se limpia en logout |

## 2.9 Contratos de datos — Validacion con Zod

Cada formulario tiene su schema Zod que define el contrato entre la UI y la API:

```ts
// features/wizard/schemas.ts
const wizardStep1Schema = z.object({
  crop_id:    z.string().min(1, 'Seleccione un cultivo'),
  crop_stage: z.string().min(1, 'Seleccione la etapa'),
  finca_id:   z.string().optional(),   // "Sin finca" es valido
})
```

Los schemas se usan como `resolver` de react-hook-form, garantizando que ningun dato invalido llega al backend.

## 2.10 Optimizacion de rendimiento

| Tecnica | Donde se aplica |
|---|---|
| Code splitting | Vite hace splitting automatico por modulo |
| Memoization | `useMemo` en `CaseWizardStep3` para `providers` y `products` — evita recalcular en cada render |
| Imagenes | No se usan imagenes pesadas; iconos son SVG inline via Lucide |
| React Query cache | Evita refetch innecesarios con `staleTime` configurado por query |

## 2.11 Testing frontend

```bash
cd src/frontend
npm run test              # Vitest, modo run (CI)
npm run test:watch        # Vitest, modo watch (desarrollo)
npm run test:coverage     # cobertura con @vitest/coverage-v8
npm run test:e2e          # Playwright
```

**Estrategia:**
- **Unit tests (Vitest + React Testing Library):** logica de helpers (`recommendationMapper.ts`, schemas Zod), componentes de UI aislados
- **Integration tests:** flujos de wizard con mocks de axios
- **E2E (Playwright):** flujo completo login → wizard → resultado contra backend real

Cobertura minima esperada: 60% en `features/wizard/` y `stores/`.

## 2.12 CI/CD frontend

```
push → lint (ESLint) → typecheck (tsc --noEmit) → test (Vitest) → build (vite build)
```

Comandos locales equivalentes:

```bash
npm run lint        # ESLint con typescript-eslint
npm run typecheck   # tsc -b --noEmit
npm run test        # Vitest
npm run build       # build de produccion
```

---

# 3. Diseno del backend y data

## 3.1 Stack tecnologico

| Tecnologia | Version | Justificacion |
|---|---|---|
| Python | 3.12 | Typing mejorado, performance; ecosistema de IA (LangChain, LangGraph) |
| FastAPI | 0.115 | ASGI nativo, async/await, OpenAPI automatico, validacion Pydantic integrada |
| SQLAlchemy | 2.0 | ORM async con asyncpg; Mapped columns para tipado estricto |
| asyncpg | latest | Driver PostgreSQL async puro; requerido por SQLAlchemy 2.0 async |
| Alembic | latest | Migraciones versionadas; unico lugar que toca el schema de DB |
| Pydantic v2 | 2.x | Validacion y serializacion de DTOs; `model_validate` para conversion ORM → schema |
| passlib[bcrypt] | latest | Hashing de contrasenas; bcrypt es el estandar de la industria |
| python-jose | latest | Firma y verificacion de JWT locales (fallback de auth) |
| Celery | 5.4 | Cola de tareas para el pipeline de agentes (10-50s no puede bloquear un request HTTP) |
| Redis | 7 | Broker de Celery (canal 1) + backend de resultados (canal 2) + pub/sub SSE (canal 0) |
| PostgreSQL | 16 + pgvector | DB relacional + extension de vectores para busqueda semantica |
| LangGraph | 1.2 | Orquestacion de agentes (preparado para grafos; actualmente uso secuencial) |
| OpenRouter | API | Acceso unificado a multiples LLMs; modelo configurable via env var |
| Gemini | text-embedding-004 | Embeddings de 768 dimensiones para la busqueda semantica de productos |

**Hosting:** Supabase (PostgreSQL 16 + pgvector + Supabase Auth). Backend y worker corren en Docker local. Redis en Docker local.

## 3.2 Arquitectura en capas

```
HTTP Request
     |
     v
[Router]      app/api/v1/*.py
     |         - Recibe y valida HTTP (path, query, body)
     |         - Delega a Service; nunca contiene logica de negocio
     |         - Lanza HTTPException con codigos HTTP apropiados
     |
     v
[Service]     app/services/*.py
     |         - Contiene TODA la logica de negocio
     |         - Puede llamar multiples repositories
     |         - Lanza excepciones de dominio (AuthError, LLMError)
     |         - No sabe nada de HTTP ni de SQLAlchemy directamente
     |
     v
[Repository]  app/repositories/*.py
     |         - Unico lugar que escribe queries SQLAlchemy
     |         - Recibe y retorna modelos ORM o DTOs simples
     |         - Nunca contiene logica de negocio
     |
     v
[Model]       app/models/*.py
               - Clases ORM de SQLAlchemy (tablas de la DB)
               - Solo define columnas, relaciones e indices
               - Nunca contiene logica de negocio
```

**Restricciones por capa:**

| Capa | Puede importar | No puede importar |
|---|---|---|
| Router | Service, Schema, Dependency | Repository, Model directamente |
| Service | Repository, Schema, Core | Router, FastAPI |
| Repository | Model, SQLAlchemy | Service, Schema de respuesta HTTP |
| Model | SQLAlchemy, Base | Todo lo demas |

Referencias: [`src/backend/app/api/v1/auth.py`](src/backend/app/api/v1/auth.py), [`src/backend/app/services/auth_service.py`](src/backend/app/services/auth_service.py), [`src/backend/app/repositories/base.py`](src/backend/app/repositories/base.py)

## 3.3 Patrones de diseno orientados a objetos

### Repository Pattern

**Problema sin patron:** los agentes y routers tendrian queries SQL directas, acoplando logica de negocio al ORM. Cambiar la DB requeriria tocar todos los agentes.

**Solucion:** `BaseRepository[T]` provee CRUD generico; cada repositorio especializado extiende con operaciones especificas del dominio.

```python
# repositories/base.py — CRUD generico con generics
class BaseRepository(Generic[ModelT]):
    def __init__(self, db: AsyncSession, model: Type[ModelT]) -> None: ...
    async def get_by_id(self, id: int) -> ModelT | None: ...
    async def create(self, data: dict) -> ModelT: ...
    async def update(self, instance: ModelT, data: dict) -> ModelT: ...
    async def delete(self, instance: ModelT) -> None: ...

# repositories/user_repository.py — especializado
class UserRepository(BaseRepository[User]):
    async def get_by_identification(self, identification: str) -> User | None: ...
    async def get_by_email(self, email: str) -> User | None: ...
```

**Clases participantes:** `BaseRepository`, `UserRepository`, `ProductRepository`, `ZoneRepository`, `RecommendationRepository`, `RegulationRepository`

Referencia: [`src/backend/app/repositories/base.py`](src/backend/app/repositories/base.py)

### Dependency Inversion Principle (DIP) — Abstract Repository

**Problema:** si `AgentOrchestrator` importa `ProductRepository` (concreto), no se puede probar sin una DB real.

**Solucion:** `AbstractProductRepository(ABC)` define el contrato; el orquestador depende de la abstraccion. En produccion se inyecta `SqlAlchemyProductRepository`; en tests, `FakeProductRepository`.

```python
# repositories/product_repository.py
class AbstractProductRepository(ABC):
    @abstractmethod
    async def search_candidates(
        self, context: ContextAnalysisOutput, *, limit: int = 15
    ) -> tuple[list[ProductCandidate], str]: ...

class SqlAlchemyProductRepository(AbstractProductRepository):
    async def search_candidates(self, context, *, limit=15) -> tuple[...]:
        # implementacion real contra PostgreSQL

class FakeProductRepository(AbstractProductRepository):
    async def search_candidates(self, context, *, limit=15) -> tuple[...]:
        # implementacion en memoria para tests
```

Referencia: [`src/backend/app/repositories/product_repository.py`](src/backend/app/repositories/product_repository.py)

### Strategy Pattern — LLMClient

**Problema:** los agentes no deben saber si el LLM es OpenRouter, un mock o cualquier otro proveedor.

**Solucion:** `LLMClient(ABC)` define la interfaz; `OpenRouterLLMClient` es la implementacion de produccion; `MockLLMClient` la de tests.

```python
# services/llm_client.py
class LLMClient(ABC):
    @abstractmethod
    async def complete_json(self, *, system_prompt, user_prompt, response_model: type[T]) -> T: ...

class OpenRouterLLMClient(LLMClient):
    async def complete_json(self, ...) -> T:
        # llama a OpenRouter, extrae JSON, valida con Pydantic
        response = await self._chat.ainvoke(messages)
        return response_model.model_validate(_extract_json(response.content))

class MockLLMClient(LLMClient):
    async def complete_json(self, ...) -> T:
        # devuelve respuesta hardcodeada sin llamadas HTTP
```

Referencia: [`src/backend/app/services/llm_client.py`](src/backend/app/services/llm_client.py)

### DTOs — Pydantic Schemas

Los schemas Pydantic son los DTOs del sistema. Estan completamente separados de los modelos ORM:

```
app/schemas/
├── user.py                      # UserLogin, TokenResponse, UserResponse
├── farmer_input.py              # FarmerContextInput (entrada del wizard)
├── agent_context.py             # ContextAnalysisOutput (salida Agente 1)
├── agent_products.py            # ProductCandidate, ResearchOutput (salida Agente 2)
├── agent_legal.py               # LegalValidationOutput (salida Agente 3)
└── agent_recommendations.py     # SynthesisOutput, PipelineResult (salida Agente 4)
```

## 3.4 Patrones arquitectonicos

### Queue-Based Load Leveling (Celery + Redis)

**Reto:** el pipeline de 4 agentes tarda entre 10 y 50 segundos. Un request HTTP no puede bloquear el servidor ese tiempo sin degradar todos los demas usuarios.

**Solucion:**

```
POST /recommendations/request
  - crea registro PENDING en DB
  - encola tarea en Redis (Celery broker)
  - retorna ticket_id inmediatamente (< 100ms)

Worker Celery (proceso separado)
  - consume la tarea de Redis
  - ejecuta AgentOrchestrator.run()
  - actualiza DB a PROCESSING / COMPLETED / FAILED
  - publica progreso en Redis pub/sub

Frontend
  - polling GET /recommendations/{id} cada 1s
  - o suscripcion al stream SSE /recommendations/stream/{ticket_id}
```

**Clases participantes:**
- `generate_recommendation` — task Celery en [`src/backend/app/workers/tasks.py`](src/backend/app/workers/tasks.py)
- `celery_app` — configuracion en [`src/backend/app/workers/celery_app.py`](src/backend/app/workers/celery_app.py)
- `AgentOrchestrator` — ejecuta el pipeline en [`src/backend/app/agents/orchestrator.py`](src/backend/app/agents/orchestrator.py)

**Manejo de excepciones:** cualquier falla dentro del pipeline marca la recomendacion como `FAILED` en DB y publica el mensaje de error via Redis para que el frontend lo muestre.

### Pub/Sub para SSE (Redis → Frontend)

**Reto:** el frontend necesita saber en que paso del pipeline esta el worker, sin hacer polling agresivo.

**Solucion:** el worker publica mensajes de progreso en un canal Redis `recommendation_progress:{ticket_id}`. El endpoint SSE `GET /recommendations/stream/{ticket_id}` suscribe al canal y hace stream de cada mensaje como `text/event-stream`.

```python
# El worker publica
await redis_client.publish(f"recommendation_progress:{ticket_id}", json.dumps(payload))

# El endpoint SSE suscribe y reenvia al navegador
async def generate():
    async with pubsub.subscribe(channel) as subscription:
        async for message in subscription:
            yield f"data: {message}\n\n"
```

### Agentic Sequential Workflow

**Reto:** el procesamiento de recomendaciones involucra 4 pasos con dependencias estrictas (cada paso necesita la salida del anterior).

**Solucion:** los 4 agentes se ejecutan en secuencia dentro de `AgentOrchestrator.run()`. El estado compartido `PipelineState` acumula las salidas para pasarlas al siguiente agente.

```
FarmerContextInput
      |
      v
[Agente 1: Analyzer]          - ContextAnalysisOutput
      |                          (cultivo, problema, condiciones, resumen RAG)
      v
[Agente 2: Researcher]        - ResearchOutput
      |                          (lista de ProductCandidate de la DB)
      v
[Agente 3: Legal Validator]   - LegalValidationOutput
      |                          (productos filtrados por regulaciones SFE)
      v
[Agente 4: Synthesizer]       - SynthesisOutput
                                 (3 recomendaciones rankeadas con justificacion)
```

**Restriccion anti-alucinacion:** ningun agente inventa datos numericos. Los precios, dosis, toxicidad e intervalos de seguridad vienen de la DB; el LLM solo genera texto interpretativo.

Referencia: [`src/backend/app/agents/orchestrator.py`](src/backend/app/agents/orchestrator.py)

## 3.5 Integraciones de sistemas

### OpenRouter (LLM de chat)

| Campo | Valor |
|---|---|
| Proveedor | OpenRouter.ai |
| Protocolo | HTTPS REST (compatible OpenAI) |
| Autenticacion | API Key en header `Authorization: Bearer` |
| Throughput | Depende del modelo; modelo free: 20 RPM |
| Tiempo de respuesta | 5-30s por llamada |
| Tamano de respuesta | JSON estructurado, < 4KB tipicamente |
| Config | `OPENROUTER_API_KEY`, `OPENROUTER_CHAT_MODEL`, `OPENROUTER_RPM_LIMIT` |
| Mitigacion de latencia | Celery async — el request HTTP retorna inmediatamente, el LLM se llama en background |
| Patron de diseno | Strategy (`LLMClient` ABC + `OpenRouterLLMClient`) |
| Retry | `tenacity` con backoff exponencial hasta `OPENROUTER_MAX_RETRIES` intentos |
| Clase | [`src/backend/app/services/llm_client.py`](src/backend/app/services/llm_client.py) |

### Google Gemini (embeddings)

| Campo | Valor |
|---|---|
| Proveedor | Google AI Studio |
| Protocolo | HTTPS REST |
| Autenticacion | API Key |
| Uso | Generacion de embeddings de 768 dims para productos y regulaciones (al hacer seeding) |
| Config | `GEMINI_API_KEY`, `GOOGLE_EMBEDDING_MODEL=models/text-embedding-004`, `EMBEDDING_DIM=768` |
| Throughput | Solo se usa al cargar datos (seed), no en el path caliente de requests |

### Supabase (PostgreSQL + Auth)

| Campo | Valor |
|---|---|
| Proveedor | Supabase.com |
| Protocolo | PostgreSQL wire protocol (asyncpg) + HTTPS REST (Auth API) |
| Autenticacion DB | Connection string con usuario/password |
| Autenticacion Auth | `SUPABASE_URL`, `SUPABASE_ANON_KEY` |
| Connection pooling | PgBouncer transaction mode — requiere `statement_cache_size=0` en asyncpg |
| Configuracion | `DATABASE_URL` (asyncpg, runtime), `DATABASE_URL_SYNC` (psycopg2, Alembic) |
| Clase | [`src/backend/app/db/session.py`](src/backend/app/db/session.py) |

**Por que dos DATABASE_URL:** SQLAlchemy async requiere asyncpg (`postgresql+asyncpg://...`). Alembic es sincrono y requiere psycopg2 (`postgresql+psycopg2://...`). Son dos drivers distintos para el mismo servidor Supabase.

### Redis

| Campo | Valor |
|---|---|
| Protocolo | RESP (Redis Serialization Protocol) |
| Canal 0 | SSE pub/sub (`recommendation_progress:*`) |
| Canal 1 | Celery broker (cola de tareas) |
| Canal 2 | Celery result backend |
| Config | `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` |
| Clase | [`src/backend/app/core/redis.py`](src/backend/app/core/redis.py) |

## 3.6 Middlewares y configuracion global

### CORS

Configurado en [`src/backend/app/main.py`](src/backend/app/main.py):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,  # lista de origenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`BACKEND_CORS_ORIGINS` acepta lista JSON o CSV en el `.env`.

### Logging

Formato estructurado con timestamp, nivel y nombre del modulo:

```
2025-06-17 10:00:00 | INFO | app.workers.tasks | Pipeline paso 1/4: Analizador de Contexto
```

Nivel configurable con `LOG_LEVEL` en `.env`.

### Health check

`GET /api/v1/health` verifica DB, Redis y disponibilidad del LLM. Retorna 200 si todos estan OK, 503 si alguno falla.

Referencia: [`src/backend/app/api/v1/health.py`](src/backend/app/api/v1/health.py)

## 3.7 Autenticacion y autorizacion

### Flujo de autenticacion

```
Frontend (cedula + password)
    |
    v
POST /api/v1/auth/login
    |
    v
authenticate_user(db, data)
    1. Resuelve cedula -> email en tabla users
    2. Llama sign_in_with_password(email, password) → Supabase Auth API
    3. Supabase retorna SupabaseSession con access_token (JWT)
    4. Fallback: si Supabase falla con 401, verifica bcrypt local (backward-compat)
    |
    v
build_token_response(user, session)
    - { access_token, refresh_token, expires_in, token_type, user }
    |
    v
Frontend guarda access_token en Zustand (localStorage)
```

**Por que cedula y no email:** el target son agricultores costarricenses. La cedula es el identificador natural en CR; el email es un campo tecnico que muchos no recuerdan. Login con cedula mejora la UX del usuario objetivo.

### Validacion de token en cada request

```python
# core/security.py — dependencia de FastAPI inyectada en routers protegidos
async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme)):
    # 1. Intenta decodificar como JWT local (fallback bcrypt)
    # 2. Si falla, valida contra Supabase Auth API
    user = await resolve_user_from_token(db, credentials.credentials)
    return {"id": user.id, "identification": user.identification}
```

Referencias: [`src/backend/app/core/security.py`](src/backend/app/core/security.py), [`src/backend/app/services/auth_service.py`](src/backend/app/services/auth_service.py)

## 3.8 Variables de entorno

Todas las variables se definen en `.env` (copiar desde `.env.example`). Las lee `pydantic-settings` con tipado estricto en [`src/backend/app/config.py`](src/backend/app/config.py).

| Variable | Descripcion | Ejemplo |
|---|---|---|
| `DATABASE_URL` | asyncpg para SQLAlchemy runtime | `postgresql+asyncpg://user:pass@db.supabase.co:5432/postgres` |
| `DATABASE_URL_SYNC` | psycopg2 para Alembic | `postgresql+psycopg2://user:pass@db.supabase.co:5432/postgres` |
| `SUPABASE_URL` | URL del proyecto Supabase | `https://xxxx.supabase.co` |
| `SUPABASE_ANON_KEY` | Clave publica de Supabase Auth | `eyJ...` |
| `JWT_SECRET` | Secreto para JWT locales (fallback) | `un-secreto-largo-y-aleatorio` |
| `JWT_EXPIRE_HOURS` | Expiracion de JWT local | `24` |
| `OPENROUTER_API_KEY` | API key de OpenRouter | `sk-or-...` |
| `OPENROUTER_CHAT_MODEL` | Modelo LLM a usar | `openrouter/free` |
| `GEMINI_API_KEY` | API key de Google AI Studio | `AIza...` |
| `REDIS_URL` | Redis para SSE pub/sub | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Redis como broker de Celery | `redis://localhost:6379/1` |
| `CELERY_RESULT_BACKEND` | Redis como backend de resultados | `redis://localhost:6379/2` |
| `BACKEND_CORS_ORIGINS` | Origenes permitidos por CORS | `["http://localhost:5173"]` |
| `VITE_API_URL` | URL base de la API (frontend) | `http://localhost:8000` |
| `APP_ENV` | Entorno actual | `development` |

**Manejo de secretos:** las API keys y secretos nunca se commitean al repositorio. `.env` esta en `.gitignore`. El `.env.example` tiene valores de placeholder.

## 3.9 Manejo de errores

### Excepciones de dominio

```python
# services/auth_service.py
class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400): ...

# services/llm_client.py
class LLMError(Exception): ...
```

Los routers capturan las excepciones de dominio y las convierten a `HTTPException` con el codigo HTTP apropiado. Las excepciones no capturadas retornan 500.

### Validacion de entrada

FastAPI valida automaticamente los bodies de los endpoints con los schemas Pydantic. Si la validacion falla, retorna 422 con detalles de cada campo invalido.

## 3.10 Observabilidad y monitoreo

- **Logging estructurado:** cada modulo tiene `logger = logging.getLogger(__name__)`. El formato incluye timestamp, nivel, modulo y mensaje.
- **Health check:** `GET /api/v1/health` verifica conectividad con DB, Redis y LLM. Ideal para monitoring externo.
- **Celery logs:** el worker loggea inicio, paso a PROCESSING, cada paso completado y resultado final o error.
- **Sentry (opcional):** `SENTRY_DSN` en `.env` activa reporte automatico de errores.

## 3.11 Connection pooling y concurrencia

SQLAlchemy async maneja un pool de conexiones configurado en [`src/backend/app/db/session.py`](src/backend/app/db/session.py):

```python
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,       # 20 conexiones base
    max_overflow=settings.db_max_overflow, # 10 conexiones adicionales bajo carga
    connect_args={"statement_cache_size": 0},  # requerido por PgBouncer transaction mode
)
```

El worker Celery corre con `concurrency=1` por defecto (un pipeline a la vez por worker). Se puede escalar horizontalmente levantando multiples workers.

## 3.12 Pipeline de agentes IA — detalle tecnico

### Agente 1: Analyzer

- **Entrada:** `FarmerContextInput` — cultivo, etapa, problema, suelo, humedad, temperatura, presupuesto
- **Proceso:** llamada al LLM con prompt que pide estructurar el contexto del agricultor
- **Salida:** `ContextAnalysisOutput` — cultivo normalizado, problema detectado, condiciones agronomicas, severidad estimada, texto denso para RAG
- **Archivo:** [`src/backend/app/agents/analyzer_agent.py`](src/backend/app/agents/analyzer_agent.py)

### Agente 2: Researcher (RAG)

- **Entrada:** `ContextAnalysisOutput` del Agente 1
- **Proceso:** busca productos en PostgreSQL usando filtros por categoria + texto ILIKE. Fallback a busqueda solo por categoria si no hay resultados. Puntua candidatos con heuristica determinista (sin LLM).
- **Salida:** `ResearchOutput` — lista de `ProductCandidate` con score de relevancia
- **Regla anti-alucinacion:** todos los datos de productos vienen de la DB; el agente no inventa precios ni dosis
- **Archivo:** [`src/backend/app/agents/researcher_agent.py`](src/backend/app/agents/researcher_agent.py)

### Agente 3: Legal Validator

- **Entrada:** `ContextAnalysisOutput` + `ResearchOutput`
- **Proceso:** validacion hibrida en dos pasos:
  1. Reglas deterministicas — verifica si el ingrediente activo coincide con regulaciones de la tabla `regulations`
  2. Interpretacion LLM — para casos ambiguos, el LLM analiza si la restriccion aplica al cultivo/uso especifico
- **Salida:** `LegalValidationOutput` — productos aprobados, rechazados (con razon) y advertencias
- **Politica conservadora:** en caso de duda, el producto se rechaza
- **Archivo:** [`src/backend/app/agents/legal_validator_agent.py`](src/backend/app/agents/legal_validator_agent.py)

### Agente 4: Synthesizer

- **Entrada:** `ContextAnalysisOutput` + `LegalValidationOutput`
- **Proceso:** el LLM recibe los productos validos y genera exactamente 3 recomendaciones rankeadas con justificacion, ventajas, riesgos y recomendacion de uso
- **Salida:** `SynthesisOutput` — lista de hasta 3 `RecommendationItem`
- **Regla:** el LLM usa `"no_disponible"` cuando no tiene dato; el worker lo convierte a `None` al guardar en DB
- **Archivo:** [`src/backend/app/agents/synthesizer_agent.py`](src/backend/app/agents/synthesizer_agent.py)

## 3.13 Reglas de negocio complejas

### Busqueda de productos (Agente 2)

```
1. Filtrar productos ACTIVOS en DB
2. Aplicar filtro de categoria (plaguicida / fertilizante) segun contexto del Agente 1
3. Busqueda hibrida: categoria + ILIKE en cultivo_objetivo, problema_objetivo, nombre_comercial, ingrediente_activo
4. Si no hay resultados: fallback a solo categoria
5. Puntuar cada candidato con heuristica determinista (0.0 - 1.0):
   - cultivo_objetivo coincide en resumen RAG: +0.35
   - problema_objetivo coincide en resumen RAG: +0.35
   - categoria correcta: +0.20
   - nombre o ingrediente relacionado: +0.10 c/u
6. Ordenar por score desc, retornar top-15
```

### Validacion legal (Agente 3)

```
1. Para cada ProductCandidate:
   a. Buscar regulaciones en DB cuyo ingrediente_activo coincida (ILIKE)
   b. Si no hay regulaciones: APROBADO (sin restricciones conocidas)
   c. Si hay regulaciones con action=PROHIBIDO: RECHAZADO automaticamente
   d. Si hay regulaciones con action=RESTRINGIDO: llamada al LLM para interpretar
      si la restriccion aplica al cultivo/uso especifico del agricultor
   e. Si el LLM no puede determinar: conservador → RECHAZADO con advertencia
2. Retornar: aprobados, rechazados (con razon), advertencias
```

## 3.14 Base de datos

### Diseno DBML

El esquema completo esta en [`Docs/database/schema.dbml`](Docs/database/schema.dbml).

**Tablas principales:**

| Tabla | Proposito | Notas |
|---|---|---|
| `users` | Agricultores registrados | `identification` (cedula) como login; `auth_user_id` liga con Supabase Auth |
| `zones` | Fincas/zonas agricolas del agricultor | FK a `users` |
| `products` | Catalogo de agroquimicos del SFE | `embedding` vector(768) para RAG |
| `distributors` | Distribuidores autorizados por producto | FK a `products` |
| `recommendations` | Solicitudes de recomendacion | Status: PENDING/PROCESSING/COMPLETED/FAILED |
| `recommendation_products` | Los 3 productos recomendados por solicitud | FK a `recommendations` y `products` |
| `regulations` | Regulaciones SFE/MAG por ingrediente | `embedding` vector(768); `action`: PROHIBIDO/RESTRINGIDO/PERMITIDO |
| `lmr` | Limites maximos de residuos por cultivo | FK a `products` |
| `audit_log` | Registro de acciones de usuarios | Trazabilidad de todas las operaciones |

### Diagrama entidad-relacion

```
users (1)----(N) zones
users (1)----(N) recommendations
users (1)----(N) audit_log

products (1)----(N) distributors
products (1)----(N) lmr
products (N)----(M) recommendations  [via recommendation_products]

regulations  (independiente — usada por Agente 3)
```

### Scripts de base de datos

```bash
# Crear tablas (Alembic)
alembic upgrade head

# Generar migracion despues de cambiar un modelo
alembic revision --autogenerate -m "descripcion del cambio"

# Rollback una migracion
alembic downgrade -1

# Seed de datos iniciales (productos SFE, distribuidores, regulaciones)
docker compose exec backend python -m app.db.seed
```

El seeding carga productos del catalogo del SFE, genera sus embeddings con Gemini y los inserta en la tabla `products`.

Referencia: [`src/backend/app/db/seed.py`](src/backend/app/db/seed.py)

### Estrategia de seguridad de datos

| Aspecto | Implementacion |
|---|---|
| Cifrado en transito | TLS entre el cliente y Supabase (provisto por Supabase) |
| Contrasenas | bcrypt con salt aleatorio via passlib; nunca se guarda en claro |
| Secretos | Variables de entorno (`.env`), nunca en codigo |
| Auditoria | Tabla `audit_log` registra todas las acciones con timestamp y user_id |
| Trazabilidad | Cada recomendacion guarda el `ticket_id` y el `user_id` que la solicito |
| Soft delete | `is_active=False` en usuarios (no se borra el registro) |
| Backups | Provisto por Supabase (diarios automaticos en plan pago) |

## 3.15 Testing backend

```bash
cd src/backend

# Todos los tests
pytest

# Test especifico
pytest tests/path/test_file.py::test_name

# Con cobertura
pytest --cov=app --cov-report=term-missing

# Solo un modulo
pytest tests/test_agents/
```

**Estrategia:**
- **Unit tests:** agentes con `MockLLMClient` y `FakeProductRepository` — sin llamadas HTTP ni DB
- **Integration tests:** endpoints con TestClient de FastAPI y DB de test
- **API tests:** coleccion de requests contra el servidor en ejecucion
- **Health checks:** `GET /api/v1/health` como smoke test en cada deploy

Cobertura minima esperada: 70% en `agents/`, 60% en `services/`, 50% en `api/v1/`.

## 3.16 CI/CD backend

```
push → ruff check → ruff format --check → mypy → pytest → build Docker image
```

Comandos locales equivalentes:

```bash
cd src/backend
ruff check . && ruff format .   # linting y formato
mypy app                         # verificacion de tipos
pytest --cov=app                 # tests con cobertura
```

---

# 4. MVP

## 4.1 Alcance formal del MVP

### Core Features (implementadas)

- Registro de agricultor con cedula costarricense
- Login con cedula + JWT via Supabase Auth
- Wizard de 2 pasos para capturar el contexto agricola
- Pipeline de 4 agentes IA que genera exactamente 3 recomendaciones rankeadas
- Tabla comparativa de productos (dosis, precio, toxicidad, intervalo de seguridad)
- Listado de distribuidores por producto recomendado
- Historial de recomendaciones anteriores
- Gestion de fincas (CRUD de zonas agricolas)

### Supporting Features (simplificadas)

- Perfil de cuenta (solo lectura, sin edicion de datos personales)
- Catalogs de cultivos, suelos y problemas (cargados desde DB al arrancar)

### Out of Scope

- Compra o pedido de productos (solo informacion)
- Notificaciones push o email
- Mapa de distribuidores
- Version movil nativa
- Soporte multilenguaje (solo espanol)
- Gestion de roles (admin, agricultor) — todos son agricultores en el MVP

### User Journeys en scope

1. **Flujo principal:** agricultor inicia sesion → completa wizard → espera resultado (10-50s) → ve 3 productos recomendados con tabla comparativa → ve proveedores
2. **Flujo de finca:** agricultor agrega una finca con datos de zona → la selecciona en el wizard para pre-llenar condiciones
3. **Flujo de historial:** agricultor vuelve al dashboard → ve recomendaciones anteriores → abre una para revisarla

## 4.2 Prerrequisitos

- [Docker](https://www.docker.com/) 24+ y Docker Compose v2
- Git
- API key de **OpenRouter** — obtener en openrouter.ai/keys
- API key de **Google AI Studio** — obtener en aistudio.google.com (embeddings gratuitos)
- Proyecto en **Supabase** — crear gratis en supabase.com (PostgreSQL + pgvector incluido)

## 4.3 Configuracion inicial

```bash
git clone https://github.com/xHellish/synapseed.git
cd synapseed

# Copiar plantilla de variables de entorno
cp .env.example .env
```

Editar `.env` con los valores reales:

```env
# Base de datos (Supabase → Settings → Database → URI)
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres
DATABASE_URL_SYNC=postgresql+psycopg2://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres

# Supabase Auth (Supabase → Settings → API)
SUPABASE_URL=https://[REF].supabase.co
SUPABASE_ANON_KEY=eyJ...

# LLM y embeddings
OPENROUTER_API_KEY=sk-or-...
GEMINI_API_KEY=AIza...

# JWT local (generar un string aleatorio largo)
JWT_SECRET=cambia-esto-con-un-secreto-seguro
```

## 4.4 Levantar el stack con Docker

```bash
# Construir y levantar los 4 servicios
docker compose up -d --build

# Ver logs en vivo
docker compose logs -f backend worker
```

**Servicios levantados:**

| Servicio | Puerto | URL |
|---|---|---|
| frontend (Vite) | 5173 | http://localhost:5173 |
| backend (FastAPI) | 8000 | http://localhost:8000 |
| backend (Swagger) | 8000 | http://localhost:8000/docs |
| worker (Celery) | - | - |
| redis | 6379 | localhost:6379 |

La base de datos es **Supabase (externa)** — no corre en Docker.

Al arrancar, el backend ejecuta automaticamente `alembic upgrade head` para aplicar migraciones pendientes en Supabase.

## 4.5 Inicializacion de datos (seed)

```bash
# Cargar catalogo de productos, distribuidores y regulaciones
docker compose exec backend python -m app.db.seed
```

Este comando inserta los datos de prueba necesarios para que el pipeline de agentes tenga productos que recomendar. Incluye productos del catalogo SFE, distribuidores y regulaciones basicas.

## 4.6 Desarrollo sin Docker (opcional)

### Backend

```bash
cd src/backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

alembic upgrade head
uvicorn app.main:app --reload --port 8000

# En otra terminal: worker de Celery
celery -A app.workers.celery_app worker --loglevel=info --concurrency=1
```

### Frontend

```bash
cd src/frontend
npm install
npm run dev        # dev server en http://localhost:5173
```

## 4.7 Verificacion

```bash
# Health check del backend
curl http://localhost:8000/api/v1/health

# Abrir la app
open http://localhost:5173

# Abrir la documentacion interactiva de la API
open http://localhost:8000/docs
```

## 4.8 Comandos utiles

```bash
# Detener todo
docker compose down

# Detener y borrar volumenes (resetea Redis)
docker compose down -v

# Ver logs de un servicio especifico
docker compose logs -f backend
docker compose logs -f worker

# Abrir shell en el backend
docker compose exec backend bash

# Reconstruir un servicio especifico
docker compose build backend && docker compose up -d backend
```

## 4.9 Agentes de IA usados en el desarrollo del MVP

### Agente SOLID (solid-code-architect)

Analiza clases del proyecto para detectar violaciones de los principios SOLID.

**Hallazgos y correcciones aplicadas:**

| Clase | Violacion detectada | Correccion |
|---|---|---|
| `ProductRepository` (original) | SRP: tenia logica de scoring mezclada con queries de DB | Se extrajo `_score_product`, `_to_candidate` y `_orm_to_record` como funciones puras separadas |
| `AgentOrchestrator` (original) | DIP: instanciaba `OpenRouterLLMClient` internamente | Se cambio a inyeccion de dependencias: el orquestador recibe `LLMClient` en el constructor |
| `LLMClient` (original) | OCP: para agregar un nuevo proveedor habia que modificar la clase | Se introdujo `LLMClient(ABC)` como interfaz; `OpenRouterLLMClient` y `MockLLMClient` son implementaciones separadas |

### Agente de Validacion Arquitectonica

Verifica que la implementacion siga la arquitectura de 4 capas disenada.

**Hallazgos y correcciones aplicadas:**

| Gap detectado | Correccion |
|---|---|
| Router de recomendaciones accedia directamente a la sesion SQLAlchemy | Se movio la logica de construccion de `FarmerContextInput` a una funcion en el service |
| Agente 2 (Researcher) accedia al ORM directamente | Se introdujo `AbstractProductRepository` para desacoplar el agente del ORM |

### Agentes tecnicos especializados

| Agente | Responsabilidad |
|---|---|
| Frontend Component Generator | Genera componentes React siguiendo el patron feature-based |
| Backend Endpoint Generator | Genera endpoints siguiendo la arquitectura de 4 capas |
| SOLID Reviewer | Revisa clases Python contra principios SOLID |
| Database Designer | Revisa diseno relacional y propone mejoras |

---

## Documentacion adicional

- [`Docs/Guia_del_Desarrollador.md`](Docs/Guia_del_Desarrollador.md) — guia tecnica completa con recetas paso a paso
- [`Docs/Spec_validada.md`](Docs/Spec_validada.md) — especificacion validada del MVP
- [`Docs/AgentOrchs.md`](Docs/AgentOrchs.md) — orquestacion detallada de los 4 agentes IA
- [`Docs/database/schema.dbml`](Docs/database/schema.dbml) — esquema DBML completo
- [`Docs/database/create_tables.sql`](Docs/database/create_tables.sql) — DDL inicial

---

## Hitos

| Hito | Fecha |
|---|---|
| Revision con profesor | 8-20 de junio de 2025 |
| Demo final (sales pitch) | 26 de junio de 2025, 9:30-11:20am |

---

## Licencia

Proyecto academico — uso educativo. TEC, Diseno de Software, Semestre II 2025.
