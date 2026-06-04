# SynapSeed — Backend

API REST construida con **FastAPI 0.115 + Python 3.12** que sirve al frontend
de SynapSeed y orquesta el pipeline de agentes IA (LangGraph + Gemini).

## Estructura

```
src/backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app factory + health check
│   ├── config.py            # pydantic-settings (lee .env)
│   ├── api/                 # (fase 2) routers: auth, users, zones, ...
│   ├── core/                # (fase 2) security, exceptions, middleware
│   ├── models/              # (fase 1) modelos SQLAlchemy
│   ├── schemas/             # (fase 2) Pydantic DTOs
│   ├── services/            # (fase 2) lógica de negocio
│   ├── repositories/        # (fase 2) acceso a datos
│   ├── agents/              # (fase 3) pipeline LangGraph
│   ├── workers/             # (fase 3) Celery app + tasks
│   └── db/                  # (fase 1) engine, sesión, seed, migrations
├── tests/                   # tests pytest
├── alembic/                 # migraciones (se crea con `alembic init`)
├── pyproject.toml
├── alembic.ini
├── Dockerfile
└── Dockerfile.worker
```

## Setup local

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Instalar en modo editable + extras de dev
pip install -e ".[dev]"

# Variables de entorno
cp ../../.env.example ../../.env
# editar ../../.env y poner tu GEMINI_API_KEY

# Aplicar migraciones (cuando existan en fase 1)
alembic upgrade head

# Levantar el servidor
uvicorn app.main:app --reload --port 8000

# (otra terminal) worker de Celery
celery -A app.workers.celery_app worker --loglevel=info --concurrency=1
```

## Endpoints (Fase 0)

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/` | Metadata de la app |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |
| GET | `/api/v1/health` | Health check (placeholder) |

Los endpoints reales se implementan en la fase 2 (ver `Docs/lista_de_tareas.md`).

## Tests

```bash
# Correr todos los tests
pytest

# Con cobertura
pytest --cov=app --cov-report=term-missing
```

## Linter y formatter

```bash
ruff check .       # lint
ruff format .      # format
mypy app           # type-check
```

## Convenciones

- Python 3.12, type hints en todo el código público
- Async-first (FastAPI + SQLAlchemy async)
- Path operations en `app/api/v1/*.py`, un router por dominio
- Modelos ORM en `app/models/*.py`
- Schemas Pydantic en `app/schemas/*.py`
- Lógica de negocio en `app/services/*.py`
- Sin acceso directo a la DB fuera de `repositories/`
