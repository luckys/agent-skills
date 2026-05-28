# Naming and Abstractions

Use this reference when the main design problem is unclear naming, over-generalization, or abstractions that do not carry their weight.

## Names Are Part of the Design

A name is not just a label. It defines the abstraction the reader will imagine.

Good names:

- are easy to pronounce
- are easy to search
- use real problem-space concepts
- distinguish similar concepts clearly
- age well as the codebase grows

Weak names:

- hide intent behind abbreviations
- depend on temporary context
- use technical noise instead of domain meaning
- create aliases for the same concept across the codebase

## If a Name Is Hard to Find, Recheck the Abstraction

When a new method, class, or variable has no convincing name, ask whether:

- it actually mixes several ideas
- it was extracted too early
- it belongs inside another object
- the domain concept is still poorly understood

Sometimes the best fix is not a better name, but a better boundary.

## Avoid Premature Abstractions

Premature abstractions create accidental complexity when:

- the abstraction is broader than current needs
- the domain language does not support it
- several future scenarios are being guessed at once
- the abstraction hides the important concept instead of clarifying it

Prefer to wait until the code reveals stable structure under real use.

## DRY Means Shared Knowledge, Not Identical Syntax

Remove duplication when the same rule or concept is implemented in multiple places.
Do not unify code that only looks similar if it represents different business reasons.

A useful test:

- If one copy changes, should the others always change too?

If not, they may not be the same knowledge.

## Use Domain Language Carefully

Prefer names from the domain when they clarify meaning.
Avoid made-up universal metaphors that disconnect the code from the problem space.

Code becomes harder to understand when:

- the metaphor in code differs from the business conversation
- one concept has many aliases
- one word means different things but context is not explicit

## Practical Checklist

Before keeping a new abstraction, ask:

- Can I name it precisely?
- Does the domain support this concept?
- Does it remove duplicated knowledge?
- Does it make the code easier to change?
- Would the next reader understand it without extra explanation?

## Name After Meaning, Not Current Implementation

Naming a method after what it does right now ties the name to the implementation (from Refactor Cotidiano — Fran Iglesias, drawing on 99 Bottles of OOP):

- a method named `beer` that returns `"beer"` cannot change its internal behavior without breaking the name
- a method named `beverage` describes what the concept represents, not the specific string it returns today
- names that are one level of abstraction above the current value survive requirement changes

Rule: name after what the concept means to the domain, not after the value or mechanism currently behind it.

## Technical Names Are a Design Smell

Embedding type information or pattern names in identifiers obscures the domain (from Codigo Sostenible — Carlos Blé):

Patterns that reduce abstraction quality:

- prefixes encoding type: `sSurname`, `IShoppingCart`, `bIsValid`
- suffixes encoding role: `AbstractShoppingCart`, `ShoppingCartImpl`, `UserFinderSingleton`, `OrderFacade`
- framework conventions imported into application code: `.NET`-style `I`-prefix applied throughout a domain model

Why these hurt:

- they offer information the IDE already provides (syntax coloring, type hints, hover metadata)
- they consume the naming budget for the important part: the domain concept
- they make it harder to find a name with genuine business meaning, which in turn hides poor design

When you cannot name an interface and its single implementation without resorting to a suffix, ask whether the interface is earning its place at all.

## Magic Values Are Unnamed Concepts

A literal value embedded directly in code is a concept that has not been given a name (from Refactor Cotidiano — Fran Iglesias):

- `.21` in `$amount * .21` is a business rule (VAT rate) hidden as a number
- giving it a name (`VAT_RATE`) makes the business rule explicit, prevents duplication, and survives a rate change

The same applies to:

- raw string patterns (regular expressions inlined instead of named constants)
- format strings repeated across the codebase
- numeric thresholds and limits with no label

Each unnamed value is an opportunity to add a name that a domain expert would recognize.

## A Name That Is Hard to Find Diagnoses the Abstraction

The difficulty of naming is data, not just friction (from Codigo Sostenible — Carlos Blé):

When you cannot find two different names for an interface and its implementation, and you fall back to `IFoo` / `FooImpl`, the naming difficulty is a signal that the separation may not be worth having.

When you cannot name a new method or class without resorting to generic words (`Manager`, `Handler`, `Helper`, `Utils`), the boundary is probably wrong.

A name that resists being chosen is telling you:

- the thing mixes several ideas (split it)
- it was extracted too early (inline it and wait)
- the domain concept is still poorly understood (talk to a domain expert)

## Alien Metaphors and Mutant Names

Two patterns that make a codebase progressively harder to read (from Codigo Sostenible — Carlos Blé):

**Alien metaphors**: technical or architectural abstractions that do not match the vocabulary of the business. A "rules engine" that validates loan applications is understandable to engineers; the business speaks of "credit assessment." Code that uses only the technical term creates a translation gap every time a domain expert and a developer communicate.

**Mutant names**: one domain concept that has accumulated different names across different files. The concept was named once, then renamed locally here and there without a global rename. Callers now refer to the same thing as `client`, `customer`, `user`, and `account` depending on where the code was written.

Both patterns compound: alien metaphors get aliased under yet another name when the original metaphor no longer fits. The result is code where understanding any one part requires knowing all the other names for the same thing.

Prevention: when renaming a concept, rename it everywhere; when introducing a technical abstraction, keep a name that the domain recognizes.

## Evolving Names as Understanding Grows

Names are not permanent. They crystallize the current understanding of the domain (from Refactor Cotidiano — Fran Iglesias):

- code always lags behind domain knowledge because the domain changes
- a name that was correct when written may be misleading after the domain evolves
- the right moment to rename is whenever you understand the domain better than the current name reflects

A practical workflow:

- when reading code to fix a bug or add a feature, look for names that no longer match what you now know
- make the rename as a safe refactor before or after the functional change, not mixed with it
- accumulate small renames continuously; do not wait for a dedicated "naming sprint"

The test for whether a rename is ready: if a new team member reads the name in context and correctly predicts what the concept does without extra explanation, the name is good enough.
