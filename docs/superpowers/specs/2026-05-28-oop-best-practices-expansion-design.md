# OOP Best Practices Skill Expansion — Design Spec

**Date:** 2026-05-28
**Skill:** `skills/oop-best-practices`

## Goal

Expand the `oop-best-practices` skill with content sourced directly from the books in `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Code/` and `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Design Patterns/`, and from the Fran Iglesias blog. All content must be in English.

## Constraints

- All new and expanded files follow the same topic-based naming convention as existing references.
- No file named after a book or author (except `fran-iglesias-practical-guidance.md` which already exists).
- Every new OOP concept added to reference files must also appear as an example in all 6 language files (TypeScript, Java, Python, C#, Ruby, PHP), unless the language does not support the concept.
- Content is extracted by reading PDFs directly, not synthesized from training data alone.

## New Reference Files

Five new files in `skills/oop-best-practices/references/`:

### `solid-principles.md`
- Covers SRP, OCP, LSP, ISP, DIP
- Each principle: what pressure it addresses, the rule, warning signs, practical heuristic
- Sources: POODR, Implementation Patterns, Codigo Sostenible, Fran Iglesias blog (design-principles tag)

### `object-calisthenics.md`
- Covers all 9 rules by Jeff Bay:
  1. One level of indentation per method
  2. Don't use the else keyword
  3. Wrap all primitives and strings
  4. First-class collections
  5. One dot per line
  6. Don't abbreviate
  7. Keep all entities small
  8. No classes with more than two instance variables
  9. No getters/setters/properties
- Each rule: intent, practical application, when to relax
- Sources: all books + blog

### `dependency-management.md`
- Covers: dependency direction heuristics, coupling vs cohesion, when to inject vs create, abstract dependencies
- Sources: POODR, Implementation Patterns, Codigo Sostenible

### `method-design.md`
- Covers: composed method pattern, single level of abstraction, intention-revealing method names, method length heuristics
- Sources: Implementation Patterns (Kent Beck), 99 Bottles, Codigo Sostenible

### `gradual-abstraction.md`
- Covers: shameless green (write the simplest working code first), flocking rules (find sameness, find difference, make the change), knowing when abstraction earns its place
- Sources: 99 Bottles (primary), POODR, Codigo Sostenible

## Existing Files to Expand

- **`fran-iglesias-practical-guidance.md`** — add sections for blog posts from the oop, good-practices, and design-principles tags not yet covered in the file
- **`advanced-modeling-concepts.md`** — add heuristics from Codigo Sostenible and El Libro Negro del Programador that fit the existing modeling topics
- **`naming-and-abstractions.md`** — add intention-revealing naming ideas from Implementation Patterns that reinforce existing content

## Language Example Files

### New concepts added to all 6 language files
(TypeScript, Java, Python, C#, Ruby, PHP)

5 new concept sections per file:
1. **SOLID — Single Responsibility Violation and Fix** (before/after showing a class split by reason to change)
2. **Object Calisthenics — Wrap Primitive** (replacing raw primitive with a typed value object)
3. **Object Calisthenics — No Else Rule** (replacing if/else with early return or polymorphism)
4. **Dependency Direction** (depending on abstractions, not volatile concretions)
5. **Composed Method** (a method that reads as a sequence of intention-revealing steps)

### `language-examples.md` update
The shared concept set grows from 13 to 18 concepts. New entries added to the index and suggested reading order.

## SKILL.md Update

The `## References` section gets 5 new entries:

```
- Read `references/solid-principles.md` when SOLID violations or design pressure around single responsibility, open-closed, or dependency inversion are the main issue.
- Read `references/object-calisthenics.md` when applying strict OO discipline rules to clean up a class or method.
- Read `references/dependency-management.md` when coupling, dependency direction, or collaborator injection decisions are the focus.
- Read `references/method-design.md` when method length, abstraction level, or intention-revealing structure is the problem.
- Read `references/gradual-abstraction.md` when the right moment to introduce abstraction is unclear or the design is being over-engineered too early.
```

## Execution Strategy

**Phase 1 — parallel (7 agents):**

| Agent | Output | Primary sources |
|---|---|---|
| A1 | `solid-principles.md` (new) | POODR, Implementation Patterns, Codigo Sostenible, Fran Iglesias blog |
| A2 | `object-calisthenics.md` (new) | All books + blog |
| A3 | `dependency-management.md` (new) | POODR, Implementation Patterns, Codigo Sostenible |
| A4 | `method-design.md` (new) | Implementation Patterns, 99 Bottles, Codigo Sostenible |
| A5 | `gradual-abstraction.md` (new) | 99 Bottles, POODR, Codigo Sostenible |
| A6 | Expand `fran-iglesias-practical-guidance.md` | Blog (oop, good-practices, design-principles tags) |
| A7 | Expand `advanced-modeling-concepts.md`, `naming-and-abstractions.md` | Codigo Sostenible, El Libro Negro, refactorcotidiano |

**Phase 2 — sequential (after all agents complete):**
- Update all 6 language example files with 5 new concept sections each
- Update `language-examples.md` index
- Update `SKILL.md` references section

## Source Books

Located at:
- `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Code/`
  - `99 Bottles of OOP — Sandi Metz.pdf`
  - `Codigo_Sostenible_Carlos_Ble.pdf`
  - `Design-And-Reality-by-Mathias-Verraes .pdf`
  - `El Libro Negro Del Programador - Rafael Gómez Blanes.pdf`
  - `Practical Object-Oriented Design in Ruby 2nd Edition.pdf`
  - `refactorcotidiano.pdf`
  - `refactoring-en-php.pdf`
  - `Working_Effectively_with_Legacy_Code.pdf`
- `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Design Patterns/`
  - `Head First Design Patterns.pdf`
  - `Implementation Patterns by Kent Beck.pdf`
  - `Drive_Into_Design_Pattern/`

## Source Blog

- https://franiglesias.github.io/tag/oop/
- https://franiglesias.github.io/tag/good-practices/
- https://franiglesias.github.io/tag/design-principles/
