# Pattern Selection Guide

Use patterns to solve recurring collaboration problems, not to decorate ordinary code.

## If the pressure is behavior variation

Prefer `Strategy` when:
- several algorithms or policies implement the same role
- runtime replacement is useful
- conditionals would otherwise spread

Prefer `State` when:
- behavior changes according to state transitions
- the transition rules are important to model explicitly
- the same object should behave differently over time

## If the pressure is construction

Prefer `Factory` when:
- creation depends on rules or configuration
- callers should not know concrete classes
- setup is repeated or error-prone

## If the pressure is incompatible interfaces

Prefer `Adapter` when:
- an external library has the wrong shape for your model
- you need to isolate third-party details
- the internal domain should not depend on vendor terminology

## If the pressure is layered behavior

Prefer `Decorator` when:
- capabilities should be added incrementally
- combinations of behaviors would explode a class hierarchy
- the core contract should remain stable

## If the pressure is part-whole structures

Prefer `Composite` when:
- leaf and group objects must answer the same messages
- recursive traversal is central to the use case

## If the pressure is event propagation

Prefer `Observer` when:
- one object's state change must trigger updates in many dependents
- the set of dependents is unknown or varies at runtime
- direct method calls would create tight coupling between producer and consumers
- avoid when a simple callback or event bus already exists and the audience is fixed

## If the pressure is encapsulating requests

Prefer `Command` when:
- you need to parameterize objects with operations
- undo/redo is required (store executed commands in a history list)
- operations need to be queued, logged, or replayed
- avoid when the operation is trivial and no deferral or history is needed

## If the pressure is a fixed algorithm with variable steps

Prefer `Template Method` when:
- the overall skeleton of an algorithm is stable but one or more steps vary
- subclasses should fill in specific steps without changing the overall flow
- prefer over `Strategy` when the variation is small and tightly coupled to the base algorithm
- prefer `Strategy` when the entire algorithm is swappable or needs runtime replacement

## If the pressure is routing requests through a chain

Prefer `Chain of Responsibility` when:
- more than one handler might process a request and the handler is not known upfront
- you want to decouple senders from receivers
- the chain is configurable or can change at runtime (e.g., middleware pipelines, filter chains)

## If the pressure is complex construction

Prefer `Builder` when:
- construction involves many optional parts or configuration steps
- the same construction process should produce different representations
- a telescoping constructor or large parameter list is already hurting readability
- avoid when the object has few required fields and no optional combinations

Prefer `Abstract Factory` when:
- you need to create families of related objects that must be used together
- the system should be independent of how its products are created
- switching families (e.g., switching UI toolkit or database driver) must be possible without altering client code

Prefer `Factory Method` when:
- the exact class to instantiate depends on a subclass decision
- you want to defer instantiation to subclasses while keeping a shared creation protocol
- you have one product, not a family — use `Abstract Factory` when products come in related groups

## If the pressure is access control or indirection

Prefer `Proxy` when:
- lazy initialization is needed (virtual proxy: defer expensive object creation)
- access control is needed (protection proxy: check permissions before delegating)
- the real object lives remotely (remote proxy: hide network detail from caller)
- avoid when simple null checks or guards already cover the case

## If the pressure is a complex subsystem

Prefer `Facade` when:
- clients are coupled to too many internal classes of a subsystem
- you want a simple entry point that covers the common use cases
- avoid making the Facade the only way in — advanced callers may still need direct access

## If the pressure is two independent dimensions of variation

Prefer `Bridge` when:
- abstraction and implementation vary independently (e.g., shape + renderer, device + remote)
- a class hierarchy would explode if both dimensions were combined into one
- you want to switch implementations at runtime without touching the abstraction

## If the pressure is data access

Prefer `Repository` when:
- domain objects must be retrieved and stored without knowing the data store
- you want to test domain logic without hitting a real database
- query logic is repeated and scattered across the codebase
- skip Repository when the application is simple CRUD with no domain logic — it adds a layer for no benefit

Prefer `Service Layer` when:
- the application boundary must be explicit (use cases are the unit of work)
- multiple clients (REST, CLI, event handlers) must share the same application logic
- transactions, authorization, and orchestration belong in one place

## Before Applying Any Pattern

Ask:
- What exact pain does this pattern remove?
- Would a rename, extract method, or extract class solve enough of the problem?
- Will the pattern make the next likely change cheaper?
- Is the variation stable enough to deserve this abstraction?
