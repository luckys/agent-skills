# Advanced Modeling Concepts

Use this reference when the design problem is no longer only about basic object boundaries, but about stronger object choices that still belong to everyday OO design.

Topics that are mainly about safe refactoring or pattern selection belong in the corresponding skills.

## Immutable Objects

Immutability works well when:

- the concept is a value, not an identity
- replacing an object is cheaper than coordinating mutable state
- you want simpler reasoning and fewer hidden side effects

Typical candidates:

- value objects
- first-class collections
- small configuration objects
- result objects

A useful rule:

- prefer returning a new object when the concept represents a value transformation
- keep mutable state only where identity and lifecycle truly matter

## Null Object

Use a null object when absence is common and callers should not branch on it constantly.

It helps when:

- the missing behavior still has a valid neutral response
- conditionals checking for missing collaborators repeat everywhere
- you want the same role to exist in all code paths

Do not use it when absence is exceptional and deserves explicit handling.

## Anemic Models versus Rich Models

An anemic model stores data while behavior and rules live elsewhere.
A rich model keeps important rules close to the concept that owns them.

Warning signs of anemia:

- state is read and changed from outside repeatedly
- services know too much about entity internals
- duplicated rule logic appears across use cases
- tests become fragile because callers must assemble too much internal state

A useful rule:

- services should orchestrate
- entities and value objects should own their rules

## Rename as a Modeling Tool

Rename is not cosmetic.
Use it to move knowledge into the code.

A useful rename:

- makes a concept explicit
- reduces the need for comments
- clarifies responsibility
- reveals when an abstraction is wrong or premature

## Fit for Purpose over Theoretical Purity

Not every system needs every advanced modeling move.
Choose the lightest concept that makes the code easier to explain and cheaper to evolve.

## When a Concept Deserves Its Own Object

A concept earns its own class when it carries more than a plain value.

Signs that a primitive or raw data field should become its own type:

- the same validation logic appears in multiple places before using the value
- several fields always travel together and must stay consistent (Data Clump)
- the concept has its own rules, constraints, or derived computations
- callers cannot trust the value without context because the type alone gives no guarantees

Practical triggers (from Refactor Cotidiano — Fran Iglesias):

- you are repeating `isValidEmail(string $email)` checks everywhere: introduce an `Email` type that validates on construction
- a `firstName` and `lastName` always appear together: introduce a `PersonName` type
- a numeric value has business meaning (a tax rate, a threshold): promote it to a named type or constant

A concept does not yet deserve its own object when:

- it is genuinely a one-off helper with no reuse or rule
- encapsulating it would add indirection without adding clarity
- the domain does not yet use it as a stable idea

## Recognizing When a Model Has Grown Wrong

A class that started as one concept and silently became two is one of the most costly modeling mistakes.

Warning pattern (from Refactor Cotidiano):

- a `Book` class gains an `issue` field to also represent magazines
- later it gains `dvd`, `ebook`, and `cd` fields
- the class now requires inspecting each instance to know what kind of thing it really is

This is the point at which the model forces the reader to think in order to understand — the opposite of what a good model should do.

Rules for detecting a concept that has outgrown its boundary:

- you need to inspect internal state to know what the object is
- null-checking or flag-checking replaces polymorphism
- a new requirement breaks existing cases because the class was never meant to cover them

When this happens, split: each distinct real-world concept becomes its own class. Hierarchy or composition can be introduced once the separation is clear.

## Where Knowledge Belongs: Information Expert and Creator

Two GRASP patterns (Craig Larman, cited in Refactor Cotidiano) answer the question "who should do this?":

**Information Expert**: assign responsibility to the object that already has the information needed to fulfill it. An object should not expose its internals so that an external service can operate on them; the operation belongs inside.

**Creator**: the object that groups or aggregates smaller objects is the right one to create them. Invoice lines do not exist outside an invoice, so `Invoice` should be the one that creates `InvoiceLine` objects — not a service that builds both separately.

These two patterns together reduce the pattern of services that reach into entities, extract data, make decisions, and then push results back in.

## Tell, Don't Ask

Querying an object's state, making a decision outside it, and then setting a result back is a symptom of knowledge in the wrong place.

The Tell, Don't Ask principle (from Refactor Cotidiano — Fran Iglesias):

- each object is responsible for its own state
- callers should tell objects what to do, not ask what they contain and compute the answer externally
- moving the computation inside the object removes the duplication of knowing its internals from outside

A practical test: if a service method reads several fields from an entity to compute one result that concerns only that entity, the method belongs on the entity.

## Delaying Abstractions until Structure Is Stable

Generalizing too early is harder to undo than it looks (from Codigo Sostenible — Carlos Blé):

- ten lines of duplicated code are easy to turn into a loop; the reverse is harder
- a generalized component hides the domain concept it was derived from
- future readers must understand the abstraction before they can understand the domain

The preferred moment to introduce a new abstraction:

- after a requirement is finished and all tests pass
- when reviewing the code reveals obvious duplication of the same business rule
- not while implementing the first occurrence

Avoid introducing abstractions to handle future scenarios that have not been requested yet.

## Intentionality as a Modeling Signal

Code without explicit intentionality forces readers to reconstruct the author's reasoning (from Codigo Sostenible — Carlos Blé).

A model has explicit intentionality when:

- method and type names communicate the purpose, not just the mechanism
- the choice of types themselves documents constraints (`Email` instead of `string`)
- the structure of the code matches the structure of the domain concept

When you inherit code and must modify it, you pay the full cost of missing intentionality immediately. The modeling investment that would have made it cheap to understand is now owed by the new reader.
