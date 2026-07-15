# Database Views

Source: CodelyTV/infrastructure_design-views-course

## Standard Database View

**Intent:** Encapsulate a complex SELECT query as a named virtual table, simplifying read access across the application.

**How it works:** A `CREATE VIEW` statement stores a query definition. Every access to the view re-executes the underlying query. The view acts like a table from the caller's perspective but does not store data — it is recomputed on every read.

**When to use:**
- Simplifying repeated JOIN queries that are used in multiple places
- Providing a stable query interface when the underlying schema may evolve
- Abstracting complexity from application code (the application queries the view, not the raw tables)
- CQRS read side for simple aggregations that do not require pre-computation

**When NOT to use:**
- When the underlying query is expensive and called frequently (each view access reruns the query — this does not scale)
- When the data must be fresh AND fast simultaneously (choose materialized view or a projection instead)
- As a substitute for proper domain models — views are a DB-level concern

**Practical heuristic:** A view is a reusable saved query, not a performance optimization. If you need performance, you need a materialized view or a projection table.

**Example:**
```sql
-- Standard view: recomputed on every SELECT
CREATE VIEW posts_with_likes AS
SELECT
  p.id,
  p.user_id,
  p.content,
  p.created_at,
  COUNT(pl.id) AS total_likes
FROM posts p
LEFT JOIN post_likes pl ON pl.post_id = p.id
GROUP BY p.id, p.user_id, p.content, p.created_at;

-- Application queries the view, not the raw tables
SELECT * FROM posts_with_likes WHERE user_id = ?;
```

---

## Refreshable Materialized View (PostgreSQL / Oracle)

**Intent:** Pre-compute and physically store the result of a complex query, enabling fast reads at the cost of stale data between refreshes.

**How it works:** `CREATE MATERIALIZED VIEW` executes the query and stores its result as a real table. Reads hit the stored snapshot — no recomputation. The view becomes stale as soon as the underlying data changes. It must be refreshed explicitly (`REFRESH MATERIALIZED VIEW`) or on a schedule.

**When to use:**
- Expensive aggregate queries (COUNT, SUM, AVG over millions of rows) that are read frequently
- Reporting and analytics dashboards where slight staleness is acceptable
- PostgreSQL, Oracle, or SQL Server environments (native materialized view support)
- Query paths that need predictable low latency over expensive precomputed results

**When NOT to use:**
- MySQL (does not support materialized views natively — use the trigger pattern instead, see below)
- When data must always be current (use a live view or a projection table with event-driven updates)
- When refresh frequency would approach write frequency (you pay the refresh cost without benefiting from staleness tolerance)

**Practical heuristic:** Measure with production-shaped data and query plans. Choose a materialized view when refresh cost and tolerated staleness fit the workload; choose an event-driven projection when incremental updates, independent ownership, or replay semantics justify its operational cost.

**Example:**
```sql
-- PostgreSQL materialized view
CREATE MATERIALIZED VIEW posts_with_likes AS
SELECT
  p.id,
  p.user_id,
  p.content,
  p.created_at,
  COUNT(pl.id) AS total_likes
FROM posts p
LEFT JOIN post_likes pl ON pl.post_id = p.id
GROUP BY p.id, p.user_id, p.content, p.created_at;

-- Refresh (can be scheduled or triggered from application)
REFRESH MATERIALIZED VIEW posts_with_likes;
```

---

## Materialized View with Triggers (MySQL Pattern)

**Intent:** Simulate a materialized view in MySQL by maintaining a projection table that is updated automatically via DB triggers.

**How it works:** Create a regular table (`posts_projection`) with the pre-computed columns. Write `AFTER INSERT` / `AFTER UPDATE` / `AFTER DELETE` triggers on the source tables. Each trigger updates the projection table incrementally — no full recomputation needed.

**When to use:**
- MySQL environments where native materialized views are unavailable
- When you need near-real-time freshness without polling or application-level projection handlers
- When the projection is simple enough that triggers can maintain it correctly

**When NOT to use:**
- Complex aggregations where triggers become hard to reason about (use event-driven projections instead)
- When triggers would fire on every row of a bulk import (performance impact during large data loads)
- When the projection logic requires application-level business rules (triggers bypass the domain model)

**Practical heuristic:** Triggers are invisible to the application and easy to forget. Document them in schema migrations and test write amplification, bulk loads, corrections, and rollback. Move to an event-driven projection when ownership, deployment, cross-context data, or operational recovery no longer fits a database trigger; line count is not the decision criterion.

**Example:**
```sql
-- Projection table (acts as the materialized view)
CREATE TABLE posts_projection (
  id           CHAR(36) PRIMARY KEY,
  user_id      CHAR(36) NOT NULL,
  content      TEXT NOT NULL,
  total_likes  INT NOT NULL,
  created_at   DATETIME NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Trigger: populate projection when a post is inserted
CREATE TRIGGER insert_post_projection_on_post_inserted
AFTER INSERT ON posts
FOR EACH ROW
BEGIN
  INSERT INTO posts_projection (id, user_id, content, total_likes, created_at)
  VALUES (new.id, new.user_id, new.content, 0, new.created_at);
END;

-- Trigger: recompute total_likes when a like is inserted
CREATE TRIGGER recalculate_total_post_projection_likes_on_post_like_inserted
AFTER INSERT ON post_likes
FOR EACH ROW
BEGIN
  UPDATE posts_projection
  SET total_likes = (SELECT COUNT(*) FROM post_likes WHERE post_id = new.post_id)
  WHERE id = new.post_id;
END;
```

---

## Views as CQRS Read Side

**Intent:** Use a view or projection table as the read model in a CQRS architecture, separating query logic from the write model.

**How it works:** The write side uses normalized tables and domain aggregates. The read side queries a view or projection table that denormalizes the data for the exact shape needed by the UI. The projection is updated either by DB triggers, event handlers, or periodic refresh.

**When to use:**
- When read queries require different data shapes than the write model
- When read and write performance requirements conflict (write optimized for consistency, read optimized for speed)
- When the same aggregate data is presented in multiple different formats to different consumers

**When NOT to use:**
- Simple CRUD applications where the read and write shape are identical
- When projection lag (eventual consistency) would confuse users in a strongly consistent flow

**Practical heuristic:** Start with the simplest mechanism that satisfies measured query cost, freshness, ownership, and rebuild requirements. A standard view is not automatically the safest starting point for an expensive or cross-context query.

---

## Materialized View — SQL Server (Indexed View)

**Intent:** Use SQL Server's indexed view to materialize a query result with automatic synchronous maintenance on every write.

**How it works:** `CREATE VIEW ... WITH SCHEMABINDING` followed by `CREATE UNIQUE CLUSTERED INDEX` on the view causes SQL Server to maintain the materialized data automatically on every `INSERT`, `UPDATE`, or `DELETE` to the underlying tables — no manual `REFRESH` needed, unlike PostgreSQL.

**When to use:**
- SQL Server environments where you want the freshness of a standard view with the performance of a materialized view
- Aggregations that must always be current (no tolerable lag)
- Scenarios where the aggregate query runs on a table that is written frequently but queried even more frequently

**When NOT to use:**
- Views with `OUTER JOIN`, `DISTINCT`, subqueries, or non-deterministic functions (SQL Server prohibits indexing these)
- Very high write throughput — every write pays the index maintenance cost
- When the view references more than one database

**Example:**
```sql
-- SQL Server indexed view (automatically maintained)
CREATE VIEW dbo.posts_with_likes
WITH SCHEMABINDING
AS
SELECT
  p.id,
  p.user_id,
  p.content,
  p.created_at,
  COUNT_BIG(*) AS total_likes    -- must use COUNT_BIG, not COUNT
FROM dbo.posts AS p
INNER JOIN dbo.post_likes AS pl ON pl.post_id = p.id  -- must be INNER JOIN
GROUP BY p.id, p.user_id, p.content, p.created_at;

-- Materializes the view; SQL Server now maintains this index automatically
CREATE UNIQUE CLUSTERED INDEX IX_posts_with_likes ON dbo.posts_with_likes (id);

-- Query hits the materialized index directly (no recomputation)
SELECT * FROM dbo.posts_with_likes WHERE user_id = '...';
```

**Practical heuristic:** SQL Server indexed views are more restrictive than PostgreSQL materialized views but more automatic. Check that your aggregation uses `COUNT_BIG`, all joins are `INNER JOIN`, and the view is bound with `SCHEMABINDING` — without these the index creation will fail.

---

## Event-Driven Projection Handler (Application Layer)

**Intent:** Maintain a projection table from domain events, keeping the read model in sync without DB triggers or scheduled refresh.

**How it works:** A domain event subscriber listens for events (e.g., `PostLikeAdded`) and updates the projection table incrementally. The projection handler is an application service in the read context — it has full access to repositories, application services, and external APIs that a DB trigger cannot call.

**When to use:**
- Projection logic requires application code (e.g., calling an external API, applying business rules, enriching with data from another context)
- Cross-context projections where the read context lives in a different service from the write context
- When trigger logic exceeds ~10 lines and becomes difficult to reason about

**When NOT to use:**
- Simple `COUNT` / `SUM` projections that triggers handle cleanly
- When you need synchronous consistency (event-driven projections are eventually consistent)

**Practical heuristic:** Prefer a DB trigger for small same-database derivations with acceptable write amplification. Prefer an event-driven projection when it needs independent ownership, another bounded context, durable replay, or separate scaling. Do not call remote services from a projector without defining retry, idempotency, and replay drift.

**Example — TypeScript event handler updating a projection:**
```typescript
// OnPostLikeAddedUpdatePostProjection.ts
export class OnPostLikeAddedUpdatePostProjection
  implements DomainEventSubscriber<PostLikeAdded>
{
  subscribedTo() {
    return [PostLikeAdded];
  }

  constructor(private readonly projectionRepository: PostProjectionRepository) {}

  async on(event: PostLikeAdded): Promise<void> {
    const projection = await this.projectionRepository.search(new PostId(event.postId));
    if (!projection) return;

    const updated = projection.incrementLikes();
    await this.projectionRepository.save(updated);
  }
}

// PostProjectionRepository — writes to the denormalized projection table
export class MariaDBPostProjectionRepository implements PostProjectionRepository {
  async save(projection: PostProjection): Promise<void> {
    await this.connection.execute(`
      INSERT INTO posts_projection (id, user_id, content, total_likes, created_at)
      VALUES (?, ?, ?, ?, ?)
      ON DUPLICATE KEY UPDATE total_likes = ?
    `);
  }
}
```

---

## Views vs Projections vs Cache: Decision Table

| Need | Solution |
|---|---|
| Simplify repeated JOINs, always fresh | Standard VIEW |
| Pre-computed aggregates, tolerate staleness, PostgreSQL | Materialized VIEW |
| Pre-computed aggregates, always fresh, MySQL | Trigger-maintained projection table |
| Pre-computed aggregates updated by business events | Event-driven projection (application layer) |
| Fast reads for individual aggregates | Cache-aside on repository (see cache.md) |
