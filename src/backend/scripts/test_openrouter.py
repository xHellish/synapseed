#!/usr/bin/env python3
"""Test completo de OpenRouter — conectividad, modelos, schemas y agentes.

Prueba:
  1. Ping básico a la API de OpenRouter
  2. Chat completion con el modelo configurado
  3. Respuesta JSON válida para el Agente 1 (Analyzer)
  4. Respuesta de texto plano para el Agente 4 (Synthesizer)
  5. Respuesta JSON para el Agente 3 (Legal Validator)
  6. Extracción de JSON de respuesta con markdown fence
  7. Rate limiting / reintentos
  8. Modelos alternativos gratuitos
"""

import asyncio
import json
import os
import re
import sys
import time
from typing import Any

# Forzar encoding UTF-8 en Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Cargar .env si python-dotenv disponible
try:
    from dotenv import load_dotenv
    # Intentar cargar .env desde varias ubicaciones
    for env_path in [
        os.path.join(os.path.dirname(__file__), "..", ".env"),
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        ".env",
    ]:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"[INFO] .env cargado desde: {env_path}")
            break
except ImportError:
    pass

import httpx

# ============================================
# Configuración
# ============================================
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
CHAT_MODEL = os.environ.get("OPENROUTER_CHAT_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

RESULTS: list[dict[str, Any]] = []


def record(test_name: str, passed: bool, detail: str = "") -> None:
    """Registrar resultado de una prueba."""
    icon = "✅" if passed else "❌"
    RESULTS.append({"name": test_name, "passed": passed, "detail": detail})
    print(f"  {icon} {test_name}" + (f" — {detail}" if detail else ""))


def extract_json(text: str) -> dict:
    """Extrae JSON de respuesta (incluye bloques markdown)."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    return json.loads(text)


# ============================================
# Tests
# ============================================

async def test_connectivity(client: httpx.AsyncClient) -> None:
    """1. Verificar conectividad con OpenRouter (GET /models)."""
    print("\n[1] Test de conectividad (GET /models)...")
    try:
        resp = await client.get(
            f"{BASE_URL}/models",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            n_models = len(data.get("data", []))
            record("Conectividad API", True, f"{n_models} modelos disponibles")
        else:
            record("Conectividad API", False, f"HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        record("Conectividad API", False, str(e)[:200])


async def test_basic_chat(client: httpx.AsyncClient) -> dict | None:
    """2. Chat completion básico — solo texto."""
    print("\n[2] Test de chat completion básico...")
    payload = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "Eres un asistente útil. Responde en español."},
            {"role": "user", "content": "¿Cuál es la capital de Costa Rica? Responde en una sola palabra."},
        ],
        "temperature": 0.0,
        "max_tokens": 50,
    }
    try:
        resp = await client.post(
            f"{BASE_URL}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            choice = data.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "")
            if content is None:
                content = ""
            usage = data.get("usage", {})
            record(
                "Chat completion básico",
                True,
                f"Respuesta: '{content.strip()[:80]}' | Tokens: prompt={usage.get('prompt_tokens', '?')}, completion={usage.get('completion_tokens', '?')}",
            )
            return data
        else:
            record("Chat completion básico", False, f"HTTP {resp.status_code}: {resp.text[:300]}")
            return None
    except Exception as e:
        record("Chat completion básico", False, str(e)[:200])
        return None


async def test_analyzer_agent(client: httpx.AsyncClient) -> None:
    """3. Agente 1 — Analyzer: debe devolver JSON válido con schema ContextAnalysisOutput."""
    print("\n[3] Test Agente 1 (Analyzer) — respuesta JSON estructurada...")

    schema_hint = """{
  "cultivo": str,
  "problema_detectado": str,
  "condiciones_agronomicas": {"tipo_suelo": str, "humedad": str, "temperatura": str, "calidad_agua": str},
  "severidad_estimada": "baja|media|alta",
  "restricciones_relevantes": [str],
  "resumen_para_rag": str (mínimo 40 palabras),
  "advertencias": [str],
  "datos_faltantes": [str],
  "confianza": float (0.0-1.0),
  "tipo_proteccion_necesaria": "herbicida|fungicida|insecticida|fertilizante|otro",
  "categoria_producto_sugerida": "plaguicida|fertilizante"
}"""

    system = (
        "Eres un agrónomo experto del SFE de Costa Rica. "
        "Analiza el contexto y devuelve JSON estructurado. "
        "NO recomiendes productos. Responde ÚNICAMENTE con JSON válido, sin markdown ni texto extra."
    )
    user = f"""Analiza el siguiente caso agrícola:

- Cultivo: tomate
- Etapa: floración
- Problema: plaga de mosca blanca
- Categoría: insecticida
- Último agroquímico: ninguno
- Presupuesto: 15000 colones/litro
- Tipo de suelo: franco-arcilloso
- Humedad: 65.5%
- Temperatura: 24°C
- Calidad del agua: buena
- Zona: Central

Devuelve JSON con este schema: {schema_hint}"""

    payload = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 1000,
    }
    try:
        resp = await client.post(
            f"{BASE_URL}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )
        if resp.status_code != 200:
            record("Agente 1 (Analyzer)", False, f"HTTP {resp.status_code}: {resp.text[:300]}")
            return

        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens_info = f"Tokens: prompt={usage.get('prompt_tokens', '?')}, completion={usage.get('completion_tokens', '?')}"

        # Intentar parsear JSON
        try:
            parsed = extract_json(content)
        except json.JSONDecodeError as e:
            record("Agente 1 (Analyzer) — JSON válido", False, f"No se pudo parsear JSON: {e}")
            print(f"    Respuesta cruda: {content[:500]}")
            return

        record("Agente 1 (Analyzer) — JSON válido", True, tokens_info)

        # Validar campos requeridos
        required_fields = [
            "cultivo", "problema_detectado", "condiciones_agronomicas",
            "severidad_estimada", "resumen_para_rag", "confianza",
            "tipo_proteccion_necesaria", "categoria_producto_sugerida",
        ]
        missing = [f for f in required_fields if f not in parsed]
        if missing:
            record("Agente 1 (Analyzer) — campos requeridos", False, f"Faltan: {missing}")
        else:
            record("Agente 1 (Analyzer) — campos requeridos", True, "Todos presentes")

        # Validar tipos
        errors = []
        if not isinstance(parsed.get("condiciones_agronomicas"), dict):
            errors.append("condiciones_agronomicas no es dict")
        if not isinstance(parsed.get("restricciones_relevantes"), list):
            errors.append("restricciones_relevantes no es list")
        if not isinstance(parsed.get("advertencias"), list):
            errors.append("advertencias no es list")
        if not isinstance(parsed.get("datos_faltantes"), list):
            errors.append("datos_faltantes no es list")
        confianza = parsed.get("confianza")
        if confianza is not None and not (0.0 <= float(confianza) <= 1.0):
            errors.append(f"confianza={confianza} fuera de rango [0,1]")
        severidad = parsed.get("severidad_estimada", "")
        if severidad not in ("baja", "media", "alta"):
            errors.append(f"severidad_estimada='{severidad}' no es válida")
        cat = parsed.get("categoria_producto_sugerida", "")
        if cat not in ("plaguicida", "fertilizante"):
            errors.append(f"categoria_producto_sugerida='{cat}' no es válida")

        if errors:
            record("Agente 1 (Analyzer) — validación tipos", False, "; ".join(errors))
        else:
            record("Agente 1 (Analyzer) — validación tipos", True)

        # Validar resumen_para_rag longitud
        resumen = parsed.get("resumen_para_rag", "")
        word_count = len(resumen.split())
        if word_count < 40:
            record("Agente 1 (Analyzer) — resumen_para_rag >= 40 palabras", False, f"Solo {word_count} palabras")
        else:
            record("Agente 1 (Analyzer) — resumen_para_rag >= 40 palabras", True, f"{word_count} palabras")

    except Exception as e:
        record("Agente 1 (Analyzer)", False, str(e)[:200])


async def test_synthesizer_agent(client: httpx.AsyncClient) -> None:
    """4. Agente 4 — Synthesizer: respuesta de texto con justificaciones."""
    print("\n[4] Test Agente 4 (Synthesizer) — texto interpretativo...")

    system = (
        "Eres un consultor agronómico costarricense. "
        "Genera justificaciones agronómicas en español. "
        "PROHIBIDO inventar dosis, precios, toxicidad o intervalos."
    )
    user = """Contexto: Agricultor con cultivo de tomate en etapa de floración, plaga de mosca blanca.

Producto 1: Imidacloprid 200 SL (ingrediente activo: imidacloprid, categoría: insecticida)
Producto 2: Piriproxifen 100 EC (ingrediente activo: piriproxifen, categoría: insecticida)

Genera una justificación breve (100-200 palabras) para cada producto."""

    payload = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": 1500,
    }
    try:
        resp = await client.post(
            f"{BASE_URL}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )
        if resp.status_code != 200:
            record("Agente 4 (Synthesizer)", False, f"HTTP {resp.status_code}: {resp.text[:300]}")
            return

        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens_info = f"Tokens: prompt={usage.get('prompt_tokens', '?')}, completion={usage.get('completion_tokens', '?')}"

        if not content or not content.strip():
            record("Agente 4 (Synthesizer)", False, "Respuesta vacía")
            return

        word_count = len(content.split())
        record("Agente 4 (Synthesizer)", True, f"{word_count} palabras | {tokens_info}")

        # Verificar que no contenga dosis inventadas (números seguidos de ml/litro)
        has_dosis = bool(re.search(r"\d+\s*(?:ml|litro|L)/(?:ha|litro|m2)", content, re.IGNORECASE))
        if has_dosis:
            record("Agente 4 — no inventa dosis", False, "Contiene dosis sospechosas")
        else:
            record("Agente 4 — no inventa dosis", True, "Sin dosis inventadas detectadas")

    except Exception as e:
        record("Agente 4 (Synthesizer)", False, str(e)[:200])


async def test_legal_validator_agent(client: httpx.AsyncClient) -> None:
    """5. Agente 3 — Legal Validator: respuesta JSON con validación normativa."""
    print("\n[5] Test Agente 3 (Legal Validator) — validación normativa...")

    schema_hint = """{
  "productos_validos": [{"producto_id": int, "notas_validacion": str}],
  "productos_descartados": [{"producto_id": int, "motivo_de_descarte": str, "regulacion_referencia": str}],
  "restricciones_detectadas": [str],
  "nivel_riesgo_legal": "bajo|medio|alto|incierto",
  "advertencias_legales": [str],
  "confianza": float (0.0-1.0),
  "normativa_insuficiente": bool
}"""

    system = (
        "Eres un especialista en normativa fitosanitaria de Costa Rica (SFE/MAG). "
        "Valida productos candidatos contra regulaciones. "
        "NO inventes leyes. Si la normativa es insuficiente, marca normativa_insuficiente=true. "
        "Responde ÚNICAMENTE con JSON válido, sin markdown ni texto extra."
    )
    user = f"""Productos candidatos:
- ID 1: Imidacloprid 200 SL (ingrediente: imidacloprid, registro: CR-001)
- ID 2: Piriproxifen 100 EC (ingrediente: piriproxifen, registro: CR-002)

Regulaciones disponibles:
- El imidacloprid está autorizado para tomate en Costa Rica (Decreto MAG-2020).
- No hay restricciones específicas para piriproxifen en tomate.

Devuelve JSON con schema: {schema_hint}"""

    payload = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 800,
    }
    try:
        resp = await client.post(
            f"{BASE_URL}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )
        if resp.status_code != 200:
            record("Agente 3 (Legal Validator)", False, f"HTTP {resp.status_code}: {resp.text[:300]}")
            return

        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens_info = f"Tokens: prompt={usage.get('prompt_tokens', '?')}, completion={usage.get('completion_tokens', '?')}"

        try:
            parsed = extract_json(content)
        except json.JSONDecodeError as e:
            record("Agente 3 (Legal Validator) — JSON válido", False, f"JSON parse error: {e}")
            print(f"    Respuesta cruda: {content[:500]}")
            return

        record("Agente 3 (Legal Validator) — JSON válido", True, tokens_info)

        # Validar campos
        required = ["nivel_riesgo_legal", "confianza", "normativa_insuficiente"]
        missing = [f for f in required if f not in parsed]
        if missing:
            record("Agente 3 — campos requeridos", False, f"Faltan: {missing}")
        else:
            record("Agente 3 — campos requeridos", True)

        nivel = parsed.get("nivel_riesgo_legal", "")
        if nivel not in ("bajo", "medio", "alto", "incierto"):
            record("Agente 3 — nivel_riesgo_legal válido", False, f"'{nivel}' no es válido")
        else:
            record("Agente 3 — nivel_riesgo_legal válido", True)

        confianza = parsed.get("confianza")
        if confianza is not None and not (0.0 <= float(confianza) <= 1.0):
            record("Agente 3 — confianza válido", False, f"{confianza} fuera de rango")
        else:
            record("Agente 3 — confianza válido", True)

    except Exception as e:
        record("Agente 3 (Legal Validator)", False, str(e)[:200])


async def test_json_with_markdown_fence(client: httpx.AsyncClient) -> None:
    """6. Verificar extracción de JSON envuelto en ```json ... ```."""
    print("\n[6] Test de extracción JSON con markdown fence...")

    payload = {
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": "Responde SIEMPRE envolviendo tu JSON en un bloque markdown ```json ... ```."},
            {"role": "user", "content": 'Devuelve: {"nombre": "test", "valor": 42, "lista": ["a", "b"]}'},
        ],
        "temperature": 0.0,
        "max_tokens": 100,
    }
    try:
        resp = await client.post(
            f"{BASE_URL}/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        if resp.status_code != 200:
            record("Extracción JSON markdown", False, f"HTTP {resp.status_code}")
            return

        choice = resp.json().get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        if not content:
            record("Extracción JSON markdown — fence presente", False, "Respuesta vacía")
            return
        has_fence = "```json" in content or "```" in content
        if not has_fence:
            record("Extracción JSON markdown — fence presente", False, "No hay bloque markdown")
            print(f"    Respuesta: {content[:300]}")
        else:
            record("Extracción JSON markdown — fence presente", True)

        parsed = extract_json(content)
        if parsed.get("nombre") == "test" and parsed.get("valor") == 42:
            record("Extracción JSON markdown — parse correcto", True)
        else:
            record("Extracción JSON markdown — parse correcto", False, f"Datos incorrectos: {parsed}")

    except Exception as e:
        record("Extracción JSON markdown", False, str(e)[:200])


async def test_rate_limit_handling(client: httpx.AsyncClient) -> None:
    """7. Test de rate limiting — enviar 3 requests rápidos."""
    print("\n[7] Test de rate limiting (3 requests rápidos)...")
    results = []
    for i in range(3):
        payload = {
            "model": CHAT_MODEL,
            "messages": [
                {"role": "user", "content": f"Responde solo el número {i+1}."},
            ],
            "temperature": 0.0,
            "max_tokens": 10,
        }
        try:
            t0 = time.time()
            resp = await client.post(
                f"{BASE_URL}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            elapsed = time.time() - t0
            results.append({
                "status": resp.status_code,
                "elapsed": f"{elapsed:.1f}s",
                "rate_limited": resp.status_code == 429,
            })
        except Exception as e:
            results.append({"status": "error", "error": str(e)[:100]})

    rate_limited = [r for r in results if r.get("rate_limited")]
    errors = [r for r in results if r.get("status") not in (200, 429)]
    successes = [r for r in results if r.get("status") == 200]

    if errors:
        record("Rate limiting", False, f"Errores: {errors}")
    elif rate_limited:
        record("Rate limiting", True, f"Rate limited en {len(rate_limited)}/3 — OK (respeta límites)")
    else:
        record("Rate limiting", True, f"3/3 exitosos: {[r['elapsed'] for r in results]}")


async def test_free_models(client: httpx.AsyncClient) -> None:
    """8. Probar modelos alternativos gratuitos."""
    print("\n[8] Test de modelos alternativos gratuitos...")

    free_models = [
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemma-4-26b-a4b-it:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "meta-llama/llama-3.2-3b-instruct:free",
    ]

    for model in free_models:
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": "Responde solo: OK"},
            ],
            "temperature": 0.0,
            "max_tokens": 10,
        }
        try:
            resp = await client.post(
                f"{BASE_URL}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                record(f"Modelo {model}", True, f"Respuesta: '{content.strip()[:40]}'")
            elif resp.status_code == 429:
                record(f"Modelo {model}", True, "Rate limited (disponible pero en límite)")
            else:
                err = resp.json().get("error", {}).get("message", resp.text[:150])
                record(f"Modelo {model}", False, f"HTTP {resp.status_code}: {err}")
        except Exception as e:
            record(f"Modelo {model}", False, str(e)[:150])


async def test_langchain_integration() -> None:
    """9. Test directo del OpenRouterLLMClient (langchain-openai)."""
    print("\n[9] Test de integración con langchain-openai (OpenRouterLLMClient)...")

    try:
        from app.config import Settings, get_settings
        from app.services.llm_client import OpenRouterLLMClient, LLMError
        from pydantic import BaseModel

        settings = get_settings()
        client = OpenRouterLLMClient(settings)

        # Definir un modelo de respuesta simple
        class SimpleAnswer(BaseModel):
            answer: str
            confidence: float

        result = await client.complete_json(
            system_prompt="Eres un asistente simple. Responde con JSON.",
            user_prompt='¿Cuánto es 2+2? Responde con {"answer": "4", "confidence": 1.0}',
            response_model=SimpleAnswer,
        )

        if result.answer and 0.0 <= result.confidence <= 1.0:
            record(
                "LangChain OpenRouterLLMClient.complete_json",
                True,
                f"answer='{result.answer}', confidence={result.confidence}",
            )
        else:
            record("LangChain OpenRouterLLMClient.complete_json", False, f"Resultado inesperado: {result}")

        # Test complete_text
        text_result = await client.complete_text(
            system_prompt="Eres un asistente simple.",
            user_prompt="Di hola en una palabra.",
        )
        if text_result and len(text_result.strip()) > 0:
            record("LangChain OpenRouterLLMClient.complete_text", True, f"Respuesta: '{text_result[:60]}'")
        else:
            record("LangChain OpenRouterLLMClient.complete_text", False, "Respuesta vacía")

    except ImportError as e:
        record("LangChain OpenRouterLLMClient", False, f"Import error: {e}")
    except LLMError as e:
        record("LangChain OpenRouterLLMClient", False, f"LLMError: {e}")
    except Exception as e:
        record("LangChain OpenRouterLLMClient", False, f"{type(e).__name__}: {e}")


# ============================================
# Main
# ============================================

DELAY_BETWEEN_TESTS = 8  # segundos para evitar rate-limiting en modelos gratuitos

async def main() -> None:
    if not API_KEY or API_KEY == "your-openrouter-api-key-here":
        print("[ERROR] OPENROUTER_API_KEY no está configurada. Configura la variable en .env")
        sys.exit(1)

    print(f"╔══════════════════════════════════════════════════╗")
    print(f"║  TEST DE OPENROUTER — SynapSeed                 ║")
    print(f"╠══════════════════════════════════════════════════╣")
    print(f"║  API Key: ...{API_KEY[-8:]:>36s}║")
    print(f"║  Base URL: {BASE_URL:<38s}║")
    print(f"║  Modelo:   {CHAT_MODEL:<38s}║")
    print(f"╚══════════════════════════════════════════════════╝")
    print(f"  [INFO] Delay entre tests: {DELAY_BETWEEN_TESTS}s (para evitar rate-limiting)\n")

    async with httpx.AsyncClient() as client:
        await test_connectivity(client)
        await asyncio.sleep(DELAY_BETWEEN_TESTS)
        await test_basic_chat(client)
        await asyncio.sleep(DELAY_BETWEEN_TESTS)
        await test_analyzer_agent(client)
        await asyncio.sleep(DELAY_BETWEEN_TESTS)
        await test_synthesizer_agent(client)
        await asyncio.sleep(DELAY_BETWEEN_TESTS)
        await test_legal_validator_agent(client)
        await asyncio.sleep(DELAY_BETWEEN_TESTS)
        await test_json_with_markdown_fence(client)
        await asyncio.sleep(DELAY_BETWEEN_TESTS)
        await test_rate_limit_handling(client)
        await asyncio.sleep(DELAY_BETWEEN_TESTS)
        await test_free_models(client)
        await asyncio.sleep(DELAY_BETWEEN_TESTS)

    await test_langchain_integration()

    # Resumen
    passed = sum(1 for r in RESULTS if r["passed"])
    failed = sum(1 for r in RESULTS if not r["passed"])
    total = len(RESULTS)

    print(f"\n{'='*55}")
    print(f"  RESUMEN: {passed}/{total} pasaron, {failed}/{total} fallaron")
    print(f"{'='*55}")

    if failed > 0:
        print(f"\n  FALLAS:")
        for r in RESULTS:
            if not r["passed"]:
                print(f"    ❌ {r['name']}: {r['detail']}")
    print()


if __name__ == "__main__":
    asyncio.run(main())