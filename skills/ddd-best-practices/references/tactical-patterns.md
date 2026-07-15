# Tactical DDD Patterns

Building blocks for modeling a domain. These are the vocabulary you use inside a Bounded Context to express domain logic in code.

---

## Entity

**Intent:** Represent a domain object whose identity persists through time and across representations, independent of its attributes.

**How it works:** An Entity carries a unique identifier that never changes, even as the object's attributes change over its life cycle. Two Entities are the same thing if they share the same identity, regardless of attribute values. The class definition, behavior, and associations are organized around who the object *is*, not what it currently *looks like*. Entities fulfill most of their responsibilities by coordinating the objects they own.

**When to use:**
- The thing must be tracked across system boundaries or over time (e.g., Customer, Order, Bank Transaction)
- Two instances with identical attributes are still conceptually distinct (two deposits of the same amount to the same account on the same day are different transactions)
- Lifecycle continuity matters to the business (an archived customer is still the same customer)

**When NOT to use:**
- The concept is defined purely by its descriptive attributes and carries no meaningful lifecycle (use Value Object instead)
- Identity exists only in-memory (a technical pointer is not a domain identity)
- The object is transient and discarded after a single operation

**Key trade-off:** Tracking identity adds analytical work and performance cost (unique key generation, distributed identity reconciliation). Every Entity requires a designed means of distinguishing it from all others — that design decision demands domain understanding.

**Related patterns:** Value Object (complementary — strip attributes from Entities into VOs), Aggregate (Entities are clustered into Aggregates with one root), Repository (provides lifecycle management for persistent Entities)

**Practical heuristic:** Strip the Entity's definition down to the minimum attributes that identify or match it. Move everything else into associated Value Objects or other Entities.

**Evans quote or key insight:** "Some objects are not defined primarily by their attributes. They represent a thread of identity that runs through time and often across distinct representations." The model must define what it *means* to be the same thing.

---

## Value Object

**Intent:** Represent a descriptive aspect of the domain that has no conceptual identity — defined entirely by its attributes.

**How it works:** A Value Object captures *what* something is, not *which* one it is. Two instances with the same defining values are interchangeable. Make observation deeply immutable by default so values can be copied or shared safely. Define semantic equality over every defining component and matching hashing where the language requires it. Keep only intrinsic, context-independent rules inside the value.

**When to use:**
- The concept is defined by its attributes: a monetary amount, a date range, an address, a color
- Interchangeability is correct — you don't care *which* instance you have, only *what* it represents
- The object is used as an attribute of an Entity or passed as a parameter
- You want sharing or copying to be safe and cheap

**When NOT to use:**
- Two instances with the same attributes need to be distinguished (they are Entities)
- The object needs to be updated in place by multiple holders (use a mutable Entity instead, but reconsider the design)
- The object needs its own lifecycle in the Repository

**Key trade-off:** Immutability enables safe sharing and stable equality but means replacement rather than in-place mutation. Keep any measured mutable optimization as an exclusively owned implementation detail rather than a mutable Value Object contract.

**Related patterns:** Entity (the contrast — Entities need identity; Values do not), Flyweight (an implementation optimization for shared immutable Values), Specification (often implemented as a Value Object). Use `oop-best-practices` for construction, equality, hashing, deep immutability, optionality, and persistence guidance.

**Practical heuristic:** If you can replace one instance with another that has the same attributes and no behavior changes, it is a Value Object. Make it immutable by default.

**Evans quote or key insight:** "An object that represents a descriptive aspect of the domain with no conceptual identity is called a VALUE OBJECT. VALUE OBJECTS are instantiated to represent elements of the design that we care about only for *what* they are, not *who* or *which* they are." The same address concept can be an Entity in one domain (postal service) and a Value Object in another (mail-order company) — the domain decides.

---

## Service (Domain Service)

**Intent:** Express a domain operation that is not a natural responsibility of any Entity or Value Object.

**How it works:** When a significant process or transformation in the domain cuts across multiple objects or simply does not conceptually belong to one of them, forcing it into an object distorts the design. A Domain Service is a stateless operation declared in terms of the domain model. Its interface is defined using domain model elements and its name comes from the Ubiquitous Language. Because it is stateless, any client can use any instance without concern for individual history.

A good Domain Service has three characteristics:
1. The operation relates to a domain concept that is not a natural part of an Entity or Value Object.
2. The interface is defined in terms of other domain model elements.
3. The operation is stateless.

**When to use:**
- A significant domain operation spans multiple Aggregates or Entities (e.g., a funds transfer that debits one Account and credits another)
- Forcing the logic into one object would give it unrelated dependencies or distort its meaning
- The operation represents a domain-meaningful *activity* (a verb, not a noun)

**When NOT to use:**
- The operation clearly belongs to one object — put it there; Services should not strip Entities of behavior
- The concept is purely technical (email sending, file I/O) — that belongs in the Infrastructure layer
- You are using a Service just to avoid thinking about which object should own the behavior (this produces anemic domain models)

**Key trade-off:** Domain Services prevent Entities from becoming bloated with unrelated logic, but overuse produces procedural, anemic models where all behavior lives in Services and objects are mere data containers.

**Related patterns:** Entity and Value Object (Services coordinate them), Application Service (a different layer — orchestrates use cases but contains no domain logic), Repository (Services often need to locate objects via Repositories)

**Practical heuristic:** Name the Service after the activity it performs (a verb phrase from the Ubiquitous Language). If the name ends in "Manager" or "Handler" with no domain meaning, look harder for the right object.

**Evans quote or key insight:** "Some concepts from the domain aren't natural to model as objects. Forcing the required domain functionality to be the responsibility of an ENTITY or VALUE either distorts the definition of a model-based object or adds meaningless artificial objects."

---

## Aggregate

**Intent:** Define a cluster of associated objects treated as a unit for the purposes of data change, with one object designated as the root controlling all access.

**How it works:** Complex object graphs create problems: invariants that span multiple objects are hard to enforce, concurrent access creates contention, and lifecycle ownership becomes unclear. An Aggregate draws a boundary around a set of Entities and Value Objects that must change consistently. One Entity — the Aggregate Root — controls all mutation. External code interacts through the root and must not retain mutable access to internals. The root enforces the cluster's invariants after every accepted command. Persistence and deletion follow the aggregate's lifecycle policy; they do not have to mirror an ORM cascade.

Rules:
- Only Aggregate Roots can be retrieved directly from the database (Repositories operate on Aggregate Roots)
- Internal members may be observed through immutable values or snapshots, but mutable references must not escape
- Objects within the boundary reference other Aggregate Roots by identity, not by a live mutable object reference

**When to use:**
- A set of objects has invariants that must hold across all of them (e.g., a Purchase Order's total must not exceed its approved limit)
- Objects have a natural ownership relationship (PO owns its line items; line items have no meaning outside that PO)
- You need to coordinate locking and transactional consistency around a coherent cluster

**When NOT to use:**
- The cluster would be so large it causes unacceptable contention — reconsider the boundary; invariants enforced at every moment may be too strict
- Objects are shared across many independently changing Aggregates (they may be their own Aggregate Roots)
- You are grouping objects for convenience rather than because they share invariants

**Key trade-off:** Tight Aggregate boundaries enforce consistency but create contention under concurrent load. Loose boundaries allow concurrency but risk invariant violations. The Purchase Order example from Evans shows the tension: locking the whole PO enforces the limit invariant but blocks concurrent edits; locking only line items allows invariant violations.

**Related patterns:** Entity (Aggregates are clusters of Entities and Value Objects), Aggregate Root (the controlling Entity), Repository (operates on Aggregate Roots), Factory (creates entire Aggregates in a consistent state). Read `aggregates.md` for the complete boundary-discovery, transaction, concurrency, and lifecycle guidance.

**Practical heuristic:** Ask: "What must be true of this cluster at all times?" That scope defines the Aggregate. If the invariant only needs to hold eventually (not at every moment), the boundary may be too tight.

**Evans quote or key insight:** "Cluster the ENTITIES and VALUE OBJECTS into AGGREGATES and define boundaries around each. Choose one ENTITY to be the root of each AGGREGATE, and control all access to the objects inside the boundary through the root." Aggregates mark the scope within which invariants must be maintained at every stage of the life cycle.

---

## Aggregate Root

**Intent:** Designate a single Entity within an Aggregate as the sole entry point for all external interaction, making it responsible for enforcing the cluster's invariants.

**How it works:** The Aggregate Root is an Entity with a global identity (accessible by Repositories and held by external objects). All other members of the Aggregate have only local identity — they may be uniquely identified within the boundary but not globally. The root enforces rules that apply to the whole cluster. It controls whether internal members can be accessed by external objects, and any access it grants is transient. Because the root controls all mutations, it can never be blindsided by changes to the internals.

**When to use:**
- When defining an Aggregate — every Aggregate must have exactly one root
- The root should be the object whose identity is meaningful beyond the cluster (e.g., PurchaseOrder, not LineItem)
- The root should naturally own the invariants of the cluster

**When NOT to use:**
- Do not designate multiple roots for a single Aggregate — this breaks the invariant-enforcement contract
- Do not use an internal member as the root just because it is convenient; the conceptual owner should be the root

**Key trade-off:** The root becomes a bottleneck for all access to the cluster. This is intentional — it is the price of coherent invariant enforcement. If the bottleneck is unacceptable, the Aggregate boundary is probably wrong.

**Related patterns:** Aggregate (the pattern the root anchors), Repository (retrieves and stores Aggregate Roots), Factory (creates valid Aggregate Roots)

**Practical heuristic:** The Aggregate Root should be the object you would naturally ask "does X exist in the system?" about — the concept whose lifecycle the domain cares about tracking.

---

## Repository

**Intent:** Provide the illusion of an in-memory collection of all objects of a given type, encapsulating the actual storage and retrieval mechanics.

**How it works:** A Repository represents all objects of a certain type as a conceptual set. Clients add and remove objects; the Repository handles the underlying insertion, deletion, and querying against whatever persistence technology is in use. Clients request objects by submitting criteria expressed in domain terms (not SQL or database keys). The Repository translates these into whatever queries the storage layer requires and reconstitutes the domain objects from the result. Repositories are only provided for Aggregate Roots that need direct global access — transient Value Objects and internal Aggregate members are found by traversal, not by Repository queries.

The Repository gives four advantages:
1. A simple model for obtaining persistent objects
2. Decoupling of domain and application code from persistence technology
3. Explicit communication of design decisions about which objects are globally accessible
4. Easy substitution of an in-memory implementation for testing

**When to use:**
- You need global access to an Aggregate Root (Customer, Order, Product)
- The domain layer must not directly deal with database queries, SQL, or ORM mechanics
- You want to be able to substitute an in-memory fake for testing

**When NOT to use:**
- For objects that are always accessed by traversal from an Aggregate Root (they don't need their own Repository)
- As a general-purpose data access layer — Repositories are domain constructs, not DAO replacements
- For Value Objects that can simply be reconstructed by value

**Key trade-off:** The Repository interface belongs to the domain layer; the implementation belongs to infrastructure. This separation is powerful but means developers must understand what happens under the hood — "all objects" query bugs (loading an entire database into memory) are the canonical failure mode.

**Related patterns:** Aggregate Root (Repositories operate only on roots), Factory (Repositories use Factories to reconstitute stored objects), Specification (used to express flexible query criteria)

**Practical heuristic:** Define the Repository interface in terms of the domain model — `findByTrackingId(TrackingId)`, not `findById(long)`. Leave transaction control to the client; the Repository should not commit.

**Evans quote or key insight:** "A REPOSITORY represents all objects of a certain type as a conceptual set (usually emulated). It acts like a collection, except with more elaborate querying capability." The key insight is the distinction from Factory: a Factory makes *new* objects; a Repository finds *existing* ones — reconstitution is not creation.

### Repository: Concrete Implementation Strategies

For the complete decision guide, including Repository vs DAO/query service/gateway, transaction propagation, concurrency, caching, pagination, and testing, read `repositories.md`.

**Aggregate-only repositories:** Only Aggregate Roots get their own Repository. Internal entities and value objects within an Aggregate are loaded by traversal from the root, never by a separate Repository query. This enforces the Aggregate boundary and prevents bypassing invariants.

**The interface lives in the domain, the implementation in infrastructure:**
```typescript
// domain/CourseRepository.ts — pure domain interface, no imports from infra
export interface CourseRepository {
  save(course: Course): Promise<void>;
  search(id: CourseId): Promise<Course | null>;
  searchAll(): Promise<Course[]>;
}

// infrastructure/PostgresCourseRepository.ts — infra implementation
export class PostgresCourseRepository
  extends PostgresRepository<Course>
  implements CourseRepository
{
  async save(course: Course): Promise<void> {
    const p = course.toPrimitives();
    await this.execute`
      INSERT INTO mooc.courses (id, name, summary, categories, published_at)
      VALUES (${p.id}, ${p.name}, ${p.summary}, ${p.categories}, ${p.publishedAt})
      ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        summary = EXCLUDED.summary,
        categories = EXCLUDED.categories,
        published_at = EXCLUDED.published_at;
    `;
  }

  async search(id: CourseId): Promise<Course | null> {
    return this.searchOne`
      SELECT id, name, summary, categories, published_at
      FROM mooc.courses WHERE id = ${id.value};
    `;
  }

  protected toAggregate(row: DatabaseCourseRow): Course {
    return Course.fromPrimitives({
      id: row.id, name: row.name, summary: row.summary,
      categories: row.categories,
      publishedAt: row.published_at.toISOString(),
    });
  }
}
```

**`search` and required existence:** Let the repository `search` return `T | null` (or `Option<T>`). When a use case requires existence, an application/domain finder translates absence into a typed error. This keeps persistence lookup separate from the caller's business meaning.

```typescript
// domain/UserRepository.ts
export interface UserRepository {
  save(user: User): Promise<void>;
  search(id: UserId): Promise<User | null>;  // caller handles null
}

// application/UserFinder.ts — wraps repository with a domain-named error
export class UserFinder {
  constructor(private readonly repository: UserRepository) {}

  async find(id: string): Promise<User> {
    const user = await this.repository.search(new UserId(id));
    if (user === null) throw new UserDoesNotExistError(id);
    return user;
  }
}
```

**Repository with Criteria (Specification-based querying):** For flexible, composable queries, the Repository accepts a `Criteria` object instead of individual filter parameters. This keeps SQL out of the domain and allows the same query logic to work across multiple storage backends.

```typescript
// domain/CourseRepository.ts — accepts Criteria, not raw SQL params
export interface CourseRepository {
  save(course: Course): Promise<void>;
  search(id: CourseId): Promise<Course | null>;
  matching(criteria: Criteria): Promise<Course[]>;
}

// infrastructure — converts Criteria to SQL
async matching(criteria: Criteria): Promise<Course[]> {
  const { query, params } = this.criteriaConverter.convert(criteria);
  const rows = await this.db.query(query, params);
  return rows.map(this.toAggregate);
}
```

**Testing repositories with an in-memory fake:** The interface-in-domain / implementation-in-infrastructure split enables a fast in-memory fake for unit and integration tests without touching a real database.

```typescript
// tests/InMemoryUserRepository.ts
export class InMemoryUserRepository implements UserRepository {
  private users: Map<string, User> = new Map();

  async save(user: User): Promise<void> {
    this.users.set(user.id.value, user);
  }

  async search(id: UserId): Promise<User | null> {
    return this.users.get(id.value) ?? null;
  }
}

// In tests — no database, fully deterministic
const repository = new InMemoryUserRepository();
const finder = new UserFinder(repository);
```

**Practical heuristic:** If your application layer imports anything from an ORM or database driver, the Repository abstraction has leaked. The application layer should only know the domain interface. Query values must still be parameterized in the adapter; introducing a Repository does not make string-built SQL safe.

### Outbox and Inbox Patterns with Domain Events

When an Aggregate raises Domain Events that must be reliably delivered to other Bounded Contexts, the simplest approach (publish to a message broker inside the same transaction that saves the Aggregate) suffers from a dual-write problem: the DB commit and the broker publish can fail independently, causing lost or phantom events.

**Outbox pattern (write side):** Instead of publishing to the broker directly, the application's `EventBus` implementation writes events to an `outbox_event_bus` table inside the same DB transaction that saves the Aggregate. A separate relay process polls the outbox and publishes to the broker, then deletes published rows.

```sql
-- outbox_event_bus table (PostgreSQL)
CREATE TABLE public.outbox_event_bus (
  event_id    UUID        NOT NULL PRIMARY KEY,
  event_name  TEXT        NOT NULL,
  aggregate_id TEXT       NOT NULL,
  payload     JSONB       NOT NULL,
  occurred_at TIMESTAMPTZ NOT NULL,
  inserted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx__outbox_event_bus__inserted_at ON public.outbox_event_bus (inserted_at);
```

```typescript
// PostgresOutboxEventBus.ts — EventBus implementation that writes to outbox table
@Service()
export class PostgresOutboxEventBus implements EventBus {
  constructor(connection: PostgresConnection) {
    this.sql = connection.sql;
  }

  async publish(events: DomainEvent[]): Promise<void> {
    if (events.length === 0) return;
    const rows = events.map((event) => ({
      event_id:    event.eventId,
      event_name:  event.eventName,
      aggregate_id: event.aggregateId,
      payload:     JSON.parse(DomainEventJsonSerializer.serialize(event)) as JSONValue,
      occurred_at: event.occurredAt,
    }));
    await this.sql`INSERT INTO public.outbox_event_bus ${this.sql(rows)}`;
  }
}
```

```typescript
// publish-outbox-to-rabbitmq.ts — relay process (runs as a background script)
const POLLING_INTERVAL_MS = 1000;
const BATCH_SIZE = 100;

async function pollAndPublish(pg: PostgresConnection, bus: RabbitMqEventBus): Promise<number> {
  return pg.sql.begin(async (tx) => {
    const events = await tx`
      SELECT event_id AS "eventId", event_name AS "eventName", payload::TEXT AS "payload"
      FROM public.outbox_event_bus
      ORDER BY inserted_at ASC
      LIMIT ${BATCH_SIZE}
      FOR UPDATE SKIP LOCKED
    `;
    if (events.length === 0) return 0;

    const domainEvents = events
      .map((e) => { try { return deserializer.deserialize(e.payload); } catch { return null; } })
      .filter((e): e is DomainEvent => e !== null);

    if (domainEvents.length > 0) await bus.publish(domainEvents);

    const eventIds = events.map((e) => e.eventId);
    await tx`DELETE FROM public.outbox_event_bus WHERE event_id = ANY(${eventIds})`;
    return events.length;
  });
}
// Runs in a while(true) loop with sleep(POLLING_INTERVAL_MS) between iterations
```

**Key details:** `FOR UPDATE SKIP LOCKED` prevents two relay instances from picking the same rows. Rows are deleted only after successful publish — if the broker call fails, the transaction rolls back and rows remain for the next poll cycle.

**Inbox pattern (read side — idempotency):** Message brokers deliver at-least-once. The Inbox pattern prevents a subscriber from processing the same event twice by recording `(event_id, subscriber_name)` in an `inbox_events` table inside the same transaction as the handler. A duplicate delivery finds the row already present and is silently discarded.

```sql
-- inbox_events table
CREATE TABLE public.inbox_events (
  event_id        UUID        NOT NULL,
  subscriber_name TEXT        NOT NULL,
  processed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (event_id, subscriber_name)
);
```

```typescript
// RabbitMqEventBus.ts (inbox-enabled consume side)
private async consumeWithInbox(
  subscriber: DomainEventSubscriber<DomainEvent>,
  domainEvent: DomainEvent,
): Promise<void> {
  await this.postgresConnection.sql.begin(async (trx) => {
    // Atomic idempotency check: INSERT … ON CONFLICT DO NOTHING
    const result = await trx`
      INSERT INTO public.inbox_events (event_id, subscriber_name)
      VALUES (${domainEvent.eventId}, ${subscriber.name()})
      ON CONFLICT (event_id, subscriber_name) DO NOTHING
      RETURNING event_id
    `;

    if (result.length === 0) {
      // Already processed — silently skip
      console.error("Ignoring duplicate event", domainEvent);
      return;
    }

    // First time seeing this event for this subscriber — process it
    await subscriber.on(domainEvent);
    // subscriber.on() and the inbox INSERT commit together atomically
  });
}
```

**Practical heuristic:**
- Use the Outbox pattern whenever a Domain Event must cross a process boundary (e.g., to a message broker). Do not publish directly from the Repository `save()` call.
- Use the Inbox pattern whenever a subscriber's handler is not naturally idempotent. The composite primary key `(event_id, subscriber_name)` means different subscribers can independently receive the same event — only duplicate deliveries to the *same* subscriber are blocked.
- Both patterns rely on the same DB that stores Aggregates. This makes them a natural fit for systems that already use PostgreSQL (or any transactional DB).

---

## Factory

**Intent:** Encapsulate the complex assembly of a domain object or entire Aggregate, ensuring the created object is in a valid, consistent state without burdening clients with construction knowledge.

**How it works:** Creating complex objects — especially entire Aggregates — requires knowledge of internal structure and invariants. If the client is responsible for construction, it becomes coupled to implementation details, invariant enforcement leaks out of the domain, and refactoring becomes expensive. A Factory centralizes this responsibility. Its interface reflects what the client wants, not how the object is assembled. Each creation method is atomic: it either returns a fully valid object (with all invariants satisfied) or it fails with an exception — it never returns a partially constructed object.

Two basic requirements for a good Factory:
1. Each creation method is atomic and enforces all invariants of the created object or Aggregate.
2. The Factory is abstracted to the type desired, not the concrete class created.

A Factory may be: a standalone Factory object/class, a Factory Method on a related Entity (e.g., `brokerageAccount.newBuyOrder(...)`), or simply a well-designed constructor for simple cases.

**When to use:**
- Creating an Aggregate involves complex assembly, hidden internal structure, or polymorphic selection among subtypes
- A related Entity naturally "spawns" the new object and controls the rules governing what can be created
- You need to enforce invariants across the whole Aggregate at creation time

**When NOT to use:**
- The class is simple, non-polymorphic, and all its attributes are available to the client — a plain constructor is clearer
- The Factory would obscure a simple object with no meaningful internal complexity

**Key trade-off:** Factories add indirection and a new design element (one that does not appear in the model itself). That cost is worth paying when construction is genuinely complex. Avoid over-engineering simple creations.

**Related patterns:** Aggregate (Factories create entire Aggregates in a valid state), Repository (uses Factories to reconstitute stored objects — reconstitution differs from creation: no new identity is assigned), Abstract Factory / Factory Method (GoF patterns applicable here)

**Practical heuristic:** If a constructor is calling other constructors, or if the client needs to know internal types to call it correctly, extract a Factory. Keep Factory method parameters at the minimum needed to establish invariants.

**Evans quote or key insight:** "Shift the responsibility for creating instances of complex objects and AGGREGATES to a separate object, which may itself have no responsibility in the domain model but is still part of the domain design. Provide an interface that encapsulates all complex assembly and that does not require the client to reference the concrete classes of the objects being instantiated. Create entire AGGREGATES as a piece, enforcing their invariants."

---

## Module (a.k.a. Package)

**Intent:** Group cohesive domain concepts together and define a high-level, navigable narrative of the domain model, with low coupling between modules and high cohesion within them.

**How it works:** Modules are not just a code organization mechanism — they are a communications mechanism. They give people two views of the model: the interior detail when needed, and the inter-module relationships for a higher-level view. The key driver for module design is conceptual cohesion, not technical layering. When you place classes together in a Module, you tell the next developer to think about them together. The Module name becomes part of the Ubiquitous Language. Modules should coevolve with the model; early module structures often freeze and lag behind the model, increasing coupling and reducing clarity.

**When to use:**
- The model is large enough that people need a higher-level organizing principle to navigate it
- A set of concepts is so closely related that discussions and design work naturally concentrate on them together
- Module names can be meaningful to domain experts

**When NOT to use:**
- Do not let technical frameworks dictate module structure (infrastructure layering, tier separation) at the cost of conceptual cohesion
- Do not freeze module structure early and stop refactoring it — agile modules coevolve with the model

**Key trade-off:** Refactoring Modules is far more disruptive than refactoring classes (naming changes ripple widely). Teams tend to under-refactor Modules, letting them drift from the model. The cost of not refactoring is a module structure that tells a misleading story about the domain.

**Related patterns:** Bounded Context (the strategic-level equivalent — Modules are within a context; Bounded Contexts are between them), Ubiquitous Language (Module names should be part of it)

**Practical heuristic:** Name modules after domain concepts, not technical roles. "customer", "shipping", "billing" — not "controllers", "services", "repositories".

**Evans quote or key insight:** "Choose MODULES that tell the story of the system and contain a cohesive set of concepts... Give the MODULES names that become part of the UBIQUITOUS LANGUAGE. MODULES and their names should reflect insight into the domain."

---

## Domain Event

**Intent:** Model something that happened in the domain that domain experts care about, making state changes explicit, named, and usable as triggers for downstream reactions.

**How it works:** A Domain Event is an immutable record of something that occurred in the domain — named in the past tense using Ubiquitous Language terms (e.g., `OrderPlaced`, `PaymentConfirmed`, `CargoBooked`). It captures the data that describes what happened (who, what, when, context). Its business payload has value semantics, while its envelope may carry an event ID, occurrence time, and delivery metadata for deduplication and tracing. Other parts of the same Bounded Context can react without tight coupling to the source Aggregate. At a context boundary, translate relevant facts into stable Integration Events rather than exposing the internal Domain Event schema.

Note: Evans' 2003 book treated events implicitly (Handling Events in the cargo example); Domain Events were later formalized as a first-class pattern by the DDD community (Evans, Fowler, and others, circa 2005–2010). The pattern is now considered a core tactical building block.

**When to use:**
- A state change in one Aggregate should trigger reactions in other Aggregates; cross-context reactions receive a translated Integration Event
- You want to decouple the source of a change from its downstream effects
- Auditing, logging, or eventual consistency between Aggregates is required
- A business expert talks about "when X happens, then Y should occur"

**When NOT to use:**
- When a simple synchronous method call inside the same Aggregate is sufficient
- When the reaction is an internal invariant of the same Aggregate (keep it inside the boundary)
- When the added asynchrony and complexity of event handling is not justified by the coupling reduction

**Key trade-off:** Events decouple producers from consumers and enable eventual consistency, but introduce ordering, idempotency, and delivery guarantee concerns. The richer the event bus infrastructure, the more non-domain complexity enters the system.

**Related patterns:** Aggregate (Aggregates raise events when their state changes), Repository (events may be persisted alongside the Aggregate for event sourcing), Domain Service (may coordinate event handling), Bounded Context (events are the primary mechanism for integration across Contexts)

**Practical heuristic:** Name events in the past tense with domain language: `OrderShipped`, not `OrderShipEvent`. Include only the data a downstream handler needs to react — do not embed the full Aggregate state.

---

## Specification

**Intent:** Encapsulate a business rule as a separate, named, reusable predicate object that can test whether a domain object satisfies certain criteria.

**How it works:** Boolean test methods naturally accumulate in domain objects, and as rules grow complex they overwhelm the object's primary responsibility. The Specification pattern extracts these rules into separate Value Objects. A Specification states a constraint on the state of another object, which may or may not be present. A client creates a Specification, then asks it to evaluate a candidate object (`isSatisfiedBy(candidate)`). The same Specification can be used for three purposes without changing its conceptual definition: (1) validation — does this object satisfy the rule now? (2) selection — find all objects in a collection satisfying the rule; (3) construction / building to order — specify what a new object must look like.

Specifications mesh naturally with Repositories: a Repository can accept a Specification as a query parameter, translating it into SQL or another query form to fetch matching objects efficiently.

**When to use:**
- A business rule is complex, growing, or appears in multiple places and needs a named home
- You need the same rule to work for validation, querying, and generation
- The rule depends on data that does not belong in the object being evaluated
- The domain expert talks about the rule as a distinct concept (e.g., "delinquency policy", "eligibility criteria")

**When NOT to use:**
- The rule is a simple, stable invariant that naturally lives as a method on the object — extracting it adds indirection without clarity
- The evaluation logic is purely technical with no domain meaning
- Full logic-programming-style predicate composition is needed — full implementation of combinable logic is a significant undertaking (Evans cautions against over-engineering this)

**Key trade-off:** Specifications make rules explicit and reusable, but they add objects and indirection. The tension with Repositories is real: expressing a Specification as SQL can leak database schema into the domain layer (Evans shows several approaches to this problem, each with trade-offs).

**Related patterns:** Value Object (Specifications are often implemented as Value Objects), Repository (Repositories accept Specifications as query criteria), Factory (can configure a Specification from contextual data), Strategy (Specification is a domain-motivated application of the same structural idea)

**Practical heuristic:** When a boolean method on a domain object is growing, has multiple callers, or depends on data from outside the object, extract a Specification. Name it after the business concept it tests: `DelinquentInvoiceSpecification`, not `InvoiceRuleChecker`.

**Evans quote or key insight:** "Create explicit predicate-like VALUE OBJECTS for specialized purposes. A SPECIFICATION is a predicate that determines if an object does or does not satisfy some criteria." The unifying insight is that validation, selection, and building-to-order are conceptually the same rule expressed in three different operational contexts.
