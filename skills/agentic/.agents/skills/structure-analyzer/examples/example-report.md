# Ejemplo de Output — Structure Analyzer

> Este archivo muestra un reporte de análisis típico generado por la skill `structure-analyzer`.

---

## Resumen ejecutivo

El proyecto `orders-api` es una API REST construida con FastAPI. Sigue una arquitectura en capas clásica (Routers → Services → Repositories) con 4 capas bien definidas. La organización es correcta pero se detectan 2 problemas críticos: un módulo `utils.py` de 847 líneas que actúa como God Module, y dependencias circulares entre `services/order_service.py` y `services/notification_service.py`.

## Árbol de estructura

```
orders-api/
├── src/
│   └── orders_api/
│       ├── __init__.py          # Versión del paquete
│       ├── main.py              # ✅ Entry point correcto
│       ├── config.py            # ✅ Configuración centralizada
│       ├── routers/             # ✅ Capa de presentación
│       ├── services/            # ✅ Lógica de negocio
│       ├── repositories/        # ✅ Acceso a datos
│       ├── models/              # ✅ Modelos SQLAlchemy
│       ├── schemas/             # ✅ Esquemas Pydantic
│       └── utils.py             # ⚠️ God Module (847 líneas)
├── tests/                   # ✅ Tests presentes
├── pyproject.toml           # ✅ Configuración moderna
└── Dockerfile               # ✅ Containerizado
```

## Patrón arquitectónico

**Layered Architecture (N-Tier)** — Evidencia: separación explícita en `routers/`, `services/`, `repositories/`. Los datos fluyen unidireccionalmente: Router → Service → Repository.

## Mapa de dependencias

```mermaid
graph LR
    R[Routers] --> S[Services]
    S --> RP[Repositories]
    RP --> DB[(PostgreSQL)]
    S --> S2[NotificationService]
    S2 --> S  %% ⚠️ Dependencia circular!
```

## Convenciones detectadas

- Nombres de archivos: `snake_case` ✅
- Nombres de clases: `PascalCase` ✅
- Imports: absolutos desde `orders_api.*` ✅
- Tests: espejo de `src/` en `tests/` ✅

## Scorecard de salud

| Aspecto | Score | Notas |
|--------|-------|-------|
| Claridad de estructura | 🟢 | Capas bien definidas |
| Separación de responsabilidades | 🟡 | `utils.py` viola SRP |
| Consistencia de nombres | 🟢 | `snake_case` uniforme |
| Gestión de dependencias | 🟡 | Dependencia circular detectada |
| Estructura de tests | 🟢 | Tests bien organizados |
| Documentación | 🔴 | Sin README actualizado |
| Configuración | 🟢 | `pyproject.toml` correcto |

## Recomendaciones

1. 🔴 **[Crítico]** Eliminar dependencia circular entre `order_service` y `notification_service`. Extraer un evento de dominio `OrderCreated` y usar el patrón Observer.
2. 🟠 **[Alto]** Dividir `utils.py` en módulos especializados: `formatting.py`, `validators.py`, `datetime_helpers.py`.
3. 🟡 **[Medio]** Actualizar README con documentación de instalación y uso.
