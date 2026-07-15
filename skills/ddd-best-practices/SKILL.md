---
name: ddd-best-practices
description: Domain-Driven Design guidance for modeling complex domains. Use when designing Bounded Contexts or Subdomains, discovering Aggregate boundaries from invariants and transactions, defining Aggregate Roots, splitting oversized Aggregates, choosing between Entities, Value Objects, and Domain Services, coordinating cross-Aggregate consistency, applying Context Mapping patterns, implementing CQRS or Event Sourcing, building a Ubiquitous Language, applying Hexagonal Architecture, or reviewing whether domain logic leaks into infrastructure or application layers.
license: MIT
metadata:
  author: luckys
  version: "1.0.0"
---

# DDD Best Practices

Use this skill when the main question is how to model a domain, where to draw boundaries, or how to structure collaboration between subdomains.

## Working Style

1. Start from the domain problem, not from technical constructs.
2. Build a Ubiquitous Language before writing any code.
3. Keep Aggregates small — consistency boundary, not convenience grouping.
4. Prefer Value Objects over primitive types for domain concepts.
5. Let Domain Events tell the story of what happened, not what to do next.
6. Never let infrastructure concerns leak into the domain model.

## Design Workflow

1. **Discover the domain.**
   - Who are the domain experts? What language do they use?
   - What are the core subdomains (Core, Supporting, Generic)?
   - Where does the most complex business logic live?

2. **Draw Bounded Contexts.**
   - One model per context — resist the urge to share models across contexts.
   - Name each context after a team or capability, not a technical layer.
   - Define context relationships explicitly (Partnership, Customer-Supplier, Anti-Corruption Layer, etc.).

3. **Design Aggregates.**
   - Start from one business command and state the invariants it must preserve.
   - Include only state that must commit or reject atomically.
   - Each Aggregate has one root Entity that controls access.
   - Reference other Aggregates by identity and make eventual consistency explicit.
   - Check lifecycle, cardinality, contention, and concurrency; table count does not define the boundary.

4. **Model with tactical patterns.**
   - Entity: has identity that persists over time.
   - Value Object: defined by its attributes; immutable; no identity.
   - Domain Service: stateless logic that doesn't belong to any single Entity.
   - Domain Event: records that something significant happened.
   - Repository: collection-like access to Aggregates.
   - Factory: encapsulates complex construction.

5. **Integrate contexts.**
   - Translate at boundaries — never let one context's model pollute another.
   - Use Anti-Corruption Layers when consuming upstream models you don't control.
   - Translate internal Domain Events into stable Integration Events before crossing a context boundary.

## Heuristics

### Bounded Context
Draw the boundary where the Ubiquitous Language changes — the same word meaning different things is a signal for a boundary.

### Aggregate
If a recognized business invariant requires two objects to commit or reject together, they likely belong in the same Aggregate. Do not confuse a convenient synchronous workflow with an invariant. If temporary inconsistency has an acceptable recovery path, prefer separate Aggregates.

### Entity vs Value Object
If you track it over time or need to distinguish between two instances with the same data, it's an Entity. If all that matters is its value, it's a Value Object.

### Domain Service
If a significant domain operation doesn't naturally belong to any Entity or Value Object, it belongs in a Domain Service — but use sparingly.

### Domain Event
Name events in the past tense: `OrderPlaced`, `PaymentFailed`, `UserRegistered`. They record facts — they don't issue commands.

### Repository
One Repository per Aggregate Root. Never expose a Repository for child entities within an Aggregate.

## Warning Signs

- Anemic Domain Model: Entities have only getters/setters; all logic is in services.
- God Aggregate: one Aggregate contains everything related to a concept.
- Shared database between Bounded Contexts — contexts are coupled through the schema.
- Ubiquitous Language drift: code uses different terms from the domain experts.
- Application Service doing domain logic instead of orchestrating domain objects.
- Repository returning arbitrary queries instead of meaningful collection operations.
- One transaction routinely modifies multiple Aggregate Roots without a documented invariant.
- Public setters or mutable child collections let callers bypass the Aggregate Root.
- Repository access exists for a child Entity inside an Aggregate.
- Aggregate boundaries mirror ORM relationships, UI screens, or table layouts.
- A global uniqueness rule is checked only in memory, without a concurrent persistence constraint.

## References

- Read `references/aggregates.md` for Aggregate discovery, boundary signals, rule ownership, creation vs. reconstitution, concurrency, cross-Aggregate coordination, persistence, and review checklists.
- Read `references/tactical-patterns.md` for Entities, Value Objects, Aggregates, Domain Services, Domain Events, Repositories, Factories.
- Read `references/strategic-design.md` for Subdomains (Core/Supporting/Generic), Bounded Contexts, and Ubiquitous Language.
- Read `references/context-mapping.md` for Context Map patterns: Partnership, Shared Kernel, Customer-Supplier, Conformist, ACL, Open Host Service, Published Language.
- Read `references/cqrs-and-events.md` for CQRS, Event Sourcing, Event Storming, and process managers.
- Read `references/hexagonal-architecture.md` for Ports & Adapters: primary/driven ports, adapters, dependency direction, test strategy, Walking Skeleton implementation, and comparison with Clean/Onion Architecture.
- Read `references/ddd-in-practice.md` for practical DDD application: discovery process (Impact Mapping, Model Exploration Whirlpool), team topology, DDD adoption anti-patterns, and PHP implementation examples (Value Objects, Entities, Aggregate Root, Application Service, Specification).
- Read `references/domain-errors.md` for typed domain error patterns: one error class per failure, error layer ownership, Result type for domain operations, common DDD problems with domain events and errors (ordering, duplication, stuck events).
- Read `references/read-models.md` for read model patterns: aggregate.toPrimitives() vs dedicated read models, CQRS read side, use case structure for queries, projection handlers (DomainEventSubscriber), idempotency, synchronous vs asynchronous projections.
- Read `references/typescript-ddd-examples.md` for the TypeScript DDD skeleton: folder structure by Bounded Context, base classes (ValueObject, Entity, AggregateRoot, DomainEvent), static factory vs reconstitution, use case structure, CommandBus/QueryBus, Object Mother, and Criteria pattern.
- Read `references/go-ddd-examples.md` for DDD in Go: folder structure by Bounded Context, Value Objects, Aggregate Root with unexported fields, Domain Events, Repository interface (port) vs implementation (adapter), Use Case, ACL, CQRS query side, Domain Service.

## Related Skills

- Use `oop-best-practices` for everyday object design within a Bounded Context.
- Use `design-patterns-best-practices` for GoF and enterprise patterns inside the domain.
- Use `refactoring-best-practices` when evolving an existing domain model safely.
- Use `tdd-best-practices` for invariant-first Aggregate tests, deterministic fixtures, and concurrency integration tests.
- Use `infrastructure-design` for transaction boundaries, optimistic locking, and reliable Outbox implementation.
- Use `rest-api-best-practices` when exposing the domain through an HTTP API and translating domain errors to status codes.

## Source Influences

This skill is synthesized from:

- *Domain-Driven Design* by Eric Evans (the blue book)
- *Implementing Domain-Driven Design* by Vaughn Vernon
- *Domain-Driven Design Distilled* by Vaughn Vernon
- *Learning Domain-Driven Design* by Vladik Khononov
- *Patterns, Principles, and Practices of Domain-Driven Design* by Scott Millett & Nick Tune
- *Hexagonal Architecture Explained* by Alistair Cockburn & Juan Manuel Garrido de Paz
- *DDD in PHP* (community resource)
- [CodelyTV Aggregates course](https://github.com/CodelyTV/aggregates-course)
