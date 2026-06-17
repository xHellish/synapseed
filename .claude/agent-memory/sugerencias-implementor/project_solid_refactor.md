---
name: project-solid-refactor
description: SOLID refactoring applied to SynapSeed backend API — new service layer files created, routing layers thinned
metadata:
  type: project
---

Applied SOLID refactoring from `Docs/sugerencias_SOLID.md` to the FastAPI backend at `src/backend/app/`.

## What was done

**New files created:**
- `app/services/auth_strategy.py` — AuthStrategy (ABC) + LocalAuthStrategy + SupabaseAuthStrategy (Strategy Pattern for OCP)
- `app/services/zone_service.py` — LocationMapper, HumidityMapper, TemperatureMapper, ZoneService
- `app/services/task_dispatcher.py` — TaskDispatcher (ABC) + CeleryTaskDispatcher
- `app/services/recommendation_stream_service.py` — RecommendationStreamService (SSE logic isolated)
- `app/services/recommendation_service.py` — RecommendationService (business logic for recommendations)

**Refactored files:**
- `app/services/auth_service.py` — now uses AuthService + AuthServiceFactory; keeps all original module-level functions as backward-compatible wrappers
- `app/api/v1/zones.py` — thin routing layer using `ZoneService` via `Depends(get_zone_service)`
- `app/api/v1/recommendations.py` — thin routing layer using `RecommendationService` and `RecommendationStreamService` via `Depends()`
- `app/services/__init__.py` — updated to export all new service classes

**Untouched (clean) files:** `auth.py`, `dependencies.py`, `health.py`, `router.py`, all model files, all repository files.

**Why:** SRP, OCP, DIP violations in zones.py, recommendations.py, and auth_service.py identified for a Software Design (TEC) course assignment.

**How to apply:** When adding new auth providers, implement a new AuthStrategy subclass. When adding new provinces, update `LocationMapper.LOCATION_REGISTRY`. When changing task queue, implement a new `TaskDispatcher` subclass.
