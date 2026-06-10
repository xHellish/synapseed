# Testing Patterns Reference

Catálogo de patrones, anti-patrones y estrategias de testing para Python y JavaScript/TypeScript.

---

## Testing Philosophy

### The Testing Pyramid

```
          ┌───────────┐
          │    E2E    │  ← Pocos, lentos, caros. Validan flujos completos.
          ├───────────┤
          │Integration│  ← Moderados. Validan interacciones entre capas.
          ├───────────┤
          │   Unit    │  ← Muchos, rápidos, baratos. Validan lógica aislada.
          └───────────┘
```

**Regla práctica:** Si tienes que elegir dónde invertir tiempo, los tests unitarios dan el mayor ROI. Los E2E tienen el costo de mantenimiento más alto.

### Test Types Defined

| Tipo | Qué prueba | Velocidad | Cantidad recomendada |
|------|-----------|-----------|---------------------|
| **Unit** | Una función/clase en aislamiento | < 1ms | ~70% del total |
| **Integration** | Dos o más capas juntas (ej: servicio + BD) | 10ms-1s | ~20% del total |
| **E2E / Acceptance** | El sistema completo desde UI hasta BD | 1s-30s | ~10% del total |
| **Snapshot** | Que el output no cambió inesperadamente | Rápido | Usar con moderación |
| **Property-based** | Invariantes con datos aleatorios | Variable | Para funciones puras complejas |

---

## Patrones de Testing

### Arrange-Act-Assert (AAA)

El patrón universal. Estructura cada test en tres bloques separados visualmente.

```python
def test_order_applies_premium_discount():
    # Arrange
    customer = Customer(tier="premium")
    order = Order(customer=customer, subtotal=Decimal("100.00"))

    # Act
    final_price = order.calculate_total()

    # Assert
    assert final_price == Decimal("90.00")
```

```typescript
it("applies premium discount of 10%", () => {
  // Arrange
  const customer = buildCustomer({ tier: "premium" });
  const order = new Order(customer, 100);

  // Act
  const total = order.calculateTotal();

  // Assert
  expect(total).toBe(90);
});
```

---

### Given-When-Then (GWT / BDD)

Variante de AAA para tests de comportamiento orientados a usuario. Ideal para tests de integración y aceptación.

```python
# pytest-bdd
Feature: Discount calculation
  Scenario: Premium customer gets 10% discount
    Given a premium customer
    When they place an order for $100
    Then the final price should be $90
```

```typescript
// Con Cucumber.js o Playwright BDD
given("a premium customer", () => {
  customer = { tier: "premium" };
});
when("they place an order for $100", () => {
  order = createOrder({ customer, amount: 100 });
});
then("the final price should be $90", () => {
  expect(order.total).toBe(90);
});
```

---

### Object Mother / Test Data Builder

Centraliza la creación de datos de test para evitar duplicación y mantener los tests legibles.

```python
# Python — Object Mother
class UserMother:
    @staticmethod
    def premium() -> User:
        return User(id="u1", tier="premium", email="test@example.com")

    @staticmethod
    def with_tier(tier: str) -> User:
        return User(id="u1", tier=tier, email="test@example.com")

# Uso en tests
def test_discount():
    user = UserMother.premium()
    assert calculate_discount(user) == 0.10
```

```typescript
// TypeScript — Builder pattern para tests
class UserBuilder {
  private user: Partial<User> = {
    id: "u1",
    email: "test@example.com",
    tier: "regular",
  };

  withTier(tier: string): this {
    this.user.tier = tier;
    return this;
  }

  build(): User {
    return this.user as User;
  }
}

const buildUser = () => new UserBuilder();

// Uso
const user = buildUser().withTier("premium").build();
```

---

### Fake Objects (In-Memory Implementations)

Implementaciones funcionales pero simplificadas. Preferibles a mocks complejos.

```python
# Python — Fake Repository
class InMemoryUserRepository:
    def __init__(self):
        self._store: dict[str, User] = {}

    def save(self, user: User) -> None:
        self._store[user.id] = user

    def find_by_id(self, user_id: str) -> User | None:
        return self._store.get(user_id)

    def find_all(self) -> list[User]:
        return list(self._store.values())

# En tests — no hay BD real, no hay mocks
def test_user_service_saves_user():
    repo = InMemoryUserRepository()
    service = UserService(repo)

    service.create_user(name="Alice", email="alice@example.com")

    users = repo.find_all()
    assert len(users) == 1
    assert users[0].name == "Alice"
```

```typescript
// TypeScript — Fake Repository
class InMemoryUserRepository implements UserRepository {
  private store = new Map<string, User>();

  async save(user: User): Promise<void> {
    this.store.set(user.id, user);
  }

  async findById(id: string): Promise<User | undefined> {
    return this.store.get(id);
  }

  async findAll(): Promise<User[]> {
    return [...this.store.values()];
  }
}
```

---

### Parametrized / Table-Driven Tests

Evita copiar el mismo test con valores diferentes.

```python
# pytest
import pytest

@pytest.mark.parametrize("input_price,tier,expected", [
    (100, "regular", 100),
    (100, "premium", 90),
    (100, "enterprise", 80),
    (0, "premium", 0),           # Edge case: zero price
    (1000, "enterprise", 800),   # Large amounts
])
def test_pricing_by_tier(input_price, tier, expected):
    user = User(tier=tier)
    result = calculate_price(user, input_price)
    assert result == expected
```

```typescript
// Vitest
test.each([
  [100, "regular", 100],
  [100, "premium", 90],
  [100, "enterprise", 80],
  [0, "premium", 0],
  [1000, "enterprise", 800],
])(
  "price %d for tier %s should be %d",
  (inputPrice, tier, expected) => {
    const user = buildUser().withTier(tier).build();
    expect(calculatePrice(user, inputPrice)).toBe(expected);
  }
);
```

---

## Anti-Patrones de Testing

### 🔴 Críticos

#### Testing de Implementación (Not Behavior)

**Problema:** Tests que verifican *cómo* funciona el código internamente en lugar de *qué* hace.

```python
# ❌ Antes — testea implementación (método privado, estado interno)
def test_user_service_internals():
    service = UserService(repo)
    service.create_user("Alice", "alice@example.com")
    assert service._cache["alice@example.com"] is not None  # Estado interno!
    assert service._validate_called == True                  # Llamada interna!

# ✅ Después — testea comportamiento observable
def test_created_user_can_be_found():
    service = UserService(InMemoryUserRepository())
    service.create_user("Alice", "alice@example.com")
    user = service.find_by_email("alice@example.com")
    assert user is not None
    assert user.name == "Alice"
```

---

#### Estado Global Compartido Entre Tests

**Problema:** Tests que modifican variables globales o singletons, causando que el orden de ejecución importe.

```python
# ❌ Antes — estado global compartido
DATABASE = {}  # Global mutable state

def test_save_user():
    DATABASE["user1"] = User("Alice")
    assert "user1" in DATABASE

def test_count_users():
    # Si test_save_user corrió primero, pasa. Si no, falla. ¡Orden-dependiente!
    assert len(DATABASE) == 1

# ✅ Después — estado aislado por test
@pytest.fixture
def empty_db():
    return {}

def test_save_user(empty_db):
    empty_db["user1"] = User("Alice")
    assert "user1" in empty_db

def test_count_users(empty_db):
    assert len(empty_db) == 0  # Siempre empieza vacío
```

---

#### Tests Sin Limpieza (Resource Leaks)

**Problema:** Tests que abren conexiones, crean archivos, o modifican env vars sin limpiar.

```python
# ❌ Antes — no hay limpieza
def test_writes_to_file():
    with open("/tmp/test_output.txt", "w") as f:
        f.write("hello")
    assert os.path.exists("/tmp/test_output.txt")
    # Archivo queda en disco

# ✅ Después — limpieza garantizada con fixtures
@pytest.fixture
def temp_file(tmp_path):
    file = tmp_path / "output.txt"
    yield file
    # pytest cleanup automático con tmp_path

def test_writes_to_file(temp_file):
    temp_file.write_text("hello")
    assert temp_file.read_text() == "hello"
```

---

### 🟠 Alta Prioridad

#### Flaky Tests (Tests Inestables)

**Causas principales y soluciones:**

```python
# ❌ Causa 1: Timing / sleeps arbitrarios
def test_async_operation():
    start_job()
    time.sleep(2)  # Flakey! Puede ser muy corto o muy largo
    assert job_completed()

# ✅ Solución: Polling con timeout o async nativo
def test_async_operation():
    start_job()
    wait_for(job_completed, timeout=10, interval=0.1)
    assert job_completed()

# ❌ Causa 2: Datos aleatorios sin semilla
def test_sort():
    data = [random.randint(0, 100) for _ in range(10)]
    result = my_sort(data)
    assert result == sorted(data)  # Pasa pero no es determinista

# ✅ Solución: Fijar la semilla o usar datos fijos
def test_sort_with_known_data():
    data = [5, 2, 8, 1, 9, 3]
    result = my_sort(data)
    assert result == [1, 2, 3, 5, 8, 9]

# ❌ Causa 3: Dependencia de APIs externas
def test_weather():
    result = get_weather("Madrid")  # Llama a API real!
    assert result["temperature"] > -50

# ✅ Solución: Mock la capa de red
def test_weather(mocker):
    mocker.patch("myapp.http.get", return_value={"temperature": 20, "city": "Madrid"})
    result = get_weather("Madrid")
    assert result["temperature"] == 20
```

---

#### Over-Mocking (Exceso de Mocks)

**Problema:** Mockear tanto que el test ya no prueba nada real.

```python
# ❌ Antes — todo mockeado, ¿qué estamos testeando?
def test_create_order(mocker):
    mock_repo = mocker.Mock()
    mock_notifier = mocker.Mock()
    mock_inventory = mocker.Mock()
    mock_pricing = mocker.Mock()
    mock_pricing.calculate.return_value = 100

    service = OrderService(mock_repo, mock_notifier, mock_inventory, mock_pricing)
    service.create_order(user_id="u1", item_id="i1", quantity=2)

    mock_repo.save.assert_called_once()
    # Testeamos solo que se llamó save, no que la lógica es correcta

# ✅ Después — usar Fakes para dependencias reales, Mock solo para efectos secundarios
def test_create_order():
    repo = InMemoryOrderRepository()
    inventory = InMemoryInventory({"i1": 10})    # Fake con lógica real
    pricing = InMemoryPricingEngine({"i1": 50})  # Fake con lógica real
    notifier = SilentNotifier()                  # Fake que no hace nada

    service = OrderService(repo, notifier, inventory, pricing)
    service.create_order(user_id="u1", item_id="i1", quantity=2)

    orders = repo.find_by_user("u1")
    assert len(orders) == 1
    assert orders[0].total == 100  # 2 × 50, lógica real probada
```

---

#### Assertion Roulette (Tests Sin Asserts Significativos)

**Problema:** Un test que no falla aunque el código esté roto.

```python
# ❌ Antes — siempre pasa, no prueba nada
def test_process_order():
    order = Order(items=[Item("book", 20)])
    result = process_order(order)
    assert result is not None  # ¡Siempre pasa!

# ✅ Después — asserts específicos y significativos
def test_process_order_returns_confirmation_number():
    order = Order(items=[Item("book", 20)])
    result = process_order(order)
    assert result.status == "confirmed"
    assert len(result.confirmation_number) == 8
    assert result.total == 20
```

---

### 🟡 Prioridad Media

#### Test Functions Gigantes

```python
# ❌ Antes — un test prueba demasiado
def test_user_flow():
    # Create
    user = create_user("Alice", "alice@example.com")
    assert user.id is not None
    # Login
    token = login("alice@example.com", "password")
    assert token is not None
    # Update profile
    updated = update_profile(user.id, name="Alicia")
    assert updated.name == "Alicia"
    # Delete
    delete_user(user.id)
    assert find_user(user.id) is None

# ✅ Después — un test por comportamiento
def test_create_user_assigns_id():
    user = create_user("Alice", "alice@example.com")
    assert user.id is not None

def test_login_returns_jwt_token():
    create_user("Alice", "alice@example.com")
    token = login("alice@example.com", "password")
    assert token is not None

def test_update_profile_changes_name():
    user = create_user("Alice", "alice@example.com")
    updated = update_profile(user.id, name="Alicia")
    assert updated.name == "Alicia"
```

---

#### Tests Acoplados (Order-Dependent)

```python
# ❌ Antes — test B depende de que test A haya corrido
class TestUserSystem:
    user_id = None  # Variable de clase compartida

    def test_a_create_user(self):
        user = create_user("Alice")
        TestUserSystem.user_id = user.id  # Guarda estado entre tests

    def test_b_find_user(self):
        # Solo funciona si test_a corrió primero
        user = find_user(TestUserSystem.user_id)
        assert user.name == "Alice"

# ✅ Después — cada test es autónomo
class TestUserSystem:
    def test_create_user(self):
        user = create_user("Alice")
        assert user.id is not None

    def test_find_user(self):
        user = create_user("Alice")  # Crea el suyo propio
        found = find_user(user.id)
        assert found.name == "Alice"
```

---

## Configuración de Frameworks

### pytest (Python)

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = """
  --cov=src
  --cov-report=term-missing
  --cov-report=html
  --cov-fail-under=80
  --strict-markers
  -v
"""
markers = [
    "unit: Unit tests (fast, no I/O)",
    "integration: Integration tests (requires DB/services)",
    "e2e: End-to-end tests (slow, full stack)",
]
```

### Vitest (TypeScript)

```typescript
// vitest.config.ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",       // o "jsdom" para UI
    setupFiles: ["./tests/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 75,
        statements: 80,
      },
      exclude: [
        "tests/**",
        "**/*.config.*",
        "**/index.ts",          // Barrel files
      ],
    },
    include: ["**/*.{test,spec}.{ts,tsx}"],
  },
});
```

---

## Criterios de Cobertura

| Métrica | Mínimo | Objetivo | Excelente |
|---------|--------|---------|-----------|
| Line coverage | 70% | 80% | 90%+ |
| Branch coverage | 65% | 75% | 85%+ |
| Function coverage | 75% | 85% | 95%+ |
| Mutation score | — | 60% | 80%+ |

> ⚠️ **100% de cobertura no significa 0 bugs.** Un test sin asserts significativos alcanza cobertura pero no aporta valor. Prefiere mutation testing sobre métricas de línea.
