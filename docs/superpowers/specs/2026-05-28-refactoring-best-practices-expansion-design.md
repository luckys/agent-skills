# Refactoring Best Practices Skill Expansion — Design Spec

**Date:** 2026-05-28
**Skill:** `skills/refactoring-best-practices`

## Goal

Expand the `refactoring-best-practices` skill with content sourced from the books in `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Refactoring/` and shared books in `Code/`, and from the Fran Iglesias blog refactoring tag. All content in English.

## Constraints

- Same conventions as `oop-best-practices`: topic-based file names, no book/author names in filenames.
- Language examples use all 6 languages (TypeScript, Java, Python, C#, Ruby, PHP) where the language supports the concept.
- Content extracted by reading PDFs directly.

## New Reference Files

Four new files in `skills/refactoring-best-practices/references/`:

### `code-smells.md`
- Covers: Long Method, Large Class, Feature Envy, Data Clumps, Primitive Obsession, Shotgun Surgery, Divergent Change, Middle Man, Inappropriate Intimacy, Comments as smell
- Each smell: what it signals, warning signs, which refactoring move to apply
- Sources: Working Effectively with Legacy Code, refactorcotidiano, Codigo Sostenible

### `legacy-code-techniques.md`
- Covers: Sprout Method, Sprout Class, Wrap Method, Wrap Class, Extract and Override, Sensing Variables, breaking dependencies without tests first
- Sources: Working Effectively with Legacy Code (primary)

### `characterization-tests.md`
- Covers: what characterization tests are, how to write them, golden master technique, approval testing, when to delete them, tests that document existing behavior
- Sources: Working Effectively with Legacy Code, refactorcotidiano, 99 Bottles of OOP

### `fran-iglesias-refactoring-guidance.md`
- Covers: insights from Fran Iglesias's refactoring tag posts not already in the skill
- Sources: https://franiglesias.github.io/tag/refactoring/

## Existing Files to Expand

### `refactoring-moves.md`
Add moves not yet covered:
- Rename (safest everyday move)
- Inline Method / Inline Class
- Extract Interface / Protocol
- Replace Temp with Query
- Separate Query from Modifier
- Split Phase

### `safe-change-workflow.md`
Add sensing & separation content from Working Effectively with Legacy Code:
- Sensing: breaking dependencies to observe effects
- Separation: isolating code under test from hard dependencies

## Language Examples

The current `language-examples.md` has only 1 example (Replace Conditional with Polymorphism). Add 5 more before/after pairs in all 6 languages:

1. **Extract Method** — long method with mixed abstraction levels split into named steps
2. **Extract Class** — class with two reasons to change split into two focused classes
3. **Introduce Value Object** — repeated primitive validation extracted into a typed object
4. **Move Method** — method that uses another object's data more than its own, moved to the right class
5. **Replace Temp with Query** — temporary variable replaced by an extracted query method

## SKILL.md Update

Add 4 new reference entries to `## References`:
- `references/code-smells.md`
- `references/legacy-code-techniques.md`
- `references/characterization-tests.md`
- `references/fran-iglesias-refactoring-guidance.md`

## Execution Strategy

**Phase 1 — parallel (6 agents):**

| Agent | Output | Primary sources |
|---|---|---|
| A1 | `code-smells.md` (new) | Working Effectively with Legacy Code, refactorcotidiano, Codigo Sostenible |
| A2 | `legacy-code-techniques.md` (new) | Working Effectively with Legacy Code (primary) |
| A3 | `characterization-tests.md` (new) | Working Effectively with Legacy Code, refactorcotidiano, 99 Bottles |
| A4 | `fran-iglesias-refactoring-guidance.md` (new) | Blog refactoring tag |
| A5 | Expand `refactoring-moves.md` | All books |
| A6 | Expand `safe-change-workflow.md` | Working Effectively with Legacy Code |

**Phase 2 — parallel (6 agents, after Phase 1):**
- One agent per language file: add 5 new before/after examples
- Update `language-examples.md` index
- Update `SKILL.md` references

## Source Books

- `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Refactoring/Working_Effectively_with_Legacy_Code.pdf`
- `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Refactoring/refactorcotidiano.pdf`
- `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Refactoring/refactoring-en-php.pdf`
- `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Code/Codigo_Sostenible_Carlos_Ble.pdf`
- `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Code/99 Bottles of OOP — Sandi Metz.pdf`

## Source Blog

- https://franiglesias.github.io/tag/refactoring/
