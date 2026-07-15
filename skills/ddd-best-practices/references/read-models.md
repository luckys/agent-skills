# Read Models and Projections

How to build the read side of CQRS: when to use read models instead of aggregates for queries, how to structure them, and how to keep them updated via projections driven by domain events. Sources: CodelyTV `use_case-aggregates_read_model_ddd-course` and `domain_modeling-projections-course`.

---

## Read Models vs. Aggregates for Queries

**Intent:** Use aggregates for writes that enforce invariants; use flat read models for queries that serve the UI.

**How it works:** Aggregates are optimized for consistency and business rule enforcement. Distinguish three read mechanisms: an aggregate-derived response DTO, a database view/materialized view, and an independently stored projection. Only the last has its own synchronization lifecycle. The write model or event history remains authoritative business state; a projection is a disposable, rebuildable query-serving copy.

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

**Practical heuristic:** If one Aggregate already contains everything the query needs, map it to a response DTO and do not call that mapping CQRS. Never expose Aggregate internals to the delivery layer. Introduce an independent projection only when its query shape, performance, ownership, or consistency lifecycle differs from the write model.

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

// Projection use case — repository performs an atomic insert/upsert
export class RetentionUserCreator {
  constructor(private readonly repository: RetentionUserRepository) {}

  async create(id: string, email: string, name: string): Promise<void> {
    const user = RetentionUser.create(id, email, name);
    await this.repository.insertIfAbsent(user);
  }
}
```

Back creation with a unique source identity and an atomic insert/upsert. `search()` followed by `save()` races when two consumers observe absence concurrently. For non-idempotent updates, store `(projection_name, event_id)` in an Inbox in the same transaction as the projection mutation.

**Practical heuristic:** Projection handlers must tolerate duplicate delivery. Prove this with database constraints, atomic operations, or a transactional Inbox; a preliminary existence query is not a correctness mechanism.

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

**How it works:** A synchronous projection is atomic only when source state and projection update share one real database transaction. Two sequential writes in the same request still have a dual-write failure window. An asynchronous projection uses a transactional Outbox, durable subscriber delivery, and an idempotent projection transaction; it trades immediate visibility for independent scaling and recovery.

**Practical heuristic:** Choose from the required consistency boundary and ownership, not latency alone. Keep a projection synchronous only when it belongs in the same transaction and database. Use durable asynchronous delivery across bounded contexts or independently operated stores, and define freshness/read-your-writes behavior explicitly.

---

## Obtaining Data Missing from an Event

Do not automatically enlarge every event or query another context during projection. Choose deliberately:

| Option | Prefer when | Main cost |
|---|---|---|
| Enrich the Integration Event | The added fact naturally belongs in the stable public contract | Contract coupling, payload growth, privacy and versioning burden |
| Query the source while handling | Same availability boundary, current state is intentionally required, replay drift is acceptable | Temporal coupling; historical replay may use today's state |
| Maintain a local supporting projection | The consumer needs autonomous, replayable facts such as post-to-owner mapping | Another projection, prerequisite ordering, bootstrap and rebuild work |

Prefer the smallest consumer-owned supporting projection for cross-context historical calculations. Translate producer events at an Anti-Corruption Layer rather than importing producer Domain Event classes as the consumer's domain model.

---

## Incremental Updates and Rebuilds

Counters, averages, bounded latest-item lists, and other incremental projections need explicit duplicate, ordering, correction, and concurrency semantics. Store source measures such as integer counts and derive ratios where possible; reconstructing totals from a floating-point average accumulates drift. Use atomic database mutations or optimistic version checks instead of concurrent load-mutate-save operations.

Every independent projection needs a rebuild contract: stable name and schema version, source cursor, checkpoint, reset/resume behavior, duplicate protection, validation criteria, cutover, and rollback. Prefer rebuilding into a shadow `vNext` store, replaying to a high-water mark, tailing live events, reconciling results, then atomically switching the read alias. Never scan mutable source state and consume live events concurrently without a defined handoff point.

A mixed read/write model is an exception, not a default. Embed denormalized display data in an Aggregate only when it is bounded, belongs to the same consistency boundary, and accepted staleness and write contention are explicit. Otherwise keep presentation fields in a dedicated projection.

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

---

## Write Use Case Structure — Command → UseCase → Repository + EventBus

**Intent:** Show the complete write path: the use case creates the aggregate, saves it, and publishes domain events through an event bus.

**How it works:** The write use case receives primitives (strings, numbers), delegates creation to the aggregate's named constructor (which records domain events internally), saves the aggregate via the repository port, and publishes the collected events via the event bus port. The aggregate's `record()` method accumulates events; `pullDomainEvents()` drains and returns them for publishing.

**Aggregate — records domain events on state change:**
```typescript
// contexts/rrss/users/domain/User.ts
import { AggregateRoot } from "../../../shared/domain/AggregateRoot";
import { UserRegisteredDomainEvent } from "./UserRegisteredDomainEvent";

export type UserPrimitives = {
  id: string;
  name: string;
  email: string;
  profilePicture: string;
  status: string;
};

export class User extends AggregateRoot {
  private constructor(
    public readonly id: UserId,
    private readonly name: UserName,
    private email: UserEmail,
    private readonly profilePicture: UserProfilePicture,
    private status: UserStatus,
  ) {
    super();
  }

  // Named constructor — records a domain event at creation
  static create(id: string, name: string, email: string, profilePicture: string): User {
    const defaultStatus = UserStatus.Active;
    const user = new User(
      new UserId(id),
      new UserName(name),
      new UserEmail(email),
      new UserProfilePicture(profilePicture),
      defaultStatus,
    );
    user.record(new UserRegisteredDomainEvent(id, name, email, profilePicture, defaultStatus));
    return user;
  }

  static fromPrimitives(primitives: UserPrimitives): User {
    return new User(
      new UserId(primitives.id),
      new UserName(primitives.name),
      new UserEmail(primitives.email),
      new UserProfilePicture(primitives.profilePicture),
      primitives.status as UserStatus,
    );
  }

  toPrimitives(): UserPrimitives {
    return {
      id: this.id.value,
      name: this.name.value,
      email: this.email.value,
      profilePicture: this.profilePicture.value,
      status: this.status,
    };
  }

  // State-changing method — records another domain event
  updateEmail(email: string): void {
    this.email = new UserEmail(email);
    this.record(new UserEmailUpdatedDomainEvent(this.id.value, email));
  }
}
```

**Domain event — carries what changed as primitives:**
```typescript
// contexts/rrss/users/domain/UserRegisteredDomainEvent.ts
import { UserDomainEvent } from "./UserDomainEvent";

export class UserRegisteredDomainEvent extends UserDomainEvent {
  static eventName = "codely.rrss.user.registered";

  constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly email: string,
    public readonly profilePicture: string,
    eventId?: string,
    occurredOn?: Date,
  ) {
    super(UserRegisteredDomainEvent.eventName, id, eventId, occurredOn);
  }

  toPrimitives() {
    return { id: this.id, name: this.name, email: this.email, profilePicture: this.profilePicture };
  }

  static fromPrimitives(aggregateId: string, eventId: string, occurredOn: Date, attributes: Record<string, unknown>) {
    return new UserRegisteredDomainEvent(
      aggregateId,
      attributes.name as string,
      attributes.email as string,
      attributes.profilePicture as string,
      eventId,
      occurredOn,
    );
  }
}
```

**Write use case — save + publish:**
```typescript
// contexts/rrss/users/application/registrar/UserRegistrar.ts
import { EventBus } from "../../../../shared/domain/event/EventBus";
import { User } from "../../domain/User";
import { UserRepository } from "../../domain/UserRepository";

export class UserRegistrar {
  constructor(
    private readonly repository: UserRepository,
    private readonly eventBus: EventBus,
  ) {}

  async registrar(id: string, name: string, email: string, profilePicture: string): Promise<void> {
    const user = User.create(id, name, email, profilePicture); // records event internally
    await this.repository.save(user);
    await this.eventBus.publish(user.pullDomainEvents()); // drains and dispatches
  }
}
```

**Practical heuristic:** The use case never constructs domain events directly — it delegates all business decisions (including which events to raise) to the aggregate's named constructor and mutation methods. The use case is the orchestrator: create, save, publish. Nothing more.
