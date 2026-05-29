---
name: ddd-best-practices
description: Domain-Driven Design guidance for modeling complex domains. Use when designing Bounded Contexts, defining Aggregates, choosing between Entities and Value Objects, mapping Context relationships, applying CQRS or Event Sourcing, building a Ubiquitous Language, or reviewing whether domain logic leaks into infrastructure layers.
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
   - Each Aggregate has one root Entity that controls access.
   - Enforce invariants within the Aggregate boundary only.
   - Reference other Aggregates by identity (ID), never by object reference.
   - Keep Aggregates small — if it spans multiple tables, reconsider.

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
   - Publish Domain Events for cross-context communication.

## Heuristics

### Bounded Context
Draw the boundary where the Ubiquitous Language changes — the same word meaning different things is a signal for a boundary.

### Aggregate
If two objects must always be consistent together, they belong in the same Aggregate. If eventual consistency is acceptable, they belong in different Aggregates.

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

## References

- Read `references/tactical-patterns.md` for Entities, Value Objects, Aggregates, Domain Services, Domain Events, Repositories, Factories.
- Read `references/strategic-design.md` for Subdomains (Core/Supporting/Generic), Bounded Contexts, and Ubiquitous Language.
- Read `references/context-mapping.md` for Context Map patterns: Partnership, Shared Kernel, Customer-Supplier, Conformist, ACL, Open Host Service, Published Language.
- Read `references/cqrs-and-events.md` for CQRS, Event Sourcing, Event Storming, and process managers.
- Read `references/ddd-in-php.md` for PHP-specific DDD implementation patterns and examples.
- Read `references/hexagonal-architecture.md` for Ports & Adapters: primary/driven ports, adapters, dependency direction, test strategy, Walking Skeleton implementation, and comparison with Clean/Onion Architecture.
- Read `references/ddd-principles.md` for practical DDD application: Knowledge Crunching, Impact Mapping, Model Exploration Whirlpool, Domain Vision Statement, Application Service Layer, team topology, DDD adoption anti-patterns, and conditions for success.

## Related Skills

- Use `oop-best-practices` for everyday object design within a Bounded Context.
- Use `design-patterns-best-practices` for GoF and enterprise patterns inside the domain.
- Use `refactoring-best-practices` when evolving an existing domain model safely.

## Source Influences

This skill is synthesized from:

- *Domain-Driven Design* by Eric Evans (the blue book)
- *Implementing Domain-Driven Design* by Vaughn Vernon
- *Domain-Driven Design Distilled* by Vaughn Vernon
- *Learning Domain-Driven Design* by Vladik Khononov
- *Patterns, Principles, and Practices of Domain-Driven Design* by Scott Millett & Nick Tune
- *Patterns, Principles, and Practices of Domain-Driven Design* by Scott Millett & Nick Tune
- *Hexagonal Architecture Explained* by Alistair Cockburn & Juan Manuel Garrido de Paz
- *DDD in PHP* (community resource)
