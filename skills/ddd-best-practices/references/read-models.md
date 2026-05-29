# Read Models and Projections

How to build the read side of CQRS: when to use read models instead of aggregates for queries, how to structure them, and how to keep them updated via projections driven by domain events. Sources: CodelyTV `use_case-aggregates_read_model_ddd-course` and `domain_modeling-projections-course`.

---

## Read Models vs. Aggregates for Queries

**Intent:** Use aggregates for writes that enforce invariants; use flat read models for queries that serve the UI.

**How it works:** Aggregates are optimized for consistency and business rule enforcement. Their structure (value objects, nested entities, private fields) is opaque to the outside world and expensive to reassemble from multiple sources for display. A read model is a plain data structure — a flat DTO or a typed object with only public primitives — shaped around what a specific view or query needs. It is built by querying a repository directly, bypassing the domain model entirely. On the write side the aggregate is the source of truth; on the read side the read model is the source of truth.

**Example:**
```typescript
// Write side: aggregate enforces invariants
export class ProductReview extends AggregateRoot {
  // private fields, value objects, business rules...
  toPrimitives(): ProductReviewPrimitives { ... }
}

// Read side: use case returns flat primitives, not the aggregate
export class ProductReviewsByUserSearcher {
  constructor(private readonly repository: ProductReviewRepository) {}

  async search(userId: string): Promise<Primitives<ProductReview>[]> {
    return (await this.repository.searchByUser(new UserId(userId)))
      .map((review) => review.toPrimitives());
  }
}
```

**Practical heuristic:** If a use case only reads data and returns a response, call `.toPrimitives()` on the aggregate and return that flat object. Never expose aggregate internals (value objects, methods) to the delivery layer.

---

## Use Case Structure for Reads

**Intent:** Keep read use cases thin — they fetch and map, nothing more.

**How it works:** A read use case receives a query parameter, creates the typed identifier, delegates to the repository, and maps results to primitives. It never contains business logic, never modifies state, and never raises domain events. The use case is the single place that converts between the domain representation and the primitive representation consumed by the delivery layer.

**Example:**
```typescript
// application/find/UserFinder.ts — read use case
export class UserFinder {
  constructor(private readonly repository: UserRepository) {}

  async find(id: string): Promise<UserPrimitives> {
    const user = await this.repository.search(new UserId(id));
    if (user === null) {
      throw new UserDoesNotExistError(id);
    }
    return user.toPrimitives();  // returns flat object, not the aggregate
  }
}
```

**Practical heuristic:** A read use case should be expressible in fewer than 10 lines. If it is longer, the logic belongs either in the repository query or in a dedicated projection.

---

## When to Build a Dedicated Read Model

**Intent:** Recognize when `.toPrimitives()` on an aggregate is insufficient and a separate read model is needed.

**How it works:** When a query requires combining data from multiple aggregates, crossing bounded context boundaries, or joining data in a way that the aggregate's structure does not support, a dedicated read model (projection) is the right tool. The read model is stored in a separate table or collection optimized for the query — denormalized, precomputed, and shaped exactly for the consumer. It is kept in sync by subscribing to domain events from the write side.

**When to use a dedicated read model:**
- A query needs fields from more than one aggregate type.
- A query crosses a bounded context boundary.
- A query requires aggregated/computed values (counts, averages, latest-of).
- The aggregate's structure is too complex to serialize efficiently for the client.

**When NOT to use a dedicated read model:**
- A simple `.toPrimitives()` on a single aggregate satisfies the query.
- The read/write load is not high enough to justify the synchronization overhead.
- The team cannot yet afford eventual consistency in the read path.

**Practical heuristic:** If you find yourself loading multiple aggregates and manually assembling a response DTO in a use case, that is the signal to introduce a dedicated read model with a projection.

---

## Projections from Domain Events

**Intent:** Keep a read model up to date by reacting to domain events emitted by the write side.

**How it works:** A projection handler (event subscriber) listens for specific domain events. When an event arrives, it updates the read model stored in a separate read store. The handler is a thin application service — it calls a use case or repository method on the read side. The read model entity itself is a plain object (not an aggregate), mutable for update operations, and stored without invariant enforcement. Because the projection is driven by events, it is eventually consistent with the write side.

**Example:**
```typescript
// Projection handler — subscribes to domain event, updates read model
export class CreateRetentionUserOnUserRegistered
  implements DomainEventSubscriber<UserDomainEvent>
{
  constructor(private readonly creator: RetentionUserCreator) {}

  async on(event: UserRegisteredDomainEvent): Promise<void> {
    await this.creator.create(event.id, event.email, event.name);
  }

  subscribedTo(): DomainEventClass[] {
    return [UserRegisteredDomainEvent];
  }

  name(): string {
    return "codely.retention.create_retention_user_on_user_registered";
  }
}

// Read model entity — flat, no invariants
export class RetentionUser {
  constructor(
    public readonly id: UserId,
    public email: string,
    public readonly name: string,
  ) {}

  static create(id: string, email: string, name: string): RetentionUser {
    return new RetentionUser(new UserId(id), email, name);
  }

  updateEmail(email: string): void {
    this.email = email;
  }

  toPrimitives(): RetentionUserPrimitives {
    return { id: this.id.value, email: this.email, name: this.name };
  }
}

// Projection use case — upserts the read model
export class RetentionUserCreator {
  constructor(private readonly repository: RetentionUserRepository) {}

  async create(id: string, email: string, name: string): Promise<void> {
    if (await this.repository.search(new UserId(id))) {
      return; // idempotent: already created
    }
    const user = RetentionUser.create(id, email, name);
    await this.repository.save(user);
  }
}
```

**Practical heuristic:** Projection handlers must be idempotent. Events can be delivered more than once; the handler must produce the same final state regardless of how many times it processes the same event.

---

## Updating a Projection on State Change

**Intent:** React to subsequent domain events to keep the read model current after initial creation.

**How it works:** Each state-changing domain event (e.g., `UserEmailUpdatedDomainEvent`) has a matching projection handler that finds the read model entry and applies the change. The read model is mutable — unlike the aggregate, there is no invariant to enforce here, only data to update. The handler follows the same `DomainEventSubscriber` contract: `subscribedTo()` declares the event type, `on()` applies the change.

**Example:**
```typescript
export class UpdateRetentionUserEmailOnUserEmailUpdated
  implements DomainEventSubscriber<UserDomainEvent>
{
  constructor(private readonly updater: RetentionUserEmailUpdater) {}

  async on(event: UserEmailUpdatedDomainEvent): Promise<void> {
    await this.updater.update(event.id, event.email);
  }

  subscribedTo(): DomainEventClass[] {
    return [UserEmailUpdatedDomainEvent];
  }

  name(): string {
    return "codely.retention.update_retention_user_email_on_user_email_updated";
  }
}
```

**Practical heuristic:** Name the subscriber class after the action it performs and the event it reacts to: `<Action>On<EventName>`. This naming makes the event-handler mapping self-documenting.

---

## Synchronous vs. Asynchronous Projections

**Intent:** Choose between updating the projection in the same transaction as the write or in a background process driven by an event bus.

**How it works:** Synchronous projection: the use case saves the aggregate and immediately updates the projection in the same request (or the same transaction). The read side is always consistent with the write side. The tradeoff is increased latency on the write path. Asynchronous projection: the use case saves the aggregate and publishes events to a bus. A background subscriber updates the projection when the event is consumed. The write path is fast but the read side lags behind (eventual consistency). Use synchronous projections when the UI must immediately reflect the write; use asynchronous projections when the read side can tolerate a delay or when the projection is in a different bounded context entirely.

**Practical heuristic:** Start with synchronous projections. Switch to asynchronous only when write latency becomes a measurable problem or when the projection lives in a separate bounded context that must decouple its lifecycle from the write side.

---

## Read Model Naming Conventions

**Intent:** Name read model classes and files to distinguish them clearly from aggregates.

**How it works:** A read model class should include the bounded context or the query purpose in its name — for example, `RetentionUser` (read model for the Retention bounded context) vs. `User` (aggregate in the RRSS context). Both may represent the same real-world user but hold different fields and serve different purposes. The projection handler name follows the pattern `<Action>On<EventName>` to make event-to-handler wiring self-documenting.

**Example:**
- Aggregate (write side): `User` in `contexts/rrss/users/domain/`
- Read model (retention context): `RetentionUser` in `contexts/retention/users/domain/`
- Handler: `CreateRetentionUserOnUserRegistered`
- Handler: `UpdateRetentionUserEmailOnUserEmailUpdated`

**Practical heuristic:** If you are tempted to add a query-specific field to an aggregate, stop — that field belongs in a read model, not in the aggregate that enforces business rules.
