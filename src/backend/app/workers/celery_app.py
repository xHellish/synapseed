"""
SynapSeed - Aplicacion Celery.

Punto de entrada del worker. Usa Redis como broker (cola de tareas) y como
backend (resultados). Las tareas que ejecutan el pipeline de agentes viven en
app.workers.tasks (registradas via `include`).
"""

from celery import Celery

from app.config import get_settings

settings = get_settings()

# Instancia principal de Celery: broker y backend apuntan a Redis (ver .env)
celery_app = Celery(
    "synapseed",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],  # modulos donde Celery busca tareas registradas
)

# Configuracion del worker
celery_app.conf.update(
    task_serializer="json",  # las tareas viajan como JSON
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,  # expone el estado STARTED ademas de PENDING/SUCCESS
    task_acks_late=True,  # confirma la tarea al terminar, no al recibirla (mas seguro ante crashes)
    worker_prefetch_multiplier=1,  # un worker toma una tarea a la vez (tareas largas de LLM)
    worker_max_tasks_per_child=50,  # recicla el proceso cada 50 tareas para evitar fugas de memoria
    broker_connection_retry_on_startup=True,
)
