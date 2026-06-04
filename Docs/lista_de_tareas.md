# SynapSeed — Lista de Tareas Concretas

> Proyecto: Plataforma de recomendación de agroquímicos para agricultores costarricenses.
> Deadline demo: **26 de junio**. Review con profe: **8–20 de junio**.
> Directorio: `e:\Escritorio\SynapSeed\`

---

## 📁 0. Infraestructura y Setup del Repositorio

- [x] **0.1** Crear la carpeta `src/backend/` y `src/frontend/` dentro del proyecto
- [x] **0.2** Crear `docker-compose.yml` con servicios: `postgres`, `redis`, `backend`, `frontend`, `worker`
- [x] **0.3** Crear `src/backend/pyproject.toml` con todas las dependencias (FastAPI, SQLAlchemy, Alembic, Celery, LangGraph, pgvector, etc.)
- [x] **0.4** Crear `src/frontend/package.json` e inicializar proyecto Vite + React + TypeScript
- [x] **0.5** Crear archivo `.env.example` con todas las variables necesarias (DB, Redis, JWT_SECRET, GEMINI_API_KEY)
- [x] **0.6** Actualizar `README.md` con instrucciones para correr el proyecto localmente

---

## 🗄️ 1. Base de Datos y Datos Semilla

- [ ] **1.1** Configurar Alembic en `src/backend/` (`alembic init`, `alembic.ini`, `env.py`)
- [ ] **1.2** Crear modelos SQLAlchemy: `User`, `Zone`, `Product`, `Distributor`, `Recommendation`, `RecommendationProduct`, `Regulation`, `AuditLog`
- [ ] **1.3** Generar primera migración (`alembic revision --autogenerate -m "initial schema"`) y aplicarla
- [ ] **1.4** Habilitar extensión `pgvector` en PostgreSQL (`CREATE EXTENSION vector`)
- [ ] **1.5** **Scrappear/descargar el catálogo de agroquímicos del SFE** (https://www.sfe.go.cr) — exportar a CSV/JSON con: nombre comercial, ingrediente activo, categoría, número de registro, estado, banda toxicológica, distribuidor
- [ ] **1.6** Scrappear o conseguir datos de **distribuidores/proveedores** costarricenses de agroquímicos: nombre, correo, teléfono, ubicación
- [ ] **1.7** Descargar/compilar las **regulaciones del MAG/SFE** relevantes (decretos, listas de sustancias prohibidas) para la tabla `regulations`
- [ ] **1.8** Crear script `src/backend/app/db/seed.py` que inserte: productos del SFE, distribuidores y regulaciones en la DB
- [ ] **1.9** Calcular y guardar los **embeddings vectoriales** (768 dimensiones, modelo `text-embedding-004` de Google) para cada producto y regulación — guardarlos en las columnas `embedding` de las tablas `products` y `regulations`

---

## ⚙️ 2. Backend — API FastAPI

### Auth
- [ ] **2.1** Crear `src/backend/app/core/security.py` — funciones bcrypt (hash + verify), generación y validación JWT
- [ ] **2.2** Crear endpoint `POST /api/v1/auth/register` — recibe: email, full_name, identification (cédula), phone, password
- [ ] **2.3** Crear endpoint `POST /api/v1/auth/login` — login con **cédula + contraseña** (NO email), retorna JWT

### Perfil
- [ ] **2.4** Crear endpoint `GET /api/v1/users/me` — retorna datos del usuario autenticado
- [ ] **2.5** Crear endpoint `PUT /api/v1/users/me` — actualiza nombre, email, teléfono
- [ ] **2.6** Crear endpoint `PUT /api/v1/users/me/password` — cambia contraseña (pide contraseña actual)

### Zonas / Fincas
- [ ] **2.7** Crear endpoint `GET /api/v1/zones/` — lista zonas del usuario autenticado
- [ ] **2.8** Crear endpoint `POST /api/v1/zones/` — crea nueva zona (name, soil_type, humidity, temperature, water_quality, location)
- [ ] **2.9** Crear endpoint `PUT /api/v1/zones/{zone_id}` — edita zona existente
- [ ] **2.10** Crear endpoint `DELETE /api/v1/zones/{zone_id}` — elimina zona

### Catálogos (opciones de los dropdowns)
- [ ] **2.11** Crear endpoint `GET /api/v1/catalogs/crops` — lista de cultivos disponibles
- [ ] **2.12** Crear endpoint `GET /api/v1/catalogs/crop-stages` — etapas de cultivo
- [ ] **2.13** Crear endpoint `GET /api/v1/catalogs/soil-types` — tipos de suelo
- [ ] **2.14** Crear endpoint `GET /api/v1/catalogs/problems` — problemas agrícolas categorizados
- [ ] **2.15** Crear endpoint `GET /api/v1/catalogs/agrochemicals` — agroquímicos conocidos (para "último usado")
- [ ] **2.16** Crear endpoint `GET /api/v1/catalogs/budgets` — rangos de presupuesto por litro

### Recomendaciones
- [ ] **2.17** Crear endpoint `POST /api/v1/recommendations/request` — recibe contexto completo del caso, crea ticket, encola en Celery, retorna `202 + ticket_id`
- [ ] **2.18** Crear endpoint `GET /api/v1/recommendations/stream/{ticket_id}` — SSE que emite estado del pipeline en tiempo real
- [ ] **2.19** Crear endpoint `GET /api/v1/recommendations/{id}` — retorna recomendación completa con los 3 productos
- [ ] **2.20** Crear endpoint `GET /api/v1/recommendations/history` — historial de recomendaciones del usuario

### Proveedores
- [ ] **2.21** Crear endpoint `GET /api/v1/recommendations/{id}/providers` — retorna distribuidores de los 3 productos recomendados (nombre, correo, teléfono, ubicación)

### Health
- [ ] **2.22** Crear endpoint `GET /api/v1/health` — verifica conexión a DB, Redis y Gemini API

---

## 🤖 3. Pipeline de Agentes IA (LangGraph + Celery)

- [x] **3.1** Configurar `Celery` con Redis como broker — crear `src/backend/app/workers/celery_app.py` *(esqueleto: broker/backend conectados a Redis; sin tareas registradas aun)*
- [ ] **3.2** Crear **Agente 1 — Analizador de Contexto**: recibe el formulario del agricultor (todos los dropdowns), produce un resumen agronómico estructurado usando Gemini
- [ ] **3.3** Crear **Agente 2 — Investigador (RAG)**: hace búsqueda vectorial semántica con pgvector sobre la tabla `products`, filtra candidatos relevantes al problema y cultivo
- [ ] **3.4** Crear **Agente 3 — Validador Legal**: cruza productos candidatos con la tabla `regulations`, descarta los que tengan sustancias prohibidas o incompatibilidades, usando Gemini para interpretar la normativa
- [ ] **3.5** Crear **Agente 4 — Sintetizador**: toma los productos válidos, los rankea por costo-beneficio y genera **exactamente 3 recomendaciones** con tabla comparativa (dosis, precio, toxicidad, intervalo de seguridad)
- [ ] **3.6** Orquestar los 4 agentes en un grafo LangGraph (`src/backend/app/agents/orchestrator.py`)
- [ ] **3.7** Publicar eventos a Redis pub/sub en cada paso del pipeline para alimentar el endpoint SSE
- [ ] **3.8** Implementar rate limiting y exponential backoff para la Gemini API (máx. 15 RPM en free tier)
- [ ] **3.9** Implementar idempotencia: si un ticket ya está `completed`, no reprocesar

---

## 🎨 4. UX / Diseño Figma

> [!IMPORTANT]
> Esta etapa es **manual** — debe hacerse en Figma antes de comenzar el frontend.

- [ ] **4.1** Definir el sistema de diseño en Figma: paleta verde, tipografía Inter, componentes base (botones, inputs/selects, cards, badges)
- [ ] **4.2** Diseñar pantalla de **Login** (cédula + contraseña, link a registro)
- [ ] **4.3** Diseñar pantalla de **Registro** (email, nombre completo, cédula, teléfono, contraseña)
- [ ] **4.4** Diseñar el **Wizard "Gestión del Caso"** — Paso 1 (zona), Paso 2 (contexto ambiental si no hay zona), Paso 3 (problema), Paso 4 (confirmación)
- [ ] **4.5** Diseñar pantalla de **Progreso** — tracker visual con 4 pasos animados (Analizando → Investigando → Validando → Generando)
- [ ] **4.6** Diseñar pantalla de **Resultado**: 3 cards de productos + tabla comparativa + botón "Ver proveedores"
- [ ] **4.7** Diseñar pantalla de **Proveedores**: lista con nombre, correo, teléfono, ubicación, botón "Contactar"
- [ ] **4.8** Diseñar pantalla de **Historial** — lista de casos anteriores
- [ ] **4.9** Diseñar pantalla de **Zonas/Fincas** — lista + formulario modal para crear/editar
- [ ] **4.10** Diseñar pantalla de **Mi Cuenta** — editar perfil y cambiar contraseña
- [ ] **4.11** Realizar **UX Testing con 4 participantes** usando el prototipo interactivo de Figma
- [ ] **4.12** Documentar resultados del testing en `Docs/ux/testing_results.md` y correcciones en `Docs/ux/corrections.md`

---

## 💻 5. Frontend — React + Vite + TypeScript

### Setup inicial
- [ ] **5.1** Inicializar proyecto Vite con template `react-ts` en `src/frontend/`
- [ ] **5.2** Instalar y configurar **TailwindCSS v4** (plugin de Vite, sin `tailwind.config.js`)
- [ ] **5.3** Inicializar **shadcn/ui** y agregar componentes: `button`, `card`, `input`, `label`, `select`, `dialog`, `toast`, `badge`, `separator`, `alert`
- [ ] **5.4** Configurar tokens del sistema de diseño en `src/styles/globals.css` — colores verdes agrícolas, fuente Inter, radios y espaciados
- [ ] **5.5** Configurar `lib/api.ts` — instancia Axios con `VITE_API_URL`, interceptores JWT (request + 401 handler)
- [ ] **5.6** Configurar `stores/authStore.ts` — Zustand con persist: token, user, logout
- [ ] **5.7** Configurar `stores/wizardStore.ts` — estado del wizard (paso actual, valores seleccionados)
- [ ] **5.8** Configurar `app/router.tsx` — rutas públicas (login, registro) y protegidas (todo lo demás)

### Pantallas
- [ ] **5.9** Implementar **pantalla de Login** — cédula + contraseña, validación Zod, manejo de errores
- [ ] **5.10** Implementar **pantalla de Registro** — todos los campos, validación Zod
- [ ] **5.11** Implementar **Wizard "Gestión del Caso"** — Paso 1: selección de zona; Paso 2: dropdowns ambientales (si no hay zona); Paso 3: dropdowns del problema; Paso 4: pantalla de confirmación
- [ ] **5.12** Implementar **pantalla de Progreso** — tracker visual SSE con animaciones para cada etapa del pipeline
- [ ] **5.13** Implementar **hook `useSSE.ts`** — EventSource para suscribirse al ticket SSE y actualizar TanStack Query cache
- [ ] **5.14** Implementar **pantalla de Resultado** — 3 cards de productos rankeados + tabla comparativa + botón "Ver proveedores"
- [ ] **5.15** Implementar **pantalla de Proveedores** — lista con nombre, correo, teléfono, ubicación, botón "Contactar" (`mailto:`)
- [ ] **5.16** Implementar **pantalla de Historial** — lista de recomendaciones pasadas, clickeable para ver detalle
- [ ] **5.17** Implementar **pantalla de Zonas/Fincas** — lista de fincas + modal para crear/editar/eliminar
- [ ] **5.18** Implementar **pantalla de Mi Cuenta** — formulario de perfil + formulario de cambio de contraseña

### Layout
- [ ] **5.19** Crear `layouts/AppLayout.tsx` — sidebar colapsable con navegación, header con avatar, responsive (hamburger en móvil)
- [ ] **5.20** Crear `layouts/AuthLayout.tsx` — centrado con branding de SynapSeed

---

## 🧪 6. Testing

- [ ] **6.1** Crear `conftest.py` con fixtures de pytest: DB de test, cliente HTTP async, usuario de prueba
- [ ] **6.2** Tests unitarios backend: auth (login con cédula, registro, token inválido), zonas (CRUD), recomendaciones (crear ticket, consultar historial)
- [ ] **6.3** Tests de los agentes IA con mocks de Gemini (no llama a la API real en tests)
- [ ] **6.4** Tests frontend con Vitest + React Testing Library: Login, wizard de contexto, pantalla de resultado
- [ ] **6.5** Tests E2E con Playwright: flujo completo (login → crear caso → ver resultado → contactar proveedor)

---

## 🚀 7. Despliegue y Demo

- [ ] **7.1** Configurar GitHub Actions CI: lint + typecheck + tests para backend (`ruff`, `pytest`) y frontend (`eslint`, `vitest`)
- [ ] **7.2** Elegir plataforma de hosting gratuita: **Vercel** (frontend) + **Railway o Render** (backend + worker) + **Neon** (PostgreSQL) + **Upstash** (Redis)
- [ ] **7.3** Desplegar a producción y verificar que el flujo completo funciona end-to-end
- [ ] **7.4** Preparar la **presentación/demo** del 26 de junio — script de demo con un caso de uso real (ej: agricultor de tomate en Cartago con plaga de áfidos)

---

## 📊 Resumen por prioridad

| Prioridad | Área | Por qué es primero |
|---|---|---|
| 🔴 **Crítico** | 1. DB + datos SFE | Sin datos de productos, la IA no puede recomendar nada |
| 🔴 **Crítico** | 4. Diseño Figma | El frontend debe partir del diseño aprobado |
| 🟠 **Alto** | 2. Backend API | Base para que el frontend funcione |
| 🟠 **Alto** | 3. Pipeline IA | El diferenciador principal del producto |
| 🟡 **Medio** | 5. Frontend | Depende de diseño + API listos |
| 🟢 **Normal** | 6. Testing | En paralelo con desarrollo |
| 🟢 **Normal** | 7. Deploy | Al final, antes del demo |

---

## 🛠️ Fixes aplicados en esta sesión (Docker / Build)

> Fecha: 6 jun 2026 — para que el `docker compose up --build -d` levante sin errores.

- [x] **FIX-1** Eliminar `google-generativeai==0.8.4` de `pyproject.toml` (redundante con `langchain-google-genai`; causaba `ResolutionImpossible` por pin incompatible con `google-ai-generativelanguage`).
- [x] **FIX-2** Subir `langchain-core` a `==0.3.62` (satisfacer `langchain-google-genai 2.1.5` que exige `>=0.3.62`).
- [x] **FIX-3** Reemplazar `pip cache purge` por `rm -rf /root/.cache/pip` en `Dockerfile` y `Dockerfile.worker` (incompatible con `PIP_NO_CACHE_DIR=1`).
- [x] **FIX-4** `alembic upgrade head` tolerante a fallo en `docker-compose.yml` (`|| true`) porque la carpeta `alembic/` con migraciones aún no existe (Fase 1 pendiente).
- [x] **FIX-5** Añadir `COPY alembic.ini ./` al `Dockerfile` del backend.
- [x] **FIX-6** Crear `app/workers/__init__.py` + `app/workers/celery_app.py` (esqueleto Celery) para que el worker arranque.
- [x] **FIX-7** `command` del worker en una sola línea (el `>` multilínea se rompía con `sh -c`).
- [x] **FIX-8** Entorno docker limpio: `docker compose down --volumes --remove-orphans`. Próximo `docker compose up --build -d` levanta from-scratch (5/5 servicios healthy verificado).
