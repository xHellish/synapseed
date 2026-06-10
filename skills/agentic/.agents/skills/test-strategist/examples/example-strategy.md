# Ejemplo de Output — Test Strategist

> Estrategia de testing para el módulo `OrderService`.

---

## Diagnóstico

El módulo `OrderService` tiene 0% de cobertura de tests. Las dependencias están hardcodeadas en el constructor, lo que dificulta el testing. Se recomienda refactorizar primero con inyección de dependencias.

## Estrategia Recomendada

- **70% Unit** — Lógica de negocio en `calculate_total`, `apply_discount`, `validate_order`
- **20% Integration** — `OrderService` + `InMemoryOrderRepository`
- **10% E2E** — Flujo completo de creación de orden vía API

## Tests Generados

```python
# tests/unit/test_order_service.py
import pytest
from decimal import Decimal
from tests.factories import OrderFactory, UserFactory
from tests.fakes import InMemoryOrderRepository, SilentNotifier
from orders_api.services.order_service import OrderService

@pytest.fixture
def order_service():
    return OrderService(
        repo=InMemoryOrderRepository(),
        notifier=SilentNotifier(),
    )

@pytest.mark.parametrize("tier,expected_discount", [
    ("regular", Decimal("0")),
    ("premium", Decimal("10")),
    ("enterprise", Decimal("20")),
])
def test_discount_by_user_tier(order_service, tier, expected_discount):
    user = UserFactory(tier=tier)
    order = OrderFactory(user=user, subtotal=Decimal("100"))
    discount = order_service.calculate_discount(order)
    assert discount == expected_discount

def test_create_order_persists_to_repository(order_service):
    user = UserFactory()
    order = order_service.create_order(user_id=user.id, item_id="item1", quantity=2)
    assert order.id is not None
    assert order_service.repo.find_by_id(order.id) is not None
```
