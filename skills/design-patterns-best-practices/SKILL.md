---
name: design-patterns-best-practices
description: Pattern selection and application guidance for OO systems. Use when choosing a GoF pattern (Strategy, State, Observer, Command, Factory, Builder, Decorator, Proxy, Adapter, Composite, etc.), applying PoEAA enterprise patterns (Transaction Script, Service Layer, Data Mapper, Unit of Work, Repository, Gateway, DTO, Money, Special Case), implementing the Criteria pattern, applying Clean Architecture layers, or reviewing whether a pattern reduces or adds accidental complexity.
license: MIT
metadata:
  author: luckys
  version: "1.0.0"
---

# Design Patterns Best Practices

Use this skill when the main question is not just code quality, but pattern choice and pattern fit.

## Working Style

1. Start from the problem shape, not from pattern names.
2. Prefer the smallest pattern that clarifies variation or collaboration.
3. Introduce patterns to reduce coupling and change cost, not to impress readers.
4. Keep the domain language more visible than the pattern vocabulary.
5. Remove or avoid patterns that explain less than the code they replace.

## Pattern Selection Workflow

1. Identify the pressure.
   - Is the problem construction complexity?
   - Is it behavior variation?
   - Is it state-dependent behavior?
   - Is it external integration mismatch?
   - Is it optional layered behavior?

2. Choose the likely pattern family.
   - Strategy for algorithm or policy variation
   - State for behavior driven by state transitions
   - Factory for meaningful construction
   - Adapter for external interface mismatch
   - Decorator for composable behavior layers
   - Composite for tree-shaped structures with uniform treatment

3. Check the fit.
   - Does the pattern remove duplication of knowledge?
   - Does it make change local?
   - Does it improve object collaboration more than a small refactor would?
   - Can the team read it easily?

4. Stop if the pattern is heavier than the problem.

## Pattern Heuristics

### Strategy

Use when behavior varies by policy or algorithm and should be swappable.

### State

Use when the same object changes behavior as it transitions through states and the transition rules matter.

### Factory

Use when creation logic is complex, repeated, or hides meaningful variation.

### Adapter

Use when external APIs do not match the internal model you want.

### Decorator

Use when behavior needs to be layered without changing the underlying contract.

### Composite

Use when leaf and group objects should answer the same messages.

### Observer

Use when one object's state change should trigger reactions in other objects without the source knowing who is listening.

### Command

Use when you need to decouple the sender of a request from its executor, or when requests need to be queued, logged, or undone.

### Template Method

Use when multiple classes share the same algorithm skeleton but differ in specific steps — and the skeleton should not be changed by subclasses.

### Builder

Use when constructing a complex object requires many steps, optional parts, or a specific construction order.

### Proxy

Use when you need a surrogate for another object — to defer creation (virtual), control access (protection), or represent a remote resource (remote).

### Facade

Use when a complex subsystem needs a simplified interface for callers who don't need its full detail.

### Repository

Use when you want to decouple business logic from data access and treat a collection of objects as if it were in memory.

## Warning Signs

- The pattern vocabulary dominates the domain language.
- A simple extraction would solve the problem just as well.
- The pattern creates many classes but leaves the coupling intact.
- Inheritance is used where composition would isolate variation better.
- The team has to understand the pattern before it can understand the business rule.

## References

- Read `references/pattern-selection-guide.md` for pattern-to-problem mapping.
- Read `references/composition-vs-inheritance.md` for structural trade-offs.
- Read `references/language-examples.md` for an index of language-specific example files (TypeScript, Java, Python, C#, Ruby, PHP).
- Read `references/behavioral-patterns.md` for Observer, Command, Template Method, Chain of Responsibility, Iterator, Mediator, Visitor, and Memento.
- Read `references/creational-patterns.md` for Builder, Abstract Factory, Factory Method, Singleton, and Prototype trade-offs.
- Read `references/structural-patterns.md` for Proxy, Facade, Bridge, Flyweight, and Adapter — including the Facade vs Adapter distinction.
- Read `references/enterprise-patterns.md` for all 51 PoEAA patterns grouped by category: Domain Logic, Data Source, ORM Behavioral/Structural, Web Presentation, Distribution, Concurrency, Session State, and Base Patterns.
- Read `references/patterns-in-practice.md` for practical heuristics on refactoring toward patterns, Observer lessons, Command Bus, Result pattern, and DI container internals.
- Read `references/implementation-patterns.md` for Kent Beck's micro-level code patterns: naming, composed methods, guard clauses, value objects, lazy/eager initialization, collection accessors, and method objects.
- Read `references/clean-architecture.md` for Clean Architecture layers (Entities, Use Cases, Interface Adapters, Frameworks), the Dependency Rule, Ports & Adapters, Skinny Controllers, and SOLID as architecture enablers.
- Read `references/criteria-pattern.md` for the Criteria pattern: composable filters (field + operator + value), ordering, pagination, CriteriaToSqlConverter in infrastructure, and Criteria.fromPrimitives() for HTTP query params.

## Related Skills

- Use `oop-best-practices` for everyday code quality choices.
- Use `refactoring-best-practices` when applying a pattern inside risky existing code.

## Source Influences

This skill is synthesized from ideas emphasized in:

- `Head First Design Patterns`
- `Drive Into Design Patterns`
- `Practical Object-Oriented Design in Ruby` by Sandi Metz
- `Implementation Patterns` by Kent Beck
