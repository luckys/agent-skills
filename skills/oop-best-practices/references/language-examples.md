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

Each language file contains examples for the same concepts:

- Value Objects and Invariants
- First-Class Collections
- Tell, Don't Ask
- Role-Based Collaboration
- Dependency Injection
- Explicit Interfaces
- Duck Typing / Protocol-Style Roles
- Composition over Inheritance
- Message-Based Design
- Law of Demeter Violation and Fix
- Immutable Objects
- Null Object
- Anemic versus Rich Model
- SOLID — Single Responsibility Violation and Fix
- Object Calisthenics — Wrap Primitive
- Object Calisthenics — No Else Rule
- Dependency Direction
- Composed Method

## How to Use This Reference

- Read the language file that matches the user's codebase first.
- If the user works across multiple languages, compare the same concept across files.
- Prefer concept-level consistency over syntax-level imitation.
- When adding a new concept, add it to every language file so the set stays aligned.
- Use `message-based-design.md`, `naming-and-abstractions.md`, `advanced-modeling-concepts.md`, or `fran-iglesias-practical-guidance.md` when an example raises a deeper OO design question.

## Suggested Reading Order

1. Start with the language the user is actively using.
2. Review value objects, rich versus anemic models, message-based design, and composition over inheritance first.
3. Compare explicit interfaces and protocol-style roles across one static language and one dynamic language.
4. Return to `core-principles.md`, `message-based-design.md`, `advanced-modeling-concepts.md`, or `fran-iglesias-practical-guidance.md` when the example raises a design question.
