# Ejemplo de Output — Docs Generator

> README generado automáticamente para el proyecto `orders-api`.

---

<div align="center">

# 📦 Orders API

**REST API para gestión de órdenes de comercio electrónico.**

[![CI](https://github.com/org/orders-api/actions/workflows/ci.yml/badge.svg)](https://github.com/org/orders-api/actions)
[![Coverage](https://img.shields.io/badge/coverage-87%25-green)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## ⚡ Quick Start

```bash
git clone https://github.com/org/orders-api.git
cd orders-api
cp .env.example .env
make docker-up
make dev
# API en http://localhost:8000 | Docs en http://localhost:8000/docs
```

## 📖 Endpoints Principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/orders` | Crear nueva orden |
| GET | `/orders/{id}` | Obtener orden por ID |
| GET | `/orders` | Listar órdenes del usuario |
| DELETE | `/orders/{id}` | Cancelar orden |

## 🔧 Configuración

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `DATABASE_URL` | ✅ | URL de PostgreSQL |
| `SECRET_KEY` | ✅ | Clave JWT (≥32 chars) |
| `DEBUG` | No | Default: `false` |
