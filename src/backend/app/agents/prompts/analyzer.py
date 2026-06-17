"""Prompts del Agente 1 - Analizador de Contexto."""

# SYSTEM_PROMPT: define el rol y las reglas fijas del agente (no cambia entre casos)
SYSTEM_PROMPT = """Eres un agrónomo experto del Servicio Fitosanitario del Estado (SFE) de Costa Rica.
Tu única tarea es analizar el contexto de un agricultor y estructurarlo para un pipeline de recomendación.
NO recomiendes productos comerciales, marcas ni dosis específicas.
Responde en español en los valores de texto.
Sé conservador: si falta información, indícalo en datos_faltantes y baja confianza.
"""

# USER_PROMPT_TEMPLATE: plantilla que se rellena con los datos concretos de cada caso
USER_PROMPT_TEMPLATE = """Analiza el siguiente caso agrícola y devuelve el JSON estructurado solicitado.

Datos del formulario:
- Cultivo: {crop}
- Etapa: {crop_stage}
- Problema: {problem}
- Categoría del problema: {problem_category}
- Último agroquímico usado: {last_agrochemical_used}
- Presupuesto: {budget_range}
- Tipo de suelo: {soil_type}
- Humedad: {humidity}
- Temperatura: {temperature}
- Calidad del agua: {water_quality}
- Zona/finca ID: {zone_id}

Campos obligatorios en tu JSON:
- cultivo
- problema_detectado
- condiciones_agronomicas (tipo_suelo, humedad, temperatura, calidad_agua)
- severidad_estimada (baja|media|alta)
- restricciones_relevantes (lista)
- resumen_para_rag (párrafo denso para búsqueda de productos, mínimo 40 palabras)
- advertencias (lista)
- datos_faltantes (lista)
- confianza (0.0 a 1.0)
- tipo_proteccion_necesaria (herbicida|fungicida|insecticida|fertilizante|otro)
- categoria_producto_sugerida (plaguicida|fertilizante)
"""
