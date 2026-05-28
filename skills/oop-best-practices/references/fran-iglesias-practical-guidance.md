# Fran Iglesias Practical Guidance

This reference distills practical ideas from Fran Iglesias's `design-principles`, `good-practices`, and `oop` articles into heuristics for everyday object-oriented design.
It keeps only the OO-focused takeaways that fit this skill. Refactoring workflows, pattern selection, and DDD-heavy modeling belong elsewhere.

## Main Themes

Across these articles, several ideas repeat consistently:

- model important concepts as objects instead of stretching primitive types
- move knowledge to the object that owns it
- prefer expressive code over explanatory comments
- keep inheritance shallow and honest
- use composition when behavior has multiple axes of variation
- make roles explicit when different objects can answer the same message
- keep dependencies visible without blindly injecting everything
- let objects control their representation instead of exposing raw structure
- use rename as a safe way to inject knowledge into the code

## Concepts over Raw Types

From `types_vs_value_objects`:

- language types are building blocks, not business concepts by themselves
- a concept should hide its representation behind a stable interface
- do not inherit from primitive-like types just to reuse behavior or satisfy type hints
- composition lets the concept evolve without inheriting invalid behavior

Practical rule:

- if a value has invariants, operations, or meaning of its own, give it its own object instead of leaking primitives through the codebase

## Representation without Leaking Structure

From `representation-2`:

- getters added only for DTOs or serialization weaken information hiding
- the object should stay in control of how its information is exposed
- define representation boundaries from consumer needs, not from the full internal structure
- prefer narrow representation collaborators over exposing every field

Practical rule:

- if a new getter exists only to feed a serializer or mapper, the boundary is probably too leaky

## Rich Objects over Anemic Objects

From `anemic-objects`:

- a data class that only exposes state and setters is often a design smell
- tell-don't-ask and the Law of Demeter are usually violated together
- duplicated rule logic outside the object is a symptom of misplaced responsibility
- tests become easier when behavior moves back into the objects that own the state

Practical rule:

- if a service repeatedly reads an object, computes a rule, and pushes state back, try moving that rule into the object

## Composition, Roles, and Honest Inheritance

From `inheritance-composition`:

- deep inheritance trees often signal too many specialization axes in one hierarchy
- inheritance works best when a small base abstraction defines a stable common behavior
- composition is often the right choice when you want behavior reuse without taxonomic coupling
- roles are a cleaner alternative when several unrelated objects can answer the same message

Practical rule:

- if two dimensions of change would multiply subclasses, prefer composition and small roles

## Interfaces as Roles, Not Taxonomy

From `polimorfismo-y-extensibilidad-de-objetos` and `principios-solid`:

- interfaces let unrelated objects answer the same message without fake inheritance
- a role contract should contain only what clients actually need
- multiple capabilities are better expressed as several small interfaces than as one bloated parent type
- inheritance is for real specialization, not for code reuse or type-hint appeasement

Practical rule:

- if inheritance exists mainly to satisfy a type hint or reuse a small fragment of code, extract a role instead

## Rename to Put Knowledge in Code

From `rename`:

- rename is one of the safest everyday refactors
- better names lower cognitive load more than comments often do
- renaming often reveals what a concept actually means or whether an abstraction is wrong

Practical rule:

- if understanding depends on external explanation, try rename before adding new structure

## Naming Discipline

From `naming-things`:

- use one word for one concept inside a context
- avoid abbreviations and single-letter names that cannot be searched or remembered easily
- keep paired actions consistent, such as `read/write` or `store/retrieve`
- distinguish repeated concepts semantically, not mechanically, such as `billingAddress` instead of `address2`
- use singular, plural, and collective names intentionally

Practical rule:

- if a name still needs a comment to explain what it really is, keep refining it

## Expressive Object Shape

From `codigo-expresivo` and `consistencia-de-objetos`:

- required data belongs in the constructor
- optional data should be introduced explicitly instead of smuggled in as null noise
- things that change together should live together
- value objects should be complete, valid, and ideally immutable
- operations on immutable objects should return new instances instead of mutating hidden state

Practical rule:

- let the public API reveal whether an object is immutable, optional, incomplete, or ready to use

## Visible Dependencies without Blind Injection

From `dependencias-acoplamiento` and `principios-solid`:

- hidden behavioral dependencies create opaque coupling
- inject collaborators when substitution or external behavior matters
- not every object needs dependency injection; simple value-like objects can be created directly
- interfaces should be defined by client needs rather than by framework pressure
- depending on abstractions helps behavioral collaborators evolve independently

Practical rule:

- inject behavior collaborators, but create fresh value-like objects directly when each instance represents data for this call

## Too Many Parameters

From `too-many-parameters`:

- positional parameters are fragile because swapping two same-typed arguments silently produces wrong results
- named parameters or parameter objects solve the ordering problem by making each argument self-documenting at the call site
- when several parameters always travel together they are a Data Clump — group them into an object
- when parameters are extracted from one object to be passed to a function, pass the whole object instead and let the function query it directly
- a constructor with many parameters often reveals missing intermediate abstractions
- a boolean flag parameter usually means the method has two distinct behaviors that should be two methods or two specializations

Practical rule:

- if a function needs three or more positional parameters of the same type, introduce named parameters, a parameter object, or refactor toward whole-object passing

## Replacing Conditionals with Polymorphism

From `introducing-polymorphism`:

- a chain of if/else or switch statements that routes behavior by checking the type or name of an object is a tell-don't-ask violation at the dispatch level
- each branch of such a conditional is a candidate for its own specialization that responds to the same message
- once each type carries its own update logic, the orchestrator simply sends a message and trusts each object to handle it correctly
- introducing a value object for a domain concept (such as quality or quantity) is often the first step before distributing the conditional logic to the right class
- polymorphism eliminates the need for the caller to know about variant types at all

Practical rule:

- if a method reads a name or type field and branches on it to decide what to do, the branching logic belongs in the objects being dispatched, not in the caller

## Separation of Concerns

From `separation-of-concerns`:

- programs should not be written as a single unit that solves the whole problem at once; different parts of the problem should be handled by different parts of the program
- mixing input, transformation, domain logic, and output in the same unit makes each concern harder to change independently
- the principle applies at every scale: within a method, within a class, and across layers
- a function that reads input, processes it, and prints the result is three concerns collapsed into one; splitting them makes each piece independently swappable
- SRP is a class-level application of this same idea — one reason to change means one concern per class

Practical rule:

- if changing the output format requires touching the same code as changing business logic, the concerns are not separated

## Large Class and Accumulated Responsibilities

From `large-class`:

- a class grows large when it is easier to add a method to an existing class than to introduce a new one; this accumulation is a design debt
- a large class typically serves multiple stakeholders with unrelated needs, so a change for one stakeholder risks breaking another's concern
- the extreme case is a God Object — one class that handles authentication, profile updates, notifications, and admin roles all at once
- splitting a large class means identifying which responsibilities respond to which stakeholder or axis of change, then extracting each into its own focused class
- a useful signal: if the class can be annotated with comment blocks like "authentication", "profile", "notifications", each block is a candidate class

Practical rule:

- if a class would need more than one comment block to organize its methods, those blocks are probably separate responsibilities that deserve separate classes

## DRY Means Knowledge, Not Code

From `dry-abstraction`:

- DRY is about knowledge, not about lines of code — "every piece of knowledge should have a single, unambiguous, authoritative representation in a system"
- two methods that look structurally similar but represent different units of knowledge are not DRY violations; merging them produces a false abstraction
- premature abstraction is not an excess of DRY — it is a failure to understand what DRY actually says; eliminating structural duplication without a real shared concept is over-engineering
- the test for a legitimate abstraction: can you name what the two things have in common at the domain level? If you can only name the implementation pattern, the abstraction is premature
- YAGNI complements DRY: do not add knowledge representations for needs you do not yet have

Practical rule:

- if merging two similar methods forces you to add a parameter that controls which behavior runs, the similarity is superficial and the abstraction is wrong

## Cohesion, Coupling, and the Forgotten Principles

From `beyond-solid`, `beyond-solid-2`, `beyond-solid-3`, and `beyond-solid-4`:

- SOLID is incomplete without two additional principles: the Law of Demeter and Tell, Don't Ask
- Tell, Don't Ask: do not read an object's state to make a decision that results in changing that object's state — ask the object to perform the behavior itself
- the Law of Demeter (Principle of Least Knowledge): a unit should only talk to its immediate collaborators; chaining calls through intermediate objects spreads knowledge of the internal structure everywhere
- together, Tell, Don't Ask and the Law of Demeter are the most practical tools for moving behavior to the right object and eliminating anemic classes
- GRASP's Information Expert pattern gives the practical answer: put the responsibility in the class that already holds the information needed to carry it out
- GRASP's Creator pattern: the responsibility for creating an object belongs to the class that aggregates it, contains it, or has the data needed to initialize it
- high cohesion means the elements of a module are strongly related and serve a single purpose; low coupling means modules interact through narrow, stable interfaces
- KISS (Keep It Simple, Stupid): most systems work better when kept simple; complexity should only appear when the problem genuinely requires it
- Fail Fast: validate inputs and invariants as early as possible; low-level modules should not accumulate knowledge about how to handle errors they cannot fix

Practical rule:

- if a method reads state from one object, computes something, and then sets state on that same object, apply Tell, Don't Ask — move the computation into the object
- if a class's creation logic is scattered across callers, the class that aggregates or contains the new object is the natural Creator

## Everyday OO Heuristics

When improving code, try this order:

1. name the concept precisely
2. wrap raw data when it carries its own rules
3. move knowledge to the owner (Information Expert)
4. make dependencies and roles visible
5. protect information hiding instead of adding convenience getters
6. let constructors establish complete valid state
7. make object shape express mutability and optionality
8. prefer composition over inheritance when specialization axes multiply
9. apply Tell, Don't Ask before adding a getter — ask the object to do the work instead
10. separate concerns at every scale: method, class, and layer
11. reduce positional parameters by grouping data clumps into objects or using named parameters
12. replace type-dispatching conditionals with polymorphism once the variants are stable
