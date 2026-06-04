# SynapSeed

## Miembros
- Josue Quirós
- Josue Calderón
- Kevin Alanis
- Daniela Suárez
- Ben Farz

**Nombre del workflow:** Generación Inteligente de Recomendaciones Agroquímicas  

**Reto a resolver:** Usar un único agente de IA aislado causaría fallos, ya que analizar el cultivo, cruzar catálogos vectoriales de bases de datos y validar normativas gubernamentales al mismo tiempo podría sobrepasar el límite lógico del LLM, generando alucinaciones o errores de formato.  

**Solución:** Patrón Híbrido de Group Orchestration + Sequential Pipeline + Tool Use. En lugar de un solo agente, se utilizarán 4 agentes especializados que se ejecutan en secuencia pasándose un estado compartido.

**Ubicación /src**
  - `/src/core/queue/` (Configuración de Celery)
  - `/src/workers/ai_tasks/` (Consumidores de cola)
  - `/src/api/routes/notifications.py` (Manejo de SSE)

**Restricciones y recomendaciones para los devs**
- Idempotencia obligatoria: El desarrollador debe asegurar que si el Background Worker Task procesa el mismo mensaje dos veces (por un fallo de red), no se generen recomendaciones duplicadas ni estados inconsistentes en PostgreSQL.

- Control de Concurrencia: El Worker debe estar configurado para consumir mensajes a un ritmo que nunca supere las capacidades del LLM  actuando como amortiguador del tráfico.

- Elección de Comunicación Web: Obligatorio usar Server-Sent Events y prohibido usar WebSockets para este flujo, ya que la notificación (estado listo) es unidireccional y usar WebSockets gastaría recursos del servidor innecesariamente. 

**Manejo de excepciones**
- Fallo de encolamiento: Si Celery está caído, el Endpoint de FastAPI debe retornar un HTTP 503 Service Unavailable.

- Fallo del Worker: Si el Worker experimenta una caída catastrófica procesando la recomendación, el mensaje no debe borrarse. Debe enviarse a una Dead Letter Queue (DLQ) para análisis manual, y disparar un evento SSE de estado "fallido" para que el usuario sea notificado.

**Responsabilidad e Inputs/Outputs de los Componentes**

- FastAPI Endpoint Component:
Input: RequestPayload del agricultor solicitando análisis.
Output: Retorna al cliente un estado de aceptación asíncrono (HTTP 202 Accepted junto a un UUID).

- Cola de Mensajes (Celery):
Input: Serialización del evento.
Responsabilidad: Persistencia del mensaje y desacoplamiento.

- Background Worker Component:
Input: Obtiene el Payload desencolado.
Output: Escribe la recomendación en BD.

- Servicio SSE Component:
Input: Escucha cambios de estado en la BD.
Output: Envía un stream de texto unidireccional tipo evento indicando "Tu recomendación ha sido generada".