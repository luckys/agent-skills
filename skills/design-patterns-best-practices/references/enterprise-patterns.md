# Enterprise Application Patterns

Enterprise application architecture provides a set of patterns for structuring the layers between a user interface and a database. These patterns — drawn primarily from Martin Fowler's *Patterns of Enterprise Application Architecture* — address the recurring tensions of object-relational mapping, transaction management, and application boundary design. Choosing the right pattern depends on the complexity of the domain logic, not on team conventions or framework defaults.

## Repository

**Intent.** Mediates between the domain and data mapping layers, acting like an in-memory collection of domain objects. Client code adds objects to and removes objects from the Repository as if working with a simple collection, while the Repository handles all underlying query and persistence concerns. The Repository presents a clean separation between the domain model and the persistence layer.

**When to use.**
- You have a rich Domain Model with complex object graphs and the domain logic needs to remain ignorant of the database structure.
- You need to swap data sources (e.g., swap a relational database adapter for an in-memory one in tests) without touching domain or application code.
- You want to enforce aggregate boundaries: the repository is the only route into and out of a cluster of domain objects.
- Multiple clients (UI, API, background workers) all need the same access contract to domain objects.

**When NOT to use.**
Many projects add a Repository as boilerplate before it earns its place. Do not introduce it when:
- Your application uses Transaction Script or Table Module patterns — a simple query helper function or a Data Mapper finder method is sufficient.
- The domain logic is simple enough that Active Record already handles persistence transparently.
- You need list/reporting views that project data from multiple tables: a Repository is designed around domain aggregates for *write* consistency, not for feeding read models or views. Using it for that purpose leads to bloated interfaces (`findAllByStatusAndRegionOrderByDate`) that are not collections — they are query services in disguise.
- The abstraction cost (interface, implementation, test double) exceeds the isolation benefit. If you never swap the data source and never test in isolation, the interface is dead weight.

The fundamental rule (Fran Iglesias): **a Repository is not the gateway to the database; it is a collection.** It should behave as if it were an in-memory store with retrieve, store, and findSatisfying operations. If a method cannot be implemented against a simple in-memory map, it does not belong in a Repository.

**Key trade-off.** Repository is a sophisticated pattern. It requires Query Object or Specification to express complex criteria declaratively, and it pairs with Unit of Work for transactional flushing. Adding it to a simple CRUD system adds an extra layer with no benefit.

**Practical heuristic.** Ask whether you can implement the Repository against a plain `Map<Id, Entity>` in a unit test. If the interface forces SQL or ORM knowledge into that test double, the interface is wrong. Start with direct Data Mapper finder methods; extract a Repository interface only when you need interchangeable strategies or true aggregate isolation.

---

## Service Layer

**Intent.** Defines the application's boundary and its set of available operations. A Service Layer coordinates the application's response to each use case: it scripts the application logic (transaction control, notifications, event publishing) and delegates domain logic to domain objects. It is the contract between the outside world (UI, API, message consumers) and the domain.

**When to use.**
- Your application has more than one kind of client (browser UI, REST API, background job) that all need to invoke the same business operations.
- Use cases require atomic coordination across multiple transactional resources — a database write, an outbound email, a message queue publication — that must all succeed or all roll back together.
- You want to keep controllers and request handlers thin: they translate the HTTP layer to a service call, then translate the result to a response.

**When NOT to use.**
- If the application has a single client (one UI) and its use cases involve a single transactional resource, Page Controllers can manage transactions directly and delegate to the Data Source layer. Adding a Service Layer is overhead without benefit.
- For pure CRUD with no cross-cutting application logic, a Service Layer is a pass-through that adds indirection.

The rule of thumb (Fowler): as soon as you envision a second kind of client or a second transactional resource in a use case, design a Service Layer in from the beginning.

**Key trade-off.** Two implementation styles exist: *domain facade* (thin, delegates everything to domain objects) and *operation script* (thicker, contains the application logic script and delegates only domain logic). Operation script is more common because application logic — sending emails, publishing events, managing transactions — belongs in neither the domain nor the controller.

**Practical heuristic.** One service class per subject area or subsystem (e.g., `ContractsService`, `RecognitionService`). Service methods map one-to-one to application use cases. If a method does not correspond to a use case, it is probably misplaced domain logic.

---

## Unit of Work

**Intent.** Maintains a list of objects affected by a business transaction and coordinates writing changes out to the database in a single commit. It tracks new objects, modified objects, and deleted objects across the span of a business interaction, then opens one database transaction at commit time — avoiding many small database calls and eliminating the need for application code to manually track what has changed.

**When to use.**
- You have multiple domain objects that must be written atomically — changes to one are meaningless without the others.
- Your business transaction spans multiple steps or requests and you cannot keep a database transaction open for the whole duration (long-running optimistic concurrency scenarios).
- You want to prevent inconsistent reads: the Unit of Work can verify that objects read at the start of the transaction have not been modified in the database by another process before committing.
- You are using Data Mapper: the mapper registers loaded objects with the Unit of Work so that dirty tracking happens automatically without the domain object knowing.

**When NOT to use.**
- Simple single-record CRUD where Active Record's own `save()` call is sufficient.
- Frameworks (ORMs like Hibernate, Entity Framework, SQLAlchemy) implement Unit of Work internally — do not build a custom one on top of an ORM's session or `DbContext`, which already is one.

**Key trade-off.** Unit of Work can be registered by the caller (every method that changes an object tells the Unit of Work explicitly) or by the object itself (the domain object registers itself when a setter is called). Caller registration is more explicit but tedious; object registration is transparent but requires the domain object to know about the Unit of Work infrastructure.

**Practical heuristic.** If you are using an ORM, you already have a Unit of Work — the session or context is it. Add a custom Unit of Work only when coordinating persistence across multiple data sources or when your hand-rolled Data Mappers need a shared commit boundary.

---

## Data Mapper vs Active Record

These two patterns represent a key architectural fork in object-relational mapping. The choice between them is driven by the complexity of the domain model, not by framework preference.

### Active Record

**Intent.** An object that wraps a row in a database table, encapsulates database access, and adds domain logic on that data. The object knows how to read and write itself to the database. One field per column; static finder methods wrap SQL queries.

**When to use.**
- Domain logic is not too complex: creates, reads, updates, deletes, single-record validations and derivations.
- The object schema and the database schema are isomorphic (one class per table, direct field-to-column mapping).
- You are working with Transaction Script and want to reduce duplication by moving common data-and-access logic into the object.
- Rapid development of simple systems where the extra isolation of Data Mapper is not yet justified.

**When NOT to use.**
- Business logic is complex and needs rich object relationships, inheritance, and collections that do not map cleanly to a single table.
- You want the database schema to evolve independently from the domain model.
- Testability is critical: Active Record objects couple tests to the database.

Active Record's primary problem is that it works well only when the schema is isomorphic. As soon as the object model diverges from the database structure, mapping piecemeal onto Active Record becomes messy and you will be pushed toward Data Mapper anyway. It also couples object design to database design, making both harder to refactor.

### Data Mapper

**Intent.** A layer of mappers that moves data between in-memory objects and the database while keeping them independent of each other. The domain objects have no knowledge of the database — no SQL, no schema awareness. Mappers handle all correspondence between the object model and the relational model.

**When to use.**
- You have a complex Domain Model where object design and database design need to evolve independently.
- The object schema and the database schema diverge — you need rich mappings (inheritance, collections, embedded value objects) that are invisible to the domain.
- You want to work on the domain model and test it entirely without a database present.
- The existing database is under someone else's control and cannot be changed to match the object model.

**When NOT to use.**
- Domain logic is simple enough that Active Record handles it directly.
- The domain model is under your control and the schema is isomorphic.

**Key trade-off.** Data Mapper adds a full extra layer (the mapper itself, plus usually Identity Map, Lazy Load, and Unit of Work) that you do not get with Active Record. The test for using it is the complexity of the business logic: more complicated logic leads to Domain Model, which leads to Data Mapper. Fowler's rule: *do not choose Data Mapper without Domain Model; do not add the complexity without the need.*

**Practical heuristic.** Start with Active Record for simple systems. When the domain model grows and object-relational friction increases — when you find yourself working around the schema in domain logic, or writing untestable code because domain objects talk to the database — extract the persistence behavior into a Data Mapper layer. Most projects should use an ORM (Hibernate, Entity Framework, SQLAlchemy, Drizzle with a mapper layer) rather than build Data Mappers by hand.

---

## Result Pattern

**Intent.** Returns a typed value representing either success or failure from an operation, instead of throwing an exception. A `Result` object carries either the successful value (`SuccessResult`) or an error (`FailedResult`). Callers inspect the result explicitly and handle both branches, making the error path part of the function's type contract rather than an invisible side channel.

**When to use.**
- An operation has expected failure modes that are not exceptional — validation failures, "not found" responses, business rule violations — and the caller always needs to handle both outcomes.
- You want to express the Fail Fast principle without relying on exceptions bubbling silently through call frames.
- You are working in a functional-leaning codebase (TypeScript, Kotlin, Rust, Swift) where `Result`/`Either` types are idiomatic.
- The operation is part of an application or domain service boundary where callers need to branch on success/failure without a try/catch.

**When NOT to use.**
- The failure is truly exceptional (disk full, network lost, programming error) — these belong to exceptions because they cannot be locally handled.
- The operation always succeeds or failures are communicated by returning null or an empty collection — do not add `Result` as ceremony where a simple return value suffices.
- Deep in a call chain where only the top-level caller cares about the outcome — exceptions do a better job of skipping intermediate frames.

**Key trade-off.** Result makes failure visible in the type signature and forces callers to handle it, which improves correctness. The cost is verbosity: every caller must check `successful()` or pattern-match before calling `unwrap()`. Calling `unwrap()` on a `FailedResult` — or calling `error()` on a `SuccessResult` — throws an exception, so the pattern enforces discipline at runtime as well as at the type level.

A minimal contract for a `Result` type:

```typescript
interface Result<T> {
  successful(): boolean;
  failure(): boolean;
  unwrap(): T;        // throws if failure
  error(): Error;     // throws if success
}
```

**Practical heuristic.** Use `Result` at application and domain service boundaries for expected business outcomes. Use exceptions for truly unexpected, unrecoverable conditions. If you find yourself wrapping every method in `Result` just to avoid exceptions, reconsider: exceptions exist precisely to skip intermediate frames without cluttering them.
