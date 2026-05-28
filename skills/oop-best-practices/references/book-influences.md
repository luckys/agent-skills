# Book Influences

This reference maps the most useful ideas from the core books behind this skill into practical object-oriented heuristics.

## `99 Bottles of OOP` by Sandi Metz

Main ideas to preserve in daily work:

- Start with the simplest understandable solution that is good enough now.
- Let stable variation earn a better abstraction instead of guessing it too early.
- Notice when conditionals are really hiding a missing collaborator or role.
- Prefer designs that make the next change local and obvious.

Actionable takeaways:

- Reach a clear first solution before chasing elegance.
- Prefer simple object boundaries over speculative extension points.
- Introduce role-based collaborators when variation is stable enough to deserve a name.

## `Codigo Sostenible` by Carlos Blé

Main ideas to preserve in daily work:

- Names are abstractions, so naming quality directly shapes design quality.
- Generality can damage comprehension when it erases real concepts.
- Premature abstractions create accidental complexity.
- DRY is about duplicated knowledge, not every repeated line that merely looks similar.

Actionable takeaways:

- Prefer concrete and pronounceable names from the problem space.
- If you cannot find a good name for an abstraction, question whether the abstraction is ready to exist.
- Remove duplicated rules and concepts, not just duplicated syntax.

## `Practical Object-Oriented Design in Ruby` by Sandi Metz

Main ideas to preserve in daily work:

- Single responsibility keeps classes understandable and cheap to change.
- Depend on behavior, not on data structure.
- Inject and isolate dependencies to reduce coupling.
- Ask collaborators for what you need instead of telling them how to do it.
- Duck typing reveals roles that transcend concrete classes.
- Message-based design leads to better object boundaries than class-first thinking.

Actionable takeaways:

- Let each class have one clear reason to change.
- Prefer explicit public interfaces and smaller contexts.
- Trust collaborators to honor their roles.
- Reach for inheritance only when the abstraction and substitution are genuinely stable.

## How to Use These Influences

When reviewing or writing object-oriented code, ask:

- Is the code only as abstract as current knowledge justifies?
- Are names helping the reader see the design intent?
- Are responsibilities, interfaces, and roles clearer after the change?
- Does the object model own its own rules instead of leaking them outward?
