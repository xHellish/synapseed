"""Abstracción de despacho de tareas en background — OCP + DIP.

Define la interfaz ``TaskDispatcher`` y la implementación concreta
``CeleryTaskDispatcher``.

Cumplimiento SOLID:
- OCP: cambiar de Celery a Kafka/RQ = implementar ``KafkaTaskDispatcher``
  sin modificar los endpoints que usan ``TaskDispatcher``.
- DIP: los endpoints dependen de la abstracción ``TaskDispatcher``,
  no de Celery directamente.
- Testabilidad: en tests se puede inyectar un ``MockTaskDispatcher``
  que no encolará tareas reales.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


# ---------------------------------------------------------------------------
# Interfaz abstracta
# ---------------------------------------------------------------------------

class TaskDispatcher(ABC):
    """Contrato para despachar tareas asíncronas a un worker en background."""

    @abstractmethod
    async def dispatch_recommendation_generation(self, ticket_id: str) -> None:
        """Encola la generación de una recomendación para el ticket dado."""


# ---------------------------------------------------------------------------
# Implementación Celery
# ---------------------------------------------------------------------------

class CeleryTaskDispatcher(TaskDispatcher):
    """Implementación concreta que encola tareas en Celery.

    La importación de ``generate_recommendation`` se hace en tiempo de ejecución
    para evitar dependencias circulares y facilitar la carga en entornos donde
    Celery no está disponible (p. ej. tests unitarios sin broker).
    """

    async def dispatch_recommendation_generation(self, ticket_id: str) -> None:
        from app.workers.tasks import generate_recommendation
        generate_recommendation.delay(ticket_id)
