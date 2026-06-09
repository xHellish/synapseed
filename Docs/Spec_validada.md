
# SynapSeed MVP — Spec Validada

> Plataforma donde una persona del sector agro ingresa su contexto (situación y problema) y un sistema de IA le encuentra el agroquímico más recomendado + los proveedores y cómo obtenerlo.
> **Solo información, nada de compras.**

---

## 1. Stack Tecnológico

| Backend | Frontend | Infra |
|---|---|---|
| Python 3.12 | TypeScript ~6 | Docker Compose |
| FastAPI | React 19 | Postgres 16 + pgvector |
| SQLAlchemy 2.0 (async) | Vite 8 | Redis 7 |
| asyncpg | TailwindCSS 4 |  |
| Alembic | shadcn/ui |  |
| Pydantic v2 | Zustand 5 |  |
| passlib[bcrypt] | @tanstack/react-query 5 |  |
| python-jose | react-router-dom 7 |  |
| Celery | react-hook-form + zod |  |
| Redis | Vitest, ESLint |  |
| LangGraph |  |  |
| OpenRouter (langchain-openai) |  |  |
| pgvector |  |  |
| pytest, Ruff |  |  |

---

## 2. Estructura de Carpetas

```
src/
	backend/
		main.py, seed.py, alembic/, api/, core/, models/, schemas/, services/, workers/, tests/
	frontend/
		index.html, package.json, vite.config.ts, src/
```

---

## 3. Modelos ORM (SQLAlchemy)

> Todos los campos según [schema.dbml](database/schema.dbml)

**Modelos:**

- **User** — id, identification (cédula, varchar, unique), email, password_hash, full_name, phone, is_active, timestamps
- **Zone** — id, user_id (FK), name, soil_type, humidity, temperature, water_quality, location, timestamps
- **Distributor** — id, name, email, phone, location, website, is_active, timestamps
- **Product** — id, name, active_ingredient, description, category, formulation, concentration, dosage_per_hectare, application_method, safety_interval_days, price_per_liter, distributor_id (FK), sfe_registration, sfe_status, toxicity_band, embedding (vector 1536), is_active, timestamps
- **Recommendation** — id, ticket_id (unique), user_id (FK), zone_id (FK nullable), status, crop, crop_stage, affected_area, soil_type, humidity, temperature, water_quality, problem_to_solve, last_agrochemical, max_budget_per_liter, agent_context (jsonb), agent_research (jsonb), agent_validation (jsonb), final_recommendation (jsonb), processing_time_ms, error_message, timestamps, completed_at
- **RecommendationProduct** — id, recommendation_id (FK), product_id (FK), rank (1-3), justification, recommended_dosage, estimated_cost, compatibility_notes, timestamps
- **Regulation** — id, regulation_code (unique), title, issuing_body, description, prohibited_substances (jsonb), restricted_crops (jsonb), is_active, source_url, embedding, timestamps
- **AuditLog** — id, user_id (FK), action, entity_type, entity_id, details (jsonb), ip_address, timestamps

---

## 4. Endpoints API (FastAPI)

> Todos los endpoints protegidos requieren `Authorization: Bearer <jwt_token>`

### Auth
| Método | Endpoint | Descripción |
|---|---|---|
| POST | /api/v1/auth/register | Registrar: email, full_name, identification, phone, password |
| POST | /api/v1/auth/login | Login con **cédula (identification) + password**, retorna JWT |

### Usuario (Mi Cuenta)
| Método | Endpoint | Descripción |
|---|---|---|
| GET | /api/v1/users/me | Obtener perfil |
| PUT | /api/v1/users/me | Actualizar datos del perfil |
| PUT | /api/v1/users/me/password | Cambiar contraseña |

### Zonas (Fincas)
| Método | Endpoint | Descripción |
|---|---|---|
| GET | /api/v1/zones/ | Listar zonas del usuario |
| POST | /api/v1/zones/ | Crear zona (name, soil_type, humidity, temperature, water_quality, location) |
| PUT | /api/v1/zones/{zone_id} | Actualizar zona |
| DELETE | /api/v1/zones/{zone_id} | Eliminar zona |

### Recomendaciones (Gestión del Caso)
| Método | Endpoint | Descripción |
|---|---|---|
| POST | /api/v1/recommendations/request | Solicitar recomendación (todos los campos del contexto como dropdowns) |
| GET | /api/v1/recommendations/stream/{ticket_id} | Progreso del pipeline vía SSE |
| GET | /api/v1/recommendations/{id} | Obtener recomendación completa + 3 productos |
| GET | /api/v1/recommendations/history | Historial de recomendaciones del usuario |

### Proveedores
| Método | Endpoint | Descripción |
|---|---|---|
| GET | /api/v1/recommendations/{id}/providers | Proveedores de los productos recomendados (name, email, phone, location) |

### Catálogos (Dropdowns)
| Método | Endpoint | Descripción |
|---|---|---|
| GET | /api/v1/catalogs/crops | Lista de cultivos disponibles para dropdown |
| GET | /api/v1/catalogs/crop-stages | Etapas de cultivo |
| GET | /api/v1/catalogs/soil-types | Tipos de suelo |
| GET | /api/v1/catalogs/problems | Problemas a resolver (categorizados) |
| GET | /api/v1/catalogs/agrochemicals | Agroquímicos conocidos (para "último usado") |
| GET | /api/v1/catalogs/budgets | Rangos de presupuesto por litro |

### Health
| Método | Endpoint | Descripción |
|---|---|---|
| GET | /api/v1/health | Health check (DB + Redis + LLM API) |

---

## 5. Seguridad

- Passwords: bcrypt
- Login: **cédula + contraseña** (NO email)
- JWT: expiración configurable (default 24h)
- CORS: solo FRONTEND_URL
- Vars sensibles: solo en .env
- Validación de inputs: Pydantic + Zod (frontend)

---

## 6. Worker Celery (LangGraph Pipeline)

- 4 nodos: ContextAnalyzer → VectorialRAG → RegulatoryValidator → Synthesizer
- El Synthesizer genera **exactamente 3 productos** recomendados + tabla comparativa
- Cada nodo actualiza status en DB y Redis PubSub
- Idempotencia: si ya está completed, no reprocesar
- Concurrencia: worker_prefetch_multiplier=1

---

## 7. Frontend (React)

### Secciones de la aplicación

| Sección | Descripción |
|---|---|
| **Login** | Cédula + contraseña. Link a registro |
| **Registro** | Formulario: email, nombre completo, cédula, teléfono, contraseña |
| **Gestión del caso** | Wizard con dropdowns: zona → contexto ambiental → problema → confirmación → enviar |
| **Progreso** | Tracker visual SSE con 4 pasos animados (Analizando → Investigando → Validando → Generando) |
| **Recomendaciones** | 3 cards de productos + tabla comparativa + botón "Ver proveedores" |
| **Proveedores** | Lista de proveedores con nombre, correo, teléfono, ubicación + botón "Contactar" (mailto:) |
| **Historial** | Lista de recomendaciones pasadas con acceso al detalle |
| **Zonas** | CRUD de zonas/fincas (nombre, suelo, humedad, temperatura, calidad agua, ubicación) |
| **Mi Cuenta** | Editar perfil (nombre, email, teléfono) + cambiar contraseña |

### Flujo del wizard "Gestión del caso"

```
Paso 1: Seleccionar zona
├── Dropdown con zonas del usuario + opción "Ninguna"
├── Si zona seleccionada → auto-llenar suelo, humedad, temp, agua → ir a Paso 3
└── Si "Ninguna" → ir a Paso 2

Paso 2: Contexto ambiental (solo si no hay zona)
├── Dropdown: Tipo de suelo
├── Dropdown: Humedad
├── Dropdown: Temperatura
└── Dropdown: Calidad del agua

Paso 3: Contexto del problema
├── Dropdown: Cultivo
├── Dropdown: Etapa del cultivo
├── Dropdown: Área afectada
├── Dropdown: Problema a resolver
├── Dropdown: Último agroquímico usado (o "Ninguno")
└── Dropdown: Presupuesto máximo por litro

Paso 4: Confirmación
├── Resumen de todos los datos seleccionados
├── Botón "Editar" para volver atrás
└── Botón "Confirmar y solicitar recomendación" → POST /recommendations/request
```

> **IMPORTANTE:** Todos los campos usan `<Select>` (shadcn/ui), NO `<Input type="text">`.

### Resultado de la recomendación

- **3 cards** de productos recomendados (rank 1, 2, 3)
- **Tabla comparativa** lado a lado: ingrediente activo, dosis, precio, toxicidad, método de aplicación, intervalo de seguridad
- **Botón "Ver proveedores"** al final que navega a la sección de proveedores
- En la vista de proveedores: cada proveedor con nombre, correo, teléfono, ubicación y botón **"Contactar"** que abre `mailto:`

---

## 8. Variables .env requeridas

> Ver `.env` para todas las claves (DB, Redis, JWT, OpenRouter, etc)

---

## 9. Comandos

```bash
docker-compose up -d
cd src/backend && pip install -r requirements.txt && alembic upgrade head && python seed.py && uvicorn main:app --reload --port 8000
celery -A workers.tasks worker --loglevel=info --concurrency=1
cd src/frontend && npm install && npm run dev
```

---

## 10. Testing

- Backend: pytest (auth, zones, recommendations, agents)
- Frontend: Vitest + RTL (Login, ContextWizard, RecommendationPage, Providers)
- Cobertura: ≥80%

---

## 11. Orden de Implementación

1. Modelos ORM + Alembic
2. Seguridad (bcrypt, JWT, get_current_user)
3. Endpoints Auth (login con cédula, registro)
4. Endpoints Zonas (CRUD)
5. Endpoints Perfil (mi cuenta + cambiar contraseña)
6. Endpoints Catálogos (dropdowns)
7. Recomendaciones (Celery, SSE, ticket_id)
8. Pipeline LangGraph (4 agentes → 3 productos)
9. Proveedores (endpoint + vista)
10. Tests
11. Frontend (login, registro, zonas, wizard, recomendaciones, proveedores, historial, mi cuenta)