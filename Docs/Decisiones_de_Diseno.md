# SynapSeed — Decisiones de Diseño y Guía de Defensa (Caso #2)

> Documento de preparación para la revisión oral del Caso #2.
> El profesor evaluará el **dominio sobre las decisiones de diseño**, vistas como
> una **pieza integral** de toda la solución, respaldadas con **evidencia en el repositorio**.
>
> No memorices: **entiende el "por qué"** de cada decisión. Cada sección trae
> la decisión, la alternativa descartada, la justificación y dónde está la evidencia en `/src`.

---

## 0. Resumen ejecutivo (elevator pitch técnico — 60 segundos)

SynapSeed es una plataforma que recomienda agroquímicos a agricultores costarricenses.
El agricultor describe su caso (cultivo, zona, problema, presupuesto) y un **pipeline de
4 agentes de IA** le devuelve **exactamente 3 productos rankeados** con tabla comparativa
y sus proveedores. **Solo información, nunca compras.**

La arquitectura es un **monorepo** con tres piezas desacopladas:
- **Frontend** React 19 + Vite + TypeScript (SPA con wizard de 4 pasos).
- **Backend** FastAPI en **capas** (Routers → Services → Repositories → Models).
- **Pipeline de IA** asíncrono ejecutado por **Celery**, con progreso en tiempo real vía **SSE**.

La decisión central de diseño: **separar el razonamiento en 4 agentes especializados**
en vez de un único prompt monolítico, porque un solo LLM tratando de analizar contexto +
buscar en catálogo + validar normativa + sintetizar **alucina y falla en formato**.

---

## 1. El problema y por qué la arquitectura lo resuelve

| Reto del dominio | Riesgo si se hace "tradicional" | Decisión de diseño |
|---|---|---|
| El LLM debe cruzar catálogo + normativa + contexto | Un solo prompt sobrecarga el límite lógico → alucinaciones | **4 agentes secuenciales** con estado compartido |
| El LLM puede inventar productos/precios | Recomendar un agroquímico inexistente o ilegal | **Datos factuales solo de la DB**; el LLM solo interpreta |
| La generación tarda 10–50 s | Si fuera síncrono, el HTTP haría timeout | **Proceso asíncrono** (Celery) + **HTTP 202** + **ticket_id** |
| El usuario necesita feedback del progreso | Polling agresivo o conexión bidireccional cara | **SSE** (unidireccional, ligero) sobre Redis pub/sub |
| Recomendar algo prohibido por el SFE | Responsabilidad legal | **Validador legal híbrido**: reglas + LLM |

Evidencia: [`Docs/AgentOrchs.md`](AgentOrchs.md), [`orchestrator.py`](../src/backend/app/agents/orchestrator.py)

---

## 2. Decisiones de arquitectura (con su "por qué")

### 2.1 Monorepo con backend y frontend independientes
- **Decisión:** un solo repo, dos apps que se despliegan por separado, orquestadas con Docker Compose.
- **Por qué:** un equipo pequeño, revisión académica única, y todos necesitan ver todo. Evita la sobrecarga de coordinar múltiples repos.
- **Alternativa descartada:** polyrepo (un repo por servicio) → demasiada fricción para 5 personas.

### 2.2 Diseño en capas en el backend
```
HTTP → Routers (api/v1/) → Services (services/) → Repositories (repositories/) → Models (models/)
                                     ↓
                              Schemas (DTOs Pydantic)
```
- **Routers:** reciben HTTP, validan con Pydantic, delegan. **No** tienen lógica de negocio.
- **Services:** lógica de negocio. **No** saben de HTTP ni de SQL crudo.
- **Repositories:** **único** lugar con acceso a la DB (SQLAlchemy async).
- **Models:** ORM. **Schemas:** DTOs separados de los modelos (no se expone el ORM).
- **Por qué:** testabilidad y cambio aislado. Puedo cambiar la DB sin tocar los routers.
- **Evidencia:** [`zones.py`](../src/backend/app/api/v1/zones.py) (router) → [`zone_repository.py`](../src/backend/app/repositories/zone_repository.py) (repo) → [`zone.py`](../src/backend/app/models/zone.py) (model).
- **Honestidad:** la capa de servicios **no está completa** en todos los dominios. Hoy `zones.py` y `recommendations.py` mezclan routing con lógica (ver §13 y §14). Es una deuda técnica **identificada y con plan**, no un descuido.

### 2.3 Asíncrono de punta a punta
- SQLAlchemy 2.0 **async** + `asyncpg`. FastAPI es async-first.
- **Por qué:** el backend hace I/O intensivo (DB, Redis, llamadas LLM). Async maximiza concurrencia sin hilos.

### 2.4 Procesamiento pesado fuera del request (Celery)
- El endpoint `POST /recommendations/request` **encola** y responde `202 Accepted` con un `ticket_id`. El worker hace el trabajo de 10–50 s.
- **Evidencia:** [`recommendations.py:63`](../src/backend/app/api/v1/recommendations.py) (`generate_recommendation.delay(ticket_id)`), [`tasks.py`](../src/backend/app/workers/tasks.py).

### 2.5 SSE en vez de WebSockets (decisión explícita y defendible)
- **Decisión:** Server-Sent Events para el progreso del pipeline. **WebSockets prohibido** para este flujo.
- **Por qué:** la notificación es **unidireccional** (servidor → cliente). WebSocket es bidireccional y gastaría recursos del servidor sin necesidad. SSE corre sobre HTTP normal, reconecta solo, y es más simple.
- **Evidencia:** [`recommendations.py` endpoint `stream()`](../src/backend/app/api/v1/recommendations.py), [`AgentOrchs.md`](AgentOrchs.md) ("Obligatorio usar Server-Sent Events y prohibido usar WebSockets").

### 2.6 Supabase como única fuente de datos y autenticación
- **Decisión:** PostgreSQL + Auth gestionados por Supabase. No hay Postgres local en el stack de desarrollo cotidiano.
- **Por qué:** pgvector incluido, Auth lista (JWT), capa gratuita suficiente para el MVP, una sola fuente de verdad para todo el equipo.
- **Servicios locales:** Redis, Backend, Worker, Frontend.

---

## 3. Patrones arquitectónicos implementados

### 3.1 Layered Architecture (capas)
Ya descrito en §2.2. Es el patrón estructural base del backend.

### 3.2 Background Worker / Queue-Based Load Leveling
- **Reto:** el LLM responde en 10–50 s y tiene límites de tasa (RPM).
- **Solución:** Celery + Redis como cola. El worker consume a un ritmo controlado (`worker_prefetch_multiplier=1`, `concurrency=1`) y actúa de **amortiguador** ante picos de tráfico.
- **Clases/componentes participantes:**
  - *Productor:* el endpoint FastAPI (`request_recommendation`).
  - *Cola:* Redis (broker de Celery).
  - *Consumidor:* `generate_recommendation` → `async_run_recommendation_pipeline`.
  - *Notificador:* `publish_progress()` (Redis pub/sub) → endpoint SSE.
- **Manejo de excepciones:** si el pipeline falla, el worker marca `FAILED`, hace rollback y publica un evento SSE de error. **Evidencia:** [`tasks.py:141-149`](../src/backend/app/workers/tasks.py).

### 3.3 Publish/Subscribe (Redis pub/sub para SSE)
- El worker publica en el canal `recommendation_progress:{ticket_id}`; el endpoint SSE se suscribe y reenvía al navegador.
- **Por qué:** desacopla quién genera el progreso (worker) de quién lo entrega (API). El worker no conoce las conexiones HTTP abiertas.

---

## 4. Patrones de diseño orientado a objetos

> Para cada patrón: qué problema resuelve, clases participantes, y dónde está en `/src`.

### 4.1 Repository Pattern
- **Qué:** abstrae el acceso a datos. La lógica de negocio no escribe SQL.
- **Clases:** `BaseRepository[ModelT]` (genérico) → `ProductRepository`, `ZoneRepository`, `RecommendationRepository`, etc.
- **Cómo:** `BaseRepository` usa **Generics** (`Generic[ModelT]`) para CRUD reutilizable; cada repo concreto agrega queries específicas.
- **Evidencia:** [`base.py`](../src/backend/app/repositories/base.py), [`product_repository.py`](../src/backend/app/repositories/product_repository.py).

### 4.2 Dependency Inversion vía interfaz abstracta (el ejemplo más fuerte)
- **Qué:** el pipeline de agentes **no depende del ORM**. Depende de una abstracción.
- **Clases:** `AbstractProductRepository(ABC)` define el contrato `search_candidates()`. El agente investigador recibe esa abstracción, no la implementación concreta.
- **Por qué importa:** en los tests inyecto un repo *mock* sin tocar la DB; en producción inyecto el real con pgvector.
- **Evidencia:** [`product_repository.py:194`](../src/backend/app/repositories/product_repository.py) (`AbstractProductRepository`), usado en [`researcher_agent.py`](../src/backend/app/agents/researcher_agent.py).

### 4.3 DTO Pattern (Data Transfer Objects)
- **Qué:** los datos que cruzan capas no son objetos ORM, son DTOs.
- **Dos formas:**
  1. **Schemas Pydantic** para HTTP (validación entrada/salida): [`schemas/`](../src/backend/app/schemas/).
  2. **`ProductRecord` (dataclass frozen)** para pasar productos al pipeline **desacoplados del ORM**: [`product_repository.py:177`](../src/backend/app/repositories/product_repository.py).
- **Por qué:** no exponer el modelo de DB al exterior; evitar acoplar el pipeline a SQLAlchemy.

### 4.4 Adapter + Strategy en el cliente LLM
- **Qué:** `LLMClient(ABC)` define el contrato (`complete_json`, `complete_text`). Dos implementaciones:
  - `OpenRouterLLMClient` (producción, habla con OpenRouter).
  - `MockLLMClient` (tests, respuestas deterministas).
- **Por qué:** puedo testear todo el pipeline **sin gastar tokens ni depender de la red**. Cambiar de proveedor = nueva implementación, sin tocar los agentes.
- **Evidencia:** [`llm_client.py`](../src/backend/app/services/llm_client.py).

### 4.5 Orchestrator / Pipeline
- **Qué:** `AgentOrchestrator.run()` ejecuta los 4 agentes en orden pasando un `PipelineState` compartido.
- **Por qué un orquestador propio y no LangGraph directo:** **testabilidad primero**. El orquestador es una clase simple, fácil de testear; cada paso es una función pura `(input, deps) → output`. Está **diseñado para migrar a LangGraph** (cada método privado puede convertirse en nodo).
- **Evidencia:** [`orchestrator.py`](../src/backend/app/agents/orchestrator.py), [`state.py`](../src/backend/app/agents/state.py).

### 4.6 Dependency Injection (FastAPI `Depends`)
- **Qué:** las dependencias (sesión DB, usuario actual) se inyectan, no se instancian.
- **Evidencia:** [`dependencies.py`](../src/backend/app/dependencies.py), `get_current_user` en [`security.py`](../src/backend/app/core/security.py).

---

## 5. Patrones agénticos de IA

> Este es el corazón "innovador" del proyecto. El profe lo va a sondear.

### 5.1 Patrón híbrido: Sequential Pipeline + Tool Use + estado compartido
- **Nombre del workflow:** *Generación Inteligente de Recomendaciones Agroquímicas*.
- **Los 4 agentes (en orden):**
  1. **Analizador de contexto** — resume el caso del agricultor en un texto apto para RAG. (LLM)
  2. **Investigador (RAG)** — busca productos candidatos con búsqueda semántica pgvector. (Tool use: DB)
  3. **Validador legal** — descarta productos contra regulaciones del SFE. (Híbrido: reglas + LLM)
  4. **Sintetizador** — produce exactamente 3 recomendaciones rankeadas + texto interpretativo. (LLM)
- **Estado compartido:** `PipelineState` acumula la salida de cada agente y la pasa al siguiente.

### 5.2 Decisión anti-alucinación (la más importante para defender la confiabilidad)
- **Regla de oro:** *los datos factuales (nombre, ingrediente, precio, dosis) salen SIEMPRE de la base de datos. El LLM solo genera texto interpretativo (justificación, ventajas, riesgos) y estima solo cuando el dato no existe.*
- **Evidencia:** [`synthesizer_agent.py`](../src/backend/app/agents/synthesizer_agent.py) — los IDs y nombres vienen de `top` (DB); el LLM solo aporta `justificacion`, `ventajas`, `riesgos`. El investigador "nunca inventa productos" ([`researcher_agent.py`](../src/backend/app/agents/researcher_agent.py)).

### 5.3 Validador legal híbrido (defensa en profundidad)
- **Dos capas de validación:**
  1. **Reglas determinísticas** (`_rule_based_discard`): si el ingrediente activo aparece literalmente en una sustancia prohibida, se descarta sin preguntarle al LLM.
  2. **Revisión LLM**: interpreta la normativa para los sobrevivientes.
- **Política conservadora:** *ante duda, NO se valida.* Solo se aprueban los productos que el LLM confirma explícitamente; los demás se descartan "sin asumir validez por omisión".
- **Por qué:** es un dominio con responsabilidad legal. Prefiero descartar de más que recomendar algo ilegal.
- **Evidencia:** [`legal_validator_agent.py:43`](../src/backend/app/agents/legal_validator_agent.py) (reglas) y `:172` (política conservadora).

### 5.4 RAG con pgvector y fallback
- Búsqueda semántica vectorial (embeddings 768-dim de Gemini). Si la búsqueda vectorial no está disponible, **cae a filtros SQL** y lo reporta como advertencia.
- **Por qué embeddings de Gemini y chat de OpenRouter:** separación por costo/capacidad. Gemini da embeddings gratis; OpenRouter da acceso a modelos de chat. Cada proveedor para lo que mejor hace.
- **Evidencia:** `search_candidates` en [`product_repository.py`](../src/backend/app/repositories/product_repository.py), método reportado por [`researcher_agent.py`](../src/backend/app/agents/researcher_agent.py).

---

## 6. El pipeline paso a paso (reglas de negocio no triviales)

> El profe pidió "documentar paso a paso las reglas de negocio que van más allá de CRUD".

1. **Entrada:** `FarmerContextInput` (cultivo, etapa, problema, suelo, humedad, temperatura, agua, presupuesto).
2. **Analizador:** LLM → `ContextAnalysisOutput` con `resumen_para_rag`, `categoria_producto_sugerida`, `tipo_proteccion_necesaria`, `confianza`.
3. **Investigador:** `search_candidates(context, limit=15)` → lista de `ProductCandidate` + método ("vectorial" | "filtros").
4. **Validador legal:**
   - Si no hay regulaciones → todo descartado, `normativa_insuficiente=True`.
   - Descarte por reglas → sobrevivientes → revisión LLM → solo IDs confirmados se validan.
   - Calcula `nivel_riesgo_legal` y `confianza` (degradada si la normativa fue insuficiente).
5. **Sintetizador:**
   - Toma los **top 3** por `score_relevancia`.
   - Datos factuales de DB; si falta dosis/precio/toxicidad/intervalo, el LLM **estima** (con rangos realistas de precio en ₡/litro).
   - Devuelve `SynthesisOutput` con ≤3 `ProductRecommendation`.
6. **Persistencia:** el worker limpia recomendaciones previas (idempotencia), inserta los 3 productos, marca `COMPLETED` y publica SSE `completed`.

**Idempotencia:** si el mismo ticket se procesa dos veces, `remove_products()` evita duplicados. **Evidencia:** [`tasks.py:97-98`](../src/backend/app/workers/tasks.py).

---

## 7. Decisiones de la capa de datos

### 7.1 Motor: PostgreSQL 16 + pgvector
- **Por qué Postgres y no NoSQL:** los datos son **relacionales** (usuarios, zonas, recomendaciones, productos con FKs). pgvector añade búsqueda semántica **sin** otra base de datos especializada → una sola tecnología para datos relacionales + vectoriales.

### 7.2 Migraciones con Alembic
- Versionado del esquema, idempotencia en migraciones que corren tanto en local como en Supabase.
- Dos URLs: `DATABASE_URL` (asyncpg, runtime) y `DATABASE_URL_SYNC` (psycopg2, solo Alembic).
- **Evidencia:** [`alembic/versions/`](../src/backend/alembic/versions/).

### 7.3 Tablas clave
`users`, `zones`, `products` (embedding 768), `distributors`, `product_distributors` (M:N), `recommendations`, `recommendation_products`, `regulations` (embedding), `lmrs` (límites máximos de residuos), `audit_logs`.

### 7.4 LMR — Límites Máximos de Residuos (regla de negocio real del agro CR)
- Tabla `lmrs` con ~8.500 registros (plaguicida × cultivo → límite nacional).
- El detalle de recomendación cruza ingrediente activo + cultivo para mostrar el LMR del SFE.
- **Evidencia:** [`lmr_repository.py`](../src/backend/app/repositories/lmr_repository.py) (incluye normalización de acentos y sinónimos químicos).

### 7.5 Auditoría
- `audit_logs` registra acciones (login, crear recomendación, ver, etc.) para trazabilidad.
- **Evidencia:** [`audit_repository.py`](../src/backend/app/repositories/audit_repository.py).

---

## 8. Decisiones del frontend

- **Stack:** React 19 + Vite 6 + TypeScript 5.7 + TailwindCSS v4 (CSS-first, sin `tailwind.config.js`) + shadcn/ui.
- **Estado:** **Zustand** (global ligero: auth, wizard) + **TanStack React Query** (estado de servidor: cache, refetch, polling).
  - **Por qué dos:** separar estado **de cliente** (UI, sesión) del estado **de servidor** (datos remotos con cache). React Query maneja cache/retries; Zustand maneja lo local.
- **Formularios:** react-hook-form + **zod** (validación declarativa, mismo espíritu que Pydantic en el back).
- **Organización:** por **features** (`features/auth`, `features/wizard`, `features/zones`, ...), no por tipo de archivo. Escala mejor.
- **Flujo principal:** wizard de 4 pasos (caso → confirmación → progreso SSE → resultados → proveedores).
- **Evidencia:** [`features/wizard/`](../src/frontend/src/features/wizard/), [`stores/`](../src/frontend/src/stores/), [`router.tsx`](../src/frontend/src/app/router.tsx).
- **Decisión UX reciente:** si el usuario elige una finca, se **ocultan** los campos de ambiente (los aporta la zona). Cultivos cargados **dinámicamente** desde la tabla `lmrs`, no hardcodeados.

---

## 9. Seguridad

| Aspecto | Decisión | Evidencia |
|---|---|---|
| Passwords | Hash **bcrypt** (nunca texto plano) | [`security.py`](../src/backend/app/core/security.py) |
| Login | Por **cédula** (identification), no email | [`auth.py`](../src/backend/app/api/v1/auth.py) |
| Sesión | **JWT** Bearer, expiración configurable (24 h) | `create_access_token` |
| Auth principal | **Supabase Auth** + fallback JWT local | [`auth_service.py`](../src/backend/app/services/auth_service.py) |
| CORS | Lista blanca de orígenes (`BACKEND_CORS_ORIGINS`) | [`main.py`](../src/backend/app/main.py) |
| Secretos | Solo en `.env`, nunca en el repo | `.env.example` |
| Validación de entrada | Pydantic (back) + zod (front) | `schemas/`, `features/*/schemas.ts` |
| Autorización | Cada recurso valida pertenencia al `user_id` | `get_by_id_and_user` en repos |

- **Por qué cédula y no email:** es el identificador natural del agricultor en CR y reduce fricción de registro.
- **OWASP:** validación de entrada (inyección), JWT firmados (broken auth), CORS restringido, autorización por dueño (broken access control).

---

## 10. Comunicación asíncrona, procesos largos, errores

- **Proceso largo:** patrón async completo (202 → ticket → worker → SSE). El front hace polling de respaldo cada 1 s además del SSE (defensa ante reconexión).
- **Manejo de errores en capas:** repos lanzan/retornan `None`; services traducen a errores de negocio; routers a `HTTPException` con código correcto.
- **Reintentos LLM:** `tenacity` con backoff exponencial dentro del cliente LLM (`max_retries=0` en el SDK porque tenacity controla los reintentos, evitando doble retry).
- **Health check:** `GET /api/v1/health` valida DB + Redis + LLM.
- **Observabilidad:** logging estructurado; `SENTRY_DSN` previsto (no activo en MVP).

---

## 11. Testing

- **Backend:** pytest. El diseño habilita tests sin red gracias a `MockLLMClient` y a las abstracciones de repositorio.
  - **Evidencia:** [`tests/agents/test_synthesizer_agent.py`](../src/backend/tests/agents/), [`tests/api/v1/test_recommendations.py`](../src/backend/tests/api/v1/).
- **Frontend:** Vitest + React Testing Library.
- **Meta de cobertura:** ≥80% (declarada en la spec).
- **Punto a defender:** el diseño (DIP + mocks) es lo que **hace testeable** el pipeline de IA — sin abstracciones, habría que llamar al LLM real en cada test.

---

## 12. CI/CD y ambientes

- **Contenedores:** Dockerfile multi-stage (dev/builder/prod) por app. Worker con su propio `Dockerfile.worker`.
- **Dev:** Docker Compose con HMR (frontend) y `--reload` (backend) vía volúmenes montados.
- **Calidad:** `ruff check` + `ruff format` + `mypy` (back); ESLint + `tsc --noEmit` (front).
- **Evidencia:** [`docker-compose.yml`](../docker-compose.yml), [`Dockerfile`](../src/backend/Dockerfile).

---

## 13. SOLID: estado actual y plan (sé honesto aquí)

Existe un análisis SOLID formal del backend: [`Docs/sugerencias_SOLID.md`](sugerencias_SOLID.md).

**Archivos limpios** (úsalos como ejemplo de lo que sí está bien):
- [`auth.py`](../src/backend/app/api/v1/auth.py) — capa de routing delgada, delega al servicio.
- [`dependencies.py`](../src/backend/app/dependencies.py) — DI correcta.

**Violaciones identificadas (con plan de refactor, no corregidas aún):**
| Archivo | Violación | Refactor propuesto |
|---|---|---|
| `recommendations.py` | SRP/DIP: `stream()` mezcla DB+Redis+SSE | extraer `RecommendationStreamService` + `TaskDispatcher` |
| `zones.py` | SRP/DIP: routing + mapeos + repos instanciados | `ZoneService` + `LocationMapper` |
| `auth_service.py` | OCP: `if _local_auth_enabled()` repetido | **Strategy Pattern** (`AuthStrategy`) |
| `main.py` | OCP: routers hard-coded | registro plugin-based |

**Cómo defenderlo:** "Usamos agentes SOLID para **auditar** el código; el reporte detectó violaciones reales, las priorizamos (P0–P3) y tenemos un roadmap de ~7.5 h. Algunas son deuda consciente: el Strategy de auth se justifica solo cuando agreguemos un tercer proveedor."

---

## 14. Gaps diseño ↔ implementación (anticipa esta pregunta)

> El profe explícitamente busca "detectar gaps entre diseño y código". **Adelántate y nómbralos tú.**

| Tema | Documentado (`schema.dbml` / spec) | Implementado (código real) | Cómo defenderlo |
|---|---|---|---|
| Tipo de PK | `uuid` | `int` serial (`IDMixin`) | El DBML fue el diseño inicial; en implementación se optó por `int` serial por simplicidad de seeding y debugging del MVP |
| Idioma de campos | inglés (`name`, `active_ingredient`) | español (`nombre_comercial`, `ingrediente_activo`) | Alineación con el dominio (datos del SFE vienen en español) |
| Resultados de agentes | columnas `jsonb` en `recommendations` (`agent_context`, `final_recommendation`...) | tabla `recommendation_products` (relacional) | Se prefirió modelo **relacional** consultable a un blob JSON; mejor para la tabla comparativa |
| Producto↔Distribuidor | FK directa `distributor_id` | tabla intermedia `product_distributors` (M:N) | Un producto lo venden varios distribuidores → M:N es lo correcto |
| Tabla `lmrs` | no existía en el DBML | implementada (~8.500 filas) | Requisito real (LMR del SFE) descubierto durante el desarrollo |
| Postgres local | README menciona "5 servicios" con postgres | Supabase, 4 servicios locales | Migración a Supabase como única fuente; **el README está desactualizado en este punto** |
| Campos de recomendación | `problem_to_solve`, `max_budget_per_liter`, `affected_area`, `processing_time_ms` | `problem`, `problem_category`, `budget_range`, `current_step` | Renombrados/ajustados durante implementación |

**Frase clave para la defensa:** *"El DBML y la spec fueron nuestro diseño de partida. Donde el código difiere, fue una decisión consciente tomada al implementar, y puedo justificar cada una. La documentación que quedó desactualizada (postgres local en el README) es la deuda que reconozco."*

---

## 15. Banco de preguntas probables y cómo responder

**P: ¿Por qué 4 agentes y no uno solo?**
R: Un solo LLM analizando contexto + buscando en catálogo + validando normativa + sintetizando supera su límite lógico y alucina o rompe el formato. Separar en agentes especializados acota la responsabilidad de cada uno, hace el flujo testeable y permite validación determinística entre pasos.

**P: ¿Cómo evitan que el LLM invente un producto o un precio?**
R: Datos factuales solo de la DB. El investigador nunca inventa productos (busca en pgvector). El sintetizador recibe los productos reales y el LLM solo genera texto interpretativo; estima un dato solo si falta, con rangos acotados. Ver `synthesizer_agent.py`.

**P: ¿Por qué SSE y no WebSockets?**
R: El progreso es unidireccional servidor→cliente. WebSocket es bidireccional y gasta recursos sin necesidad. SSE corre sobre HTTP, reconecta solo y es más simple. Fue una restricción de diseño explícita.

**P: ¿Qué pasa si el worker se cae a mitad de la recomendación?**
R: El estado queda en `PROCESSING`; al reintentar, `remove_products()` garantiza idempotencia. Si falla definitivamente, se marca `FAILED` y se publica un evento SSE de error. En diseño contemplamos Dead Letter Queue para fallos catastróficos.

**P: ¿Dónde está el patrón Repository y por qué?**
R: `BaseRepository[ModelT]` genérico + repos concretos. Aísla el SQL para que services y agentes no dependan de SQLAlchemy. El caso más fuerte es `AbstractProductRepository` (ABC) que desacopla el pipeline del ORM y permite mocks en tests.

**P: ¿Cómo testean el pipeline de IA sin gastar tokens?**
R: `LLMClient` es una interfaz; `MockLLMClient` da respuestas deterministas. Los repos también se pueden mockear. Es DIP en acción.

**P: ¿Cómo escalarían a más usuarios?**
R: El worker es horizontalmente escalable (más réplicas Celery). La cola amortigua picos. La DB en Supabase escala aparte. El front es estático (CDN).

**P: Veo que `zones.py` mezcla varias responsabilidades, ¿eso no viola SRP?**
R: Correcto, lo detectamos con nuestro agente SOLID (P0). El plan es extraer `ZoneService` + mappers. Es deuda técnica priorizada y documentada, no algo que se nos pasó.

**P: ¿Por qué Supabase?**
R: PostgreSQL + pgvector + Auth listos, capa gratuita, una sola fuente de verdad para el equipo. Nos quita trabajo de infraestructura para concentrarnos en el dominio.

**P: ¿Cómo manejan la validación legal con responsabilidad real?**
R: Validador híbrido. Primero reglas determinísticas (descarte por sustancia prohibida literal), luego LLM interpretando la normativa. Política conservadora: si no se confirma validez explícita, se descarta. Preferimos descartar de más.

**P: ¿Por qué dos manejadores de estado en el front (Zustand + React Query)?**
R: Estado de cliente (sesión, wizard) vs estado de servidor (datos remotos con cache, refetch, polling). Cada herramienta para su trabajo.

---

## 16. Mapa de evidencia — dónde está cada cosa en `/src`

| Concepto | Archivo |
|---|---|
| App factory, CORS, routers | [`backend/app/main.py`](../src/backend/app/main.py) |
| Configuración (.env) | [`backend/app/config.py`](../src/backend/app/config.py) |
| Orquestador 4 agentes | [`backend/app/agents/orchestrator.py`](../src/backend/app/agents/orchestrator.py) |
| Agente analizador | [`backend/app/agents/analyzer_agent.py`](../src/backend/app/agents/analyzer_agent.py) |
| Agente investigador (RAG) | [`backend/app/agents/researcher_agent.py`](../src/backend/app/agents/researcher_agent.py) |
| Agente validador legal (híbrido) | [`backend/app/agents/legal_validator_agent.py`](../src/backend/app/agents/legal_validator_agent.py) |
| Agente sintetizador | [`backend/app/agents/synthesizer_agent.py`](../src/backend/app/agents/synthesizer_agent.py) |
| Cliente LLM (Adapter+Strategy) | [`backend/app/services/llm_client.py`](../src/backend/app/services/llm_client.py) |
| Repository base (Generics) | [`backend/app/repositories/base.py`](../src/backend/app/repositories/base.py) |
| Abstracción repo (DIP) | [`backend/app/repositories/product_repository.py`](../src/backend/app/repositories/product_repository.py) |
| Worker Celery + idempotencia | [`backend/app/workers/tasks.py`](../src/backend/app/workers/tasks.py) |
| Endpoint async + SSE | [`backend/app/api/v1/recommendations.py`](../src/backend/app/api/v1/recommendations.py) |
| Seguridad (bcrypt + JWT) | [`backend/app/core/security.py`](../src/backend/app/core/security.py) |
| Modelos ORM | [`backend/app/models/`](../src/backend/app/models/) |
| Esquema DBML | [`Docs/database/schema.dbml`](database/schema.dbml) |
| Análisis SOLID | [`Docs/sugerencias_SOLID.md`](sugerencias_SOLID.md) |
| Diseño de agentes | [`Docs/AgentOrchs.md`](AgentOrchs.md) |
| Wizard frontend | [`frontend/src/features/wizard/`](../src/frontend/src/features/wizard/) |
| Stores (Zustand) | [`frontend/src/stores/`](../src/frontend/src/stores/) |

---

## 17. Checklist mental para la revisión

- [ ] Sé explicar el flujo completo: agricultor → wizard → 202+ticket → Celery → 4 agentes → SSE → 3 productos.
- [ ] Sé nombrar **2 patrones arquitectónicos** (Capas, Queue-Based Load Leveling / Background Worker) y **1 agéntico** (Sequential Pipeline + Tool Use).
- [ ] Sé señalar el patrón Repository y el DIP con `AbstractProductRepository`.
- [ ] Sé defender SSE vs WebSockets.
- [ ] Sé por qué 4 agentes y la regla anti-alucinación.
- [ ] Sé reconocer los gaps diseño-código **antes** de que me los señalen (§14).
- [ ] Sé dónde está cada cosa en `/src` (§16).
- [ ] Sé el estado de SOLID y el plan de refactor (§13).
```
