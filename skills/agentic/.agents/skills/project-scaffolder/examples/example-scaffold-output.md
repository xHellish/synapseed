# Ejemplo de Output — Project Scaffolder

> Este archivo muestra el output típico de scaffolding de un proyecto FastAPI.

---

## Estructura Propuesta

```
my-orders-api/
├── src/
│   └── my_api/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── routers/
│       ├── services/
│       ├── repositories/
│       ├── models/
│       └── schemas/
├── tests/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── Makefile
```

## Scripts Disponibles

```bash
make dev         # Inicia servidor con hot reload
make test        # Ejecuta tests con cobertura
make lint        # Ruff check + mypy
make format      # Ruff format
make docker-up   # Levanta PostgreSQL + API
```

## Guía de Inicio Rápido

```bash
cd my-orders-api
cp .env.example .env
pip install -e ".[dev]"
make docker-up
make dev
# API disponible en http://localhost:8000
# Docs en http://localhost:8000/docs
```
