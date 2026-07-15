---
name: oop-best-practices
description: Day-to-day OOP guidance for writing and reviewing clean, maintainable code. Use when naming classes and methods, defining object boundaries, introducing or reviewing Value Objects (equality, hashing, immutability, parsing, normalization, optionality), designing first-class collections, applying Tell Don't Ask or Law of Demeter, enforcing Object Calisthenics, reducing cohesion problems, choosing between inheritance and composition, or reviewing SOLID violations in TypeScript, Java, C#, Python, Ruby, PHP, Go, or Rust.
license: MIT
metadata:
  author: luckys
  version: "1.0.0"
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
- Introduce a Value Object when identity does not matter and semantic guarantees, type safety, or behavior justify a domain type.
- Prefer telling collaborators what to do over asking for their data and deciding elsewhere.
- Introduce first-class collections when collections have their own invariants.
- Give Value Objects semantic equality, matching hash behavior, and deeply immutable observation; do not rely on object-reference equality or shallow `readonly`.
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
- Read `references/language-examples.md` for an index of language-specific example files (TypeScript, Java, Python, C#, Ruby, PHP, Go, Rust).
- Read `references/go-examples.md` for OOP concepts in Go (structs, implicit interfaces, composition, no inheritance).
- Read `references/rust-examples.md` for OOP concepts in Rust (structs, traits, newtype pattern, ownership as immutability).
- Read `references/simple-design-rules.md` for Kent Beck's 4 Rules of Simple Design: passes tests, reveals intention, no duplication, fewest elements — with CodelyTV examples.
- Read `references/oop-good-practices-examples.md` for corrected cross-language lessons on Demeter, Tell Don't Ask, named construction, collection identity, dependency roles, and course counterexamples.
- Read `references/value-objects-advanced.md` as the canonical Value Object guide: selection criteria, invariant ownership, construction/parsing, equality and hashing, deep immutability, behavior, optionality, first-class collections, persistence, testing, and safe evolution.

## Related Skills

- Use `ddd-best-practices` when object ownership also defines a consistency, lifecycle, repository, or transaction boundary.
- Use `tdd-best-practices` for Value Object contract tests, boundary analysis, property-based tests, and deterministic fixtures.
- Use `refactoring-best-practices` for risky or legacy code changes.
- Use `design-patterns-best-practices` when the main question is pattern selection.
- Use `rest-api-best-practices` when designing the HTTP API surface that exposes these objects.

## Source Influences

This skill is synthesized from ideas emphasized in:

- `Codigo Sostenible` by Carlos Blé
- `Implementation Patterns` by Kent Beck
- `Practical Object-Oriented Design in Ruby` by Sandi Metz
- `99 Bottles of OOP` by Sandi Metz
- Fran Iglesias's `design-principles` articles
- Fran Iglesias's `good-practices` articles
- Fran Iglesias's `Object Calisthenics` series
- [CodelyTV OOP Good Practices course](https://github.com/CodelyTV/object_oriented_programming-good_practices-course) (including progressive and overwritten educational counterexamples)
- [CodelyTV Aggregates course](https://github.com/CodelyTV/aggregates-course)
- [CodelyTV Value Objects course](https://github.com/CodelyTV/value_objects-course)
- [CodelyTV Four Rules of Simple Design course](https://github.com/CodelyTV/four_rules_of_simple_design-course) (including intentional naming, YAGNI, interface, duplication, and testing counterexamples)
