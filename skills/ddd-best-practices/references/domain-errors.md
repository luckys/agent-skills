# Domain Errors

How to model failures that happen inside the domain in a maintainable, explicit, and layer-appropriate way. Source: CodelyTV `domain_modeling-errors-course`.

---

## DomainError Abstract Base Class

**Intent:** Provide a common base for all domain errors that enables type-safe catch blocks, structured serialization for API responses, and infrastructure-level error mapping without parsing message strings.

**How it works:** `DomainError` extends `Error` and declares a stable machine-readable `type`. Expose only explicitly approved public context to delivery; keep diagnostic fields and sensitive values in server-side observability.

**Example:**
```typescript
// shared/domain/DomainError.ts
export abstract class DomainError extends Error {
  abstract type: string;
  abstract message: string;

  toPublicPrimitives(): { type: string; description: string; data: Record<string, unknown> } {
    return {
      type: this.type,
      description: this.publicDescription(),
      data: this.publicContext(),
    };
  }

  protected publicDescription(): string { return "The request could not be completed"; }
  protected publicContext(): Record<string, unknown> { return {}; }
}

// Concrete domain error — extends DomainError, not plain Error
export class UserDoesNotExistError extends DomainError {
  type = "UserDoesNotExistError";
  message: string;

  constructor(public readonly id: string) {
    super(`The user ${id} does not exist`);
    this.message = `The user ${id} does not exist`;
  }
}
```

**Why `type` instead of relying on `constructor.name`:** Minification renames classes in production builds. A stable string literal in `type` survives bundling and is the production-safe mapping key.

**Practical heuristic:** Use a stable domain error contract for failures callers must distinguish. Infrastructure should not translate business failures into database or transport terminology; let application/delivery boundaries map them deliberately.

---

## Typed Domain Errors (Exceptions as Domain Concepts)

**Intent:** Give each domain failure its own type so callers can distinguish between them without parsing error messages.

**How it works:** Create a dedicated type when callers need to distinguish, map, recover from, or attach structured context to a failure. Name it after the domain concept that failed, not the technical action ("UserDoesNotExistError", not "NotFoundException"). It may be an exception, `Result` error variant, or discriminated union according to the expected control flow.

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

**Practical heuristic:** Give recoverably different failures stable machine-readable types or codes. Do not force callers to parse messages, but do not create a class for every programmer assertion when no caller can handle it differently.

---

## Which Layer Should Throw?

**Intent:** Keep infrastructure errors out of the domain and domain errors out of infrastructure.

**How it works:** The domain reports typed business failures through exceptions or result values. The application layer orchestrates and translates at system boundaries when needed. Infrastructure reports technical failures without importing domain policy, and the domain never catches infrastructure exceptions. Delivery maps application outcomes to protocol semantics.

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

**Practical heuristic:** Preserve failure ownership while errors move upward. Translate at boundaries; do not relabel a database outage as a business rejection or leak SQL details to delivery.

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

**How it works:** A domain error means the operation was invalid according to business rules ("this user does not exist", "the email address is already taken"). An infrastructure exception means the system failed to complete a technically valid operation ("database connection refused", "message broker timeout"). Domain errors usually have an explicit caller-facing outcome. Infrastructure exceptions require operational handling such as retry, fallback, or alerting and must not be swallowed.

**Example:**
```typescript
// Domain error — expected, user-facing
export class UserDoesNotExistError extends Error { ... }

// Infrastructure exception — unexpected, operational
export class TooManyMariaDbConnectionsException extends Error { ... }
```

**Practical heuristic:** Classify by ownership and recovery, not message wording. A domain failure may still need redaction, and an infrastructure failure may produce a safe user-facing response while retaining technical detail only in observability.

---

## Surfacing Errors from Aggregates

**Intent:** Let the aggregate signal invalid state transitions without returning null or using out-of-band error codes.

**How it works:** Aggregates and Value Objects reject invalid transitions or construction through their chosen typed failure mechanism. Constructors/factories may throw for trusted domain code; parsers may return `Result` when invalid external input is expected. Every successful public construction path must produce a valid value.

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

**Practical heuristic:** Make absence semantics explicit in the operation name and type. A `search`/`tryFind` may return optional absence; a `getRequired`/`findOrFail` reports a typed failure. Choose one contract instead of surprising callers.

---

## Delivery Layer Helpers: executeWithErrorHandling and executeWithMappedErrorHandling

**Intent:** Eliminate repetitive try/catch boilerplate in API route handlers by centralizing domain-error-to-HTTP-status mapping in two reusable infrastructure utilities.

**How it works:** Both helpers wrap the use-case call in a try/catch. If the caught error is a `DomainError`, they apply a mapping to produce the correct HTTP status. Unrecognized errors fall through as 500.

`executeWithErrorHandling` accepts a callback `onError(error)` that returns a `NextResponse | void` — flexible for single-controller customization. `executeWithMappedErrorHandling` accepts a record `{ DomainErrorType: httpStatus }` keyed by the stable `error.type` value — better for controllers that handle multiple error types uniformly.

**Example:**
```typescript
// executeWithErrorHandling — flexible per-handler callback
export async function executeWithErrorHandling(
  fn: () => Promise<NextResponse>,
  onError: (error: DomainError) => NextResponse | void = () => undefined,
): Promise<NextResponse> {
  try {
    return await fn();
  } catch (error: unknown) {
    if (error instanceof DomainError) {
      const response = onError(error);
      if (response) return response;
    }
    return HttpNextResponse.internalServerError();
  }
}

// executeWithMappedErrorHandling — table-driven mapping
export async function executeWithMappedErrorHandling(
  fn: () => Promise<NextResponse>,
  errorMap: Record<string, number> = {},
): Promise<NextResponse> {
  try {
    return await fn();
  } catch (error: unknown) {
    if (error instanceof DomainError && errorMap[error.type]) {
      return HttpNextResponse.domainError(error, errorMap[error.type]);
    }
    return HttpNextResponse.internalServerError();
  }
}

// Usage in a Next.js route handler
export async function GET(_req: NextRequest, { params }: { params: { id: string } }) {
  return executeWithMappedErrorHandling(
    () => userFinder.find(params.id).then((u) => HttpNextResponse.ok(u)),
    { UserDoesNotExistError: 404 },
  );
}
```

**Practical heuristic:** Use `executeWithMappedErrorHandling` as the default — the error map is self-documenting and easy to extend. Switch to `executeWithErrorHandling` only when the handler needs custom response bodies that go beyond a status code.

---

## Functional Error Handling: Either and Result Types

**Intent:** Return errors as values instead of throwing exceptions, making the error path explicit in the type signature and enabling composition without try/catch.

**How it works:** Source: CodelyTV `domain_modeling-errors-course` chapter 05.

`Either<L, R>` is a generic discriminated union: `Left<L>` carries the error case, `Right<R>` carries the success case. It is fully generic — neither side is constrained to a specific base class. `Result<O, E extends DomainError>` is a narrowed variant where the error side is constrained to `DomainError` — useful when you only need to model domain errors, not arbitrary left types.

Both expose `map()`, `fold()`, `isLeft()/isRight()` (or `isOk()/isError()`), and safe unwrapping via `get()` and `getError()`/`getLeft()`.

**Full Either implementation:**
```typescript
type Left<L> = { kind: "left"; leftValue: L };
type Right<R> = { kind: "right"; rightValue: R };

export class Either<L, R> {
  private constructor(private readonly value: Left<L> | Right<R>) {}

  static left<L, R>(value: L): Either<L, R> {
    return new Either<L, R>({ kind: "left", leftValue: value });
  }

  static right<L, R>(value: R): Either<L, R> {
    return new Either<L, R>({ kind: "right", rightValue: value });
  }

  isLeft(): boolean { return this.value.kind === "left"; }
  isRight(): boolean { return this.value.kind === "right"; }

  get(): R {
    return this.fold(
      () => { throw new Error("Cannot get right value from Left Either"); },
      (r) => r,
    );
  }

  getLeft(): L {
    return this.fold(
      (l) => l,
      () => { throw new Error("Cannot get left value from Right Either"); },
    );
  }

  map<T>(fn: (r: R) => T): Either<L, T> {
    return this.fold(
      (l) => Either.left(l),
      (r) => Either.right(fn(r)),
    );
  }

  fold<LR, RR>(leftFn: (l: L) => LR, rightFn: (r: R) => RR): LR | RR {
    switch (this.value.kind) {
      case "left":  return leftFn(this.value.leftValue);
      case "right": return rightFn(this.value.rightValue);
    }
  }
}
```

**Full Result implementation (domain-error constrained):**
```typescript
import { DomainError } from "./DomainError";

type Ok<O> = { kind: "ok"; okValue: O };
type Err<E extends DomainError> = { kind: "error"; errorValue: E };

export class Result<O, E extends DomainError> {
  private constructor(private readonly value: Ok<O> | Err<E>) {}

  static ok<O, E extends DomainError>(value: O): Result<O, E> {
    return new Result<O, E>({ kind: "ok", okValue: value });
  }

  static error<O, E extends DomainError>(value: E): Result<O, E> {
    return new Result<O, E>({ kind: "error", errorValue: value });
  }

  isOk(): boolean { return this.value.kind === "ok"; }
  isError(): boolean { return this.value.kind === "error"; }

  get(): O {
    return this.fold(
      (ok) => ok,
      () => { throw new Error("Cannot get ok value from error Result"); },
    );
  }

  getError(): E {
    return this.fold(
      () => { throw new Error("Cannot get error value from ok Result"); },
      (err) => err,
    );
  }

  map<T>(fn: (ok: O) => T): Result<T, E> {
    return this.fold(
      (ok) => Result.ok(fn(ok)),
      (err) => Result.error(err),
    );
  }

  fold<ER, OR>(okFn: (ok: O) => OR, errorFn: (err: E) => ER): ER | OR {
    switch (this.value.kind) {
      case "ok":    return okFn(this.value.okValue);
      case "error": return errorFn(this.value.errorValue);
    }
  }
}
```

**Either vs Result — when to use which:**
| | `Either<L, R>` | `Result<O, E extends DomainError>` |
|---|---|---|
| Error type constraint | Unconstrained | Must extend `DomainError` |
| Use when | Mixed error types, FP pipelines | Pure domain-error returns |
| Interop | General purpose | Works directly with an explicitly redacted `DomainError.toPublicPrimitives()` |

**When to prefer throw vs. return Either/Result:**
- **Throw (default):** Use exceptions for failures that are exceptional — invariant violations, infrastructure errors. The delivery layer catches and maps to HTTP status. This is the pattern used throughout the CodelyTV courses.
- **Return Either/Result:** Use when the caller must handle both paths in the same function without try/catch — common in functional pipelines, validation chains, or when multiple errors can accumulate. Avoid mixing: pick one style per bounded context and be consistent.

**Practical heuristic:** Start with throw-based domain errors. Introduce `Either` or `Result` only when try/catch nesting makes the code unreadable or when the caller genuinely needs to compose multiple fallible operations without exception control flow.

---

## DDD Problems: Domain Events Error Handling

Source: CodelyTV `ddd_problems-domain_events_errors_handling-course`. These are real-world problems that arise when publishing and consuming domain events in production systems.

---

## Problem: Unordered Events

**Intent:** Handle domain events that arrive out of order at the consumer without corrupting state.

**How it works:** Brokers provide ordering only within documented scopes such as a partition or queue. A `CourseRenamed` event may arrive before the `CourseCreated` event when routing, retries, or parallel consumers differ. Carry an Aggregate version/source sequence, partition related messages by Aggregate when order matters, and update projections with an atomic compare-and-set.

1. **Source-version guard:** Store the last applied source version and accept only the expected/newer version according to projection policy. Buffer gaps or rebuild when every transition matters.

2. **Commutative/current-state projection:** Apply messages in any order only when the operation is mathematically commutative or the message carries an authoritative source version and complete consumer-required state. Do not use wall-clock time as causal order across machines.

**Example:**
```typescript
// Consumer stores last-applied event date and discards stale ones
async handleCourseRenamed(event: CourseRenamedDomainEvent): Promise<void> {
  await this.repo.upsertIfNewer({
    id: event.aggregateId,
    name: event.newName,
    sourceVersion: event.aggregateVersion,
  }); // one conditional statement: WHERE source_version < incoming version
}
```

**Practical heuristic:** Define ordering scope and source sequence explicitly. Event time may drive behavior only when the domain itself defines event-time precedence.

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

**Practical heuristic:** Design every event consumer to be idempotent by default. Use a transactional Inbox for local database effects such as counters. For email or payment, use the provider's idempotency key or persist a durable intent and reconcile uncertain outcomes; an Inbox cannot make a remote call atomic with your database.

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

This is the core production pattern for reliable domain event publishing in DDD systems. Use `infrastructure-design` for Outbox, retries, and delivery implementation.

**Example:**
```typescript
// Aggregate save + outbox write in ONE transaction
async save(aggregate: AggregateRoot): Promise<void> {
  const pending = aggregate.pendingDomainEvents();
  const messages = toIntegrationMessages(pending);
  await this.db.transaction(async (tx) => {
    await tx.execute`INSERT INTO aggregates ...`;

    for (const message of messages) {
      await tx.execute`
        INSERT INTO outbox (id, event_name, payload, published_at)
        VALUES (${message.id}, ${message.type}, ${JSON.stringify(message)}, null)
      `;
    }
  });
  aggregate.clearDomainEvents(pending);
}
```

The relay must claim rows with locking or leases, preserve each message ID across retries, and complete claims conditionally. Multiple workers must not select the same unclaimed batch concurrently; use the dedicated infrastructure event-delivery guidance for the relay implementation.

**Practical heuristic:** If your aggregate `save()` method calls `eventBus.publish()` directly without the Outbox Pattern, you have a reliability gap. Any deployment restart or crash silently drops unpublished events.

---

## Summary: Domain Event Problem Checklist

| Problem | Symptom | Solution |
|---|---|---|
| Unordered events | Consumer processes rename before create | Partition by source identity + source version/CAS; buffer gaps when transitions are required |
| Duplicated events | Counter over-counted, emails sent twice | Idempotent logic or Inbox deduplication table |
| Queued / stuck events | One bad message blocks the whole queue | Dead-letter queue + retry with backoff |
| Lost events on crash | Events disappear after deploy/restart | Outbox Pattern + relay process |
