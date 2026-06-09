# ============================================
# SynapSeed — Backend Dockerfile
# ============================================
# Imagen multi-stage para FastAPI + uvicorn

# ---------- Etapa base ----------
FROM python:3.12-slim AS base

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias de sistema mínimas (psycopg2, bcrypt, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# ---------- Etapa de desarrollo ----------
FROM base AS dev

# Instalar el proyecto en modo editable + extras de dev
COPY pyproject.toml ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
RUN pip install --upgrade pip && \
    pip install -e ".[dev]" && \
    rm -rf /root/.cache/pip

# Puerto de uvicorn
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Comando por defecto: aplicar migraciones y arrancar uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]

# ---------- Etapa de producción ----------
FROM base AS prod

COPY pyproject.toml ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
RUN pip install --upgrade pip && \
    pip install -e ".[prod]" && \
    rm -rf /root/.cache/pip

# Usuario no-root por seguridad
RUN useradd --create-home --shell /bin/bash synapseed && \
    chown -R synapseed:synapseed /app
USER synapseed

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Producción: gunicorn + uvicorn workers
CMD ["sh", "-c", "alembic upgrade head && gunicorn app.main:app \
        -k uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000 \
        --workers 2 \
        --timeout 120 \
        --access-logfile - \
        --error-logfile -"]
