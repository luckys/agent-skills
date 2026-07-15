# CQRS and Event-Driven Patterns

Patterns for separating reads from writes, communicating through events, and modeling time-based business processes. These complement tactical DDD patterns and enable scalability without sacrificing domain model integrity.

---

## CQRS (Command Query Responsibility Segregation)

**Intent:** Separate the model used to mutate state (write side) from the model used to answer queries (read side).

**How it works:** Commands go through the domain model, enforcing all business rules and invariants via aggregates. Queries bypass the domain model entirely and hit a purpose-built read model — typically a flat, denormalized projection optimized for the UI or reporting layer. The read model is updated asynchronously by subscribing to domain events emitted by the write side. This makes the two sides eventually consistent.

**When to use:**
- The system has fundamentally different read and write workloads (heavy reporting, dashboards, search views alongside a rich command model).
- The domain model's structure is too complex to serve query requirements efficiently (e.g., aggregates that hide data needed for displays).
- You are already using event sourcing — CQRS is a natural complement because projections must be built from events anyway.
- Bounded contexts that need multiple independent read representations of the same data.

**When NOT to use:**
- Simple CRUD systems where read and write shapes are nearly identical.
- Small teams where the operational overhead of maintaining two models outweighs the benefit.
- Early-stage products where the query requirements are still unknown and premature optimization is costly.
- Supporting or generic subdomains with simple business logic — transaction script or active record suffices.

**Key trade-off:** Read models are eventually consistent with the write model. Callers must tolerate a window of staleness after a command completes. Absolute consistency across both sides requires either synchronous projection (negates the scalability benefit) or special UI handling.

**Related patterns:** Event Sourcing (events are the natural feed for projections), Domain Events (carry the data needed to update read models), Outbox Pattern (ensures events reach the projection engine reliably).

**Practical heuristic:** If a query requires joining more than 3 aggregates or crosses bounded context boundaries, that query does not belong in the domain model — build a dedicated read model projection for it.

---

## Event Sourcing

**Intent:** Persist an aggregate's state as an immutable, append-only sequence of domain events rather than storing the current state snapshot.

**How it works:** Every state transition in an aggregate produces a domain event that is appended to the event store. To restore an aggregate, the system replays all of its events in order, applying each one to rebuild current state. The event store becomes the single source of truth. Projections (read models) are built by consuming the event stream and computing derived state. Because the full history is preserved, past states can be reconstructed and the log provides a built-in audit trail.

**When to use:**
- The domain requires a deep, reliable audit log (financial transactions, compliance, legal records).
- Business stakeholders need to analyze behavior over time or reconstruct historical state.
- The domain model is complex enough to warrant it (i.e., already applying the domain model pattern).
- The subdomain tracks monetary transactions or is legally obligated to record every change.
- You need to support temporal queries: "What was the state of X at time T?"

**When NOT to use:**
- Simple subdomains (transaction script, active record) — the overhead is unjustified.
- Teams without experience managing event schema evolution — versioning events is non-trivial.
- Systems where query performance is critical and you cannot afford projection rebuilds.
- When the business has no interest in history — forcing event sourcing for its own sake adds accidental complexity.

**Key trade-off:** Event sourcing solves the audit log and temporal query problems elegantly, but introduces significant complexity: event schema versioning, projection rebuild time, eventual consistency between the event store and read models, and a steep learning curve for developers unfamiliar with the pattern.

**Related patterns:** CQRS (projections are the read side), Domain Events (the events stored are domain events), Outbox Pattern (used to reliably publish stored events to external consumers).

**Practical heuristic:** Ask three questions before adopting event sourcing: Does this subdomain track money or require an audit log? Does the business want time-travel queries? Is the business logic complex enough to already need a domain model? If all three are yes, event sourcing is appropriate. If only one or two, a domain model with conventional persistence is likely sufficient.

---

## Domain Events vs. Integration Events

**Intent:** Distinguish between events that communicate state changes within a bounded context (domain events) and events that communicate across bounded context boundaries (integration events).

**How it works:** A domain event is part of the ubiquitous language of a bounded context. It is named from the domain's perspective ("CampaignActivated", "OrderPlaced") and carries the information needed for other aggregates or sagas within the same context to react. An integration event is a message published to a message bus for consumption by other bounded contexts or external systems. Integration events are intentionally decoupled from the domain model's internal representation — they use a stable public contract to avoid coupling consumers to internal implementation details. In practice, a domain event handler translates the domain event into an integration event before publishing externally.

**When to use:**
- Use domain events for intra-context reactions (triggering sagas, updating projections within the same bounded context).
- Use integration events for inter-context communication (notifying other bounded contexts, triggering processes in external systems).

**When NOT to use:**
- Do not publish raw domain events directly across bounded context boundaries — this couples consumers to your internal model.
- Do not use integration events for enforcing business invariants within a single aggregate — that belongs inside the aggregate boundary.

**Key trade-off:** The separation requires an explicit translation step (domain event → integration event), which adds a layer of indirection but protects the public API from internal model changes. Skipping this translation creates tight coupling that makes future refactoring expensive.

**Related patterns:** Outbox Pattern (ensures integration events are published reliably), CQRS (domain events feed projections on the read side), Saga (domain events trigger saga steps).

**Practical heuristic:** If an event needs to cross a bounded context boundary, define a separate integration event type for it — do not reuse the internal domain event class.

---

## Event Storming

**Intent:** A collaborative workshop technique that uses domain events to rapidly explore, map, and align understanding of a business domain across technical and non-technical stakeholders.

**How it works:** Participants gather in front of a large modeling surface (physical or virtual) using color-coded sticky notes. Domain events (things that happened, in past tense — orange) are placed first in rough chronological order. The group then identifies commands (blue — actions that cause events), policies (lilac — automated rules triggered by events), read models (green — information needed to decide which command to issue), external systems (pink), and finally aggregates (yellow — the clusters of domain logic that own the events). The process reveals gaps, conflicts, and complexities in domain knowledge that written specifications miss. EventStorming runs in three variants: Big Picture (entire domain, all stakeholders, hours), Process Level (one workflow in depth), and Design Level (aggregate and bounded context boundaries, for developers).

**When to use:**
- Kickstarting a new project or feature with diverse stakeholders who share implicit knowledge.
- Identifying bounded contexts and aggregate boundaries during strategic design.
- Discovering pain points, bottlenecks, and unclear business rules in an existing system.
- Onboarding a new team to a complex legacy domain.

**When NOT to use:**
- Small, well-understood domains where the overhead of the workshop exceeds its value.
- Teams working alone on a subdomain they already deeply understand.
- When key domain experts are unavailable — EventStorming without the right participants produces incomplete models.

**Key trade-off:** EventStorming produces a shared mental model and surfaces complexity quickly, but the output (sticky notes) must be translated into formal artifacts (aggregates, bounded contexts, ubiquitous language) to be useful in implementation. The session is only as good as the domain experts in the room.

**Related patterns:** Bounded Contexts (a primary output of Big Picture EventStorming), Aggregates (identified in Design Level EventStorming), Domain Events (the core language of the workshop), Saga (process-level flows often map directly to sagas).

**Practical heuristic:** Run a Big Picture EventStorming before committing to any bounded context boundaries. The events and pain points that emerge will reveal where the natural seams in the domain lie better than any upfront analysis.

---

## Saga / Process Manager

**Intent:** Coordinate a multi-step business process that spans multiple aggregates or bounded contexts, maintaining eventual consistency across all participants.

**How it works:** A saga reacts to domain events by issuing commands to other aggregates or services. It is stateless in the simplest case — it is instantiated by a triggering event and executes a linear sequence of event-to-command mappings (e.g., CampaignActivated → PublishAdvertisement, PublishingConfirmed → TrackConfirmation). A process manager is the stateful variant: it has an explicit identity, persists its execution state, and implements business logic to determine which step to take next based on that state. The process manager is implemented as an aggregate (often event-sourced) that subscribes to events, transitions its internal state, and publishes CommandIssuedEvent entries that an outbox relay executes. All participants remain only eventually consistent — no two commands in a saga are atomic.

**When to use:**
- Business processes that span multiple aggregates and cannot be placed within a single aggregate boundary (Saga for linear flows).
- Complex, branching business workflows with conditional logic based on intermediate results (Process Manager).
- Recovering from partial failures across distributed components through compensating transactions.

**When NOT to use:**
- When the operations actually belong inside a single aggregate — use proper aggregate boundaries first. Do not use sagas to compensate for incorrectly split aggregates.
- When strong consistency is required — sagas are eventually consistent by design.
- For simple intra-aggregate coordination — the aggregate handles this internally.

**Key trade-off:** Sagas enable multi-component coordination without distributed transactions, but the eventual consistency model means the system can be in inconsistent intermediate states. Compensating transactions are complex to design and test, and failures at any step require careful recovery logic.

**Related patterns:** Domain Events (the signals sagas listen to), Outbox Pattern (ensures saga-issued commands are executed reliably), Process Manager (stateful extension of the saga pattern), Aggregates (sagas coordinate between aggregate boundaries).

**Practical heuristic:** If you find yourself needing strongly consistent data across two aggregates managed by a saga, review the boundary with `aggregates.md` before reaching for coordination. A saga can manage recovery and eventual consistency, but cannot make separate commits atomic.

---

## Outbox Pattern

**Intent:** Guarantee that domain or integration events are published to external systems reliably, even if the process fails after committing a database transaction but before sending the message.

**How it works:** Instead of publishing directly to a message bus after the domain state change, the application or Unit of Work persists Aggregate state and outgoing messages in the same database transaction, typically using an `outbox` table. A separate relay polls the outbox, publishes unpublished messages, and marks them as sent. The shared database transaction makes state and durable handoff atomic. Relay retries can publish duplicates, so delivery is normally at least once and consumers must be idempotent or deduplicate by message ID. In event-sourced systems, the event store can serve as the durable source for the relay.

**When to use:**
- Any time you need to publish events or commands to an external system as a result of a domain state change.
- Saga and process manager implementations where command execution must survive process restarts.
- Microservices that need at-least-once delivery guarantees for inter-service messages.

**When NOT to use:**
- Intra-process, in-memory event dispatch (domain events within a single bounded context that do not leave the process boundary).
- When the message broker already provides transactional publish semantics with your database (rare, but some systems support this natively).

**Key trade-off:** The outbox pattern solves the dual-write problem at the cost of added operational complexity: the outbox table must be polled or tailed, relay infrastructure must be maintained, and consumers must implement idempotency to handle duplicate deliveries.

**Related patterns:** Domain Events and Integration Events (what the outbox publishes), Saga / Process Manager (outbox is the standard delivery mechanism for saga-issued commands), Event Sourcing (event store doubles as the outbox in event-sourced systems).

**Practical heuristic:** Any time you write to a database and need to send a message to another service in the same operation, use the outbox pattern. Avoid the temptation to publish directly in the service layer — a process crash between commit and publish will silently lose the message.

---

## Raising Domain Events from Aggregates

**Intent:** Let the aggregate itself record domain events so the use case never needs to know which events to create.

**How it works:** The `AggregateRoot` base class maintains a private `domainEvents` list. Aggregates call `this.record(event)` inside named constructors or mutating methods — never inside the regular constructor. After persisting the aggregate, the use case calls `aggregate.pullDomainEvents()` to drain the list and hands the events to the `EventBus`. The pull clears the list atomically, making repeated calls safe.

**Example:**
```typescript
// AggregateRoot base class
export abstract class AggregateRoot {
  private domainEvents: DomainEvent[] = [];

  pullDomainEvents(): DomainEvent[] {
    const events = this.domainEvents;
    this.domainEvents = [];
    return events;
  }

  protected record(event: DomainEvent): void {
    this.domainEvents.push(event);
  }
}

// Aggregate named constructor raises the event
export class User extends AggregateRoot {
  static create(id: string, name: string, email: string, profilePicture: string): User {
    const user = new User(new UserId(id), new UserName(name), new UserEmail(email), ...);
    user.record(new UserRegisteredDomainEvent(id, name, email, profilePicture));
    return user;
  }

  updateEmail(email: string): void {
    this.email = new UserEmail(email);
    this.record(new UserEmailUpdatedDomainEvent(this.id.value, email));
  }
}

// Use case publishes after saving
export class UserRegistrar {
  constructor(
    private readonly repository: UserRepository,
    private readonly eventBus: EventBus,
  ) {}

  async registrar(id: string, name: string, email: string, profilePicture: string): Promise<void> {
    const user = User.create(id, name, email, profilePicture);
    await this.repository.save(user);
    await this.eventBus.publish(user.pullDomainEvents());
  }
}
```

**Practical heuristic:** Record events inside named constructors and mutating methods — never in the plain constructor. The use case only persists and publishes; it never constructs events manually.

---

## EventBus Interface and DomainEventSubscriber

**Intent:** Decouple the domain from event transport infrastructure and define a standard contract for reacting to domain events.

**How it works:** The `EventBus` interface lives in the domain layer alongside `DomainEvent`. Infrastructure provides concrete implementations (`InMemoryEventBus`, RabbitMQ adapter, etc.). The use case receives the bus via constructor injection, so tests can swap in a mock without touching real infrastructure.

The `DomainEventSubscriber<T>` interface defines how handlers declare which events they care about. Each subscriber implements `subscribedTo()` — returning the event class constructors it handles — and `on(event)` — the handler called on dispatch. The `InMemoryEventBus` builds a `Map<eventName, handlers[]>` at startup by iterating all registered subscribers.

**Example — complete wiring:**
```typescript
// Domain port
export interface EventBus {
  publish(events: DomainEvent[]): Promise<void>;
}

// Domain port — subscriber contract
export interface DomainEventSubscriber<T extends DomainEvent> {
  on(domainEvent: T): Promise<void>;
  subscribedTo(): DomainEventName<T>[];  // array of event class constructors
}

// Concrete event
export class UserRegisteredDomainEvent extends DomainEvent {
  constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly email: string,
    public readonly profilePicture: string,
  ) {
    super();
  }
}

// Infrastructure — InMemoryEventBus registers subscribers at construction time
export class InMemoryEventBus implements EventBus {
  private readonly subscriptions: Map<string, Function[]> = new Map();

  constructor(subscribers: DomainEventSubscriber<DomainEvent>[]) {
    this.registerSubscribers(subscribers);
  }

  async publish(events: DomainEvent[]): Promise<void> {
    const executions: unknown[] = [];

    events.forEach((event) => {
      const subscribers = this.subscriptions.get(event.eventName);
      if (subscribers) {
        subscribers.forEach((subscriber) => {
          executions.push(subscriber(event));
        });
      }
    });

    await Promise.all(executions).catch((error) => {
      console.error("Executing subscriptions:", error);
    });
  }

  private registerSubscribers(subscribers: DomainEventSubscriber<DomainEvent>[]): void {
    subscribers.forEach((subscriber) => {
      subscriber.subscribedTo().forEach((event) => {
        this.subscribe(event.eventName, subscriber);
      });
    });
  }

  private subscribe(eventName: string, subscriber: DomainEventSubscriber<DomainEvent>): void {
    const current = this.subscriptions.get(eventName);
    const handler = subscriber.on.bind(subscriber);
    if (current) {
      current.push(handler);
    } else {
      this.subscriptions.set(eventName, [handler]);
    }
  }
}
```

**Key design decisions in `InMemoryEventBus`:**
- Subscribers are registered at construction time — no runtime `addSubscriber()` calls.
- The `Map` key is `event.eventName` (a string constant on the event class), not the class reference — this survives serialization boundaries.
- `Promise.all` dispatches all handlers concurrently per `publish()` call. Errors in one handler do not block others but are logged.
- The same `publish()` signature works for both in-memory and broker-backed implementations — the use case never changes.

**Practical heuristic:** Keep `EventBus`, `DomainEvent`, and `DomainEventSubscriber` in `shared/domain/event/` — they are the only shared kernel between bounded contexts inside the same process.

---

## Aggregate Reconstruction: fromPrimitives and toPrimitives

**Intent:** Separate the path that creates new aggregates (triggering domain events) from the path that restores existing aggregates from storage (no events raised).

**How it works:** Give creation and restoration different semantic entry points. A named factory such as `create()` may record creation facts; a reconstitution factory or dedicated persistence mapper restores existing state without recording new facts. Restrict raw construction where practical so callers cannot accidentally choose the wrong lifecycle path.

`fromPrimitives()`/`toPrimitives()` is a useful implementation style, not a requirement. Prefer a dedicated mapper when public serialization methods would expose persistence concerns or weaken encapsulation.

**Practical heuristic:** Reconstitution must never invoke creation behavior or emit `Created` again. Read `aggregates.md` for lifecycle, historical-data, and mapping trade-offs.

---

## Where to Publish Domain Events: Use Case vs. Aggregate

**Intent:** Decide which layer is responsible for handing events to the EventBus.

**How it works:** The aggregate records events internally (`this.record(event)`). The use case is the only actor with access to the EventBus — it saves the aggregate and then calls `eventBus.publish(aggregate.pullDomainEvents())`. Publishing from inside the aggregate requires injecting the EventBus into the domain, which crosses the dependency rule and makes testing harder. Publishing from the use case keeps domain and infrastructure concerns cleanly separated.

**When NOT to:** Do not inject EventBus into the aggregate. Do not publish from a repository save hook — a failed publish after a successful save creates a split-brain state that is hard to detect.

**Practical heuristic:** Keep event selection in the aggregate and delivery outside it. `save aggregate -> pull events -> publish` is acceptable only for best-effort in-process delivery: it has a crash window and pulling may clear events before publication succeeds. For durable delivery, persist aggregate state and outbox records in one transaction, then relay with retries and idempotent consumers. Read `aggregates.md` for the aggregate-side boundary and use `infrastructure-design` for implementation.
