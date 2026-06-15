#!/usr/bin/env python3
"""Prueba manual del pipeline de agentes (mock o OpenRouter real).

Uso desde la raíz del repo:
  cd src/backend
  python -m scripts.run_agent_pipeline

Con OpenRouter real (requiere .env en raíz del repo):
  python -m scripts.run_agent_pipeline --live

Con base de datos real (Supabase/local):
  python -m scripts.run_agent_pipeline --live --db
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Raíz backend en PYTHONPATH
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

REPO_ROOT = BACKEND_ROOT.parent.parent
ENV_FILE = REPO_ROOT / ".env"
if ENV_FILE.exists():
    import os

    os.chdir(REPO_ROOT)

from app.agents.orchestrator import AgentOrchestrator
from app.repositories.product_repository import FakeProductRepository, ProductRecord
from app.repositories.regulation_repository import FakeRegulationRepository, RegulationRecord
from app.schemas.farmer_input import FarmerContextInput
from app.services.llm_client import MockLLMClient, OpenRouterLLMClient


def _mock_llm() -> MockLLMClient:
    llm = MockLLMClient()
    llm.register(
        "Analiza el siguiente caso",
        {
            "cultivo": "tomate",
            "problema_detectado": "áfidos en floración",
            "condiciones_agronomicas": {
                "tipo_suelo": "franco-arcilloso",
                "humedad": "media",
                "temperatura": "24°C",
                "calidad_agua": "regular",
            },
            "severidad_estimada": "media",
            "restricciones_relevantes": ["presupuesto medio"],
            "resumen_para_rag": (
                "Tomate en floración con plaga de áfidos, suelo franco-arcilloso, "
                "humedad media, presupuesto medio, sin agroquímico reciente."
            ),
            "advertencias": [],
            "datos_faltantes": [],
            "confianza": 0.85,
            "tipo_proteccion_necesaria": "insecticida",
            "categoria_producto_sugerida": "plaguicida",
        },
    )
    llm.register(
        "normativa fitosanitaria",
        {
            "productos_validos_ids": [1, 2],
            "descartes": [],
            "restricciones_detectadas": [],
            "nivel_riesgo_legal": "bajo",
            "advertencias_legales": [],
            "confianza": 0.9,
            "normativa_insuficiente": False,
        },
    )
    llm.register(
        "consultor agronómico",
        {
            "items": [
                {
                    "product_id": 1,
                    "justificacion": "Mejor ajuste para áfidos en tomate.",
                    "ventajas": ["Alta relevancia"],
                    "riesgos": ["Respetar EPP"],
                    "recomendacion_uso_general": "Seguir etiqueta SFE.",
                },
                {
                    "product_id": 2,
                    "justificacion": "Alternativa económica.",
                    "ventajas": ["Menor costo"],
                    "riesgos": ["Mayor toxicidad"],
                    "recomendacion_uso_general": "Aplicar con precaución.",
                },
            ],
        },
    )
    return llm


def _mock_repos():
    products = [
        ProductRecord(
            id=1,
            numero_registro="SFE-001",
            nombre_comercial="Insecticida Demo A",
            ingrediente_activo="Imidacloprid",
            categoria="plaguicida",
            cultivo_objetivo="tomate",
            problema_objetivo="áfidos",
            precio_referencia_por_litro=12000.0,
            banda_toxicologica="amarilla",
            dosis_recomendada="1.5 L/ha",
            intervalo_seguridad_dias=14,
        ),
        ProductRecord(
            id=2,
            numero_registro="SFE-002",
            nombre_comercial="Insecticida Demo B",
            ingrediente_activo="Lambda-cihalotrina",
            categoria="plaguicida",
            cultivo_objetivo="tomate",
            problema_objetivo="insectos",
            precio_referencia_por_litro=9000.0,
            banda_toxicologica="roja",
            dosis_recomendada="0.8 L/ha",
            intervalo_seguridad_dias=7,
        ),
    ]
    regulations = [
        RegulationRecord(
            id=1,
            numero="Lista Prohibida SFE",
            titulo="Prohibidas",
            tipo="lista_prohibida",
            resumen="Sustancias prohibidas",
            sustancias_afectadas="Endosulfán",
            cultivos_afectados="Todos",
        )
    ]
    return FakeProductRepository(products), FakeRegulationRepository(regulations)


async def _run(*, live: bool, use_db: bool) -> None:
    farmer = FarmerContextInput(
        crop="tomate",
        crop_stage="floración",
        problem="áfidos en hojas jóvenes",
        problem_category="plaga",
        last_agrochemical_used="ninguno",
        budget_range="medio",
        soil_type="franco-arcilloso",
        humidity="media",
        temperature="24",
        water_quality="regular",
    )

    if live:
        llm = OpenRouterLLMClient()
    else:
        llm = _mock_llm()

    if use_db and live:
        from app.db.session import get_db_session
        from app.repositories.product_repository import SqlAlchemyProductRepository
        from app.repositories.regulation_repository import SqlAlchemyRegulationRepository

        async with get_db_session() as session:
            orchestrator = AgentOrchestrator(
                llm=llm,
                product_repo=SqlAlchemyProductRepository(session),
                regulation_repo=SqlAlchemyRegulationRepository(session),
            )
            result = await orchestrator.run(farmer)
    else:
        product_repo, regulation_repo = _mock_repos()
        orchestrator = AgentOrchestrator(
            llm=llm,
            product_repo=product_repo,
            regulation_repo=regulation_repo,
        )
        result = await orchestrator.run(farmer)

    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Ejecutar pipeline de agentes SynapSeed")
    parser.add_argument("--live", action="store_true", help="Usar OpenRouter real")
    parser.add_argument("--db", action="store_true", help="Usar repositorios SQLAlchemy (requiere --live)")
    args = parser.parse_args()
    asyncio.run(_run(live=args.live, use_db=args.db))


if __name__ == "__main__":
    main()
