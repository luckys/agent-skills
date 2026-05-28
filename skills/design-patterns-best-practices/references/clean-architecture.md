# Clean Architecture Patterns

Architectural patterns from Robert C. Martin's Clean Architecture, applied in PHP context by Kristopher Wilson. These patterns define how to structure application layers so that business rules are independent of frameworks, UI, databases, and external services.

## The Dependency Rule

The fundamental rule: **source code dependencies must point inward**. Inner layers know nothing about outer layers. Outer layers (frameworks, UI, DB) depend on inner layers (use cases, entities) — never the reverse.

```
Frameworks & Drivers → Interface Adapters → Use Cases → Entities
```

In Wilson's Onion Architecture framing this is expressed as:

```
User Interface / Tests / Infrastructure → Application Services → Domain Services → Domain Model
```

---

## Entities (Domain Model Layer)

**Layer:** Entities

**Intent:** Represent the core business objects of the application as plain objects with no external dependencies.

**How it works:** Entities are simple PHP objects (POPOs) with properties and getters/setters that represent the data and identity of a business concept. They have no knowledge of databases, frameworks, or any infrastructure concern. Because they depend on nothing but the language itself, they are completely portable and trivially testable.

**When to use:**
- Every time you need to represent a business concept: Customer, Order, Invoice, Product, Employee
- When you need an object that survives framework or database changes
- As the first step when building a new feature — model the thing before the plumbing

**When NOT to use:**
- Do not put persistence logic (SQL, ORM annotations that drive behavior) directly on the entity
- Do not put HTTP request/response logic in an entity
- Do not inherit from framework base classes (e.g. Eloquent's `Model`) if you want true independence

**Practical heuristic:** If removing all framework `use` statements causes a compile error in this class, it is not a clean entity.

---

## Domain Services Layer

**Layer:** Use Cases / Domain Services

**Intent:** Provide business logic, factories, and repository contracts that operate on entities, forming the true core of the application.

**How it works:** The Domain Services layer sits just outside the Domain Model and may only depend inward on it. It is composed of three sub-types: **Repositories** (interfaces defining data contracts), **Factories** (creational logic for entities), and **Services** (business processes). Nothing outside this layer should be able to break these classes without changing a business rule.

**When to use:**
- When business rules involve multiple entities or complex creation logic
- When you need a stable API that controllers, CLI commands, and other delivery mechanisms can all call identically
- When you want to be able to test business logic without a database or HTTP stack

**When NOT to use:**
- Do not couple Domain Services to a specific ORM, mailer, or HTTP client
- Do not place infrastructure concerns (SQL queries, API calls) in this layer — those belong in the Persistence / Infrastructure layer

**Practical heuristic:** Every class in the Domain Services layer should be fully testable with plain `new` construction and in-memory fakes, no database required.

---

## Repository Interface (Gateway Pattern)

**Layer:** Domain Services (interface) / Infrastructure (implementation)

**Intent:** Decouple the domain from data storage by defining retrieval and persistence as a contract the infrastructure must fulfill.

**How it works:** A repository interface lives in the Domain Services layer and declares the data operations the application needs (`getAll()`, `getById()`, `getBy()`, `save()`). The concrete implementation lives in the Persistence/Infrastructure layer and can use any ORM, raw SQL, API calls, or in-memory arrays. Domain code always depends on the interface, never the concrete class. Dependency injection wires the correct implementation at runtime.

**When to use:**
- Whenever the domain needs to retrieve or persist entities
- When you anticipate needing to swap storage backends (e.g. MySQL → REST API, SQL → NoSQL)
- When you want to unit-test domain logic with an in-memory fake repository

**When NOT to use:**
- Do not create a repository for every table — create one per aggregate root / entity type that the domain cares about
- Do not leak ORM-specific types (Doctrine `Query`, Eloquent `Builder`) through the interface return types

**Practical heuristic:** The interface belongs next to the domain entity it serves; the concrete class belongs in `src/Persistence/Repository/`.

---

## Factory (Creational Pattern in Domain Services)

**Layer:** Domain Services

**Intent:** Encapsulate complex entity creation logic in a single, reusable, testable location.

**How it works:** A Factory class knows how to create a fully initialized entity, applying all default values and business rules that apply at creation time (e.g. new customers always have a `pending` status and a `$0` credit limit, and must be assigned the next available account manager). The factory may depend on repository interfaces to look up related entities. All callers get the same initialization logic without duplication.

**When to use:**
- When creating an entity requires more than `new Entity()` — default values, related lookups, or validation
- When creation logic would otherwise be duplicated across multiple controllers or services
- When the creation rules change frequently

**When NOT to use:**
- Do not use a factory when `new Entity()` with a simple constructor is sufficient
- Static factories are fine for simple cases but avoid them when the factory itself has dependencies

**Practical heuristic:** If you find yourself writing the same three lines to initialize a new entity in two different places, extract a factory.

---

## Domain Service (Business Process Object)

**Layer:** Domain Services

**Intent:** Implement a business process that operates on entities and uses repositories and factories, without tying itself to any delivery mechanism.

**How it works:** A service class like `BillingService` is injected with the repository interfaces it needs, then exposes methods that execute business workflows. For example, `generateInvoices(\DateTime $date)` retrieves active orders via `OrderRepositoryInterface`, creates invoice objects via `InvoiceFactory`, and persists them via `InvoiceRepositoryInterface`. The service knows nothing about HTTP, frameworks, or databases.

**When to use:**
- Business processes that span multiple entities or repositories (billing runs, approval workflows, cost calculations)
- Logic that needs to be triggered from multiple delivery mechanisms (HTTP controller, CLI command, queue worker)
- Any process that would otherwise live in a fat controller

**When NOT to use:**
- Do not use a service for simple CRUD where a controller calling a repository directly is sufficient
- Do not mix presentation concerns (response formatting, HTTP headers) into a domain service

**Practical heuristic:** A domain service should read like a business specification, not like a framework tutorial.

---

## Application Services Layer (Controller / Orchestration)

**Layer:** Interface Adapters

**Intent:** Translate delivery-mechanism requests (HTTP, CLI, queue messages) into domain service calls, and translate domain results back into responses.

**How it works:** Controllers, console commands, and queue handlers live in this layer. They receive input from the delivery mechanism, call the appropriate Domain Services, and return a response in the format the delivery mechanism expects. Controllers should be thin — all logic is delegated to domain services. The book's rule: controllers are **response factories**, responsible for building a response based on HTTP input.

**When to use:**
- As the entry point for any HTTP request, CLI command, or queue event
- When you need to translate between framework-specific request objects and domain objects

**When NOT to use:**
- Do not put business logic in controllers — if a controller has a `foreach` with domain logic, extract it to a service
- Do not let controllers directly instantiate concrete repository implementations

**Practical heuristic:** A controller action that is more than 10–15 lines likely contains logic that belongs in a domain service.

---

## Framework Independence (Ports & Adapters / Hexagonal)

**Layer:** Interface Adapters

**Intent:** Prevent business logic from being locked to any specific framework by wrapping all framework-specific code behind interfaces and adapters.

**How it works:** Every framework service you need (mailer, YAML parser, geocoder, HTTP client) gets an interface defined in the domain, and a concrete adapter class that wraps the framework's implementation. The adapter implements the interface. All client code depends only on the interface. The framework's concrete class is referenced in exactly one place: the adapter. Switching frameworks means writing new adapters, not rewriting domain logic.

**When to use:**
- Whenever you use a framework-specific facade, service, or library in a class that contains domain or application logic
- For any third-party library that might be abandoned, upgraded with breaking changes, or replaced

**When NOT to use:**
- Very small or short-lived applications where a full rewrite is cheaper than the abstraction cost
- Pure infrastructure configuration code that has no business logic

**Practical heuristic:** Every direct framework class name that appears in a domain or application service class is a coupling smell; wrap it in an adapter.

---

## Database Independence (Persistence Layer Separation)

**Layer:** Frameworks & Drivers (Persistence/Infrastructure)

**Intent:** Keep database technology out of the domain by placing all ORM and SQL code in a separate Persistence layer that implements repository interfaces.

**How it works:** The Domain Services layer defines repository interfaces with no ORM types. The Persistence layer provides concrete implementations that use Doctrine, Eloquent, raw PDO, or any other mechanism. The persistence layer sits on the outermost ring of the onion — nothing else depends on it. Dependency injection containers wire the concrete repository into whatever domain factory or service needs the interface.

**When to use:**
- All applications where the database could change (MySQL → API, SQL → NoSQL) or where the ORM could be swapped
- When you need fast unit tests that do not hit a real database

**When NOT to use:**
- When an application is a pure data-access script with no domain logic, the full separation may not pay off

**Practical heuristic:** Organize code as `src/Domain/Entity/`, `src/Domain/Repository/` (interfaces), `src/Domain/Service/`, `src/Persistence/Repository/` (implementations).

---

## Adapter Pattern (for External Agency Independence)

**Layer:** Interface Adapters / Infrastructure

**Intent:** Wrap any third-party library or framework service so that client code couples to your interface, not the vendor's API.

**How it works:** Define an interface in your domain or application layer that describes the capability you need (e.g. `MailerInterface`, `GeocoderInterface`, `YamlParserInterface`). Write a concrete adapter class that implements your interface and delegates to the third-party library. Register the adapter in the DI container as the binding for the interface. If the library changes or is replaced, only the adapter needs to be rewritten; all domain and application code is untouched.

**When to use:**
- Any third-party library used inside domain or application services
- Framework services (Laravel `Mail`, Symfony `Yaml`, etc.) called from controllers or domain classes
- Any integration point that might change provider (email: Mailgun → Postmark)

**When NOT to use:**
- Simple utility functions with no external I/O where coupling is harmless
- Infrastructure bootstrap code that is inherently framework-specific

**Practical heuristic:** One interface per capability, one adapter per provider implementation.

---

## Dependency Injection & Programming by Contract

**Layer:** All layers (wiring pattern)

**Intent:** Decouple class construction from class usage by passing dependencies in from outside, always typed to interfaces.

**How it works:** Classes declare their dependencies in their constructor, typed to interfaces (not concrete classes). This is "programming by contract" — the class does not care what concrete object it receives, only that it fulfills the interface. A DI container or service locator resolves the concrete class at runtime. This makes every class independently testable by injecting fakes or mocks in tests.

**When to use:**
- Everywhere that a class needs a collaborator it does not create itself (repositories, services, factories, adapters)
- Whenever you want to unit-test a class in isolation

**When NOT to use:**
- Do not use constructor injection for value objects or simple data holders
- Avoid injecting the DI container itself into domain classes — that is a Service Locator anti-pattern

**Practical heuristic:** If you see `new ConcreteClass()` inside a domain or application service (not a factory), it is a dependency that should be injected.

---

## Onion / Layered Architecture (Structural Overview)

**Layer:** All

**Intent:** Organize all code into concentric layers where each layer may only depend on layers deeper (more inward) than itself.

**How it works:** From innermost to outermost: (1) **Domain Model** — pure entities, no dependencies. (2) **Domain Services** — repositories (interfaces), factories, services; depends only on Domain Model. (3) **Application Services** — controllers, CLI handlers; depends on Domain Services. (4) **Infrastructure / Persistence** — ORM repositories, adapters; depends on Domain Services interfaces to implement them. (5) **User Interface / Tests / External Libraries** — outermost ring, depends on everything below it but nothing depends on it.

**When to use:**
- Medium-to-large applications expected to live for years, change frameworks, or switch databases
- Applications that need comprehensive unit test coverage of business logic

**When NOT to use:**
- Tiny scripts or very simple CRUD apps where the overhead outweighs the benefit — a straightforward MVC approach is fine until business complexity grows

**Practical heuristic:** The domain model layer must contain zero `use` statements pointing to framework or library namespaces.

---

## Skinny Controller Pattern

**Layer:** Interface Adapters

**Intent:** Keep controllers as thin response factories that delegate all processing to domain or application services.

**How it works:** A controller action should do three things only: (1) extract parameters from the request, (2) call a domain service method, (3) load the result into a response. All business logic, validation logic beyond input format, and data transformation belong in domain or application services. Controllers that extend a framework base class are acceptable — the coupling is managed by keeping them thin enough that rewriting them when switching frameworks is cheap.

**When to use:**
- Always — this is a universal rule in Clean Architecture

**When NOT to use:**
- Never put business logic in controllers; the question is only how thin is thin enough

**Practical heuristic:** Read the controller action aloud as plain English. If it sounds like business logic rather than "get this, call that, return response," something belongs in a service.

---

## SOLID Principles as Architecture Enablers

**Layer:** All

**Intent:** Five object-oriented design principles that, when applied consistently, make the layered architecture workable.

**How it works:** (1) **SRP** — each class has one reason to change; prevents the obese model and fat controller problems. (2) **OCP** — open for extension, closed for modification; use interfaces and strategy so new behaviors don't require editing existing domain code. (3) **LSP** — subtypes must be substitutable; ensures repository implementations are interchangeable without breaking callers. (4) **ISP** — prefer many small interfaces over one large one; keeps repository contracts focused. (5) **DIP** — depend on abstractions; the mechanism by which the Dependency Rule is enforced in code.

**When to use:**
- Every class in the system, continuously during code review

**When NOT to use:**
- Never skip SOLID; the only debate is degree of strictness for very small throwaway scripts

**Practical heuristic:** Before adding a method to a class, ask: "does this class now have two reasons to change?" If yes, extract a new class.

---

## Coupling as the Primary Architectural Enemy

**Layer:** All

**Intent:** Identify and eliminate tight coupling as the root cause of untestable, hard-to-refactor, and framework-locked code.

**How it works:** Coupling is the amount of dependency one component has on another. High coupling means a change in one place cascades to many others. The Clean Architecture reduces coupling through: fewer dependencies (small, single-purpose classes), dependency injection (pass dependencies in rather than `new`-ing them inside), interfaces instead of concrete classes, and adapters around third-party code. The goal is code where any class can be tested in isolation and any layer can be swapped without rewriting the others.

**When to use:**
- As the primary lens during any design or code review decision

**When NOT to use:**
- Some coupling is unavoidable and acceptable — the domain model necessarily couples to itself; the question is whether coupling crosses layer boundaries in the wrong direction

**Practical heuristic:** Can you instantiate this class in a unit test with no database, no HTTP server, and no framework bootstrap? If not, it has too much coupling.
