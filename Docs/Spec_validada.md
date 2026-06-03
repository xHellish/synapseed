
# SynapSeed MVP

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
| Gemini (langchain-google-genai) |  |  |
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

> Todos los campos según schema.dbml

**Modelos:**

- User
- Zone
- Distributor
- Product
- Recommendation
- RecommendationProduct
- Regulation
- AuditLog
- Subscription
- Feedback

---

## 4. Endpoints API (FastAPI)

> Todos los endpoints protegidos requieren `Authorization: Bearer <jwt_token>`

### Auth
| Método | Endpoint | Descripción |
|---|---|---|
| POST | /api/v1/auth/register | Registrar usuario |
| POST | /api/v1/auth/login | Login, retorna JWT |

### Usuario
| Método | Endpoint | Descripción |
|---|---|---|
| GET | /api/v1/users/me | Obtener perfil |
| PUT | /api/v1/users/me | Actualizar perfil/contraseña |

### Zonas
| Método | Endpoint | Descripción |
|---|---|---|
| GET | /api/v1/zones/ | Listar zonas del usuario |
| POST | /api/v1/zones/ | Crear zona |
| PUT | /api/v1/zones/{zone_id} | Actualizar zona |
| DELETE | /api/v1/zones/{zone_id} | Eliminar zona |

### Recomendaciones
| Método | Endpoint | Descripción |
|---|---|---|
| POST | /api/v1/recommendations/request | Solicitar recomendación (wizard) |
| GET | /api/v1/recommendations/stream/{ticket_id} | Progreso SSE |
| GET | /api/v1/recommendations/{id} | Obtener recomendación + productos |
| GET | /api/v1/recommendations/history | Listar recomendaciones del usuario |

### Feedback
| Método | Endpoint | Descripción |
|---|---|---|
| POST | /api/v1/feedback/ | Calificar producto en recomendación |

### Productos
| Método | Endpoint | Descripción |
|---|---|---|
| GET | /api/v1/products/catalog | Listar/filtrar productos |

---

## 5. Seguridad

- Passwords: bcrypt
- JWT: expiración configurable (default 24h)
- CORS: solo FRONTEND_URL
- Vars sensibles: solo en .env
- Validación de inputs: Pydantic

---

## 6. Worker Celery (LangGraph Pipeline)

- 4 nodos: ContextAnalyzer → VectorialRAG → RegulatoryValidator → Synthesizer
- Cada nodo actualiza status en DB y Redis PubSub
- Idempotencia: si ya está completed, no reprocesar
- Concurrencia: worker_prefetch_multiplier=1

---

## 7. Frontend (React)

- Auth: Zustand (solo memoria)
- Zonas: CRUD, cards, modal
- ContextWizard: 4 pasos, progreso en localStorage
- RecommendationPage: SSE, 3 cards, feedback modal
- Profile: Editar info, cambiar contraseña

---

## 8. Variables .env requeridas

> Ver `.env` para todas las claves (DB, Redis, JWT, Gemini, etc)

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
- Frontend: Vitest + RTL (Login, ContextWizard, RecommendationPage)
- Cobertura: ≥80%

---

## 11. Orden de Implementación

1. Modelos ORM + Alembic
2. Seguridad (bcrypt, JWT, get_current_user)
3. Endpoints Auth
4. Endpoints Zonas
5. Endpoints Perfil
6. Recomendaciones (Celery, SSE)
7. Pipeline LangGraph
8. Catálogo de productos
9. Feedback
10. Tests
11. Frontend (auth, dashboard, zonas, wizard, recommendation, profile)