# Composition vs Inheritance

This is one of the most important design decisions in object-oriented systems.

## Prefer Composition When

- behavior can vary independently from the host object
- behavior should be replaceable at runtime
- multiple combinations of behavior are possible
- inheritance would force subclasses to inherit behavior they do not want
- the subtype relationship is doubtful or unstable

## Prefer Inheritance When

- the subtype genuinely satisfies the parent contract
- shared invariants are stable
- polymorphism is central and well understood
- composition would add ceremony without reducing coupling

## Red Flags for Inheritance

- overriding methods only to disable parent behavior
- subclasses that use only part of the parent API
- deep hierarchies
- parallel hierarchies created to combine multiple dimensions of variation

## A Useful Rule

If you are using inheritance mainly to reuse code, stop and re-evaluate. Reuse alone is usually not strong enough justification.

## Design Principles at Stake

From Head First Design Patterns (Freeman & Freeman):

- **Encapsulate what varies** — identify the aspects of your application that change and separate them from what stays the same; inheritance bakes variation into the class hierarchy
- **Program to interfaces, not implementations** — declare variables using a supertype so the actual runtime object can be any concrete implementation; this is what makes composition swappable
- **Favor composition over inheritance** (HAS-A can be better than IS-A) — composing objects gives you runtime flexibility and lets you change behavior by swapping the composed object
- **Open-Closed Principle** — classes should be open for extension but closed for modification; composition achieves extension without touching existing code; deep inheritance requires modifying the hierarchy to add behavior
- **Liskov Substitution Principle** — a subtype must be substitutable for its supertype everywhere; if a subclass must override methods to disable or weaken parent behavior, it violates LSP and inheritance is the wrong tool

## The Inheritance Trap

Using inheritance for code reuse — rather than subtyping — produces these failure modes:

- subclasses inherit behavior they do not need and cannot safely override (e.g., `RubberDuck.fly()` that does nothing)
- behavior is locked in at compile time; there is no way to change it at runtime
- adding a new variation (e.g., rocket-powered flying) forces a new subclass and touches the hierarchy
- methods added to the superclass propagate to all subclasses whether they are appropriate or not
- parallel hierarchies emerge when a second dimension of variation is added

The signal: you are overriding methods only to empty them, throw exceptions, or compensate for something the parent assumed was true.

## When to Use Template Method Instead

Template Method is the "composition-with-a-fixed-skeleton" answer to a specific problem: the overall algorithm stays the same but one or more steps differ across variants.

Use Template Method when:
- the invariant steps and the variant steps are clearly separated
- subclasses should only fill in the variant steps — they must not reorder or skip the skeleton
- the variation is small and tightly coupled to the base class (the step belongs in the same class hierarchy)

Use Strategy instead when:
- the entire algorithm is interchangeable, not just a step
- the algorithm needs to change at runtime
- you want to reuse the same algorithm across unrelated types

Template Method is one of the few places where inheritance is the right answer because the IS-A relationship is genuine: the subclass really is a specialized version of the base algorithm.

## The Two-Dimension Rule

When a class varies along two independent axes, inheritance explodes.

Example: `Shape` (Circle, Rectangle) crossed with `Renderer` (VectorRenderer, RasterRenderer) produces four subclasses. Add a third shape and a third renderer: nine classes. N shapes × M renderers = N×M subclasses.

The fix:
- use `Bridge` to separate the two dimensions into independent hierarchies connected by composition
- the abstraction (Shape) holds a reference to the implementation (Renderer) and delegates to it
- adding a new shape or a new renderer is one new class, not N or M new subclasses

Apply this rule whenever you notice parallel hierarchies growing at the same rate.
