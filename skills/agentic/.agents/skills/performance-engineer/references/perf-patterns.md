# Performance Patterns and Methodologies

This document outlines standard patterns, metrics, and methodologies used by the `performance-engineer`.

## 1. Key Metrics

- **Latency**: The time it takes to process a single request and return a response (usually measured in percentiles: p50, p95, p99).
- **Throughput**: The rate at which requests are processed, usually measured in Requests Per Second (RPS) or Transactions Per Second (TPS).
- **Error Rate**: The percentage of requests that result in errors (e.g., HTTP 5xx).
- **Resource Utilization**: CPU, Memory, Disk I/O, and Network I/O consumption.
- **Concurrency**: The number of requests being processed simultaneously.

## 2. Profiling Methodologies

### USE Method (Utilization, Saturation, Errors)
Used for analyzing infrastructure and system resources.
- **Utilization**: The average time the resource was busy.
- **Saturation**: The degree to which extra work is queued because the resource is busy.
- **Errors**: The count of error events.

### RED Method (Rate, Errors, Duration)
Used for monitoring microservices and request-driven applications.
- **Rate**: The number of requests per second.
- **Errors**: The number of those requests that are failing.
- **Duration**: The amount of time those requests take.

## 3. Caching Strategies

### Cache-Aside (Lazy Loading)
- **How it works**: The application checks the cache first. If there's a miss, it queries the database, returns the data, and stores it in the cache for future requests.
- **Pros**: Only requested data is cached. Cache failures don't bring down the application (fallback to DB).
- **Cons**: Cache misses result in 3 trips (Check Cache -> Query DB -> Update Cache), leading to initial latency. Data can become stale.

### Write-Through
- **How it works**: Data is written into the cache and the corresponding database at the same time.
- **Pros**: Data in the cache is never stale. Fast reads.
- **Cons**: Write operations involve an extra step, causing higher write latency. Caches data that might never be read.

### Write-Behind (Write-Back)
- **How it works**: Data is written only to the cache initially. The cache asynchronously writes to the database.
- **Pros**: Very low write latency. Handles write spikes well.
- **Cons**: Risk of data loss if the cache crashes before the database is updated. Complex to implement.

## 4. Common Antipatterns
- **N+1 Query Problem**: Fetching parent entities and then executing a separate query for each child entity's related data.
- **Blocking the Event Loop (Node.js)**: Performing heavy synchronous CPU tasks on the main thread, preventing other I/O operations from being handled.
- **Memory Leaks**: Holding references to objects that are no longer needed, eventually exhausting available memory.
- **Synchronous External Calls**: Making API calls or DB queries synchronously, causing threads to idle while waiting for a response.
