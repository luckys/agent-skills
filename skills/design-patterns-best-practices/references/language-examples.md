# Language Examples

Use this file as an index to the language-specific example references.

## Covered Languages

- `references/typescript-examples.md`
- `references/java-examples.md`
- `references/python-examples.md`
- `references/csharp-examples.md`
- `references/ruby-examples.md`
- `references/php-examples.md`

## Shared Concept Set

Each language file contains examples for the same patterns:

- Strategy — isolating algorithm or policy variation behind a role
- State — behavior driven by state transitions, each state as an object
- Factory Method — construction deferred to subclasses, callers depend on a shared interface
- Decorator — layered behavior composed at construction time without subclassing
- Observer — decoupled notification from Subject to registered listeners

## How to Use This Reference

- Read the language file that matches the user's codebase first.
- If the user works across multiple languages, compare the same pattern across files.
- Prefer concept-level consistency over syntax-level imitation.
- When adding a new pattern, add it to every language file so the set stays aligned.
- Use `pattern-selection-guide.md`, `behavioral-patterns.md`, `creational-patterns.md`, or `structural-patterns.md` when an example raises a deeper pattern selection question.

## Suggested Reading Order

1. Start with the language the user is actively using.
2. Review Strategy and State first — they are the most common pattern introductions in everyday OO code.
3. Compare Decorator and Observer to understand how composition and notification decouple behavior.
4. Return to `pattern-selection-guide.md` or the specific pattern family file when the example raises a design question.
