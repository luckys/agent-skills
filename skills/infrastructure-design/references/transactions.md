# Transactions

Source: [CodelyTV/infrastructure_design-transactions-course](https://github.com/CodelyTV/infrastructure_design-transactions-course), corrected for connection scope, side effects, cleanup, and concurrency.

## Core Guarantee

A transaction is atomic only when every participating database operation uses the same transaction-scoped connection. Opening a transaction on one connection while repositories borrow others from a pool provides no shared commit or rollback. Pass the scoped handle explicitly or bind it to request/job-local async context; never store the active connection in a singleton shared by concurrent requests.

## Repository-Owned Business Transaction (Anti-Pattern)

**Intent:** Avoid letting each repository independently own and commit the business transaction.

**How it fails:** A repository `save()` opens and commits before the use case finishes. Multiple repository calls then run in separate transactions, making partial failure possible.

**When to use:**
- Never let an adapter commit independently when it must compose into a larger unit of work
- An adapter may use an internal transaction to persist one Aggregate across tables only when no outer transaction exists and the API still supports propagation/composition

**When NOT to use:**
- Any use case that calls `repositoryA.save()` AND `repositoryB.save()` — the two saves are not atomic

**Practical heuristic:** The anti-pattern is independent commit ownership, not every internal adapter transaction. If the use case coordinates atomic work, it owns the boundary and repositories join it.

---

## Transaction in Use Case (Application Service)

**Intent:** Wrap the entire unit of work for a use case in a single transaction at the application service level.

**How it works:** The use case opens a transaction before doing any work, executes all repository operations within that transaction, and commits (or rolls back on error) at the end. Repositories receive the active transaction context explicitly or through a request/job-local async-context store.

**When to use:**
- Use cases that persist one Aggregate through multiple statements or tables
- Multiple local writes that a documented business invariant requires to commit atomically
- Domain events that must be saved atomically with the aggregate (see event-bus.md Outbox pattern)

**When NOT to use:**
- Simple reads that accept the database's default statement-level consistency
- A single atomic database statement that needs no stronger isolation guarantee
- Use cases that span multiple bounded contexts or remote services (use sagas / process managers instead)
- Very long-running operations (holding a DB transaction for seconds causes lock contention)

**Practical heuristic:** The use case commonly owns the transaction boundary, but the Aggregate owns the consistency boundary. Updating multiple Aggregate Roots in one local transaction is possible, yet it is a design warning: first verify that the rule is truly atomic rather than a workflow that can use events or a process manager. Multiple tables belonging to one Aggregate are not multiple consistency boundaries. Use `ddd-best-practices` to review the boundary.

**Example:**
```typescript
// InlineTransactionalPostPublisher.ts — explicit inline strategy
export class InlineTransactionalPostPublisher {
  constructor(
    private readonly clock: Clock,
    private readonly repository: PostRepository,
    private readonly outbox: IntegrationMessageOutbox,
    private readonly transactionManager: TransactionManager,
  ) {}

  async publish(id: string, userId: string, content: string): Promise<void> {
    const post = Post.publish(id, userId, content, this.clock);
    let handedOff: readonly DomainEvent[] = [];
    await this.transactionManager.run(async (tx) => {
      handedOff = post.pendingDomainEvents(); // non-destructive, stable event IDs
      const messages = toIntegrationMessages(handedOff);
      await this.repository.with(tx).save(post);
      await this.outbox.with(tx).append(messages);
    });
    post.clearDomainEvents(handedOff); // clear only after commit
  }
}
```

The Unit of Work must not permanently discard pulled events when the transaction rolls back. Append them durably before commit and retain/recover pending events on failure, or inspect pending events without draining until the handoff succeeds. See `event-bus.md` for the full Outbox contract.

---

## Transaction Decorator (Transparent Wrapping)

**Intent:** Add transaction semantics to a use case without modifying its code, using the Decorator pattern.

**How it works:** As an alternative to the inline strategy above, a `TransactionalPostPublisher` wraps a transaction-unaware `PostPublisher`. Before delegating to the inner use case, it opens a transaction; after successful execution it commits; on exception it rolls back. Never apply this decorator to an already transactional use case.

**When to use:**
- When you want to apply transactions uniformly to many use cases
- When transaction management is a cross-cutting concern you want to keep out of business logic
- In frameworks with DI containers that support decoration (NestJS interceptors, diod decorators)

**When NOT to use:**
- When the transaction boundary requires conditional logic that the decorator cannot express
- When different use case methods need different transaction scopes

**Practical heuristic:** Start with the transaction inside the use case. Extract to a decorator only when you see the same wrapping code copy-pasted across multiple use cases.

**Example:**
```typescript
// TransactionalPostPublisher.ts — decorator approach
export class TransactionalPostPublisher implements PostPublisherInterface {
  constructor(
    private readonly wrapped: PostPublisher,
    private readonly transactionManager: TransactionManager,
  ) {}

  async publish(id: string, userId: string, content: string): Promise<void> {
    await this.transactionManager.run(async () => {
      await this.wrapped.publish(id, userId, content);
    });
  }
}
```

---

## Transaction at Entry Point

**Intent:** Open the transaction at the HTTP controller or message consumer level, wrapping the entire request.

**How it works:** Middleware or an interceptor starts a transaction before the request reaches the use case, and commits or rolls back after the response is produced.

**When to use:**
- Framework-level transaction management (e.g., Spring `@Transactional` on controller, NestJS interceptor)
- When every endpoint in a group always needs a transaction

**When NOT to use:**
- Simple GET endpoints that need no multi-query snapshot, explicit lock, or stronger isolation
- When only some endpoints in a group need transactions
- When different transports calling the same use case would receive different transaction semantics

**Practical heuristic:** Entry-point transactions are convenient but coarse. If a controller coordinates a business operation, extract an application command handler/orchestrator and place the boundary there. A message consumer commonly needs a transaction precisely to commit its Inbox and local effect atomically; transport-level idempotency does not replace that transaction.

---

## Generic Proxy Decorators

A generic JavaScript `Proxy` that wraps every function is usually too implicit: it also transacts read-only/helpers, erases useful method types, hides isolation requirements, and can start a nested transaction accidentally. Prefer an explicit typed decorator per use-case contract or framework metadata that selects named methods. Register it at the composition root and test that only intended methods are wrapped.

Nested calls need a declared propagation policy: join the existing transaction, create a savepoint, or reject nesting. Calling `beginTransaction()` again on one mutable connection is not a policy. The outermost owner normally commits; an inner participant must not independently commit or release the shared connection.

## Connection Lifecycle and Failure Semantics

Acquire one connection per transaction and release it in `finally`, after commit or rollback attempts. Clear request-local state even when cleanup fails. Do not retain the connection after commit, rollback, or pool release.

Track whether begin succeeded; do not blindly rollback a transaction that never started. Preserve the primary application error if rollback also fails, while recording the rollback failure for operators. A commit failure has an uncertain outcome: classify it as ambiguous and non-retryable by default, then reconcile. Retry only when effective idempotency or the database/driver contract makes replay demonstrably safe.

Never interpolate values or identifiers into SQL merely because a transaction exists. Parameterize values and allow-list dynamic identifiers; atomic SQL injection is still SQL injection.

## Side Effects

Database rollback cannot undo email, broker publication, HTTP calls, filesystem writes, or another database. Do not execute irreversible side effects inside a local transaction and call the result atomic. Persist an Outbox/intent in the same transaction, commit, and process it later. If a synchronous in-process reaction performs only writes through the same scoped connection, it may participate; otherwise treat it as an external effect.

A deferred in-memory Event Bus is not an Outbox. Its buffer can leak between concurrent requests when singleton-scoped, disappears on process crash, and publishing before commit can expose state that later rolls back. Keep pending events invocation-local and durably hand them off in the transaction.

## Isolation and Time

Choose isolation from the invariant and anomaly, not a global default. Optimistic version checks prevent lost updates but do not automatically prevent write skew across multiple rows. Use stronger isolation, explicit locks, or a constraint when the invariant requires it. Keep transactions short: do not include user think time, sleeps, slow queries unrelated to the write, or remote I/O.

Retry deadlocks and serialization failures only around the complete transaction, with bounded backoff, and only when replaying the command is safe. Never retry permanent constraint violations or an ambiguous commit as though no work occurred.

---

## Optimistic Concurrency at the Aggregate Boundary

**Intent:** Reject stale writes instead of silently overwriting a decision made from newer Aggregate state.

**How it works:** Persist a version with the Aggregate. Update with both identity and expected version (`WHERE id = ? AND version = ?`) and increment the version atomically. Treat zero affected rows as a concurrency conflict. The application decides whether to reload and retry a commutative command or return a conflict for user review.

**When to use:**
- Concurrent commands can target the same Aggregate Root
- Lost updates could violate a business decision
- Holding pessimistic locks across user or network time is unacceptable

**When NOT to use:**
- Blind last-write-wins is explicitly acceptable
- The operation is an atomic database primitive that does not depend on previously loaded state

**Practical heuristic:** Version the Aggregate, not each table or child independently. Add an integration test with two readers of the same version and prove that only one stale-dependent write succeeds.

---

## Cross-Service Workflows

**Intent:** Coordinate work across independently owned services or resources.

**How it works:** Two-phase commit requires compatible participants and carries availability, lock, and operational costs. A common alternative is local transactions plus Outbox and a Saga/process manager, with compensations where business semantics permit them.

**When to use:**
- Use 2PC only in controlled environments where every participant supports it and its failure/availability costs are accepted
- Use a Saga/process manager when a workflow spans autonomous services

**When NOT to use:**
- Do not introduce a shared integration database merely to avoid a distributed workflow
- Do not describe compensation as rollback: it is a new business action and can also fail

**Practical heuristic:** Recheck the consistency boundary and service split first. If autonomy is intentional, preserve ownership and coordinate explicitly rather than coupling services through shared tables.
