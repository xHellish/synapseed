# Database Patterns and Best Practices

This document provides deep-dive best practices for database design, indexing, performance optimization, and migrations.

## 1. Relational vs NoSQL Choices

### Relational (SQL)
- **Strengths**: Strong ACID compliance, structured data, complex joins, relational integrity.
- **When to use**: Financial systems, ERPs, structured reporting, systems where relationships are complex and data integrity is paramount.
- **Key pattern**: Normalize to 3NF to avoid data anomalies.

### NoSQL (Document / Key-Value)
- **Strengths**: Flexible schema, horizontal scalability, high write throughput, hierarchical data.
- **When to use**: Catalogs, content management, real-time analytics, user preferences, caching.
- **Key pattern**: Design based on access patterns (query-driven design). Denormalize and nest data that is read together.

## 2. Indexing Strategies

Proper indexing is critical for read performance, but adds overhead to write operations.

### B-Tree Indexes
- **Usage**: Default index type. Good for exact matches, range queries (`>`, `<`), and sorting.
- **Rule of thumb**: Index foreign keys, primary lookup columns, and columns frequently used in `WHERE` and `ORDER BY` clauses.

### Hash Indexes
- **Usage**: Memory-efficient for exact equality checks (`=`). Not suitable for range queries.
- **Rule of thumb**: Use when only exact lookups are needed, such as session IDs or unique hashes.

### Compound (Composite) Indexes
- **Usage**: Indexing multiple columns together.
- **Rule of thumb**: Column order matters. Place the most selective column first, or match the order of your `WHERE` and `ORDER BY` clauses (Left-most prefix rule).

### Covering Indexes
- **Usage**: An index that contains all the columns required to satisfy a query, preventing the DB from needing to look up the actual table row.
- **Rule of thumb**: Useful for highly-frequent read queries. Include selected columns in the `INCLUDE` clause (PostgreSQL) if they aren't part of the filter condition.

## 3. N+1 Query Problem Prevention

The N+1 query problem occurs when an application makes one query to retrieve a list of $N$ entities, and then $N$ additional queries to retrieve related data.

### Identification
Look for loops in the application code iterating over a result set and lazy-loading relationships.

### Prevention Strategies
- **Eager Loading**: Use ORM features to load relationships in advance (e.g., `JOIN FETCH` in Hibernate, `joinedload` in SQLAlchemy, `include` in Prisma).
- **Batching / Data Loaders**: Group requests for related entities and fetch them in a single query using `IN (...)`. This is especially useful in GraphQL APIs.

## 4. Safe Database Migrations (Zero Downtime)

Applying schema changes in production without locking tables or causing downtime.

### The Expand and Contract Pattern
Instead of renaming or altering a column in a single destructive step, use a multi-step process:

1. **Expand**: Add the new column/table alongside the old one.
2. **Migrate Code**: Update the application to write to both the old and new columns, but read from the old one.
3. **Backfill**: Migrate historical data from the old column to the new column in small batches in the background.
4. **Transition Code**: Update the application to read from the new column.
5. **Contract**: Remove the old column/table and any dual-writing logic.

### Avoiding Table Locks
- Do not add columns with a dynamic default value (unless supported by your DB version efficiently, like Postgres 11+).
- Build indexes concurrently (`CREATE INDEX CONCURRENTLY` in Postgres).
- Add constraints as `NOT VALID` first, then validate them in a separate transaction.
