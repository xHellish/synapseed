# Design Patterns Reference

A practical reference for design patterns commonly used in Python and JavaScript/TypeScript projects. Focused on real-world usage, not academic theory.

---

## Creational Patterns

### Factory

**Problem**: You need to create objects without specifying the exact class, or you want to centralize complex creation logic.

**When to use**:
- Object creation involves logic beyond simple instantiation
- You need to return different subtypes based on input
- You want to decouple client code from concrete classes

**Python**:
```python
from typing import Protocol

class Notifier(Protocol):
    def send(self, message: str) -> None: ...

class EmailNotifier:
    def send(self, message: str) -> None:
        print(f"Email: {message}")

class SlackNotifier:
    def send(self, message: str) -> None:
        print(f"Slack: {message}")

def create_notifier(channel: str) -> Notifier:
    notifiers = {
        "email": EmailNotifier,
        "slack": SlackNotifier,
    }
    if channel not in notifiers:
        raise ValueError(f"Unknown channel: {channel}")
    return notifiers[channel]()
```

**TypeScript**:
```typescript
interface Notifier {
  send(message: string): void;
}

class EmailNotifier implements Notifier {
  send(message: string): void {
    console.log(`Email: ${message}`);
  }
}

class SlackNotifier implements Notifier {
  send(message: string): void {
    console.log(`Slack: ${message}`);
  }
}

function createNotifier(channel: "email" | "slack"): Notifier {
  const notifiers = {
    email: () => new EmailNotifier(),
    slack: () => new SlackNotifier(),
  };
  return notifiers[channel]();
}
```

**Pitfalls**:
- Over-abstracting when you only have one implementation
- Creating a factory for objects that don't need polymorphism
- Factories that grow into god-objects with too many creation methods

---

### Builder

**Problem**: You need to construct complex objects step-by-step, especially when the constructor would have many parameters.

**When to use**:
- Object has many optional configuration parameters
- Construction requires multiple steps or validation
- You want to create different representations of the same object

**Python**:
```python
from dataclasses import dataclass, field

@dataclass
class QueryBuilder:
    _table: str = ""
    _conditions: list[str] = field(default_factory=list)
    _order_by: str | None = None
    _limit: int | None = None

    def table(self, name: str) -> "QueryBuilder":
        self._table = name
        return self

    def where(self, condition: str) -> "QueryBuilder":
        self._conditions.append(condition)
        return self

    def order(self, column: str) -> "QueryBuilder":
        self._order_by = column
        return self

    def limit(self, n: int) -> "QueryBuilder":
        self._limit = n
        return self

    def build(self) -> str:
        query = f"SELECT * FROM {self._table}"
        if self._conditions:
            query += " WHERE " + " AND ".join(self._conditions)
        if self._order_by:
            query += f" ORDER BY {self._order_by}"
        if self._limit:
            query += f" LIMIT {self._limit}"
        return query

# Usage
query = (
    QueryBuilder()
    .table("users")
    .where("active = true")
    .where("age > 18")
    .order("created_at")
    .limit(10)
    .build()
)
```

**TypeScript**:
```typescript
class QueryBuilder {
  private _table = "";
  private _conditions: string[] = [];
  private _orderBy?: string;
  private _limit?: number;

  table(name: string): this {
    this._table = name;
    return this;
  }

  where(condition: string): this {
    this._conditions.push(condition);
    return this;
  }

  order(column: string): this {
    this._orderBy = column;
    return this;
  }

  limit(n: number): this {
    this._limit = n;
    return this;
  }

  build(): string {
    let query = `SELECT * FROM ${this._table}`;
    if (this._conditions.length > 0) {
      query += ` WHERE ${this._conditions.join(" AND ")}`;
    }
    if (this._orderBy) query += ` ORDER BY ${this._orderBy}`;
    if (this._limit) query += ` LIMIT ${this._limit}`;
    return query;
  }
}
```

**Pitfalls**:
- Using a builder when a simple constructor or config object suffices
- Forgetting to validate required fields in `build()`
- Making builders mutable when they should produce immutable objects

---

### Singleton (Use with Caution)

**Problem**: You need exactly one instance of a class, typically for shared resources like configuration, connection pools, or loggers.

**When to use**:
- Managing a shared resource that must not be duplicated (e.g., DB connection pool)
- Global configuration that is read-only after initialization
- **Prefer dependency injection over singletons in most cases**

**Python**:
```python
# Preferred: module-level instance (Python's natural singleton)
# config.py
class _Config:
    def __init__(self) -> None:
        self.debug = False
        self.db_url = ""

    def load(self, **kwargs: object) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

config = _Config()  # Module-level — imported as a singleton

# Usage: from config import config
```

**TypeScript**:
```typescript
// Preferred: module-level instance
class Config {
  debug = false;
  dbUrl = "";

  load(options: Partial<Config>): void {
    Object.assign(this, options);
  }
}

export const config = new Config();
```

**Pitfalls**:
- Hidden global state that makes testing difficult
- Thread-safety issues in concurrent environments
- Tight coupling — components depend on the global instance
- **Prefer DI containers** in production applications
