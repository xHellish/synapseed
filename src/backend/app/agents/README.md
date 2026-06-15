# Pipeline de Agentes IA — SynapSeed

Módulo aislado para el pipeline de **4 agentes** de recomendación de agroquímicos.
Listo para integración posterior vía FastAPI, Celery o LangGraph.

## Arquitectura

```
FarmerContextInput
       │
       ▼
┌──────────────────────┐
│ 1. Analizador        │  OpenRouter — estructura contexto agronómico
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 2. Investigador RAG  │  SQLAlchemy → products (filtros; vector pendiente)
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 3. Validador Legal   │  Reglas SFE + OpenRouter sobre normativa real
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 4. Sintetizador      │  Top 3 desde DB + OpenRouter solo para texto
└──────────┬───────────┘
           ▼
    PipelineResult
```

## Contratos por agente

### Entrada global — `FarmerContextInput`

| Campo | Tipo | Obligatorio |
|-------|------|-------------|
| `crop`, `crop_stage`, `problem`, `problem_category` | str | Sí |
| `last_agrochemical_used`, `budget_range`, `soil_type`, `water_quality` | str \| null | No |
| `humidity`, `temperature` | float \| str \| null | No |
| `zone_id` | int \| null | No |

### Agente 1 — Analizador (`ContextAnalysisOutput`)

**Entrada:** `FarmerContextInput`  
**Salida principal:** `cultivo`, `problema_detectado`, `condiciones_agronomicas`, `severidad_estimada`, `restricciones_relevantes`, `resumen_para_rag`, `advertencias`, `datos_faltantes`, `confianza`, `tipo_proteccion_necesaria`, `categoria_producto_sugerida`

No recomienda productos. Usa **OpenRouter**.

### Agente 2 — Investigador (`ResearchOutput`)

**Entrada:** `ContextAnalysisOutput`  
**Salida:** `candidatos[]` (`ProductCandidate`), `metodo_busqueda`, `total_encontrados`, `advertencias`

Cada candidato incluye `product_id`, datos de catálogo y `score_relevancia`. **No usa LLM.** Lee solo de repositorio/DB.

### Agente 3 — Validador Legal (`LegalValidationOutput`)

**Entrada:** `ContextAnalysisOutput` + `ResearchOutput`  
**Salida:** `productos_validos[]`, `productos_descartados[]`, `restricciones_detectadas`, `nivel_riesgo_legal`, `advertencias_legales`, `confianza`, `normativa_insuficiente`

Regla de ingeniería: **ante duda legal, no validar automáticamente**. Solo entran a `productos_validos` los IDs confirmados explícitamente por el LLM tras pasar reglas determinísticas. Usa **OpenRouter** + DB (`regulations`).

### Agente 4 — Sintetizador (`SynthesisOutput`)

**Entrada:** `ContextAnalysisOutput` + `LegalValidationOutput`  
**Salida:** `recomendaciones[]` (máx. 3), `candidatos_validos_totales`, `advertencias`, `confianza`

Datos factuales (`dosis`, `precio`, `toxicidad`, `intervalo_seguridad`) vienen de DB; si faltan → `"no_disponible"`. El LLM solo genera texto interpretativo. Usa **OpenRouter**.

### Resultado final — `PipelineResult`

Incluye `input`, las cuatro salidas intermedias y `processing_steps`.

## Comportamiento ante fallos y datos faltantes

| Situación | Comportamiento |
|-----------|----------------|
| **Sin productos en DB** | Investigador devuelve `candidatos=[]` + advertencia; pipeline continúa |
| **Sin regulaciones en DB** | Validador descarta todos, `normativa_insuficiente=True`, `productos_validos=[]` |
| **LLM legal sin IDs válidos** | No se asume validez; candidatos van a `productos_descartados` con motivo procedural |
| **Sin productos legalmente válidos** | Sintetizador devuelve `recomendaciones=[]` + advertencia |
| **Menos de 3 válidos** | Sintetizador devuelve los disponibles (1 o 2) + advertencia explícita |
| **Fallo LLM / JSON inválido** | `LLMError` desde `llm_client`; no se fabrica salida falsa (propaga al caller) |
| **Datos factuales faltantes** | `"no_disponible"` en salida del sintetizador; no se inventan valores |

## Orquestador — integración para compañeros

```python
from app.agents.orchestrator import AgentOrchestrator
from app.services.llm_client import OpenRouterLLMClient
from app.repositories.product_repository import SqlAlchemyProductRepository
from app.repositories.regulation_repository import SqlAlchemyRegulationRepository
from app.schemas.farmer_input import FarmerContextInput

# En FastAPI: async with get_db_session() as session:
orchestrator = AgentOrchestrator(
    llm=OpenRouterLLMClient(),
    product_repo=SqlAlchemyProductRepository(session),
    regulation_repo=SqlAlchemyRegulationRepository(session),
)
result = await orchestrator.run(farmer_input)
# result.model_dump() → persistir o responder por API/Celery
```

Clase: `AgentOrchestrator.run()` en `orchestrator.py` — pipeline secuencial Python (LangGraph pendiente).

## Qué usa mocks, DB real y OpenRouter

| Componente | Tests unitarios | Script default | Producción futura |
|------------|-----------------|----------------|-------------------|
| LLM | `MockLLMClient` | `MockLLMClient` | `OpenRouterLLMClient` |
| Productos | `FakeProductRepository` | Fake | `SqlAlchemyProductRepository` |
| Regulaciones | `FakeRegulationRepository` | Fake | `SqlAlchemyRegulationRepository` |

## Cliente LLM

- `app/services/llm_client.py`
- `OpenRouterLLMClient`: OpenRouter vía `langchain-openai` + retries (`tenacity`)
- `MockLLMClient`: tests y script mock
- JSON inválido → `LLMError` (no silencioso)
- **No usa Gemini**

Variables: `OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OPENROUTER_CHAT_MODEL`

## Tests

```bash
cd src/backend
pip install -e ".[dev]"
pytest tests/agents -v
```

Todos los tests usan **mocks** — no llaman OpenRouter ni DB real.

## Prueba manual

```bash
cd src/backend

# Mock completo (sin API ni DB)
python -m scripts.run_agent_pipeline

# OpenRouter real + repos mock
python -m scripts.run_agent_pipeline --live

# OpenRouter + Supabase/local DB
python -m scripts.run_agent_pipeline --live --db
```

> Ejecutar desde `src/backend` con `.env` en la raíz del repo (el script cambia cwd).

## Límites conocidos

1. **Búsqueda vectorial pendiente** — fallback por filtros SQL + scoring heurístico.
2. **OpenRouter real no probado automáticamente** — solo mocks en CI/tests.
3. **Repositorios SQLAlchemy no cubiertos por tests unitarios** — requieren integración/DB.
4. **Workaround pytest en `pyproject.toml`** — se ignora `sqlalchemy.exc.SADeprecationWarning` al importar modelos ORM existentes (`User.recommendations`). Solo afecta tests, no runtime. La corrección definitiva es arreglar el ORM (fuera de este módulo).

## Decisiones técnicas

1. Orquestador simple en lugar de LangGraph (testabilidad primero).
2. OpenRouter para razonamiento; Gemini solo en `seed.py` (embeddings).
3. Validador híbrido estricto: reglas + LLM; sin auto-validación por omisión.
4. Sintetizador: datos factuales solo desde DB; LLM para texto.
5. Sin migraciones JSONB en esta entrega.

## Pendiente para integración (fuera de este módulo)

- [ ] Endpoint `POST /api/v1/recommendations/request`
- [ ] Celery task que invoque `AgentOrchestrator`
- [ ] SSE / Redis pub/sub
- [ ] Columnas JSONB `agent_context`, `agent_research`, etc.
- [ ] LangGraph como reemplazo del orquestador secuencial
- [ ] Búsqueda vectorial con embeddings de query en runtime

## Documentación guía

- `Docs/Spec_validada.md` — contratos funcionales
- `Docs/AgentOrchs.md` — pipeline secuencial de 4 agentes
- `Docs/lista_de_tareas.md` — tareas 3.1–3.9
