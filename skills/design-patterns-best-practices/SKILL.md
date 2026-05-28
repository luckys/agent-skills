---
name: design-patterns-best-practices
description: Practical guidance for selecting and applying design patterns in object-oriented systems. Use when deciding between composition and inheritance, introducing Strategy, State, Factory, Adapter, Decorator, or similar patterns, replacing conditionals with collaboration, or reviewing whether a pattern clarifies the model or adds accidental complexity.
---

# Design Patterns Best Practices

Use this skill when the main question is not just code quality, but pattern choice and pattern fit.

## Working Style

1. Start from the problem shape, not from pattern names.
2. Prefer the smallest pattern that clarifies variation or collaboration.
3. Introduce patterns to reduce coupling and change cost, not to impress readers.
4. Keep the domain language more visible than the pattern vocabulary.
5. Remove or avoid patterns that explain less than the code they replace.

## Pattern Selection Workflow

1. Identify the pressure.
   - Is the problem construction complexity?
   - Is it behavior variation?
   - Is it state-dependent behavior?
   - Is it external integration mismatch?
   - Is it optional layered behavior?

2. Choose the likely pattern family.
   - Strategy for algorithm or policy variation
   - State for behavior driven by state transitions
   - Factory for meaningful construction
   - Adapter for external interface mismatch
   - Decorator for composable behavior layers
   - Composite for tree-shaped structures with uniform treatment

3. Check the fit.
   - Does the pattern remove duplication of knowledge?
   - Does it make change local?
   - Does it improve object collaboration more than a small refactor would?
   - Can the team read it easily?

4. Stop if the pattern is heavier than the problem.

## Pattern Heuristics

### Strategy

Use when behavior varies by policy or algorithm and should be swappable.

### State

Use when the same object changes behavior as it transitions through states and the transition rules matter.

### Factory

Use when creation logic is complex, repeated, or hides meaningful variation.

### Adapter

Use when external APIs do not match the internal model you want.

### Decorator

Use when behavior needs to be layered without changing the underlying contract.

### Composite

Use when leaf and group objects should answer the same messages.

## Warning Signs

- The pattern vocabulary dominates the domain language.
- A simple extraction would solve the problem just as well.
- The pattern creates many classes but leaves the coupling intact.
- Inheritance is used where composition would isolate variation better.
- The team has to understand the pattern before it can understand the business rule.

## References

- Read `references/pattern-selection-guide.md` for pattern-to-problem mapping.
- Read `references/composition-vs-inheritance.md` for structural trade-offs.
- Read `references/language-examples.md` for small examples.

## Related Skills

- Use `oop-best-practices` for everyday code quality choices.
- Use `refactoring-best-practices` when applying a pattern inside risky existing code.

## Source Influences

This skill is synthesized from ideas emphasized in:

- `Head First Design Patterns`
- `Drive Into Design Patterns`
- `Practical Object-Oriented Design in Ruby` by Sandi Metz
- `Implementation Patterns` by Kent Beck
