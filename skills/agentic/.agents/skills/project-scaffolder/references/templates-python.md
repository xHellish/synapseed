# Project Templates Reference

This document contains ready-to-use project templates with complete directory structures, configuration files, and development scripts.

> **⚠️ Versiones de dependencias**: Las versiones especificadas en este documento fueron verificadas en **2026-05-28**.
> Se recomienda revisar y actualizar las versiones trimestralmente o antes de iniciar un proyecto en producción.
> Usa `pip index versions <package>` (Python) o `npm show <package> version` (Node) para verificar la versión más reciente.

---

## Python Templates

---

### 1. python-api — FastAPI REST API

**When to use**: Building a REST API, microservice, or backend service. Ideal for JSON APIs with automatic OpenAPI documentation.

#### Directory Tree

```
my-api/
├── src/
│   └── my_api/
│       ├── __init__.py              # Package init, version
│       ├── main.py                  # FastAPI app entry point
│       ├── config.py                # Settings via pydantic-settings
│       ├── dependencies.py          # Shared FastAPI dependencies
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── health.py            # Health check endpoint
│       │   └── items.py             # Example resource router
│       ├── models/
│       │   ├── __init__.py
│       │   └── item.py              # SQLAlchemy / ORM models
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── item.py              # Pydantic request/response schemas
│       ├── services/
│       │   ├── __init__.py
│       │   └── item_service.py      # Business logic layer
│       └── db/
│           ├── __init__.py
│           ├── session.py           # Database session management
│           └── migrations/          # Alembic migrations directory
│               ├── env.py
│               ├── script.py.mako
│               └── versions/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Shared fixtures (test client, db)
│   ├── test_health.py
│   └── test_items.py
├── pyproject.toml                   # Single source of truth
├── Dockerfile                       # Multi-stage production build
├── docker-compose.yml               # Local dev with DB
├── .env.example                     # Environment variable template
├── .gitignore
├── .editorconfig
├── .python-version                  # e.g., 3.12
├── README.md
└── Makefile                         # Dev task runner
```

#### Core Configuration: `pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-api"
version = "0.1.0"
description = "A FastAPI REST API"
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "pydantic>=2.9",
    "pydantic-settings>=2.6",
    "sqlalchemy>=2.0",
    "alembic>=1.14",
    "httpx>=0.27",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-asyncio>=0.24",
    "pytest-cov>=6.0",
    "ruff>=0.8",
    "mypy>=1.13",
    "pre-commit>=4.0",
]

[tool.ruff]
target-version = "py312"
line-length = 88
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "S", "B", "A", "C4", "PT", "RUF"]
ignore = ["S101"]  # Allow assert in tests

[tool.ruff.lint.isort]
known-first-party = ["my_api"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "--cov=src/my_api --cov-report=term-missing"

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]

[tool.hatch.build.targets.wheel]
packages = ["src/my_api"]
```

#### Dockerfile (Multi-stage)

```dockerfile
# Stage 1: Build
FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Stage 2: Production
FROM python:3.12-slim AS production
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ ./src/

EXPOSE 8000
CMD ["uvicorn", "my_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./src:/app/src  # Hot reload in dev

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: app_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

#### Makefile

```makefile
.PHONY: dev test lint format migrate

dev:
	uvicorn my_api.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

lint:
	ruff check src/ tests/
	mypy src/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(msg)"

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down
```

#### CI Workflow: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: ruff check src/ tests/
      - run: ruff format --check src/ tests/
      - run: mypy src/

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd="pg_isready -U test"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: pytest --cov-report=xml
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test_db
```

---

### 2. python-lib — Reusable Python Library

**When to use**: Creating a pip-installable library or SDK to be published on PyPI. Suitable for internal shared packages as well.

#### Directory Tree

```
my-lib/
├── src/
│   └── my_lib/
│       ├── __init__.py              # Public API, __version__
│       ├── core.py                  # Core functionality
│       ├── utils.py                 # Internal utilities
│       ├── exceptions.py            # Custom exceptions
│       └── py.typed                 # PEP 561 marker for typed package
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Shared fixtures
│   ├── test_core.py
│   └── test_utils.py
├── docs/
│   ├── index.md                     # Documentation home
│   ├── getting-started.md
│   ├── api-reference.md
│   └── changelog.md
├── examples/
│   └── basic_usage.py               # Runnable example
├── pyproject.toml                   # Build, metadata, tools
├── LICENSE                          # MIT license text
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md                     # Keep-a-Changelog format
├── .gitignore
├── .editorconfig
├── .python-version
└── .pre-commit-config.yaml
```

#### Core Configuration: `pyproject.toml`

```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
name = "my-lib"
dynamic = ["version"]
description = "A useful Python library"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
    { name = "Your Name", email = "you@example.com" },
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Typing :: Typed",
]
keywords = ["library", "utility"]

[project.urls]
Homepage = "https://github.com/user/my-lib"
Documentation = "https://my-lib.readthedocs.io"
Repository = "https://github.com/user/my-lib"
Changelog = "https://github.com/user/my-lib/blob/main/CHANGELOG.md"

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-cov>=6.0",
    "ruff>=0.8",
    "mypy>=1.13",
    "pre-commit>=4.0",
    "build>=1.2",
    "twine>=5.1",
]
docs = [
    "mkdocs>=1.6",
    "mkdocs-material>=9.5",
    "mkdocstrings[python]>=0.26",
]

[tool.hatch.version]
source = "vcs"

[tool.hatch.build.targets.wheel]
packages = ["src/my_lib"]

[tool.ruff]
target-version = "py310"
line-length = 88
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "D", "S", "B", "A", "C4", "PT", "RUF"]
ignore = ["S101", "D100", "D104"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.isort]
known-first-party = ["my_lib"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src/my_lib --cov-report=term-missing --strict-markers"

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
```

#### `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: []
        args: [--strict]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
```

#### CI Workflow: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: ruff check src/ tests/
      - run: ruff format --check src/ tests/
      - run: mypy src/
      - run: pytest --cov-report=xml

  publish:
    needs: test
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

#### Development Scripts

```bash
# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov-report=html

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/

# Build package
python -m build

# Upload to PyPI (after building)
twine upload dist/*

# Docs
pip install -e ".[docs]"
mkdocs serve
```

---

### 3. python-cli — CLI Application

**When to use**: Building command-line tools, developer utilities, or automation scripts that need argument parsing, subcommands, and rich output.

#### Directory Tree

```
my-cli/
├── src/
│   └── my_cli/
│       ├── __init__.py              # Version info
│       ├── main.py                  # Typer app, entry point
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── init.py              # `mycli init` command
│       │   └── run.py               # `mycli run` command
│       ├── config.py                # Config file loading (TOML/YAML)
│       ├── console.py               # Rich console setup
│       └── utils.py                 # Shared helpers
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # CLI test fixtures
│   ├── test_init_command.py
│   └── test_run_command.py
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── .editorconfig
└── .python-version
```

#### Core Configuration: `pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-cli"
version = "0.1.0"
description = "A powerful CLI tool"
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
dependencies = [
    "typer>=0.13",
    "rich>=13.9",
    "pydantic>=2.9",
    "tomli>=2.0; python_version < '3.11'",
]

[project.scripts]
mycli = "my_cli.main:app"

[project.optional-dependencies]
dev = [
    "pytest>=8.3",
    "pytest-cov>=6.0",
    "ruff>=0.8",
    "mypy>=1.13",
]

[tool.hatch.build.targets.wheel]
packages = ["src/my_cli"]

[tool.ruff]
target-version = "py311"
line-length = 88
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "S", "B", "A", "C4", "PT", "RUF"]
ignore = ["S101"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src/my_cli --cov-report=term-missing"

[tool.mypy]
python_version = "3.11"
strict = true
```

#### Example `main.py`

```python
"""Main CLI entry point."""

import typer
from rich.console import Console

from my_cli.commands import init, run

app = typer.Typer(
    name="mycli",
    help="A powerful CLI tool for project automation.",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()

app.add_typer(init.app, name="init")
app.add_typer(run.app, name="run")


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Configure global options."""
    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")


if __name__ == "__main__":
    app()
```

#### CI Workflow: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: ruff check src/ tests/
      - run: mypy src/
      - run: pytest
```
