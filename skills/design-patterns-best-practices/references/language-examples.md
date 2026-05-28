# Language Examples

Use this file as an index to the language-specific example references.

## Covered Languages

- `references/typescript-examples.md`
- `references/java-examples.md`
- `references/python-examples.md`
- `references/csharp-examples.md`
- `references/ruby-examples.md`
- `references/php-examples.md`

## Shared Concept Set

Each language file contains examples for the same 19 patterns:

**Behavioral**
- Strategy — isolating algorithm or policy variation behind a role
- State — behavior driven by state transitions, each state as an object
- Observer — decoupled notification from Subject to registered listeners
- Command — encapsulating a request as an object with execute/undo support
- Template Method — fixed algorithm skeleton with overridable steps in subclasses
- Chain of Responsibility — passing a request along a handler chain
- Iterator — accessing collection elements without exposing internal structure
- Mediator — centralizing communication so objects don't reference each other directly

**Creational**
- Factory Method — construction deferred to subclasses, callers depend on a shared interface
- Builder — step-by-step construction with a fluent interface
- Abstract Factory — creating families of related objects without naming concrete classes
- Singleton — single instance (including trade-off note on global state and testing difficulty)

**Structural**
- Decorator — layered behavior composed at construction time without subclassing
- Proxy — surrogate for another object (lazy loading, protection, remote)
- Facade — simplified interface to a complex subsystem
- Bridge — decoupling abstraction from implementation across two independent axes
- Flyweight — sharing intrinsic state across many fine-grained objects
- Composite — treating leaf and group objects uniformly through a shared interface

**Other**
- Result Pattern — typed success/failure return instead of exceptions

**Enterprise Application Patterns (PoEAA)**
- Transaction Script — procedural logic per use case with direct DB access
- Service Layer — application boundary coordinating domain objects and repositories
- Data Mapper — class that maps between domain objects and DB rows without polluting the domain
- Unit of Work — tracks new/dirty/removed objects and flushes all changes in one transaction
- Data Transfer Object (DTO) — plain immutable object for moving data across layer boundaries
- Value Object (Money) — immutable object with value semantics for monetary amounts
- Special Case — subclass replacing null with safe default behavior
- Gateway — clean interface wrapping an external API or service
- Query Object — encapsulates filter criteria for a collection query
- Layer Supertype — base class for an entire layer holding shared infrastructure behavior

## How to Use This Reference

- Read the language file that matches the user's codebase first.
- If the user works across multiple languages, compare the same pattern across files.
- Prefer concept-level consistency over syntax-level imitation.
- When adding a new pattern, add it to every language file so the set stays aligned.
- Use `pattern-selection-guide.md`, `behavioral-patterns.md`, `creational-patterns.md`, `structural-patterns.md`, or `enterprise-patterns.md` when an example raises a deeper pattern selection question.

## Suggested Reading Order

1. Start with the language the user is actively using.
2. Review Strategy and State first — they are the most common pattern introductions in everyday OO code.
3. Compare Decorator and Observer to understand how composition and notification decouple behavior.
4. Return to `pattern-selection-guide.md` or the specific pattern family file when the example raises a design question.
