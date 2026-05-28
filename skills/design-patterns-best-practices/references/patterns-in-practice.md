# Patterns in Practice

Practical heuristics for applying patterns from real implementation examples.

---

## Refactoring Toward Strategy

**The pattern:** Strategy encapsulates interchangeable algorithms behind a common interface so the caller can select behavior at runtime without knowing the implementation.

**When this is the right move:**
- A method contains a growing `if/else` or `switch` that dispatches to different output formats, pricing rules, or calculation variants.
- Adding a new variant requires editing existing, already-working code.
- The branching logic mirrors a real-world concept ("format", "discount type", "region rule") that deserves its own name.

**The key insight:** The refactoring move is not "extract a strategy object." It is "find the single responsibility that each branch already has and give it a home." Start by extracting the body of each branch into a method, then lift those methods into separate classes that share an interface. A factory (or a registry) then maps the selection condition to the right implementation, removing the branch from the caller entirely.

**Practical rule:** When you catch yourself adding a new `else if` to handle a new output format or algorithm variant, that is the moment to introduce Strategy — not before. Introduce it by extracting the existing branches first, then making the new variant just another class.

---

## Observer in Practice

**The pattern:** Observer lets a subject broadcast state changes to any number of subscribers without knowing who they are, eliminating direct coupling between the producer and every consumer.

**When this is the right move:**
- Two subsystems need to react to each other's changes but should not import or depend on each other directly.
- A single event (score changes, order placed, file saved) must trigger multiple independent reactions.
- The set of reactions is expected to grow without modifying the event source.

**The key insight:** The real value of Observer is not the notification mechanism — it is what it *hides*. The subject never knows who is listening or how many listeners exist. This is also Observer's main design decision: **push vs. pull**. In push mode the subject sends the new state along with the notification (the observer receives a `Score` object, not just a signal). In pull mode the observer queries the subject after being notified. Push is simpler and more explicit; pull is better when observers need to choose which data they actually read.

**Practical rule:** Default to push notification (pass the relevant data with the event). Switch to pull only when different observers need different subsets of the subject's state, and passing everything would create unnecessary coupling to the subject's full interface.

---

## Command Pattern and the Command Bus

**The pattern:** Command encapsulates a request as an object, decoupling the code that decides what to do (the invoker) from the code that knows how to do it (the handler/receiver).

**When this is the right move:**
- Application-layer use cases must be invoked from multiple entry points (HTTP controller, CLI, event listener) without duplicating dispatch logic.
- You need cross-cutting concerns (logging, transactions, authorization, retries) applied uniformly across all operations without modifying individual handlers.
- The set of operations will grow frequently; you want each addition to be a new file, not a change to existing routing code.

**The key insight:** A Command Bus is a Command-pattern router at scale. Its two responsibilities are separate: a **Resolver** maps a command class name to its handler (configured at startup, not at call time), and a **Middleware chain** wraps the execution pipeline. Because handlers are registered by name at composition time, adding a new command never requires touching the bus or any existing handler — it is open for extension by configuration alone. The Middleware chain makes cross-cutting concerns composable: each middleware receives the command and a reference to the bus itself, does its work before and after, then delegates via `bus.handle(command)`.

**Practical rule:** Keep the command object a plain data bag (no behavior, no dependencies). Keep the handler focused on a single use case. Push all cross-cutting logic (logging, error capture, timing) into middleware so handlers stay clean regardless of how many infrastructure concerns are added later.

---

## The Result Pattern

**The pattern:** Result is a value object that wraps either a successful return value or a failure, forcing the caller to explicitly handle both outcomes before accessing the value.

**When this is the right move:**
- A function can fail for business reasons (not infrastructure failures) and the caller needs to decide what to do about it rather than having the stack unwound by an exception.
- The operation is domain-level (validation, business rule check, calculation) and the failure is a normal, expected outcome — not an exceptional event.
- You want the type system to make it impossible to use a result before checking whether it succeeded.

**The key insight:** Exceptions are a flow-control escape hatch: they cross many stack frames and make the main path harder to read. Result keeps failure *in-band* — it is just a value the caller receives and interrogates. The discipline of calling `result.failure()` before `result.unwrap()` is enforced by the type contract (unwrapping a failed result throws), not by convention. This makes every call site self-documenting about its error handling strategy.

**Practical rule:** Use Result for domain operations where "it did not work" is a valid business outcome the caller should reason about explicitly. Keep exceptions for truly unexpected infrastructure failures (disk full, network down) where recovery logic does not belong at the call site.

---

## Dependency Injection Container Internals

**The pattern:** A DI container is a registry of factory functions that resolves object graphs on demand, managing singleton vs. transient lifetimes automatically.

**When this is the right move:**
- Your application has a non-trivial dependency graph and manually wiring it in `main` is fragile or repetitive.
- You need to guarantee a single shared instance of certain components (database connection, in-memory store) across the whole application without using static state.
- You want to swap implementations for testing or different environments by changing configuration, not code.

**The key insight:** A DI container has exactly two responsibilities: **registration** (associate a name with a factory function) and **resolution** (invoke the factory, or return a cached instance for singletons). Understanding this is what prevents cargo-culting: the container is not magic — it is a map of strings to closures. For singletons, the container invokes the factory once and stores the result; subsequent `resolve()` calls return the cached value. Transient dependencies call the factory every time. Factories can call `container.resolve()` themselves to pull their own dependencies, making complex graphs automatic.

**Practical rule:** When building or evaluating a DI container, check that it separates `registerSingleton` from `registerTransient` explicitly — a boolean flag buried in one method is a design smell. If you ever wonder why an object is being recreated or shared unexpectedly, trace it back to which registration method was used.

---

## Crossing Bounded Context Boundaries with Meaningful Types

**The pattern:** Instead of passing raw primitives or anemic DTOs across layer boundaries, use Generic Value Objects (Meaningful Types) — validated wrappers like `NotEmptyString`, `PositiveInteger`, or `Identity` — that carry domain-agnostic invariants without belonging to any specific domain.

**When this is the right move:**
- Data enters the application as raw primitives (JSON, form input, query parameters) and must be validated before reaching domain objects.
- The same validation rule (non-empty string, positive number, UUID format) appears repeatedly across different domain contexts.
- Controllers or application services are doing defensive checks that really belong closer to the data itself.

**The key insight:** There are three distinct transformation steps when data crosses from outside into the domain: (1) raw input → Request DTO with primitives (structural validation only), (2) Request DTO → Command/Query DTO with Generic Value Objects (type-level invariants enforced), (3) Command/Query DTO → Domain Entities/Value Objects (business rules applied). Generic Value Objects live at step 2: they are not domain concepts, but they are not primitives either. A `NotEmptyString` does not belong to your e-commerce domain, but it is a safe building block for a domain-specific `Title` or `CustomerName`.

**Practical rule:** When a domain Value Object's only job is to wrap a string that must not be empty, extract that constraint into a `NotEmptyString` generic type and compose the domain object from it. This keeps domain objects thin, makes the invariant reusable across contexts, and ensures that by the time a Command reaches a use case, all its fields are already guaranteed valid — no defensive checks needed inside the handler.
