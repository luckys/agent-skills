# Domain Errors

How to model failures that happen inside the domain in a maintainable, explicit, and layer-appropriate way. Source: CodelyTV `domain_modeling-errors-course`.

---

## Typed Domain Errors (Exceptions as Domain Concepts)

**Intent:** Give each domain failure its own type so callers can distinguish between them without parsing error messages.

**How it works:** Create a dedicated class per failure, extending the language's base `Error`. Name it after the domain concept that failed, not the technical action ("UserDoesNotExistError", not "NotFoundException"). The class lives in the domain layer alongside the aggregate it belongs to. Because it extends `Error`, it can be thrown and caught normally, but it carries a domain name that infrastructure and application layers can switch on.

**Example:**
```typescript
// domain/UserDoesNotExistError.ts
export class UserDoesNotExistError extends Error {
  constructor(id: string) {
    super(`The user ${id} does not exist`);
  }
}

// domain/UserFinder.ts  — throws in domain service
export class UserFinder {
  constructor(private readonly repository: UserRepository) {}

  async find(id: string): Promise<User> {
    const user = await this.repository.search(new UserId(id));
    if (user === null) {
      throw new UserDoesNotExistError(id);
    }
    return user;
  }
}
```

**Practical heuristic:** One error class per distinct failure. Never reuse a generic "DomainError" with a message string — that forces callers to parse text, breaking the abstraction.

---

## Which Layer Should Throw?

**Intent:** Keep infrastructure errors out of the domain and domain errors out of infrastructure.

**How it works:** The domain throws typed domain errors (e.g., `UserDoesNotExistError`). The application layer (use case) catches domain errors and re-throws or translates them for the delivery layer. The infrastructure layer throws its own typed exceptions for technical failures (e.g., `TooManyMariaDbConnectionsException`) — these are never caught in the domain. The API/controller layer catches both and maps them to HTTP status codes.

**Example:**
```typescript
// application/find/UserFinder.ts — use case catches and re-raises domain error
export class UserFinder {
  constructor(private readonly repository: UserRepository) {}

  async find(id: string): Promise<UserPrimitives> {
    const user = await this.repository.search(new UserId(id));
    if (user === null) {
      throw new UserDoesNotExistError(id);  // domain error surfaces to delivery layer
    }
    return user.toPrimitives();  // map to primitives on the happy path
  }
}

// infrastructure/TooManyMariaDbConnectionsException.ts — infra-only, never reaches domain
export class TooManyMariaDbConnectionsException extends Error {
  constructor() {
    super("Too many open MariaDB connections");
  }
}
```

**Practical heuristic:** Domain errors flow upward (domain → application → delivery). Infrastructure errors stay in infrastructure or are wrapped by an anti-corruption layer before reaching the application layer.

---

## Error Handling in the Delivery Layer

**Intent:** Translate typed domain errors to protocol-appropriate responses (HTTP codes, gRPC status, etc.) without leaking domain internals.

**How it works:** The API route/controller wraps the use case call in a try/catch. It checks the error type with `instanceof` and maps each domain error to the correct HTTP status. Unrecognized errors propagate as 500. The domain never knows about HTTP.

**Example:**
```typescript
// app/api/users/[id]/route.ts
export async function GET(
  _request: NextRequest,
  { params: { id } }: { params: { id: string } },
): Promise<Response> {
  try {
    const user = await userFinder.find(id);
    return Response.json(user);
  } catch (error) {
    if (error instanceof UserDoesNotExistError) {
      return new Response(error.message, { status: 404 });
    }
    throw error; // let unknown errors propagate as 500
  }
}
```

**Practical heuristic:** Map errors to HTTP status codes in the delivery layer only. A single `switch`/`instanceof` chain at the controller boundary keeps the mapping in one place.

---

## Domain Error vs. Infrastructure Exception

**Intent:** Distinguish business rule violations (domain errors) from technical failures (infrastructure exceptions) so each is handled appropriately.

**How it works:** A domain error means the operation was invalid according to business rules ("this user does not exist", "the email address is already taken"). An infrastructure exception means the system failed to complete a technically valid operation ("database connection refused", "message broker timeout"). Domain errors are expected and must be handled gracefully. Infrastructure exceptions are unexpected and should surface as alerts/retries, not be swallowed.

**Example:**
```typescript
// Domain error — expected, user-facing
export class UserDoesNotExistError extends Error { ... }

// Infrastructure exception — unexpected, operational
export class TooManyMariaDbConnectionsException extends Error { ... }
```

**Practical heuristic:** If the error message belongs in a user-facing response body, it is a domain error. If it belongs in a monitoring alert, it is an infrastructure exception.

---

## Surfacing Errors from Aggregates

**Intent:** Let the aggregate signal invalid state transitions without returning null or using out-of-band error codes.

**How it works:** Aggregates throw typed domain errors from their methods and named constructors when invariants are violated. Value objects validate in their constructor and throw immediately. This means invalid state can never be constructed — the aggregate is either valid or throws. The use case propagates these errors up to the delivery layer.

**Example:**
```typescript
// Value object validates on construction
export class UserEmail extends StringValueObject {
  constructor(value: string) {
    super(value);
    this.ensureIsValidEmail(value);
  }

  private ensureIsValidEmail(value: string): void {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      throw new InvalidEmailError(value);
    }
  }
}

// Domain service throws when entity not found
export class UserFinder {
  async find(id: string): Promise<User> {
    const user = await this.repository.search(new UserId(id));
    if (user === null) {
      throw new UserDoesNotExistError(id);
    }
    return user;
  }
}
```

**Practical heuristic:** Never return `null` from a domain finder — throw a typed error. `null` forces callers to null-check everywhere; a typed error carries domain meaning and is caught in one place.

---

## DDD Problems: Domain Events Error Handling

Source: CodelyTV `ddd_problems-domain_events_errors_handling-course`. These are real-world problems that arise when publishing and consuming domain events in production systems.

---

## Problem: Unordered Events

**Intent:** Handle domain events that arrive out of order at the consumer without corrupting state.

**How it works:** Message brokers do not guarantee ordered delivery. A `CourseRenamed` event may arrive before the `CourseCreated` event that it depends on, causing the consumer to try to rename a course that does not yet exist. Two strategies:

1. **Last-event-has-preference:** Ignore ordering entirely; always apply the latest state. Works when the event carries the full new state (not a delta) and idempotency is already enforced. If `CourseRenamed` carries the full course name, applying it regardless of order produces a correct final state.

2. **Prefer-by-recent-date:** Compare the event's `occurredOn` timestamp against the consumer's last-applied timestamp. Discard the event if it is older than the already-applied state. Requires storing a `lastUpdatedAt` field on the consumer's projection.

**Example:**
```typescript
// Consumer stores last-applied event date and discards stale ones
async handleCourseRenamed(event: CourseRenamedDomainEvent): Promise<void> {
  const projection = await this.repo.search(new CourseId(event.aggregateId));

  if (projection && projection.updatedAt > event.occurredOn) {
    return; // stale event — already processed a newer rename
  }

  await this.repo.save(new CourseNameProjection({
    id: event.aggregateId,
    name: event.newName,
    updatedAt: event.occurredOn,
  }));
}
```

**Practical heuristic:** If your events carry full state (not deltas), last-event-has-preference is simpler and sufficient. Use prefer-by-recent-date only when events carry deltas or when the order of operations is semantically meaningful.

---

## Problem: Duplicated Events

**Intent:** Prevent duplicate domain event processing from causing incorrect side-effects.

**How it works:** At-least-once delivery means brokers will re-deliver events on consumer crashes or network failures. A counter that increments on each `UserRegistered` event will be over-counted if the event is delivered twice. Solutions:

1. **Idempotent business logic:** Design the consumer operation so applying it twice produces the same result as applying it once. A `SET` operation is idempotent; an `INCREMENT` is not. Where possible, replace increments with SET-from-event-data.

2. **Inbox / deduplication table:** Record processed message IDs in a database table (the Inbox Pattern). Before processing, check if the ID already exists — if so, skip. The check and the business effect execute in the same database transaction.

**Example (idempotent counter using Inbox):**
```typescript
async handleUserRegistered(event: UserRegisteredDomainEvent): Promise<void> {
  await this.db.transaction(async (tx) => {
    const isDuplicate = await tx.queryOne`
      SELECT 1 FROM processed_events WHERE event_id = ${event.eventId}
    `;
    if (isDuplicate) return;

    await tx.execute`
      INSERT INTO processed_events (event_id) VALUES (${event.eventId})
    `;
    await tx.execute`
      UPDATE retention.total_registered_users SET total = total + 1
    `;
  });
}
```

**Practical heuristic:** Design every event consumer to be idempotent by default. Use the Inbox table for non-idempotent operations (email sends, payment charges, counter increments).

---

## Problem: Queued / Dead-Letter Events

**Intent:** Prevent one failing event from blocking the entire consumer queue.

**How it works:** When a consumer throws an error processing an event, the broker re-queues it. If the error is permanent (malformed payload, deleted aggregate), the event blocks the queue forever. Solutions:

1. **Dead-letter queue (DLQ):** Configure the broker so that after N failed attempts, the event is moved to a separate dead-letter queue. The DLQ can be monitored, inspected, and replayed manually after fixing the root cause.

2. **Retry with exponential backoff:** Re-queue the failed event with an increasing delay between attempts. Prevents thundering-herd on transient failures (network blips, DB timeouts) without blocking the main queue.

3. **Poison-message handling:** Log the event payload and the error, then ACK (remove) the message from the queue to unblock processing of subsequent events. Use only when events are truly unprocessable and losing them is acceptable (rare).

**Practical heuristic:** Always configure a dead-letter queue before going to production. A queue with no DLQ will eventually block on the first malformed or unprocessable event.

---

## Problem: Eventual Consistency — Ensuring Events Are Always Published

**Intent:** Guarantee that domain events are published even when the application crashes between saving the aggregate and publishing the events.

**How it works:** The naive approach calls `eventBus.publish(events)` after `repository.save(aggregate)`. If the process crashes between save and publish, the events are lost permanently. The Outbox Pattern solves this:

1. Save the aggregate and write events to an `outbox` table in the same database transaction.
2. A relay process reads unpublished events from the outbox and publishes them to the broker.
3. Mark events as published after successful delivery.

This is the core production pattern for reliable domain event publishing in DDD systems. See also: **Outbox Pattern** in `enterprise-patterns.md`.

**Example:**
```typescript
// Aggregate save + outbox write in ONE transaction
async save(aggregate: AggregateRoot): Promise<void> {
  await this.db.transaction(async (tx) => {
    await tx.execute`INSERT INTO aggregates ...`;

    for (const event of aggregate.pullDomainEvents()) {
      await tx.execute`
        INSERT INTO outbox (id, event_name, payload, published_at)
        VALUES (${event.eventId}, ${event.eventName}, ${JSON.stringify(event)}, null)
      `;
    }
  });
}

// Relay — separate process, runs on a schedule
async relay(): Promise<void> {
  const pending = await this.db.query`
    SELECT * FROM outbox WHERE published_at IS NULL ORDER BY created_at
  `;
  for (const row of pending) {
    await this.eventBus.publish(row.event_name, row.payload);
    await this.db.execute`
      UPDATE outbox SET published_at = now() WHERE id = ${row.id}
    `;
  }
}
```

**Practical heuristic:** If your aggregate `save()` method calls `eventBus.publish()` directly without the Outbox Pattern, you have a reliability gap. Any deployment restart or crash silently drops unpublished events.

---

## Summary: Domain Event Problem Checklist

| Problem | Symptom | Solution |
|---|---|---|
| Unordered events | Consumer processes rename before create | Last-event-preference or prefer-by-recent-date |
| Duplicated events | Counter over-counted, emails sent twice | Idempotent logic or Inbox deduplication table |
| Queued / stuck events | One bad message blocks the whole queue | Dead-letter queue + retry with backoff |
| Lost events on crash | Events disappear after deploy/restart | Outbox Pattern + relay process |
