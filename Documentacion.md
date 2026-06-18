## 1. Problem Statement - el problema que resuelve SynapSeed

Los agricultores costarricenses no tienen acceso facil a recomendaciones tecnicas de agroquimicos adaptadas a su cultivo, zona y presupuesto especifico. Recurren a distribuidores que priorizan ventas sobre idoneidad tecnica, o a informacion generica que no considera sus condiciones reales.

Solucion: asistente digital que (dado el contexto del agricultor)  recomienda exactamente que producto comprar, a que dosis, donde conseguirlo y por que, respaldado por regulaciones del SFE.

## 2. Prototipo interactivo - enlace a Figma/Maze con el flujo principal
https://www.figma.com/files/team/1435304554989030854/recents-and-sharing?fuid=1435304553432694147 

## 3. UX Testing - participantes, tareas definidas, capturas, observaciones, métricas

Usuarios participantes en el UX Testing (Pymeboost):
![Participantes](Docs/assets/participantes.png)

### Capturas del prototipo (heatmaps)

Inicio de sesión (primer pantalla del flujo principal)
![Login](Docs/assets/login.png)

Registro (registro de nuevo usuario)
![Registro](Docs/assets/register.png)

Mi cuenta (Pestaña de configuración de cuenta, donde el usuario puede actualizar su información personal y preferencias)
![Mi cuenta](Docs/assets/mi_cuenta.png)

Zonas de cultivo / Fincas (Apartado para agregar y gestionar las zonas de cultivo o fincas del usuario, con detalles como ubicación, tipo de cultivo, tamaño, etc.)
![Zonas](Docs/assets/zonas.png)

Nueva zona de cultivo (Pantalla para confirmar una nueva zona de cultivo)
![Nueva zona](Docs/assets/nueva_zona.png)

Gestión de caso (Pantalla para gestionar un caso específico, donde el usuario puede ingresar detalles sobre un problema agrícola, para recibir recomendaciones personalizadas.)
![Contexto 1](Docs/assets/context1.png)

Confirmar caso (Pantalla para confirmar los detalles del caso ingresado por el usuario, antes de generar las recomendaciones.)
![Confirmar caso](Docs/assets/confirmar_caso.png)

Recomendación de producto e información extra de los agroquímicos (Luego del pipeline)
![Recomendaciones](Docs/assets/recomendaciones.png)

Proveedores (Nombre de proveedores recomendados para adquirir los productos sugeridos, con información de contacto y ubicación + botón de búsqueda en google)
![Proveedores](Docs/assets/proveedores.png)

## 4. Problemas detectados y correcciones - qué problema resolvía cada cambio y criterio de decisión

El primer enfoque del avance de SynapSeed era una integración entre comparativa de productos y compra-venta. Utilizando una técnica de votación, se optó por eliminar la parte de compra-venta y enfocarse en la comparativa de productos, ya que era el núcleo del problema a resolver y permitía una solución más rápida y efectiva para los usuarios. La decisión se basó en la prioridad de entregar valor rápidamente y validar la propuesta de valor central antes de expandirse a funcionalidades adicionales.
![GoalMap](Docs/assets/SynapSeed_Goalmap_votos.png)

## 5. Stack tecnológico frontend 


| Tecnología | Versión | Justificación |
|-----------|---------|--------------|
| React | 19.0.0 | Ecosistema maduro, concurrent rendering, `useTransition` para UX fluida |
| TypeScript | ~5.7.2 | Tipado estático que captura errores en compile-time; contratos de API verificados |
| Vite | 6.0.7 | Build ultra-rápido, HMR nativo, plugin de TailwindCSS sin configuración extra |
| React Router DOM | 7.1.1 | Enrutamiento del lado del cliente con rutas protegidas |
| TanStack React Query | 5.62.16 | Caché de servidor, deduplicación de requests, estados de carga declarativos |
| Zustand | 5.0.2 | Estado global mínimo sin boilerplate Redux; persiste en localStorage |
| react-hook-form | 7.54.2 | Forms performantes (no re-render por cada keystroke); uncontrolled por defecto |
| Zod | 3.24.1 | Validación tipada en runtime; los schemas generan los tipos de TypeScript |
| Axios | 1.7.9 | Cliente HTTP con interceptores para manejar el token JWT globalmente |
| Radix UI | varias | Componentes headless accesibles (a11y nativo), sin estilos propios |
| TailwindCSS | 4.0.0 | CSS-first (sin `tailwind.config.js`), tokens declarados en `globals.css` |
| lucide-react | 0.469.0 | Iconografía SVG consistente |
| Vitest | 2.1.8 | Tests unitarios con API compatible con Jest, integrado a Vite |
| Playwright | 1.49.1 | Tests E2E con soporte multi-browser |

## 6. Hosting y servicios cloud - dónde corre el frontend

### Ambiente Local (MVP)

El frontend corre como contenedor Docker con Vite en modo desarrollo (HMR activo):


```yaml
# docker-compose.yml
frontend:
  build:
    context: ./src/frontend
    dockerfile: Dockerfile
    target: dev
  ports:
    - "${FRONTEND_PORT:-5173}:5173"
  environment:
    VITE_API_URL: http://backend:8000
```


**Proxy de desarrollo:** Vite redirige `/api/*` al backend para evitar CORS en local:


```ts
// src/frontend/vite.config.ts — líneas 22-29
server: {
  proxy: {
    '/api': {
      target: process.env.VITE_API_URL ?? 'http://localhost:8000',
      changeOrigin: true,
    },
  },
},
```


### Producción (post-MVP)


Para producción se compilaría con `npm run build` (salida estática en `/dist`) y se desplegaría en:
- **Vercel / Netlify** — deploy continuo desde GitHub, CDN global, sin servidor.
- **Firebase Hosting** — alternativa con dominio `.web.app`.


El build genera chunks separados por dominio (vendor, query, forms) para reducir el bundle inicial. Configurado en [`vite.config.ts`](../src/frontend/vite.config.ts):


```ts
// src/frontend/vite.config.ts — líneas 43-49
rollupOptions: {
  output: {
    manualChunks: {
      vendor: ['react', 'react-dom', 'react-router-dom'],
      query: ['@tanstack/react-query'],
      forms: ['react-hook-form', 'zod', '@hookform/resolvers'],
    },
  },
},
```


---

## 7. Estructura de carpetas 

```
src/frontend/src/
├── main.tsx                    ← Punto de entrada: monta React + QueryClient + Router
├── App.tsx                     ← Componente raíz (actualmente delega en router)
├── app/
│   ├── router.tsx              ← Definición de todas las rutas (createBrowserRouter)
│   └── ProtectedRoute.tsx      ← Guard: redirige a /login si no autenticado
├── features/                   ← Módulos por dominio de negocio
│   ├── auth/                   ← Login, Register, AuthLayout
│   ├── dashboard/              ← Pantalla post-login
│   ├── layout/                 ← AppLayout (shell de la app autenticada)
│   ├── account/                ← Perfil y cambio de contraseña
│   ├── zones/                  ← CRUD de zonas/fincas
│   └── wizard/                 ← Flujo principal: 4 pasos de recomendación
│       ├── CaseWizardStep1.tsx ← Paso 1: cultivo, zona, condiciones
│       ├── CaseWizardConfirm.tsx ← Paso 2: confirmación
│       ├── CaseWizardStep3.tsx ← Paso 3: resultados SSE + tabla
│       ├── CaseWizardStep4.tsx ← Paso 4: distribuidores
│       ├── schemas.ts          ← Validación Zod del formulario
│       ├── constants.ts        ← Opciones de dropdowns
│       └── recommendationMapper.ts ← Transforma respuesta API a modelo UI
├── stores/
│   ├── authStore.ts            ← Estado de autenticación (Zustand + localStorage)
│   └── wizardStore.ts          ← Estado del wizard (Zustand + localStorage)
├── components/
│   └── ui/                     ← Componentes reutilizables (wrappers de Radix/Tailwind)
├── lib/
│   ├── apiError.ts             ← Normalización de errores HTTP
│   └── cn.ts                   ← Utilidad clsx + tailwind-merge
└── styles/
    └── globals.css             ← Tokens de diseño + reset base (TailwindCSS v4)
```

Cada carpeta en `features/` es un módulo autónomo. Los componentes reutilizables van en `components/ui/`. Las utilidades globales en `lib/`. Esta estructura sigue el patrón **Feature-Sliced Design** adaptado.

## 8. Convenciones de nomenclatura 
| Elemento | Convención | Ejemplo |
|----------|-----------|---------|
| Componentes | PascalCase | `CaseWizardStep1`, `LoginPage` |
| Archivos de componentes | PascalCase + `.tsx` | `LoginPage.tsx` |
| Stores | camelCase + `Store` + `.ts` | `authStore.ts` |
| Hooks | `use` + PascalCase | `useAuthStore`, `useWizardStore` |
| Schemas Zod | camelCase + `Schema` | `caseStep1Schema` |
| Tipos inferidos | PascalCase + `Form` / `Data` | `CaseStep1Form`, `WizardData` |
| Constantes | SCREAMING_SNAKE_CASE | `TEMPERATURE_OPTIONS`, `HUMIDITY_OPTIONS` |
| Carpetas de features | kebab-case | `auth/`, `wizard/`, `zones/` |
| Alias de imports | `@/` apunta a `src/` | `import { router } from '@/app/router'` |

Lineamientos CSS y branding — colores, tipografías, iconografía, espaciados, responsive, logo
Definidos como tokens CSS en [`src/frontend/src/styles/globals.css`](../src/frontend/src/styles/globals.css), usando la sintaxis `@theme` de TailwindCSS v4 (sin archivo de configuración JS).


### Paleta de Colores


```css
/* src/frontend/src/styles/globals.css */
@theme {
  /* Primarios — Verdes agrícolas */
  --color-primary-50:  #f0fdf4;
  --color-primary-500: #22c55e;   /* verde principal */
  --color-primary-600: #16a34a;   /* hover/énfasis */
  --color-primary-700: #15803d;   /* activo/pressed */
  --color-primary-800: #166534;
  --color-primary-900: #14532d;


  /* Secundarios — Tierra/ámbar */
  --color-secondary-500: #eab308;
  --color-secondary-700: #a16207;


  /* Semánticos */
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error:   #dc2626;
  --color-info:    #3b82f6;


  /* Neutros */
  --color-background: #f7f8f2;    /* fondo principal (blanco verdoso) */
  --color-foreground: #111827;    /* texto principal */
  --color-muted:      #f7f8f2;
  --color-border:     #e5e7eb;
  --color-ring:       #16a34a;    /* focus ring accesible */
}
```


### Tipografía


```css
--font-sans: "Inter", ui-sans-serif, system-ui, ...;
--font-mono: "JetBrains Mono", ui-monospace, ...;
```


**Inter** es la fuente principal — moderna, legible a cualquier tamaño, gratuita vía Google Fonts.


### Border Radius


```css
--radius-sm: 0.375rem;
--radius-md: 0.5rem;
--radius-lg: 0.75rem;
--radius-xl: 1rem;
```


### Branding


- **Nombre**: SynapSeed (Synapse + Seed — sinapsis agrícola)
- **Colores principales**: verde agrícola (#22c55e) + tierra (#eab308)
- **Tono visual**: natural, confiable, profesional — alejado de lo corporativo
- **Iconografía**: lucide-react (stroke uniforme de 1.5px, estilo outline)
- **Fondo**: `#f7f8f2` (blanco con toque verdoso, evoca campo)


### Focus Ring Accesible


```css
:focus-visible {
  outline: 2px solid var(--color-ring);  /* #16a34a */
  outline-offset: 2px;
}
```


Cumple WCAG 2.1 AA — el foco es visible en todos los elementos interactivos.


---


## 9. Lineamientos CSS y branding - colores, tipografías, iconografía, espaciados, responsive, logo

Se usa TailwindCSS v4 en modo CSS-first: no existe `tailwind.config.js`. Los tokens de diseno viven como variables CSS y se aplican como utilidades directamente en el JSX.

Paleta de colores:

| Token | Valor | Uso |
|---|---|---|
| Verde primario | `#16A34A` | Botones, iconos OK, acentos de marca |
| Indigo | `#4F46E5` | Badges de ranking |
| Amber | `#F59E0B` | Advertencias y badges intermedios |
| Rojo | `#DC2626` | Errores y estado FAILED |
| Gris texto | `#111827` | Texto principal |
| Gris secundario | `#6B7280` | Labels y subtitulos |
| Borde | `#E5E7EB` | Divisores y tablas |

- Tipografia: Inter (font-sans del sistema).
- Iconografia: Lucide React (`lucide-react`), SVG inline, sin imagenes pesadas.
- Logo: icono `Leaf` en verde primario.
- Responsive: breakpoints estandar de Tailwind (`sm`, `lg`). La grilla de 3 productos colapsa a 1 columna en movil; la tabla comparativa usa `overflow-x-auto`.
- Primitivas reutilizables: `Panel`, `SynapButton`, `CaseStepper`, `PageHeader` en [`src/frontend/src/components/ui/prototype.tsx`](src/frontend/src/components/ui/prototype.tsx).

## 10. Patrones arquitectónicos frontend - Feature-based, presentational vs container, React Query vs Zustand

- Feature-based: cada dominio (auth, wizard, zones, account) es un modulo independiente en `features/`. Una feature no importa de otra; solo comparten `stores/`, `components/ui/` y `lib/`.
- Container / Presentational: las paginas (`LoginPage`, `CaseWizardStep3`) manejan estado y queries; los componentes de UI (`ProductCard`, `Panel`) solo reciben props y renderizan.
- Server state vs client state: React Query para datos de API; Zustand para estado de cliente (ver punto 13).

Referencia: [`src/frontend/src/app/router.tsx`](src/frontend/src/app/router.tsx)

## 11. Patrones de componentes - shadcn/ui wrappers, composición

- shadcn/ui no es un paquete: el codigo de cada componente vive en `components/ui/` y se edita libremente.
- Compound components: Dialog y Select (Radix) usan un padre que controla el estado y slots hijos atomicos.
- Composicion por props: los componentes presentacionales reciben datos ya transformados (ej. `buildProductComparisons`) en vez de hacer fetching.
- `ProtectedRoute` compone rutas privadas con el patron `Outlet` de React Router, sin prop drilling.

## 12. Seguridad frontend - autenticación, JWT en Zustand, expiración de tokens, ProtectedRoute, OWASP

- El JWT (emitido por Supabase Auth) se guarda en `localStorage` via Zustand `persist` (clave `synapseed-auth`).
- `ProtectedRoute` verifica `isAuthenticated && token`: dos condiciones para evitar acceso con un flag stale.
- Logout: `queryClient.clear()` borra el cache de React Query y `navigate('/login', { replace: true })` saca la ruta del historial.
- Expiracion: los JWT de Supabase expiran (default 1h); no hay refresh automatico, al expirar la siguiente peticion da 401 y se re-autentica.

| Riesgo OWASP | Mitigacion |
|---|---|
| A01 Broken Access Control | ProtectedRoute + validacion JWT en backend |
| A02 Cryptographic Failures | JWT de Supabase; contrasenas con bcrypt |
| A03 Injection | Validacion Zod antes de enviar a la API |
| A07 Auth Failures | Token verificado en cada request; logout limpia cache |

Referencias: [`src/frontend/src/app/ProtectedRoute.tsx`](src/frontend/src/app/ProtectedRoute.tsx), [`src/frontend/src/features/layout/AppLayout.tsx`](src/frontend/src/features/layout/AppLayout.tsx)

## 13. Manejo de estado - Zustand (cliente) vs React Query (servidor)

| React Query (estado servidor) | Zustand (estado cliente) |
|---|---|
| Recomendaciones, zonas, catalogs, providers | Token JWT, usuario, isAuthenticated |
| Cache, revalidacion en focus, loading/error automaticos | Paso actual del wizard, datos del formulario |
| No se persiste (datos sensibles/frescos) | Se persiste en localStorage (token) |

Por que la separacion: React Query sabe cuando revalidar; Zustand no. Ningun dato de API debe guardarse en Zustand. `queryClient.clear()` en logout borra todo el estado servidor sin tocar Zustand.

Referencias: [`src/frontend/src/stores/authStore.ts`](src/frontend/src/stores/authStore.ts), [`src/frontend/src/stores/wizardStore.ts`](src/frontend/src/stores/wizardStore.ts)

## 14. Comunicación asíncrona - axios, contratos Zod, retries, manejo de errores

Las llamadas HTTP usan `axios` desde las `queryFn` de React Query. El baseURL viene de `VITE_API_URL`.

```tsx
const { data, isLoading, isError } = useQuery({
  queryKey: ['recommendation', id],
  queryFn: () => axios.get(`/api/v1/recommendations/${id}`, {
    headers: { Authorization: `Bearer ${token}` },
  }).then(r => r.data),
  enabled: !!token && !!id,
})
```

- Contratos: cada formulario tiene un schema Zod usado como `resolver` de react-hook-form; ningun dato invalido llega al backend.
- Retries: React Query reintenta 3 veces en error de red por defecto.
- Errores: `useQuery` expone `isError`; `lib/apiError.ts` extrae el mensaje legible (`error.response.data.detail`).

Referencia: [`src/frontend/src/lib/apiError.ts`](src/frontend/src/lib/apiError.ts)

## 15. SSE y procesos largos - progreso del pipeline en tiempo real

El pipeline tarda 10-50s. Hay dos canales de progreso:

- Backend: el worker publica cada paso en Redis pub/sub; el endpoint `GET /recommendations/stream/{ticket_id}` lo reenvia como `text/event-stream` (SSE).
- Frontend (actual): usa polling del endpoint REST cada 1s mientras el estado es `pending`/`processing`, y actualiza el cache de React Query. Se detiene al pasar a `completed`/`failed`.

```tsx
useEffect(() => {
  if (recommendation?.status !== 'pending' && recommendation?.status !== 'processing') return
  const interval = setInterval(() => {
    axios.get(`/api/v1/recommendations/${id}`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => queryClient.setQueryData(['recommendation', id], r.data))
  }, 1000)
  return () => clearInterval(interval)
}, [id, token, recommendation, queryClient])
```

Referencia: [`src/frontend/src/features/wizard/CaseWizardStep3.tsx`](src/frontend/src/features/wizard/CaseWizardStep3.tsx)

## 16. Storage - localStorage vs memoria

| Dato | Donde | Por que |
|---|---|---|
| JWT token, usuario | localStorage (Zustand persist) | Sobrevive recargas de pagina |
| Paso y datos del wizard | Zustand en memoria | Se limpia al terminar el flujo |
| Cache de recomendaciones, zonas | React Query en memoria | Se limpia en logout |

## 17. Testing frontend - Vitest, React Testing Library, cobertura

```bash
cd src/frontend
npm run test            # Vitest (run)
npm run test:coverage   # cobertura con @vitest/coverage-v8
npm run test:e2e        # Playwright
```

- Unit (Vitest + React Testing Library): helpers (`recommendationMapper`, schemas Zod) y componentes aislados.
- Integration: flujos de wizard con mocks de axios.
- E2E (Playwright): login -> wizard -> resultado contra backend real.
- Cobertura minima esperada: 60% en `features/wizard/` y `stores/`.

## 18. CI/CD frontend - lint, typecheck, build

```
push -> lint (ESLint) -> typecheck (tsc --noEmit) -> test (Vitest) -> build (vite build)
```

```bash
npm run lint        # ESLint + typescript-eslint
npm run typecheck   # tsc -b --noEmit
npm run build       # build de produccion
```

## 19. Optimización de rendimiento - code splitting, memoization

- Code splitting automatico por modulo (Vite).
- `useMemo` en `CaseWizardStep3` para `providers` y `products` (evita recalcular en cada render).
- Iconos SVG inline (Lucide); sin imagenes pesadas.
- React Query cachea por `queryKey` y evita refetch innecesarios.

## 20. Stack tecnológico backend - versiones y justificación

| Tecnologia | Version | Justificacion |
|---|---|---|
| Python | 3.12 | Typing y performance; ecosistema de IA |
| FastAPI | 0.115 | ASGI async, OpenAPI automatico, validacion Pydantic |
| SQLAlchemy | 2.0 | ORM async (asyncpg), Mapped columns tipadas |
| Alembic | latest | Migraciones versionadas; unico que toca el schema |
| Pydantic | v2 | DTOs, validacion y `model_validate` |
| passlib[bcrypt] | latest | Hashing de contrasenas (fallback de auth) |
| python-jose | latest | Firma/verificacion de JWT locales |
| Celery | 5.4 | Cola de tareas para el pipeline (10-50s) |
| Redis | 7 | Broker + result backend + pub/sub SSE |
| PostgreSQL | 16 + pgvector | DB relacional + busqueda semantica |
| LangGraph | 1.2 | Orquestacion de agentes |
| OpenRouter | API | LLM de chat, modelo configurable |
| Gemini | text-embedding-004 | Embeddings de 768 dims |

## 21. Hosting y servicios cloud

- Supabase: PostgreSQL 16 + pgvector + Supabase Auth (externo, no en Docker).
- Redis: contenedor Docker local.
- Backend (FastAPI) y worker (Celery): contenedores Docker locales.
- El MVP corre solo en ambiente local.

## 22. Arquitectura en capas - Router, Service, Repository, Model

```
HTTP -> [Router] -> [Service] -> [Repository] -> [Model] -> DB
```

| Capa | Responsabilidad | No debe |
|---|---|---|
| Router (`api/v1/`) | Recibe y valida HTTP, delega, lanza HTTPException | Contener logica de negocio |
| Service (`services/`) | Toda la logica de negocio, orquesta repos | Saber de HTTP o SQLAlchemy |
| Repository (`repositories/`) | Unico que escribe queries SQLAlchemy | Contener logica de negocio |
| Model (`models/`) | Columnas, relaciones, indices ORM | Logica de negocio |

Referencias: [`src/backend/app/api/v1/auth.py`](src/backend/app/api/v1/auth.py), [`src/backend/app/services/auth_service.py`](src/backend/app/services/auth_service.py), [`src/backend/app/repositories/base.py`](src/backend/app/repositories/base.py)

### Diagramas C4
![c1](Docs/assets/c1.png)
![c2](Docs/assets/c2.png)
![c3](Docs/assets/c3.png)
![c4](Docs/assets/c4.png)

## 23. Patrones de diseño OO - Repository, DIP, Strategy

Repository Pattern: `BaseRepository[T]` provee CRUD generico; cada repo especializado extiende con queries del dominio.

```python
class BaseRepository(Generic[ModelT]):
    async def get_by_id(self, id: int) -> ModelT | None: ...
    async def create(self, data: dict) -> ModelT: ...

class UserRepository(BaseRepository[User]):
    async def get_by_identification(self, identification: str) -> User | None: ...
```

DIP - Abstract Repository: `AbstractProductRepository(ABC)` define el contrato; el orquestador depende de la abstraccion. En produccion se inyecta `SqlAlchemyProductRepository`, en tests `FakeProductRepository`.

Strategy - LLMClient: `LLMClient(ABC)` define `complete_json`; `OpenRouterLLMClient` es produccion y `MockLLMClient` es para tests. Los agentes no saben que proveedor de LLM usan.

Referencias: [`src/backend/app/repositories/base.py`](src/backend/app/repositories/base.py), [`src/backend/app/repositories/product_repository.py`](src/backend/app/repositories/product_repository.py), [`src/backend/app/services/llm_client.py`](src/backend/app/services/llm_client.py)

## 24. Patrones arquitectónicos - Queue-based, Pub/Sub, RAG

Queue-Based Load Leveling (Celery + Redis): un request HTTP no puede bloquearse 10-50s. El endpoint crea un registro PENDING, encola la tarea y retorna `ticket_id` en menos de 100ms; el worker procesa aparte.

Pub/Sub para SSE: el worker publica progreso en `recommendation_progress:{ticket_id}`; el endpoint SSE suscribe y reenvia al navegador.

RAG pipeline: el Agente 2 busca productos por filtros + texto en la DB y los puntua; los datos factuales nunca los inventa el LLM.

Referencias: [`src/backend/app/workers/tasks.py`](src/backend/app/workers/tasks.py), [`src/backend/app/agents/orchestrator.py`](src/backend/app/agents/orchestrator.py)

## 25. Patrones agentic design - Sequential Workflow (Prompt Chaining)

El pipeline usa Sequential Workflow: 4 agentes en orden, cada uno consume la salida del anterior. Un estado compartido `PipelineState` acumula los resultados.

```
FarmerContextInput
  -> Analyzer       -> ContextAnalysisOutput
  -> Researcher     -> ResearchOutput
  -> Legal Validator-> LegalValidationOutput
  -> Synthesizer    -> SynthesisOutput (3 recomendaciones)
```

Reto: pasos con dependencia estricta. Solucion: orquestacion secuencial con estado compartido y callback de progreso por paso. Manejo de excepciones: cualquier fallo marca la recomendacion FAILED y publica el error.

Referencia: [`src/backend/app/agents/orchestrator.py`](src/backend/app/agents/orchestrator.py)

## 26. Diseño de integración de sistemas - fichas por integración

OpenRouter (LLM de chat):
- Protocolo: HTTPS REST (compatible OpenAI). Auth: API Key (`Authorization: Bearer`).
- Throughput: depende del modelo; modelo free 20 RPM. Latencia 5-30s por llamada.
- Config: `OPENROUTER_API_KEY`, `OPENROUTER_CHAT_MODEL`, `OPENROUTER_RPM_LIMIT`.
- Mitigacion de latencia: Celery async (el request retorna ya, el LLM corre en background). Retry con backoff (`tenacity`).
- Clase: [`src/backend/app/services/llm_client.py`](src/backend/app/services/llm_client.py)

Gemini (embeddings):
- Protocolo: HTTPS REST. Auth: API Key.
- Uso: genera embeddings de 768 dims para productos y regulaciones al hacer seeding (no en el path caliente).
- Config: `GEMINI_API_KEY`, `GOOGLE_EMBEDDING_MODEL`, `EMBEDDING_DIM=768`.

Supabase (DB + Auth):
- Protocolo: PostgreSQL wire (asyncpg) + HTTPS REST (Auth).
- Connection pooling: PgBouncer transaction mode, requiere `statement_cache_size=0` en asyncpg.
- Config: `DATABASE_URL` (asyncpg, runtime), `DATABASE_URL_SYNC` (psycopg2, Alembic), `SUPABASE_URL`, `SUPABASE_ANON_KEY`.
- Clase: [`src/backend/app/db/session.py`](src/backend/app/db/session.py)

Redis:
- Protocolo: RESP. Canal 0 = SSE pub/sub, canal 1 = Celery broker, canal 2 = result backend.
- Config: `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`.
- Clase: [`src/backend/app/core/redis.py`](src/backend/app/core/redis.py)

## 27. Middlewares - CORS, manejo de errores, logging

- CORS: `CORSMiddleware` con `allow_origins=settings.backend_cors_origins` (acepta JSON o CSV).
- Errores: los routers convierten excepciones de dominio en `HTTPException`; las no capturadas dan 500.
- Logging: formato `timestamp | nivel | modulo | mensaje`, nivel por `LOG_LEVEL`.

Referencia: [`src/backend/app/main.py`](src/backend/app/main.py)

## 28. Autenticación y autorización - Supabase + fallback bcrypt

```
cedula + password -> POST /api/v1/auth/login
  authenticate_user:
    1. resuelve cedula -> email en tabla users
    2. sign_in_with_password(email, password) en Supabase Auth
    3. Supabase retorna SupabaseSession con access_token (JWT)
    4. fallback: si Supabase da 401, verifica bcrypt local
  build_token_response -> { access_token, refresh_token, expires_in, user }
```

- Login por cedula (no email) porque es el identificador natural del agricultor en CR.
- Validacion en cada request: `get_current_user` intenta decodificar JWT local y, si no, valida contra Supabase via `resolve_user_from_token`.

Referencias: [`src/backend/app/services/auth_service.py`](src/backend/app/services/auth_service.py), [`src/backend/app/core/security.py`](src/backend/app/core/security.py)

## 29. Variables de entorno - tabla completa

| Variable | Descripcion | Ejemplo |
|---|---|---|
| `DATABASE_URL` | asyncpg para runtime | `postgresql+asyncpg://user:pass@db.supabase.co:5432/postgres` |
| `DATABASE_URL_SYNC` | psycopg2 para Alembic | `postgresql+psycopg2://user:pass@db.supabase.co:5432/postgres` |
| `SUPABASE_URL` | URL del proyecto Supabase | `https://xxxx.supabase.co` |
| `SUPABASE_ANON_KEY` | Clave publica de Supabase Auth | `eyJ...` |
| `JWT_SECRET` | Secreto de JWT locales | `secreto-largo-aleatorio` |
| `JWT_EXPIRE_HOURS` | Expiracion del JWT local | `24` |
| `OPENROUTER_API_KEY` | API key de OpenRouter | `sk-or-...` |
| `OPENROUTER_CHAT_MODEL` | Modelo LLM | `openrouter/free` |
| `GEMINI_API_KEY` | API key de Google AI Studio | `AIza...` |
| `REDIS_URL` | Redis SSE pub/sub | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Broker de Celery | `redis://localhost:6379/1` |
| `CELERY_RESULT_BACKEND` | Result backend | `redis://localhost:6379/2` |
| `BACKEND_CORS_ORIGINS` | Origenes permitidos | `["http://localhost:5173"]` |
| `VITE_API_URL` | URL base de la API (frontend) | `http://localhost:8000` |
| `APP_ENV` | Entorno | `development` |

Las lee `pydantic-settings` con tipado en [`src/backend/app/config.py`](src/backend/app/config.py). `.env` esta en `.gitignore`; el `.env.example` trae placeholders.

## 30. Manejo de errores - AuthError, LLMError, HTTPException

- Excepciones de dominio: `AuthError(message, status_code)` y `LLMError`.
- Los routers las capturan y devuelven `HTTPException` con el codigo apropiado.
- FastAPI valida los bodies con Pydantic; si fallan devuelve 422 con detalle por campo.
- Las excepciones no capturadas devuelven 500.

## 31. Observabilidad y monitoreo - logging, health check

- Logging estructurado por modulo (`logging.getLogger(__name__)`).
- `GET /api/v1/health` verifica DB, Redis y LLM (200 si OK, 503 si falla alguno).
- El worker loggea inicio, PROCESSING, cada paso y resultado/error.
- `SENTRY_DSN` opcional activa reporte de errores.

Referencia: [`src/backend/app/api/v1/health.py`](src/backend/app/api/v1/health.py)

## 32. Procesos largos y colas - Celery + Redis

```
POST /recommendations/request  -> crea PENDING + encola + retorna ticket_id
Worker Celery                  -> consume tarea, corre AgentOrchestrator.run()
                               -> actualiza DB (PROCESSING/COMPLETED/FAILED)
                               -> publica progreso en Redis pub/sub
Frontend                       -> polling /recommendations/{id} (o SSE stream)
```

El worker es sincrono; abre un event loop con `asyncio.run()` para correr el pipeline async.

Referencia: [`src/backend/app/workers/tasks.py`](src/backend/app/workers/tasks.py)

## 33. Connection pooling y threading - asyncpg, pool, concurrencia

```python
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,        # 20
    max_overflow=settings.db_max_overflow,  # 10
    connect_args={"statement_cache_size": 0},  # requerido por PgBouncer
)
```

El worker Celery corre con `concurrency=1` (un pipeline por worker); escala horizontalmente con mas workers.

Referencia: [`src/backend/app/db/session.py`](src/backend/app/db/session.py)

## 34. DTOs y validación - Pydantic schemas separados del ORM

Los schemas Pydantic son los DTOs y estan separados de los modelos ORM:

```
app/schemas/
  user.py                   # UserLogin, TokenResponse, UserResponse
  farmer_input.py           # FarmerContextInput (entrada del wizard)
  agent_context.py          # ContextAnalysisOutput (Agente 1)
  agent_products.py         # ProductCandidate, ResearchOutput (Agente 2)
  agent_legal.py            # LegalValidationOutput (Agente 3)
  agent_recommendations.py  # SynthesisOutput, PipelineResult (Agente 4)
```

Conversion ORM -> DTO con `Schema.model_validate(orm_obj)`.

## 35. Pipeline de agentes IA - entrada, proceso, salida, anti-alucinación

| Agente | Entrada | Proceso | Salida |
|---|---|---|---|
| 1. Analyzer | FarmerContextInput | LLM estructura el contexto agronomico | ContextAnalysisOutput |
| 2. Researcher | ContextAnalysisOutput | Busqueda en DB (filtros + ILIKE) + scoring determinista | ResearchOutput (ProductCandidate) |
| 3. Legal Validator | contexto + research | Reglas deterministas + LLM para casos ambiguos | LegalValidationOutput |
| 4. Synthesizer | contexto + validacion | LLM genera 3 recomendaciones rankeadas | SynthesisOutput |

- Anti-alucinacion: precios, dosis, toxicidad e intervalo vienen de la DB; el LLM solo genera texto interpretativo (justificacion, ventajas, riesgos).
- Validador hibrido (Agente 3): si una regulacion es PROHIBIDO -> rechazo automatico; si es RESTRINGIDO -> el LLM interpreta; ante la duda, rechaza (politica conservadora).

Archivos: [`analyzer_agent.py`](src/backend/app/agents/analyzer_agent.py), [`researcher_agent.py`](src/backend/app/agents/researcher_agent.py), [`legal_validator_agent.py`](src/backend/app/agents/legal_validator_agent.py), [`synthesizer_agent.py`](src/backend/app/agents/synthesizer_agent.py)

## 36. Base de datos - DBML

```mermaid
erDiagram 
    users ||--o{ zones : tiene
    users ||--o{ recommendations : solicita
    users |o--o{ audit_logs : genera
    zones |o--o{ recommendations : contextualiza
    distributors |o--o{ products : provee
    recommendations ||--o{ recommendation_products : contiene_3
    products ||--o{ recommendation_products : aparece_en

    users {
        uuid id PK
        varchar identification UK "cedula login"
        varchar email UK
        varchar password_hash "hash bcrypt"
        varchar full_name
        varchar phone
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    zones {
        uuid id PK
        uuid user_id FK
        varchar name
        varchar soil_type "arcilloso arenoso franco"
        varchar humidity "baja media alta"
        varchar temperature "rango en grados C"
        varchar water_quality "buena regular mala"
        varchar location
        timestamptz created_at
        timestamptz updated_at
    }

    distributors {
        uuid id PK
        varchar name
        varchar email
        varchar phone
        varchar location
        varchar website
        boolean is_active
        timestamptz created_at
    }

    products {
        uuid id PK
        varchar name "nombre comercial"
        varchar active_ingredient
        text description
        varchar category "herbicida fungicida insecticida"
        varchar formulation
        varchar concentration
        varchar dosage_per_hectare
        varchar application_method
        int safety_interval_days "periodo pre cosecha"
        float price_per_liter "CRC"
        uuid distributor_id FK
        varchar sfe_registration
        varchar sfe_status "active expired revoked"
        varchar toxicity_band "I II III IV"
        vector embedding "768 dims pgvector"
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    recommendations {
        uuid id PK
        varchar ticket_id UK "tracking SSE"
        uuid user_id FK
        uuid zone_id FK "null si elige Ninguna"
        varchar status "pending a completed o failed"
        varchar crop
        varchar crop_stage
        varchar affected_area
        varchar soil_type
        varchar humidity
        varchar temperature
        varchar water_quality
        varchar problem_to_solve
        varchar last_agrochemical
        varchar max_budget_per_liter
        jsonb agent_context "Agente 1"
        jsonb agent_research "Agente 2 RAG"
        jsonb agent_validation "Agente 3"
        jsonb final_recommendation "Agente 4"
        int processing_time_ms
        text error_message
        timestamptz created_at
        timestamptz completed_at
    }

    recommendation_products {
        uuid id PK
        uuid recommendation_id FK
        uuid product_id FK
        int rank "1 2 o 3"
        text justification
        varchar recommended_dosage
        float estimated_cost
        text compatibility_notes
        timestamptz created_at
    }

    regulations {
        uuid id PK
        varchar regulation_code UK
        varchar title
        varchar issuing_body "SFE MAG SENASA"
        text description
        jsonb prohibited_substances
        jsonb restricted_crops
        boolean is_active
        varchar source_url
        vector embedding "768 dims"
        timestamptz created_at
    }

    audit_logs {
        uuid id PK
        uuid user_id FK
        varchar action "login register create_recommendation"
        varchar entity_type
        uuid entity_id
        jsonb details
        varchar ip_address
        timestamptz created_at
    }
```

| Tabla | Proposito | Notas |
|---|---|---|
| `users` | Agricultores | `identification` (cedula) login; `auth_user_id` liga Supabase |
| `zones` | Fincas del agricultor | FK a users |
| `products` | Catalogo SFE | `embedding` vector(768) |
| `distributors` | Distribuidores por producto | FK a products |
| `recommendations` | Solicitudes | Status PENDING/PROCESSING/COMPLETED/FAILED |
| `recommendation_products` | 3 productos por solicitud | FK a recommendations y products |
| `regulations` | Regulaciones SFE/MAG | `embedding` vector(768); action PROHIBIDO/RESTRINGIDO/PERMITIDO |
| `lmr` | Limites maximos de residuos | FK a products |
| `audit_log` | Trazabilidad de acciones | FK a users |

```
users (1)-(N) zones | recommendations | audit_log
products (1)-(N) distributors | lmr
products (N)-(M) recommendations  [via recommendation_products]
regulations  (independiente, usada por Agente 3)
```

Esquema completo: [`Docs/database/schema.dbml`](Docs/database/schema.dbml)

## 37. Scripts de DB - migraciones, seeding, rollback

```bash
alembic upgrade head                              # aplica migraciones
alembic revision --autogenerate -m "descripcion" # genera migracion
alembic downgrade -1                              # rollback
docker compose exec backend python -m app.db.seed  # carga datos iniciales
```

El seeding carga productos del catalogo SFE, genera sus embeddings con Gemini e inserta distribuidores y regulaciones.

Referencia: [`src/backend/app/db/seed.py`](src/backend/app/db/seed.py)

## 38. Seguridad de datos - cifrado, audit_log, secretos

- Cifrado en transito: TLS hacia Supabase.
- Contrasenas: bcrypt con salt (passlib); nunca en claro.
- Secretos: en `.env` (gitignored), nunca en codigo.
- Auditoria: tabla `audit_log` con timestamp y user_id.
- Soft delete: `is_active=False` en usuarios.
- Backups: provistos por Supabase; no hay backups locales.

## 39. Testing backend - pytest, cobertura, mocks

```bash
cd src/backend
pytest                              # todos
pytest tests/path::test_name        # uno
pytest --cov=app --cov-report=term-missing
```

- Unit: agentes con `MockLLMClient` y `FakeProductRepository` (sin HTTP ni DB).
- Integration: endpoints con TestClient y DB de test.
- Health check como smoke test.
- Cobertura esperada: 70% en `agents/`, 60% en `services/`, 50% en `api/v1/`.

## 40. CI/CD backend - ruff, mypy, pytest

```
push -> ruff check -> ruff format --check -> mypy -> pytest -> build Docker
```

```bash
ruff check . && ruff format .
mypy app
pytest --cov=app
```

## 41. Alcance formal del MVP - Core, Supporting, Out of scope, User journeys

Core Features:
- Registro y login con cedula (Supabase Auth + JWT).
- Wizard para capturar el contexto agricola.
- Pipeline de 4 agentes que genera 3 recomendaciones rankeadas.
- Tabla comparativa (dosis, precio, toxicidad, intervalo de seguridad).
- Listado de distribuidores por producto.
- Historial de recomendaciones.
- Gestion de fincas (CRUD de zonas).

Supporting Features:
- Perfil de cuenta (solo lectura).
- Catalogs (cultivos, suelos, problemas) cargados desde DB al arrancar.

Out of Scope:
- Compra/pedido de productos (solo informacion).
- Notificaciones push/email, mapa de distribuidores, app movil nativa, multilenguaje, roles.

User journeys en scope:
1. Login -> wizard -> espera (10-50s) -> 3 productos + tabla -> proveedores.
2. Agregar finca -> seleccionarla en el wizard para pre-llenar condiciones.
3. Dashboard -> historial -> abrir una recomendacion anterior.

## 42. Cómo correr el proyecto - prerrequisitos, .env, docker compose

Prerrequisitos: Docker 24+ y Compose v2, Git, API key de OpenRouter, API key de Google AI Studio, proyecto Supabase.

```bash
git clone https://github.com/xHellish/synapseed.git
cd synapseed
cp .env.example .env     # editar con valores reales
docker compose up -d --build
docker compose logs -f backend worker
```

Servicios: frontend `:5173`, backend `:8000` (`/docs` Swagger), worker (sin puerto), redis `:6379`. La DB es Supabase (externa). Al arrancar, el backend corre `alembic upgrade head`.

Comandos utiles:

```bash
docker compose down              # detener
docker compose down -v           # resetear Redis
docker compose exec backend bash # shell
docker compose build backend && docker compose up -d backend
```

## 43. Ejecución por capa - Frontend, Backend, Data Layer, Worker

Backend:

```bash
cd src/backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Worker (otra terminal):

```bash
celery -A app.workers.celery_app worker --loglevel=info --concurrency=1
```

Frontend:

```bash
cd src/frontend
npm install
npm run dev    # http://localhost:5173
```

Data layer: PostgreSQL + pgvector en Supabase (externo); Redis local via Docker.

## 44. Seed data - cargar datos iniciales para la demo

```bash
docker compose exec backend python -m app.db.seed
```

Inserta productos del catalogo SFE (con embeddings de Gemini), distribuidores y regulaciones, para que el pipeline tenga productos que recomendar en la demo.

Referencia: [`src/backend/app/db/seed.py`](src/backend/app/db/seed.py)

## 45. Agentes de IA usados en desarrollo - hallazgos y correcciones

Agente SOLID (solid-code-architect):

| Clase | Violacion | Correccion |
|---|---|---|
| ProductRepository | SRP: scoring mezclado con queries | Se extrajeron `_score_product`, `_to_candidate`, `_orm_to_record` |
| AgentOrchestrator | DIP: instanciaba el LLM client | Inyeccion de dependencias por constructor |
| LLMClient | OCP: agregar proveedor requeria modificar la clase | `LLMClient(ABC)` + implementaciones separadas |

Agente de Validacion Arquitectonica:

| Gap | Correccion |
|---|---|
| Router accedia a la sesion SQLAlchemy directo | Logica movida al service |
| Agente Researcher accedia al ORM | Se introdujo `AbstractProductRepository` |

Agentes tecnicos especializados: generador de componentes (frontend), generador de endpoints (backend), revisor SOLID, disenador de base de datos. Cada uno aplica validaciones antes de generar codigo final.

