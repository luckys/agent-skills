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

## Before Applying Any Pattern

Ask:
- What exact pain does this pattern remove?
- Would a rename, extract method, or extract class solve enough of the problem?
- Will the pattern make the next likely change cheaper?
- Is the variation stable enough to deserve this abstraction?
