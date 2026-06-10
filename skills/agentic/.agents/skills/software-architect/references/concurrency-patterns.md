# Concurrency Patterns Reference — Software Architect

> Language-specific concurrency patterns for Go and Java.
> Used by the `software-architect` skill when designing concurrent systems.

---

## Go Concurrency Patterns

### Goroutines + Channels

Use for producer-consumer, fan-out/fan-in, pipeline patterns.

```go
// Fan-out/Fan-in pattern
func fanOut(input <-chan Item, workers int) []<-chan Result {
    channels := make([]<-chan Result, workers)
    for i := 0; i < workers; i++ {
        channels[i] = process(input)
    }
    return channels
}

func fanIn(channels ...<-chan Result) <-chan Result {
    var wg sync.WaitGroup
    merged := make(chan Result, 10)
    output := func(c <-chan Result) {
        defer wg.Done()
        for r := range c {
            merged <- r
        }
    }
    wg.Add(len(channels))
    for _, c := range channels {
        go output(c)
    }
    go func() {
        wg.Wait()
        close(merged)
    }()
    return merged
}
```

### Worker Pool

Limit concurrency with buffered channels and a fixed number of goroutines.

```go
func processItems(ctx context.Context, items []Item, workers int) error {
    g, ctx := errgroup.WithContext(ctx)
    jobs := make(chan Item, len(items))

    // Enqueue all jobs
    for _, item := range items {
        jobs <- item
    }
    close(jobs)

    // Launch workers
    for i := 0; i < workers; i++ {
        g.Go(func() error {
            for item := range jobs {
                if err := process(ctx, item); err != nil {
                    return err
                }
            }
            return nil
        })
    }
    return g.Wait()
}
```

### Context Propagation

Always thread `context.Context` through goroutine boundaries for cancellation and timeouts.

```go
func fetchWithTimeout(ctx context.Context, url string) ([]byte, error) {
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()

    req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
    if err != nil {
        return nil, err
    }
    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    return io.ReadAll(resp.Body)
}
```

### errgroup for Coordinated Error Handling

```go
func fetchAll(ctx context.Context, urls []string) ([][]byte, error) {
    g, ctx := errgroup.WithContext(ctx)
    results := make([][]byte, len(urls))

    for i, url := range urls {
        i, url := i, url // capture loop variables
        g.Go(func() error {
            data, err := fetchWithTimeout(ctx, url)
            if err != nil {
                return fmt.Errorf("fetching %s: %w", url, err)
            }
            results[i] = data
            return nil
        })
    }

    if err := g.Wait(); err != nil {
        return nil, err
    }
    return results, nil
}
```

### Sync Primitives

```go
// sync.Mutex for shared state
type SafeCounter struct {
    mu    sync.Mutex
    count int
}

func (c *SafeCounter) Inc() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.count++
}

func (c *SafeCounter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.count
}

// sync.Once for lazy initialization
var (
    instance *Service
    once     sync.Once
)

func GetService() *Service {
    once.Do(func() {
        instance = newService()
    })
    return instance
}
```

### Go Concurrency Checklist

- ✅ Always check returned errors — never use `_` for error values in production
- ✅ Goroutines must have exit conditions — no goroutine leaks
- ✅ Close channels from the sender side only
- ✅ Prefer `errgroup` over raw `sync.WaitGroup` for error propagation
- ✅ Always pass `context.Context` as first parameter in all I/O functions
- ✅ Run tests with `-race` flag: `go test -race ./...`
- ❌ Avoid shared mutable state — prefer channels or mutex-protected structs
- ❌ Never close a nil channel (panics)

---

## Java Concurrency Patterns

### CompletableFuture (Java 8+)

For async composition, analogous to Promise chaining.

```java
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor(); // Java 21+

CompletableFuture<UserOrder> fetchUserOrder(String userId) {
    CompletableFuture<User> userFuture =
        CompletableFuture.supplyAsync(() -> userService.findById(userId), executor);

    CompletableFuture<List<Order>> ordersFuture =
        CompletableFuture.supplyAsync(() -> orderService.findByUser(userId), executor);

    return userFuture.thenCombine(ordersFuture, UserOrder::new)
        .exceptionally(ex -> {
            log.error("Failed to fetch user order for {}", userId, ex);
            throw new ServiceException("User order fetch failed", ex);
        });
}
```

### Virtual Threads (Java 21+)

Prefer over thread pools for I/O-bound tasks — eliminates the overhead of thread-per-request model.

```java
// Use virtual threads for I/O-bound parallel work
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<Result>> futures = urls.stream()
        .map(url -> executor.submit(() -> fetchUrl(url)))
        .toList();

    return futures.stream()
        .map(f -> {
            try { return f.get(); }
            catch (Exception e) { throw new RuntimeException(e); }
        })
        .toList();
}
```

### Structured Concurrency (Java 21+)

Use `StructuredTaskScope` for scoped parallelism with automatic cleanup.

```java
import java.util.concurrent.StructuredTaskScope;

UserOrder fetchUserOrder(String userId) throws InterruptedException, ExecutionException {
    try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
        // Fork parallel subtasks
        StructuredTaskScope.Subtask<User> userTask =
            scope.fork(() -> userService.findById(userId));
        StructuredTaskScope.Subtask<List<Order>> ordersTask =
            scope.fork(() -> orderService.findByUser(userId));

        scope.join()           // Wait for all subtasks
             .throwIfFailed(); // Propagate first failure

        return new UserOrder(userTask.get(), ordersTask.get());
    } // Scope auto-closes, cancels any remaining subtasks
}
```

### Reactive (Project Reactor / WebFlux)

For high-concurrency, non-blocking I/O at scale.

```java
import reactor.core.publisher.Mono;
import reactor.core.publisher.Flux;

// Non-blocking parallel fetch
Mono<UserOrder> fetchUserOrder(String userId) {
    return Mono.zip(
        Mono.fromCallable(() -> userService.findById(userId)).subscribeOn(Schedulers.boundedElastic()),
        Mono.fromCallable(() -> orderService.findByUser(userId)).subscribeOn(Schedulers.boundedElastic())
    ).map(tuple -> new UserOrder(tuple.getT1(), tuple.getT2()));
}
```

### Java Concurrency Checklist

- ✅ Prefer Virtual Threads (Java 21+) over thread pools for I/O-bound work
- ✅ Use `StructuredTaskScope` instead of raw `CompletableFuture` when on Java 21+
- ✅ Mark mutable shared state with `volatile` or use `java.util.concurrent` classes
- ✅ Use `AtomicInteger`/`AtomicReference` for lock-free counter/reference updates
- ✅ Prefer immutable objects (`record`, `final` fields) to avoid synchronization
- ❌ Never call blocking code inside reactive streams (use `.subscribeOn(Schedulers.boundedElastic())`)
- ❌ Avoid `synchronized` methods on high-contention paths — prefer `ReentrantReadWriteLock`
- ❌ Never ignore `InterruptedException` — always restore interrupt status or rethrow

---

## Python Async Patterns

### asyncio (Python 3.11+)

```python
import asyncio
from typing import Any

# Concurrent tasks with gather
async def fetch_all(urls: list[str]) -> list[Any]:
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Filter out exceptions
        return [r for r in results if not isinstance(r, Exception)]

# TaskGroup (Python 3.11+) — structured concurrency
async def fetch_user_order(user_id: str) -> UserOrder:
    async with asyncio.TaskGroup() as tg:
        user_task = tg.create_task(fetch_user(user_id))
        orders_task = tg.create_task(fetch_orders(user_id))
    # Both tasks complete (or one raises, cancelling the rest)
    return UserOrder(user=user_task.result(), orders=orders_task.result())

# Rate limiting with Semaphore
async def fetch_with_rate_limit(urls: list[str], max_concurrent: int = 10) -> list[Any]:
    semaphore = asyncio.Semaphore(max_concurrent)
    async def bounded_fetch(url: str):
        async with semaphore:
            return await fetch_url(url)
    return await asyncio.gather(*[bounded_fetch(url) for url in urls])
```

### Python Async Checklist

- ✅ Use `asyncio.TaskGroup` (Python 3.11+) instead of `asyncio.gather` for structured concurrency
- ✅ Use `asyncio.Semaphore` to limit concurrent I/O operations
- ✅ Avoid blocking calls inside async functions — use `loop.run_in_executor` for CPU-bound work
- ✅ Handle `asyncio.CancelledError` explicitly in long-running tasks
- ❌ Never use `time.sleep()` inside async code — use `await asyncio.sleep()`
- ❌ Avoid creating tasks without storing a reference (they can be garbage-collected mid-execution)

---

## TypeScript Async Patterns

```typescript
// Promise.all for concurrent independent fetches
async function fetchUserOrder(userId: string): Promise<UserOrder> {
  const [user, orders] = await Promise.all([
    userService.findById(userId),
    orderService.findByUser(userId),
  ]);
  return { user, orders };
}

// Promise.allSettled when you want all results regardless of failures
async function fetchAllWithFallback(ids: string[]): Promise<Result[]> {
  const results = await Promise.allSettled(ids.map(id => fetchItem(id)));
  return results.map(r =>
    r.status === 'fulfilled' ? r.value : { error: r.reason.message }
  );
}

// Concurrency limiting
async function processWithLimit<T, R>(
  items: T[],
  fn: (item: T) => Promise<R>,
  limit: number
): Promise<R[]> {
  const results: R[] = [];
  const chunks = Array.from({ length: Math.ceil(items.length / limit) },
    (_, i) => items.slice(i * limit, (i + 1) * limit)
  );
  for (const chunk of chunks) {
    const chunkResults = await Promise.all(chunk.map(fn));
    results.push(...chunkResults);
  }
  return results;
}
```
