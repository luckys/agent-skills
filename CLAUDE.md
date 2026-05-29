# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

A curated collection of reusable agent skills for software design, refactoring, and implementation work. Skills are activated automatically when a task matches their description — they are not invoked by name.

## Structure

```
skills/<skill-name>/
  SKILL.md          # Main operating instructions and frontmatter (name, description, trigger)
  references/       # Detailed guidance loaded on demand by the skill
  scripts/          # Optional deterministic automation
```

## Skill Anatomy

Each `SKILL.md` must have YAML frontmatter with `name` and `description`. The `description` is the activation trigger — it must be precise enough that a model can decide whether to invoke the skill from it alone.

```markdown
---
name: my-skill
description: When to invoke this skill — specific task types and contexts.
---

# Skill Title

...
```

## Current Skills

| Skill | When to invoke |
|---|---|
| `oop-best-practices` | Naming, object boundaries, value objects, cohesion, message-based design |
| `refactoring-best-practices` | Safe incremental changes to existing/legacy code without breaking behavior |
| `design-patterns-best-practices` | Pattern selection (Strategy, State, Factory, Adapter, Decorator, Composite, GoF, PoEAA, Criteria) |
| `ddd-best-practices` | Domain modeling, Bounded Contexts, Aggregates, Domain Events, CQRS, Event Sourcing, Hexagonal Architecture |
| `infrastructure-design` | Event bus, transactions, caching strategies, database views, read model infrastructure |
| `tdd-best-practices` | Red-Green-Refactor cycle, test doubles (mock/stub/fake), outside-in vs inside-out TDD, BDD, test anti-patterns, test pyramid |
| `fp-best-practices` | Pure functions, immutability, function composition/pipe, algebraic data types (Maybe, Either), managing side effects, higher-order functions (map/filter/reduce), currying, FP in JS/TS/Haskell/Elm/Clojure/F#/Elixir |

## Adding a New Skill

1. Create `skills/<skill-name>/SKILL.md` with frontmatter and operating instructions.
2. Add `references/` documents for guidance that should only load on demand.
3. Update `README.md` with a short entry under **Available Skills**.
4. Keep `references/` focused — each file should address one lens or decision type.

## Writing Guidelines

- `description` in frontmatter is the model's decision signal — write it as "Use when…" covering concrete task types.
- `SKILL.md` holds workflow steps and day-to-day rules. Keep it scannable.
- `references/` files are loaded only when the skill directs the model there — keep them detailed and focused.
- Skills cross-link each other via **Related Skills** sections rather than duplicating guidance.
