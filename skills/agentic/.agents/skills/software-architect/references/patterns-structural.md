# Design Patterns Reference

A practical reference for design patterns commonly used in Python and JavaScript/TypeScript projects. Focused on real-world usage, not academic theory.

---

## Structural Patterns

### Adapter

**Problem**: You need to make incompatible interfaces work together without modifying existing code.

**When to use**:
- Integrating a third-party library with a different interface
- Migrating from one service/library to another
- Wrapping legacy code with a modern interface

**Python**:
```python
from typing import Protocol

class PaymentGateway(Protocol):
    def charge(self, amount_cents: int, currency: str) -> dict: ...

class StripeAdapter:
    """Adapts Stripe SDK to our PaymentGateway interface."""
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def charge(self, amount_cents: int, currency: str) -> dict:
        # Wraps stripe.PaymentIntent.create(...)
        return {"id": "pi_xxx", "status": "succeeded", "amount": amount_cents}

class PayPalAdapter:
    """Adapts PayPal SDK to our PaymentGateway interface."""
    def __init__(self, client_id: str, secret: str) -> None:
        self.client_id = client_id
        self.secret = secret

    def charge(self, amount_cents: int, currency: str) -> dict:
        amount_dollars = amount_cents / 100
        return {"id": "PAY-xxx", "status": "approved", "amount": amount_dollars}
```

**TypeScript**:
```typescript
interface PaymentGateway {
  charge(amountCents: number, currency: string): Promise<PaymentResult>;
}

interface PaymentResult {
  id: string;
  status: string;
  amount: number;
}

class StripeAdapter implements PaymentGateway {
  constructor(private apiKey: string) {}

  async charge(amountCents: number, currency: string): Promise<PaymentResult> {
    // Wraps Stripe API call
    return { id: "pi_xxx", status: "succeeded", amount: amountCents };
  }
}
```

**Pitfalls**:
- Creating adapters when you control both interfaces (just change one)
- Leaking abstraction details from the adapted library
- Over-adapting — adding logic beyond simple interface translation

---

### Decorator

**Problem**: You need to add behavior to objects dynamically without modifying their class.

**When to use**:
- Adding cross-cutting concerns (logging, caching, retry, auth)
- Composing behaviors at runtime
- Extending functionality without subclassing

**Python**:
```python
import functools
import time
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

def retry(max_attempts: int = 3, delay: float = 1.0):
    """Decorator that retries a function on failure."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_error: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (2 ** attempt))
            raise last_error  # type: ignore
        return wrapper
    return decorator

@retry(max_attempts=3, delay=0.5)
def fetch_data(url: str) -> dict:
    # ... HTTP request
    pass
```

**TypeScript**:
```typescript
function withRetry<T>(
  fn: (...args: unknown[]) => Promise<T>,
  maxAttempts = 3,
  delay = 1000
): (...args: unknown[]) => Promise<T> {
  return async (...args) => {
    let lastError: Error | undefined;
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        return await fn(...args);
      } catch (error) {
        lastError = error as Error;
        if (attempt < maxAttempts - 1) {
          await new Promise((r) => setTimeout(r, delay * 2 ** attempt));
        }
      }
    }
    throw lastError;
  };
}
```

**Pitfalls**:
- Stacking too many decorators — makes debugging hard
- Order dependency between decorators
- Losing function signatures and type information (use `functools.wraps` in Python)

---

### Facade

**Problem**: You need a simplified interface to a complex subsystem with many interacting parts.

**When to use**:
- Hiding complexity of a multi-step process
- Providing a high-level API for a library or subsystem
- Reducing coupling between client code and subsystem internals

**Python**:
```python
class DeploymentFacade:
    """Simplifies the multi-step deployment process."""
    def __init__(self, builder, tester, deployer, notifier):
        self.builder = builder
        self.tester = tester
        self.deployer = deployer
        self.notifier = notifier

    def deploy(self, version: str) -> bool:
        artifact = self.builder.build(version)
        if not self.tester.run_tests(artifact):
            self.notifier.send("Tests failed")
            return False
        self.deployer.deploy(artifact)
        self.notifier.send(f"v{version} deployed successfully")
        return True
```

**TypeScript**:
```typescript
class DeploymentFacade {
  constructor(
    private builder: Builder,
    private tester: Tester,
    private deployer: Deployer,
    private notifier: Notifier
  ) {}

  async deploy(version: string): Promise<boolean> {
    const artifact = await this.builder.build(version);
    if (!(await this.tester.runTests(artifact))) {
      await this.notifier.send("Tests failed");
      return false;
    }
    await this.deployer.deploy(artifact);
    await this.notifier.send(`v${version} deployed successfully`);
    return true;
  }
}
```

**Pitfalls**:
- Facade becoming a god object that does too much
- Hiding important configuration that clients need access to
- Not providing escape hatches for advanced use cases

---

### Proxy

**Problem**: You need to control access to an object, add lazy initialization, caching, or access control.

**When to use**:
- Lazy loading expensive resources
- Adding access control or permission checks
- Caching expensive operation results
- Logging/auditing access to an object

**Python**:
```python
class CachedRepository:
    """Proxy that caches results from the underlying repository."""
    def __init__(self, repo, cache_ttl: int = 300):
        self._repo = repo
        self._cache: dict[str, tuple[float, object]] = {}
        self._ttl = cache_ttl

    def get(self, id: str):
        import time
        if id in self._cache:
            timestamp, value = self._cache[id]
            if time.time() - timestamp < self._ttl:
                return value
        value = self._repo.get(id)
        self._cache[id] = (time.time(), value)
        return value
```

**TypeScript**:
```typescript
class CachedRepository<T> {
  private cache = new Map<string, { timestamp: number; value: T }>();

  constructor(
    private repo: { get(id: string): Promise<T> },
    private ttlMs: number = 300_000
  ) {}

  async get(id: string): Promise<T> {
    const cached = this.cache.get(id);
    if (cached && Date.now() - cached.timestamp < this.ttlMs) {
      return cached.value;
    }
    const value = await this.repo.get(id);
    this.cache.set(id, { timestamp: Date.now(), value });
    return value;
  }
}
```

**Pitfalls**:
- Cache invalidation complexity ("the hardest problem in CS")
- Proxy hiding important errors from the underlying object
- Adding too many responsibilities to a single proxy
