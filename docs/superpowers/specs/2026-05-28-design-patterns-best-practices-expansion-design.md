# Design Patterns Best Practices Skill Expansion — Design Spec

**Date:** 2026-05-28
**Skill:** `skills/design-patterns-best-practices`

## Goal

Expand the `design-patterns-best-practices` skill with content sourced from books in `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Design Patterns/` and `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Architecture/Patterns of Enterprise Application Architecture/`, and from the Fran Iglesias blog design-patterns tag. All content in English.

## Constraints

- Same conventions as `oop-best-practices` and `refactoring-best-practices`: topic-based file names, no book/author names in filenames.
- Language examples use all 6 languages (TypeScript, Java, Python, C#, Ruby, PHP) where the language supports the concept.
- Content extracted by reading PDFs directly.

## New Reference Files

Five new files in `skills/design-patterns-best-practices/references/`:

### `behavioral-patterns.md`
- Covers: Observer, Command, Template Method, Chain of Responsibility, Iterator, Mediator
- Each pattern: intent, pressure that calls for it, warning signs, practical heuristic
- Sources: Head First Design Patterns, Drive Into Design Patterns TypeScript, Fran Iglesias blog (observer kata, command bus series)

### `creational-patterns.md`
- Covers: Builder, Abstract Factory, Factory Method (vs simple Factory distinction), Singleton (and why to avoid)
- Each pattern: intent, when to use, warning signs
- Sources: Head First Design Patterns, Drive Into Design Patterns TypeScript

### `structural-patterns.md`
- Covers: Proxy (virtual/protection/remote variants), Facade (with Facade vs Adapter distinction), Bridge, Flyweight
- Sources: Head First Design Patterns, Drive Into Design Patterns TypeScript

### `enterprise-patterns.md`
- Covers: Repository, Service Layer, Unit of Work, Data Mapper vs Active Record, Result pattern
- Sources: Patterns of Enterprise Application Architecture (Fowler), Fran Iglesias blog (result-pattern, repository discussion)

### `patterns-in-practice.md`
- Covers: practical heuristics from real pattern applications: refactoring toward Strategy, Observer lessons, Command Bus implementation, Result pattern, DI container internals, crossing boundaries with meaningful objects
- Sources: Fran Iglesias blog posts (refactor-to-strategy, score-keeper-kata, command_bus_1/2/3, result-pattern, dependency-injection-container, crossing-boundaries)

## Existing Files to Expand

### `pattern-selection-guide.md`
Add new patterns to the pressure → pattern mapping:
- Behavioral: Observer, Command, Template Method, Chain of Responsibility
- Creational: Builder, Abstract Factory, Factory Method
- Structural: Proxy, Facade (expanded), Bridge
- Enterprise: Repository, Service Layer

### `composition-vs-inheritance.md`
Enrich with additional heuristics from Head First Design Patterns and POODR:
- Design principle: program to interfaces, not implementations
- Design principle: favor composition over inheritance
- Concrete examples of when to break the rule
- The OCP angle (open for extension, closed for modification)

## SKILL.md Update

Add 5 new reference entries to `## References`:
- `references/behavioral-patterns.md`
- `references/creational-patterns.md`
- `references/structural-patterns.md`
- `references/enterprise-patterns.md`
- `references/patterns-in-practice.md`

Expand `## Pattern Heuristics` section with brief entries for:
- Observer, Command, Template Method, Builder, Proxy, Facade, Repository

## Language Examples

The current `language-examples.md` has only 1 example (Strategy). Add 4 more before/after pairs in all 6 languages:

1. **State** — object that changes behavior as it transitions through states
2. **Factory Method** — construction with meaningful variation hidden from callers
3. **Decorator** — layered behavior without changing the underlying contract
4. **Observer** — decoupled notification between objects

## Execution Strategy

**Phase 1 — parallel (7 agents):**

| Agent | Output | Primary sources |
|---|---|---|
| A1 | `behavioral-patterns.md` (new) | Head First Design Patterns, Drive Into Design Patterns TS, Fran Iglesias blog |
| A2 | `creational-patterns.md` (new) | Head First Design Patterns, Drive Into Design Patterns TS |
| A3 | `structural-patterns.md` (new) | Head First Design Patterns, Drive Into Design Patterns TS |
| A4 | `enterprise-patterns.md` (new) | Patterns of Enterprise Application Architecture, Fran Iglesias blog |
| A5 | `patterns-in-practice.md` (new) | Fran Iglesias blog (design-patterns tag) |
| A6 | Expand `pattern-selection-guide.md` + `composition-vs-inheritance.md` | Head First Design Patterns, POODR |
| A7 | Update `SKILL.md` | All sources |

**Phase 2 — parallel (6 agents, after Phase 1):**
- One agent per language: add 4 new before/after examples (State, Factory Method, Decorator, Observer)
- Update `language-examples.md` index
- Commit all changes

## Source Books

- `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Design Patterns/Head First Design Patterns.pdf`
- `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Design Patterns/Drive_Into_Design_Pattern/TypeScript/src/`
- `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Design Patterns/Drive_Into_Design_Pattern/design-patterns-es.pdf`
- `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Design Patterns/Implementation Patterns by Kent Beck.pdf`
- `/home/luckys/Documents/Luisi/Courses/Ingeniería_Software/Architecture/Patterns of Enterprise Application Architecture/Patterns of Enterprise Application Architecture - Martin Fowler.pdf`

## Source Blog

- https://franiglesias.github.io/tag/design-patterns/
- Key posts: refactor-to-strategy, score-keeper-kata, command_bus_1, command_bus_2, command_bus_3, result-pattern, dependency-injection-container, crossing-boundaries
