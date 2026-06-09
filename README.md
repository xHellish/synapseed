# 🌱 SynapSeed

> Plataforma de recomendación de agroquímicos para agricultores costarricenses.
> Solo información, **nada de compras**.

SynapSeed es un proyecto del curso **Diseño de Software — TEC** (Caso 2) que ayuda a los
agricultores a encontrar el agroquímico más recomendado para su caso, junto con los
distribuidores autorizados. El motor de recomendaciones es un pipeline de **4 agentes IA
(LangGraph + OpenRouter)** que analiza el contexto del agricultor, busca productos con
búsqueda semántica (RAG + pgvector), valida contra regulaciones del SFE/MAG y sintetiza
**exactamente 3 recomendaciones** con tabla comparativa.

---

## ✨ Características principales

- 🔐 **Autenticación con cédula** (no email) y JWT
- 🧙 **Wizard de 4 pasos** con dropdowns para describir el caso (zona → contexto ambiental → problema → confirmación)
- 🤖 **Pipeline de 4 agentes IA** orquestado con LangGraph
- ⚡ **Progreso en tiempo real** vía Server-Sent Events (SSE)
- 🧪 **3 productos rankeados** con tabla comparativa (dosis, precio, toxicidad, intervalo de seguridad)
- 🏪 **Listado de proveedores** con datos de contacto y botón `mailto:`
- 📜 **Historial** de recomendaciones pasadas
- 🗺️ **Gestión de zonas/fincas** del agricultor

---

## 🧰 Stack tecnológico

| Backend | Frontend | Infra |
|---|---|---|
| Python 3.12 | TypeScript 5.8 | Docker Compose |
| FastAPI 0.115 | React 19 | PostgreSQL 16 + pgvector |
| SQLAlchemy 2.0 (async) | Vite 6 | Redis 7 |
| asyncpg | TailwindCSS 4 | |
| Alembic | shadcn/ui | |
| Pydantic v2 | Zustand 5 | |
| passlib[bcrypt] | @tanstack/react-query 5 | |
| python-jose | react-router-dom 7 | |
| Celery 5.4 | react-hook-form + zod | |
| LangGraph 1.2 | Vitest, ESLint | |
| OpenRouter (langchain-openai) | | |

---

## 📁 Estructura del proyecto

```
SynapSeed/
├── src/
│   ├── backend/                # FastAPI + Python
│   │   ├── app/                # código de la aplicación
│   │   ├── tests/              # tests pytest
│   │   ├── alembic/            # migraciones
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   └── Dockerfile.worker
│   └── frontend/               # React + Vite + TypeScript
│       ├── src/
│       ├── package.json
│       ├── vite.config.ts
│       ├── tsconfig.json
│       └── Dockerfile
├── Docs/                       # Documentación
│   ├── Caso2_asignacion_entrega.md
│   ├── Spec_validada.md
│   ├── implementation_plan_1.md
│   ├── lista_de_tareas.md
│   ├── AgentOrchs.md
│   └── database/               # DBML, ERD, create_tables.sql
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Cómo correr el proyecto localmente

### 1. Prerrequisitos

- [Docker](https://www.docker.com/) 24+ y Docker Compose v2
- [Git](https://git-scm.com/)
- Una API key de **OpenRouter** — obtener en
  [openrouter.ai/keys](https://openrouter.ai/keys)

> Si querés correr el backend sin Docker: Python 3.12+ y un Postgres+Redis locales
> (no recomendado para desarrollo, pero útil para iterar sobre un solo servicio).

### 2. Clonar y configurar

```bash
git clone https://github.com/xHellish/synapseed.git
cd synapseed

# Copiar las variables de entorno
cp .env.example .env

# IMPORTANTE: editar .env y poner tu OPENROUTER_API_KEY real
# (reemplazar "your-openrouter-api-key-here")
```

### 3. Levantar el stack completo con Docker Compose

```bash
# Construir imágenes y levantar todos los servicios en background
docker compose up -d --build

# Ver logs en vivo (opcional)
docker compose logs -f backend worker
```

Esto levanta 5 servicios:

| Servicio | Puerto | URL |
|---|---|---|
| **frontend** (Vite) | 5173 | http://localhost:5173 |
| **backend** (FastAPI) | 8000 | http://localhost:8000 |
| **backend** (OpenAPI docs) | 8000 | http://localhost:8000/docs |
| **worker** (Celery) | — | — |
| **postgres** (pgvector) | 5432 | `localhost:5432` |
| **redis** | 6379 | `localhost:6379` |

> El contenedor `backend` ejecuta automáticamente `alembic upgrade head` al arrancar,
> aplicando las migraciones de la base de datos.

### 4. Verificar que todo funciona

```bash
# Health check del backend (DB + Redis + LLM)
curl http://localhost:8000/api/v1/health

# Abrir la documentación interactiva
open http://localhost:8000/docs

# Abrir la app en el navegador
open http://localhost:5173
```

### 5. Comandos útiles

```bash
# Detener todo
docker compose down

# Detener y borrar volúmenes (resetea la DB)
docker compose down -v

# Reconstruir un servicio específico
docker compose build backend
docker compose up -d backend

# Ejecutar el seeding de datos (productos SFE, distribuidores, regulaciones)
docker compose exec backend python -m app.db.seed

# Abrir un shell en el backend
docker compose exec backend bash

# Ver logs solo de un servicio
docker compose logs -f frontend
```

---

## 🛠️ Desarrollo sin Docker (opcional)

### Backend

```bash
cd src/backend
python -m venv .venv
source .venv/bin/activate          # En Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Asegurarse de tener Postgres+Redis corriendo y .env configurado
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# En otra terminal: worker de Celery
celery -A app.workers.celery_app worker --loglevel=info --concurrency=1
```

### Frontend

```bash
cd src/frontend
npm install
npm run dev         # dev server en http://localhost:5173
npm run build       # build de producción en dist/
npm run test        # tests con Vitest
npm run lint        # ESLint
npm run typecheck   # tsc --noEmit
```

---

## 🧪 Tests

```bash
# Backend (dentro de src/backend)
pytest --cov=app --cov-report=term-missing

# Frontend (dentro de src/frontend)
npm run test
```

---

## 🤝 Contribuir

1. Crear una rama desde `main`: `git checkout -b feature/mi-cambio`
2. Hacer commits descriptivos
3. Abrir un PR contra `main`

Convenciones:
- Backend: formatear con `ruff format` y `ruff check`
- Frontend: ESLint + Prettier
- Mensajes de commit: `tipo(scope): descripción` (Conventional Commits)

---

## 📚 Documentación adicional

- [`Docs/lista_de_tareas.md`](Docs/lista_de_tareas.md) — lista de tareas del proyecto
- [`Docs/Spec_validada.md`](Docs/Spec_validada.md) — especificación validada del MVP
- [`Docs/implementation_plan_1.md`](Docs/implementation_plan_1.md) — plan de implementación integral
- [`Docs/AgentOrchs.md`](Docs/AgentOrchs.md) — orquestación de los 4 agentes IA
- [`Docs/database/schema.dbml`](Docs/database/schema.dbml) — esquema DBML
- [`Docs/database/create_tables.sql`](Docs/database/create_tables.sql) — DDL inicial

---

## 📅 Hitos

| Hito | Fecha |
|---|---|
| Review con profesor | 8–20 de junio |
| Demo final | 26 de junio |

---

## 📄 Licencia

Proyecto académico — uso educativo.
