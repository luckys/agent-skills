---
name: oop-best-practices
description: Day-to-day coding guidance for writing and reviewing clean, maintainable object-oriented code. Use when naming classes and methods, defining object boundaries, introducing value objects, reducing method or class complexity, improving collaboration between objects, or writing new TypeScript, Java, C#, Python, Ruby, PHP, and similar object-oriented code.
---

# OOP Best Practices

Use this skill for everyday coding decisions that shape readability, cohesion, and long-term maintainability.

Use it especially when the task benefits from:

- stronger naming and more explicit abstractions
- clearer object responsibilities and encapsulated invariants
- message-based collaboration and role-oriented objects
- composition over inheritance in everyday design choices

## Working Style

1. Write code for the next reader, not just for the compiler.
2. Keep behavior close to the concept that owns it.
3. Prefer simple collaborations over clever object graphs.
4. Use names, boundaries, and APIs to reveal intent.
5. Let objects carry their own rules when they can.

## Review Workflow

1. Identify the concept.
   - What concept is this code modeling?
   - What rules or invariants belong to that concept?

2. Check the boundary.
   - Is the object exposing raw data or meaningful behavior?
   - Are callers forced to know too much about internal structure?

3. Check the shape.
   - Are methods mixing multiple abstraction levels?
   - Is the class carrying more than one reason to change?
   - Are names explicit enough to understand intent quickly?

4. Apply the lightest useful improvement.
   - rename for clarity
   - extract method
   - extract value object
   - extract first-class collection
   - move behavior to the object that owns the data
   - split the class by responsibility

## Additional Review Lenses

### Naming and abstraction discipline

- If a name is weak, question the abstraction before polishing the wording.
- Avoid premature abstractions that erase the concept or guess too much future reuse.
- Remove duplicated knowledge, not merely duplicated syntax.

### Encapsulation and object responsibility

- Move rules to the concept that owns them.
- Prefer rich objects over data carriers when the concept has meaningful behavior.
- Let services orchestrate when objects can own the rule.

### Message-based design

- Prefer asking collaborators for meaningful behavior over pulling data out.
- Depend on roles and messages rather than concrete internal structure.
- Keep public interfaces small, explicit, and intention revealing.

### Structural simplicity

- Prefer composition when behavior changes independently.
- Keep inheritance shallow and honest.
- Avoid object graphs that force train-wreck navigation.

## Day-to-Day Rules

- Prefer intention-revealing names over short names.
- Keep methods shallow and centered on one level of abstraction.
- Use early returns when they reduce branching noise.
- Keep classes cohesive instead of merely small.
- Replace primitive obsession with value objects when values carry rules.
- Prefer telling collaborators what to do over asking for their data and deciding elsewhere.
- Introduce first-class collections when collections have their own invariants.
- Depend on small roles instead of volatile concrete details.
- Prefer composition when behavior changes independently.
- Keep public APIs smaller than internal implementation detail.

## Good Signals

- The class name matches the behavior it owns.
- Invalid states are rejected early.
- Most methods can be understood without reading unrelated helpers.
- Callers depend on a small surface area.
- The same concept is named consistently across the codebase.

## Warning Signs

- A method needs several comments to be readable.
- A class mostly exposes getters and setters.
- Many callers repeat the same validation or branching logic.
- A change in one concept forces edits across many unrelated files.
- The object model looks like data transport with behavior bolted on elsewhere.

## References

- Read `references/core-principles.md` for condensed coding heuristics.
- Read `references/book-influences.md` for a source-oriented map of the key books behind this skill.
- Read `references/naming-and-abstractions.md` when naming or abstraction quality is the main issue.
- Read `references/message-based-design.md` when object collaboration and roles matter most.
- Read `references/advanced-modeling-concepts.md` for richer object choices that still stay within everyday OO design.
- Read `references/fran-iglesias-practical-guidance.md` for practical OO heuristics distilled from Fran Iglesias.
- Read `references/solid-principles.md` when SOLID violations or design pressure around single responsibility, open-closed, or dependency inversion are the main issue.
- Read `references/object-calisthenics.md` when applying strict OO discipline rules to clean up a class or method.
- Read `references/dependency-management.md` when coupling, dependency direction, or collaborator injection decisions are the focus.
- Read `references/method-design.md` when method length, abstraction level, or intention-revealing structure is the problem.
- Read `references/gradual-abstraction.md` when the right moment to introduce abstraction is unclear or the design is being over-engineered too early.
- Read `references/language-examples.md` for small multi-language examples.
- Read `references/simple-design-rules.md` for Kent Beck's 4 Rules of Simple Design: passes tests, reveals intention, no duplication, fewest elements — with CodelyTV examples.
- Read `references/oop-good-practices-examples.md` for Law of Demeter, Tell Don't Ask, Named Constructors, and cohesion/coupling examples from CodelyTV.
- Read `references/value-objects-advanced.md` for advanced Value Object patterns: base class hierarchies (StringValueObject, Uuid), optional field strategies, typed collections, domain exceptions as named classes.

## Related Skills

- Use `refactoring-best-practices` for risky or legacy code changes.
- Use `design-patterns-best-practices` when the main question is pattern selection.

## Source Influences

This skill is synthesized from ideas emphasized in:

- `Codigo Sostenible` by Carlos Blé
- `Implementation Patterns` by Kent Beck
- `Practical Object-Oriented Design in Ruby` by Sandi Metz
- `99 Bottles of OOP` by Sandi Metz
- Fran Iglesias's `design-principles` articles
- Fran Iglesias's `good-practices` articles
- Fran Iglesias's `Object Calisthenics` series
