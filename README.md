# Agent Skills

Custom collection of reusable agent skills for software design, refactoring, and implementation work.

This repository follows a `vercel-labs/agent-skills` inspired layout so it can grow as a curated set of focused skills:

- `skills/<skill-name>/SKILL.md`
- `skills/<skill-name>/references/`
- `skills/<skill-name>/scripts/`

## Available Skills

### oop-best-practices

Day-to-day coding guidance focused on:

- intention-revealing names
- cohesive classes and methods
- value objects and first-class collections
- explicit object boundaries
- message passing over data digging

### refactoring-best-practices

Safe change guidance focused on:

- characterization tests
- seam discovery
- incremental refactoring
- splitting large classes and methods
- evolving legacy object-oriented code without breaking behavior

### design-patterns-best-practices

Pattern selection guidance focused on:

- choosing the right pattern for the pressure
- composition vs inheritance
- replacing branching with collaboration
- introducing Strategy, State, Factory, Adapter, Decorator, and Composite only when they clarify the model

## Usage

Skills are meant to be activated automatically when a task matches their description.

Example prompts:

```text
Improve this class design without overengineering it
Refactor this legacy service safely
Should this use Strategy or State?
Replace this type switch with a better object collaboration
```

## Skill Structure

Each skill contains:

- `SKILL.md` for the main operating instructions
- `references/` for detailed guidance loaded only when needed
- `scripts/` for optional deterministic automation
