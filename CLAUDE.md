# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SynapSeed** is a Spanish-language agrotech recommendation platform for Costa Rican farmers. Given a farmer's crop, zone conditions, and budget, it recommends appropriate agrochemicals via a 4-agent LLM pipeline. Information and recommendations only — no purchasing functionality.

This is an academic project (TEC — Diseño de Software). The codebase is a monorepo containing an independent FastAPI backend and a React/Vite frontend, orchestrated via Docker Compose.

## Commands

### Docker (primary dev workflow)
```bash
docker compose up -d --build      # Start all 5 services
docker compose down               # Stop all
docker compose logs -f backend    # Stream backend logs
docker compose exec backend bash  # Shell into backend container
```

### Backend (Python 3.12 + FastAPI)
```bash
cd src/backend
pip install -e ".[dev]"           # Install with dev extras
uvicorn app.main:app --reload --port 8000
alembic upgrade head              # Apply migrations
alembic revision --autogenerate -m "description"  # Generate migration
celery -A app.workers.celery_app worker --loglevel=info
pytest                            # All tests
pytest tests/path/test_file.py::test_name  # Single test
pytest --cov=app                  # With coverage
ruff check . && ruff format .
mypy app
```

### Frontend (Node 20+ / React + Vite)
```bash
cd src/frontend
npm install
npm run dev          # Dev server on :5173
npm run build
npm run lint
npm run lint:fix
npm run typecheck
npm run test
npm run test:watch
```

## Architecture

### Stack
- **Backend**: FastAPI 0.115, SQLAlchemy 2.0 async (asyncpg), Alembic, Celery, PostgreSQL 16 + pgvector, Redis 7
- **Auth**: Supabase Auth (primary) + local JWT fallback via `python-jose` + `bcrypt`
- **Agents**: LangGraph 1.2 + OpenRouter (LLM) + Gemini embeddings
- **Frontend**: React 19, Vite 6, TypeScript 5.7, React Router 7, TanStack React Query 5, Zustand 5, shadcn/ui, TailwindCSS v4 (CSS-first, no `tailwind.config.js`)
- **Forms**: react-hook-form + zod

### Backend layers
```
Routers (api/v1/) → Services (services/) → Repositories (repositories/) → Models (models/)
```
Routers receive HTTP, services contain business logic, repositories do DB queries with the async SQLAlchemy session. Schemas (Pydantic DTOs) live in `schemas/` and are separate from ORM models.

### Agent pipeline (`app/agents/`)
Four agents run sequentially orchestrated by `AgentOrchestrator`:
1. **Analyzer** — summarizes farmer context with an OpenRouter LLM call
2. **Researcher** — pgvector semantic search to find candidate products
3. **Legal Validator** — filters products against regulations via LLM
4. **Synthesizer** — produces exactly 3 ranked recommendations with a comparison table

The orchestrator is invoked as a Celery background task. Progress is streamed to the frontend via Server-Sent Events (SSE) using Redis pub/sub. WebSockets were explicitly rejected in favor of SSE.

### Frontend structure
```
src/features/           # Feature modules (auth, wizard, account, zones, dashboard)
src/components/         # Reusable UI components (shadcn/ui wrappers)
src/stores/             # Zustand stores (auth, wizard state, UI)
src/lib/                # Axios API client, utilities
src/app/                # Router config, entry point
```
The main user flow is a 4-step wizard (`features/wizard/`) that collects crop, zone, problem, and budget info, then polls/streams for the recommendation result.

### Key entry points
| File | Purpose |
|---|---|
| `src/backend/app/main.py` | FastAPI app factory, CORS, router registration, lifespan |
| `src/backend/app/config.py` | All settings via `pydantic-settings` (reads `.env`) |
| `src/backend/app/db/session.py` | Async SQLAlchemy session factory |
| `src/backend/app/agents/orchestrator.py` | 4-agent pipeline |
| `src/backend/app/api/v1/` | All HTTP route handlers |
| `src/frontend/src/main.tsx` | React entry point |
| `src/frontend/src/app/router.tsx` | Route definitions |

### API routes
- `POST /api/v1/auth/register`, `/auth/login`, `/auth/reset-password`
- `GET /api/v1/users/me`
- `GET/POST/PUT/DELETE /api/v1/zones`
- `GET /api/v1/catalogs/*` — dropdown data (crops, problems, soil types, budgets)
- `POST /api/v1/recommendations/request` — starts Celery task, returns `ticket_id`
- `GET /api/v1/recommendations/stream/{ticket_id}` — SSE progress stream
- `GET /api/v1/recommendations/history`
- `GET /api/v1/health`

### Database
PostgreSQL with pgvector. Key tables: `users`, `zones`, `products` (768-dim embeddings), `distributors`, `recommendations` (status: PENDING/PROCESSING/COMPLETED/FAILED), `regulations` (with embeddings), `audit_log`. Migrations managed with Alembic.

Two `DATABASE_URL` vars are required: `DATABASE_URL` uses `asyncpg` (runtime), `DATABASE_URL_SYNC` uses `psycopg2` (Alembic only).

## Environment

Copy `.env.example` to `.env`. Critical variables:
- `DATABASE_URL` / `DATABASE_URL_SYNC` — async and sync Postgres connection strings
- `OPENROUTER_API_KEY` — LLM for agents
- `GEMINI_API_KEY` — embeddings generation
- `JWT_SECRET` — local auth signing
- `SUPABASE_URL` / `SUPABASE_ANON_KEY` — Supabase Auth
- `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` — Celery + SSE
- `VITE_API_URL` — frontend API base URL
- `BACKEND_CORS_ORIGINS` — list of allowed origins
