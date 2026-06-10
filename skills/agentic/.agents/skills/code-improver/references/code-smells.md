# Code Smells Catalog

Quick-reference catalog of common code smells organized by category. For each smell: what it is, how to spot it, why it hurts, and how to fix it.

---

## Bloaters

Bloaters are code constructs that have grown so large they become hard to work with.

### Long Method

**What**: A function/method that does too much — typically over 20–30 lines of logic.

**Symptoms**: You need to scroll to read it; multiple levels of indentation; comments separating "sections" within the function.

**Why it's a problem**: Hard to understand, test, and reuse. Changes in one section risk breaking another.

**Fix**: Extract Method — break into smaller, named functions.

**Python**:
```python
# ❌ Before
def process_order(order):
    # validate
    if not order.items:
        raise ValueError("Empty order")
    if order.total < 0:
        raise ValueError("Negative total")
    # calculate discount
    discount = 0
    if order.customer.is_premium:
        discount = order.total * 0.1
    # apply tax
    tax = (order.total - discount) * 0.16
    # save
    db.save(order)
    email.send(order.customer, "Order confirmed")

# ✅ After
def process_order(order):
    validate_order(order)
    discount = calculate_discount(order)
    tax = calculate_tax(order.total, discount)
    finalize_order(order)
```

**JS/TS**:
```typescript
// ❌ Before
function processOrder(order: Order) {
  // 50+ lines doing validation, calculation, saving, emailing...
}

// ✅ After
function processOrder(order: Order) {
  validateOrder(order);
  const discount = calculateDiscount(order);
  const tax = calculateTax(order.total, discount);
  await finalizeOrder(order);
}
```

---

### Large Class

**What**: A class with too many responsibilities, fields, or methods (God Class).

**Symptoms**: Hundreds of lines; unrelated methods grouped together; many instance variables; class name is vague (e.g., `Manager`, `Handler`, `Utils`).

**Why it's a problem**: Violates Single Responsibility. Hard to test, understand, and extend.

**Fix**: Extract Class — split into focused, cohesive classes.

**Python**:
```python
# ❌ Before
class UserManager:
    def authenticate(self, ...): ...
    def send_email(self, ...): ...
    def generate_report(self, ...): ...
    def export_csv(self, ...): ...

# ✅ After
class Authenticator: ...
class UserNotifier: ...
class UserReportGenerator: ...
```

**JS/TS**:
```typescript
// ❌ Before
class UserManager {
  authenticate() { ... }
  sendEmail() { ... }
  generateReport() { ... }
}

// ✅ After
class AuthService { authenticate() { ... } }
class NotificationService { sendEmail() { ... } }
class ReportService { generateReport() { ... } }
```

---

### Long Parameter List

**What**: A function that takes 4+ parameters.

**Symptoms**: Hard to remember parameter order; many boolean flags; callers pass `None`/`null` for unused params.

**Why it's a problem**: Hard to call correctly; signals the function does too much.

**Fix**: Introduce Parameter Object or use a config/options pattern.

**Python**:
```python
# ❌ Before
def create_user(name, email, age, role, department, is_active, send_welcome):
    ...

# ✅ After
@dataclass
class UserConfig:
    name: str
    email: str
    age: int
    role: str = "viewer"
    department: str = ""
    is_active: bool = True
    send_welcome: bool = False

def create_user(config: UserConfig):
    ...
```

**JS/TS**:
```typescript
// ❌ Before
function createUser(name: string, email: string, age: number, role: string, dept: string) { ... }

// ✅ After
interface CreateUserOptions {
  name: string;
  email: string;
  age: number;
  role?: string;
  department?: string;
}
function createUser(options: CreateUserOptions) { ... }
```

---

### Primitive Obsession

**What**: Using primitive types (strings, numbers) instead of small domain objects for concepts like money, email, phone, date ranges.

**Symptoms**: Validation logic scattered everywhere; string manipulation for structured data; comments explaining what a string "really" represents.

**Why it's a problem**: Duplicated validation; easy to mix up parameters of the same primitive type; no type safety.

**Fix**: Replace with Value Objects or branded types.

**Python**:
```python
# ❌ Before
def charge(amount: float, currency: str): ...

# ✅ After
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

def charge(money: Money): ...
```

**JS/TS**:
```typescript
// ❌ Before
function charge(amount: number, currency: string) { ... }

// ✅ After
class Money {
  constructor(readonly amount: number, readonly currency: string) {
    if (amount < 0) throw new Error("Amount cannot be negative");
  }
}
function charge(money: Money) { ... }
```

---

### Data Clumps

**What**: Groups of variables that always appear together across multiple functions or classes.

**Symptoms**: Same 3+ parameters passed together repeatedly; related fields without a grouping structure.

**Why it's a problem**: Duplication; changing the group means updating many call sites.

**Fix**: Extract a class or data structure to group them.

**Python**:
```python
# ❌ Before
def distance(x1, y1, x2, y2): ...
def midpoint(x1, y1, x2, y2): ...

# ✅ After
@dataclass
class Point:
    x: float
    y: float

def distance(a: Point, b: Point): ...
def midpoint(a: Point, b: Point): ...
```

**JS/TS**:
```typescript
// ❌ Before
function distance(x1: number, y1: number, x2: number, y2: number) { ... }

// ✅ After
interface Point { x: number; y: number; }
function distance(a: Point, b: Point) { ... }
```

---

## Object-Orientation Abusers

Misuse of OOP mechanisms.

### Switch Statements (Type-Code Smell)

**What**: Long `switch`/`if-elif` chains that dispatch behavior based on a type or status code.

**Symptoms**: Same switch appears in multiple places; adding a new type requires modifying multiple functions.

**Why it's a problem**: Violates Open/Closed Principle; scatters related logic.

**Fix**: Replace with polymorphism or a strategy/registry pattern.

**Python**:
```python
# ❌ Before
def calculate_area(shape):
    if shape.type == "circle":
        return math.pi * shape.radius ** 2
    elif shape.type == "rectangle":
        return shape.width * shape.height

# ✅ After
class Circle:
    def area(self) -> float:
        return math.pi * self.radius ** 2

class Rectangle:
    def area(self) -> float:
        return self.width * self.height
```

**JS/TS**:
```typescript
// ❌ Before
function calculateArea(shape: Shape) {
  switch (shape.type) {
    case "circle": return Math.PI * shape.radius ** 2;
    case "rectangle": return shape.width * shape.height;
  }
}

// ✅ After
interface Shape { area(): number; }
class Circle implements Shape { area() { return Math.PI * this.radius ** 2; } }
class Rectangle implements Shape { area() { return this.width * this.height; } }
```

---

### Parallel Inheritance Hierarchies

**What**: Every time you add a subclass in one hierarchy, you must also add one in another.

**Symptoms**: Paired class names like `OrderProcessor` / `OrderValidator`, `UserService` / `UserRepository` that always grow together.

**Why it's a problem**: Shotgun surgery — one conceptual change touches multiple hierarchies.

**Fix**: Merge hierarchies or use composition to eliminate the forced parallelism.

---

### Refused Bequest

**What**: A subclass inherits methods/properties it doesn't need or use.

**Symptoms**: Subclass overrides methods to throw `NotImplementedError`; inherited methods don't make sense for the subclass.

**Why it's a problem**: Violates Liskov Substitution; misleading API.

**Fix**: Replace inheritance with composition, or restructure the hierarchy.

**Python**:
```python
# ❌ Before
class Bird:
    def fly(self): ...

class Penguin(Bird):
    def fly(self):
        raise NotImplementedError  # Penguins can't fly!

# ✅ After
class Bird: ...
class FlyingBird(Bird):
    def fly(self): ...
class Penguin(Bird): ...  # No fly method
```

---

## Change Preventers

These smells make changes disproportionately difficult.

### Divergent Change

**What**: A single class is modified for many different, unrelated reasons.

**Symptoms**: One file appears in most diffs; "I need to change X, so I edit `utils.py` again."

**Why it's a problem**: High coupling; merge conflicts; hard to understand what the class is responsible for.

**Fix**: Extract classes so each changes for only one reason.

---

### Shotgun Surgery

**What**: A single logical change requires editing many files/classes.

**Symptoms**: Adding a field requires changes in model, serializer, API, tests, docs, etc. — all scattered.

**Why it's a problem**: Easy to miss a spot; tedious and error-prone.

**Fix**: Move related logic closer together; consolidate responsibilities.

---

### Feature Envy

**What**: A method uses data/methods from another class more than its own.

**Symptoms**: Lots of `other_object.field` accesses; the method would be more at home in the other class.

**Why it's a problem**: Wrong placement of logic; high coupling.

**Fix**: Move Method to the class whose data it actually uses.

**Python**:
```python
# ❌ Before
class OrderPrinter:
    def print_details(self, order):
        print(order.customer.name)
        print(order.customer.address)
        print(order.customer.phone)

# ✅ After — move to Customer
class Customer:
    def contact_details(self) -> str:
        return f"{self.name}\n{self.address}\n{self.phone}"
```

---

## Dispensables

Code that serves no purpose and should be removed.

### Dead Code

**What**: Code that is never executed — unused functions, unreachable branches, commented-out blocks.

**Symptoms**: IDE greys it out; no callers; `# TODO: remove this` comments from months ago.

**Why it's a problem**: Noise; maintenance burden; confusion about intent.

**Fix**: Delete it. Version control remembers.

---

### Speculative Generality

**What**: Code, abstractions, or parameters added "just in case" for future use that never comes.

**Symptoms**: Abstract classes with a single subclass; unused method parameters; overly generic frameworks.

**Why it's a problem**: Complexity without value; YAGNI violation.

**Fix**: Remove until actually needed. Refactoring later is cheaper than maintaining unused abstractions now.

---

### Duplicate Code

**What**: Same or very similar code in multiple places.

**Symptoms**: Copy-paste patterns; bug fixes applied in one place but not another; similar functions with minor differences.

**Why it's a problem**: Bugs must be fixed in multiple places; inconsistencies creep in.

**Fix**: Extract shared logic into a function, base class, or utility module.

---

### Lazy Class

**What**: A class that does too little to justify its existence.

**Symptoms**: Wrapper with one method; class with only getters/setters; pass-through delegation.

**Why it's a problem**: Unnecessary indirection; cognitive overhead.

**Fix**: Inline Class — merge it into its caller or the class it wraps.

---

## Couplers

These smells indicate excessive coupling between components.

### Inappropriate Intimacy

**What**: Two classes know too much about each other's internals.

**Symptoms**: Accessing private/protected fields; circular dependencies; tightly paired classes.

**Why it's a problem**: Changes in one break the other; can't use them independently.

**Fix**: Move methods to reduce coupling; introduce an interface; apply mediator pattern.

---

### Message Chains

**What**: Long chains of method calls: `a.getB().getC().getD().doSomething()`.

**Symptoms**: Navigation through object graph to reach deep data; fragile if any intermediate object changes.

**Why it's a problem**: Violates Law of Demeter; tight coupling to the full chain structure.

**Fix**: Hide Delegate — provide a direct method on the nearest object.

**Python**:
```python
# ❌ Before
city = order.customer.address.city

# ✅ After
city = order.shipping_city  # Delegate internally
```

**JS/TS**:
```typescript
// ❌ Before
const city = order.customer.address.city;

// ✅ After
const city = order.shippingCity; // Computed property or method
```

---

### Middle Man

**What**: A class that delegates almost everything to another class, adding no value.

**Symptoms**: Most methods are one-line delegations; the class is a hollow shell.

**Why it's a problem**: Unnecessary indirection; violates KISS.

**Fix**: Remove Middle Man — let callers talk directly to the real worker, or inline the class.

---

## JavaScript/TypeScript-Specific

### Callback Hell

**What**: Deeply nested callbacks that form a "pyramid of doom."

**Symptoms**: 4+ levels of nesting; hard to follow control flow; error handling is scattered or missing.

**Why it's a problem**: Unreadable; error-prone; hard to debug.

**Fix**: Use `async/await` or Promise chains.

```typescript
// ❌ Before
getUser(id, (user) => {
  getOrders(user.id, (orders) => {
    getItems(orders[0].id, (items) => {
      console.log(items);
    });
  });
});

// ✅ After
const user = await getUser(id);
const orders = await getOrders(user.id);
const items = await getItems(orders[0].id);
console.log(items);
```

---

### Prop Drilling

**What**: Passing props through many component layers just to reach a deeply nested child.

**Symptoms**: Intermediate components accept props they don't use; adding a prop requires editing 5+ files.

**Why it's a problem**: Tight coupling between component layers; hard to refactor.

**Fix**: Use React Context, composition (children pattern), or state management.

```tsx
// ❌ Before — drilling `theme` through 4 levels
<App theme={theme}>
  <Layout theme={theme}>
    <Sidebar theme={theme}>
      <MenuItem theme={theme} />
    </Sidebar>
  </Layout>
</App>

// ✅ After — context
const ThemeContext = createContext<Theme>(defaultTheme);

function MenuItem() {
  const theme = useContext(ThemeContext);
  // ...
}
```

---

### Over-rendering

**What**: Components re-render unnecessarily, causing performance issues.

**Symptoms**: UI feels sluggish; React DevTools shows excessive renders; callbacks or objects recreated every render.

**Why it's a problem**: Wasted CPU cycles; poor user experience.

**Fix**: `React.memo`, `useMemo`, `useCallback`; stable references; proper key usage.

```tsx
// ❌ Before — new object every render
function Parent() {
  return <Child style={{ color: "red" }} onClick={() => handleClick()} />;
}

// ✅ After — stable references
function Parent() {
  const style = useMemo(() => ({ color: "red" }), []);
  const onClick = useCallback(() => handleClick(), []);
  return <Child style={style} onClick={onClick} />;
}
```

---

### Uncontrolled Side Effects

**What**: Functions that modify external state, make API calls, or cause mutations without clear boundaries.

**Symptoms**: Hard to predict function behavior; tests require complex mocking; random bugs when call order changes.

**Why it's a problem**: Breaks referential transparency; hard to test and reason about.

**Fix**: Isolate side effects at boundaries; use pure functions for logic; clearly mark effectful code.

```typescript
// ❌ Before — side effect buried in logic
function calculateTotal(items: Item[]) {
  const total = items.reduce((sum, i) => sum + i.price, 0);
  analytics.track("total_calculated", { total }); // hidden side effect!
  return total;
}

// ✅ After — pure calculation, side effect at boundary
function calculateTotal(items: Item[]): number {
  return items.reduce((sum, i) => sum + i.price, 0);
}

// Caller handles the side effect
const total = calculateTotal(items);
analytics.track("total_calculated", { total });
```

---

## Python-Specific

### Mutable Default Arguments

**What**: Using mutable objects (`list`, `dict`, `set`) as default parameter values.

**Symptoms**: Function behaves differently on subsequent calls; shared state between invocations.

**Why it's a problem**: Default values are evaluated once at function definition, not per call. All callers share the same mutable object.

**Fix**: Use `None` as default and create inside the function.

```python
# ❌ Before
def add_item(item, items=[]):
    items.append(item)
    return items

add_item("a")  # ["a"]
add_item("b")  # ["a", "b"] — surprise!

# ✅ After
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

---

### Bare Except

**What**: Catching all exceptions without specifying a type.

**Symptoms**: `except:` or `except Exception:` swallowing errors silently; bugs disappear instead of surfacing.

**Why it's a problem**: Hides real errors (including `KeyboardInterrupt`, `SystemExit`); makes debugging nearly impossible.

**Fix**: Catch specific exceptions; log unexpected ones.

```python
# ❌ Before
try:
    process()
except:
    pass  # What went wrong? Nobody knows.

# ✅ After
try:
    process()
except ValueError as e:
    logger.warning(f"Invalid value: {e}")
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
    raise
```

---

### God Module

**What**: A single Python file that contains hundreds/thousands of lines with many unrelated functions and classes.

**Symptoms**: `utils.py` or `helpers.py` with 50+ functions; hard to find anything; circular import issues.

**Why it's a problem**: No cohesion; hard to navigate; import side effects; testing nightmares.

**Fix**: Split into focused modules organized by domain or responsibility.

```python
# ❌ Before — one massive utils.py
# utils.py (2000 lines)
def format_date(): ...
def send_email(): ...
def calculate_tax(): ...
def resize_image(): ...

# ✅ After — focused modules
# formatting.py
def format_date(): ...

# notifications.py
def send_email(): ...

# billing.py
def calculate_tax(): ...

# media.py
def resize_image(): ...
```

---

### Import Side Effects

**What**: Module-level code that executes side effects when imported (DB connections, API calls, file writes).

**Symptoms**: Importing a module triggers unexpected behavior; tests break due to import order; circular import issues.

**Why it's a problem**: Makes imports unpredictable; breaks test isolation; slows startup.

**Fix**: Wrap side effects in functions; use lazy initialization; guard with `if __name__ == "__main__"`.

```python
# ❌ Before
# config.py
import requests
settings = requests.get("https://api.example.com/config").json()  # Runs on import!

# ✅ After
# config.py
import requests
from functools import lru_cache

@lru_cache
def get_settings():
    return requests.get("https://api.example.com/config").json()
```

---

## Quick Severity Guide

| Severity | Impact | Examples |
|----------|--------|----------|
| 🔴 Critical | Security risk, data loss, crashes | Bare except hiding errors, mutable shared state, SQL injection |
| 🟠 High | Major maintainability/reliability issues | God class, deep nesting, missing error handling |
| 🟡 Medium | Code quality degradation over time | Duplication, long parameter lists, feature envy |
| 🟢 Low | Style/convention issues | Magic numbers, naming, missing type hints |

---

*This catalog is a practical quick-reference. For each finding, always explain the specific impact in the current codebase rather than citing general rules.*
