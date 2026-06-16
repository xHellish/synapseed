#!/usr/bin/env python3
"""Script de prueba de integración para el pipeline de agentes asíncrono.

Realiza el ciclo completo:
1. Registro / Login de un usuario de pruebas.
2. Petición de recomendación asíncrona (envía a Celery).
3. Monitoreo (polling) del estado de la recomendación en la base de datos hasta que termine.
4. Muestra del resultado final con los productos recomendados por los agentes.
"""

import time
import requests
import json
import sys

# Forzar encoding UTF-8 en stdout/stderr para evitar problemas en consolas Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "identification": "1234567891",
    "password": "secret123",
    "email": "test_user_pipeline_2@example.com",
    "full_name": "Agricultor de Pruebas",
    "phone": "88888888"
}

def run_test():
    print("=== INICIANDO PRUEBA DE INTEGRACION ===")
    
    # 1. Intentar registrar al usuario (si ya existe dará error, lo ignoramos)
    print("\n1. Intentando registrar usuario de prueba...")
    try:
        res = requests.post(f"{BASE_URL}/auth/register", json=TEST_USER)
        if res.status_code == 201:
            print("   Usuario registrado con exito.")
        else:
            print(f"   Registro retornado: {res.status_code} (posiblemente ya existe)")
    except Exception as e:
        print(f"   Error al registrar: {e}")

    # 2. Iniciar sesión para obtener el token
    print("\n2. Iniciando sesion...")
    login_payload = {
        "identification": TEST_USER["identification"],
        "password": TEST_USER["password"]
    }
    res = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
    if res.status_code != 200:
        print(f"[ERROR] Error al iniciar sesion ({res.status_code}): {res.text}")
        return
        
    token = res.json()["access_token"]
    print("   Sesion iniciada con exito. Token obtenido.")
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Solicitar recomendación
    print("\n3. Enviando solicitud de recomendacion asincrona...")
    rec_payload = {
        "crop": "tomate",
        "crop_stage": "floracion",
        "problem_to_solve": "plaga",
        "soil_type": "franco-arcilloso",
        "humidity": 65.5,
        "temperature": 24.0,
        "water_quality": "buena",
        "max_budget_per_liter": 15000.0,
        "last_agrochemical": "ninguno"
    }
    
    res = requests.post(f"{BASE_URL}/recommendations/request", json=rec_payload, headers=headers)
    if res.status_code != 202:
        print(f"[ERROR] Error al solicitar recomendacion ({res.status_code}): {res.text}")
        return
        
    data = res.json()
    ticket_id = data["ticket_id"]
    recommendation_id = data["recommendation_id"]
    print(f"   Solicitud aceptada. Ticket ID: {ticket_id}, Recommendation ID: {recommendation_id}")
    print("   Encolado en Celery. Esperando procesamiento...")

    # 4. Polling del estado
    print("\n4. Monitoreando estado de la recomendacion (polling)...")
    max_attempts = 45
    attempt = 0
    status = "pending"
    
    while status in ["pending", "processing"] and attempt < max_attempts:
        attempt += 1
        time.sleep(2)
        res = requests.get(f"{BASE_URL}/recommendations/{recommendation_id}", headers=headers)
        if res.status_code != 200:
            print(f"[ERROR] Error consultando el detalle ({res.status_code}): {res.text}")
            return
            
        data = res.json()
        status = data["status"]
        step = data.get("current_step")
        print(f"   [Intento {attempt}/{max_attempts}] Estado: {status.upper()}" + (f" (Paso: {step})" if step else ""))
        
        if status in ["completed", "failed"]:
            break
            
    if status == "completed":
        print("\n[OK] PRUEBA EXITOSA! El pipeline completo el procesamiento.")
        print("\n=== DETALLE DE RECOMENDACION ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif status == "failed":
        print(f"\n[ERROR] El pipeline fallo. Mensaje de error: {data.get('error_message')}")
    else:
        print("\n[WARN] Se supero el tiempo maximo de espera sin que termine el procesamiento.")

if __name__ == "__main__":
    run_test()
