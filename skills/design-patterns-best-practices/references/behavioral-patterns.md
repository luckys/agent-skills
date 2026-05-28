# Behavioral Patterns

Behavioral patterns define how objects communicate and distribute responsibility. Choose them when the collaboration structure — not just the data structure — is the source of coupling or rigidity. Each pattern below addresses a specific kind of conversational pressure between objects.

---

## Observer

**Intent:** Define a one-to-many subscription mechanism so that multiple objects are notified automatically whenever a subject's state changes.

**Pressure that calls for it:**
You have two parts of a system that must stay in sync — a score tracker and a display, a model and its views, a domain object and its audit log — but they must not know about each other directly. You find yourself calling `display.update()` from inside business logic, or polling a state object in a loop just to detect changes.

**Warning signs you need it:**
- Business logic methods end with explicit calls to update unrelated objects (`scoreDisplay.refresh()`, `logger.record()`).
- A class maintains a reference to a concrete consumer just to push state changes to it.
- You are polling an object on a timer because there is no notification mechanism.

**Warning signs you're overusing it:**
- The flow of a feature requires reading code across five or more detached observer callbacks to understand what happens when an event fires — the indirection now harms comprehension more than coupling would.
- Observers are registered and never deregistered, creating memory leaks or ghost side-effects in tests.
- You reach for Observer when the relationship between publisher and subscriber is always one-to-one and fixed — a direct call or a callback parameter is simpler.

**Practical heuristic:** Prefer the *push* model (subject sends relevant data in the notification) over the *pull* model (observer queries the subject after being notified) — it keeps observers independent and removes the temptation for observers to reach back into the subject for extra state. Register observers at the boundary (composition root or constructor), not inside business methods.

---

## Command

**Intent:** Encapsulate a request as a stand-alone object so it can be parameterized, queued, logged, and undone independently of who issued it.

**Pressure that calls for it:**
You need to decouple the moment a user decision is made (a button click, a menu selection, an API call) from the moment and place where it is executed. You also feel this pressure when you need to support undo, batch execution, scheduling, or audit trails — all of which require treating operations as first-class values.

**Warning signs you need it:**
- An invoker (controller, UI handler) contains the business logic it triggers — it knows *how* to do the work, not just *what* to request.
- You want to support undo but have no way to record what happened; the operation leaves no reversible trace.
- You need to queue, delay, retry, or replay operations, but they are buried inside method calls with no portable representation.

**Warning signs you're overusing it:**
- Every simple method call in the codebase is wrapped in a Command class with a single `execute()` that delegates to one line — the overhead of the abstraction exceeds its benefit.
- You create a Command for a read-only query that has no side effects, no undo requirement, and no scheduling need.
- The Invoker and Receiver are always the same object, so the indirection adds nothing.

**Practical heuristic:** The Invoker must not know the Receiver's concrete type — wire them through a registry or dependency injection at the composition root (a Resolver that maps command types to handlers). When you find yourself building a command bus, the pattern is fully justified; when you only have one command and one handler that never change, a direct method call is cleaner.

---

## Template Method

**Intent:** Define the skeleton of an algorithm in a base class, deferring specific steps to subclasses without letting them alter the overall sequence.

**Pressure that calls for it:**
Several classes share the same multi-step process but differ only in how a few steps are carried out. You find yourself copying algorithm scaffolding across subclasses, or you have a process (parse → validate → format → output) where the steps are fixed but each variant swaps one or two implementations.

**Warning signs you need it:**
- Two or more classes contain nearly identical methods that share a sequence of steps, differing only in details — copy-paste variants of the same workflow.
- The order of operations is invariant (always: open, process, close), but the implementation of each step varies per subclass.
- A subclass must call `super.method()` at the right moment to participate in a shared protocol, which is a code smell signaling that Template Method is already implicit.

**Warning signs you're overusing it:**
- The template method calls so many abstract steps that each concrete subclass must implement ten methods, turning the hierarchy into a fragile, hard-to-navigate tree.
- You introduce Template Method for a process that has only one variant — use a simple function with injected strategies instead.
- Hooks are added preemptively for "future flexibility" without any concrete need, bloating the base class interface.

**Practical heuristic:** Distinguish *required operations* (abstract — must be overridden) from *hooks* (have a sensible default — may be overridden). Keep hooks few and named after what they represent (`hookFormatSubHeader`), not after when they run (`beforeStep3`). If the number of abstract methods grows past three or four, consider replacing Template Method with Strategy to avoid deep inheritance.

---

## Chain of Responsibility

**Intent:** Pass a request along a chain of handlers, each deciding either to process it or forward it to the next handler.

**Pressure that calls for it:**
You have a sequence of checks, filters, or processing steps where the set of handlers, their order, or which one ultimately handles a request may vary at runtime. You feel it when a single method has a long chain of `if/else if` blocks each doing a different kind of validation or routing.

**Warning signs you need it:**
- A monolithic method performs authentication, then authorization, then rate-limit check, then payload validation — all in one place, making each concern hard to test or reorder.
- The set of handlers for a request type changes per environment or customer, but they are hardcoded in a single conditional block.
- You want some requests to be handled and others to fall through silently without the caller knowing which handler acted.

**Warning signs you're overusing it:**
- Every request must always be handled by all handlers in sequence — a pipeline or decorator is a clearer fit than a chain where forwarding is the exception.
- The chain is always the same fixed sequence with no dynamic routing — a simple list of function calls communicates the same intent with less ceremony.
- Handlers are so tightly coupled by shared state that reordering them breaks behavior, defeating the purpose of a chain.

**Practical heuristic:** Build the chain at the composition root using `setNext()` chaining (`basicAuth.setNext(apiKey).setNext(jwt)`), not inside the handlers themselves. Each handler should have one responsibility and return a result (or `null`) rather than mutating shared state — this makes the chain testable in isolation and safe to reorder.

---

## Iterator

**Intent:** Provide a standard way to traverse a collection's elements sequentially without exposing the collection's underlying structure.

**Pressure that calls for it:**
You need to iterate over a custom data structure (a tree, a graph, a paginated result set, a contact hierarchy) using the same `for...of` or `while (iterator.valid())` loop syntax that works for arrays, without leaking internal indices or representation details into the caller.

**Warning signs you need it:**
- Client code accesses a collection's internal array, index, or cursor directly to traverse it — the traversal logic is duplicated wherever the collection is used.
- You have multiple traversal strategies for one collection (alphabetical order, reverse, breadth-first) and want to switch them without changing the client.
- Traversal requires maintaining non-trivial state (multi-level indices, visited nodes) that does not belong in the caller.

**Warning signs you're overusing it:**
- The "collection" is just a plain array and you are implementing Iterator to wrap a `forEach` — the language already provides the abstraction.
- You implement Iterator for a collection that is only ever traversed in one place and one way — a method returning an array is sufficient.
- The Iterator adds mutable position state to an otherwise immutable value object, introducing unexpected side effects.

**Practical heuristic:** Implement the language's native iterator protocol (`Symbol.iterator` / `IterableIterator<T>` in TypeScript) so the collection integrates with `for...of`, spread, and destructuring without any adaptor code. Keep traversal state entirely inside the iterator object, never inside the collection itself — this allows multiple independent iterators over the same collection simultaneously.

---

## Mediator

**Intent:** Reduce chaotic direct dependencies between objects by routing all their communications through a central mediator object.

**Pressure that calls for it:**
A set of collaborating objects (UI components, service classes, chat participants) knows about each other directly, so adding or removing one participant requires changes across many files. Every object has references to several others, and the dependency graph looks like a web rather than a hub-and-spoke.

**Warning signs you need it:**
- Changing one component requires touching several others because they all hold direct references to each other.
- Objects communicate by calling each other's methods in ways that are hard to trace — you must read all participating classes to understand what happens when one event fires.
- You want to add a new participant (a new type of observer, a new UI widget) without modifying the existing participants.

**Warning signs you're overusing it:**
- The mediator grows into a "god object" that contains the full business logic of all its colleagues, turning colleagues into dumb data holders — the coupling moved but did not decrease.
- There are only two collaborators that will never grow beyond two — a direct reference or callback is simpler and just as maintainable.
- You use Mediator to avoid injecting one dependency into a class, when dependency injection would communicate intent more clearly.

**Practical heuristic:** Colleagues should know only the mediator interface — never each other. Keep the mediator's `notify(sender, event, payload?)` logic as a dispatcher: it routes events to the correct colleagues but does not contain business logic itself. If the mediator's `notify` method grows beyond a simple event switch, extract the business rules into the colleagues or domain services and have the mediator call them.

---

## Visitor

**Intent:** Separate an algorithm from the object structure it operates on — let you add new operations to existing object types without modifying them.

**How it works:** Define a Visitor interface with a `visit` method for each concrete element type. Each element class implements `accept(visitor)` which calls `visitor.visit(this)`. To add a new operation, add a new Visitor implementation without touching the element classes.

**When to use:**
- You have a stable object hierarchy (rarely adds new types) but need to add new operations often.
- You need to perform unrelated operations on an object structure and want to keep them separate from the elements.
- Working with ASTs, DOM trees, IR nodes, or similar structures where traversal operations multiply.

**When NOT to use:**
- The object hierarchy changes often — adding a new element type forces changes to every Visitor.
- Operations are naturally part of the element's responsibility (behavior belongs with the object).

**Key trade-off:** Centralizes operations (easy to add operations) but breaks encapsulation (Visitor needs access to element internals) and makes hierarchy extension painful.

**Related patterns:** Composite (Visitor often traverses Composite trees), Iterator (alternative for uniform traversal), Strategy (alternative when operations vary by algorithm, not structure).

**Practical heuristic:** Reach for Visitor when you see a switch/instanceof chain on element types repeated across multiple independent operations — it inverts the dependency so each operation lives in one place.

---

## Memento

**Intent:** Capture and externalize an object's internal state so it can be restored later, without violating encapsulation.

**How it works:** The Originator creates a Memento containing a snapshot of its current state. The Caretaker stores the Memento but never inspects its contents. When rollback is needed, the Originator restores itself from the Memento. The Memento's internal state is only accessible to the Originator.

**When to use:**
- You need undo/redo functionality.
- You need to snapshot state before a risky operation to allow rollback.
- You want to restore an object to a known checkpoint without exposing its internals.

**When NOT to use:**
- The state is large and snapshots are expensive — consider incremental diff-based approaches.
- The object has many references to external resources that can't be meaningfully snapshotted.

**Key trade-off:** Preserves encapsulation of internal state at the cost of memory — each snapshot duplicates state.

**Related patterns:** Command (Memento often stores the state Command needs to undo), Prototype (alternative for cloning state), Iterator (can use Memento to save traversal position).

**Practical heuristic:** If your undo stack stores raw field values extracted from an object, replace it with Mementos — the object knows how to snapshot and restore itself better than any external code does.
