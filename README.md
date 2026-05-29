# Agent Skills

A curated collection of reusable agent skills for software design, refactoring, and implementation work. Skills activate automatically when a task matches their description — no explicit invocation needed.

## Installation

Install all skills into your project using the [skills CLI](https://www.skills.sh):

```bash
npx skills add luckys/agent-skills
```

Install a single skill:

```bash
npx skills add luckys/agent-skills/oop-best-practices
npx skills add luckys/agent-skills/refactoring-best-practices
npx skills add luckys/agent-skills/design-patterns-best-practices
npx skills add luckys/agent-skills/ddd-best-practices
npx skills add luckys/agent-skills/infrastructure-design
npx skills add luckys/agent-skills/tdd-best-practices
```

Run the command from your project root. Claude Code and other supported agents pick up `SKILL.md` files automatically on the next session.

> Supported agents: Claude Code, Cursor, Codex, GitHub Copilot, Windsurf, Gemini, Cline, and [more](https://www.skills.sh).

## Available Skills

### oop-best-practices

Day-to-day OOP guidance for writing and reviewing clean, maintainable code.

- Naming, object boundaries, and encapsulation
- Tell Don't Ask, Law of Demeter, Object Calisthenics
- Value objects, first-class collections, and primitive obsession
- Message-based design and role-oriented objects
- SOLID principles in practice

### refactoring-best-practices

Safe change guidance for legacy and existing codebases.

- Characterization tests and seam discovery
- Incremental refactoring without breaking behavior
- Splitting large classes and methods
- Sprout, Wrap, and Extract-and-Override techniques
- Decision rules: refactor now vs wait

### design-patterns-best-practices

Pattern selection and application guidance for OO systems.

- All 23 GoF patterns (behavioral, creational, structural)
- All 51 PoEAA enterprise patterns (Transaction Script, Data Mapper, Unit of Work, Repository, Gateway, DTO, Money, Special Case, and more)
- Criteria pattern (composable filters, ordering, pagination)
- Clean Architecture layers and the Dependency Rule
- Kent Beck's Implementation Patterns

### ddd-best-practices

Domain-Driven Design guidance for modeling complex domains.

- Bounded Contexts, Subdomains (Core/Supporting/Generic), Ubiquitous Language
- Aggregates, Entities, Value Objects, Domain Services, Factories
- Context Mapping (ACL, Open Host Service, Partnership, Shared Kernel, and more)
- CQRS, Event Sourcing, Event Storming, Saga, Outbox/Inbox
- Hexagonal Architecture (Ports & Adapters)
- TypeScript DDD skeleton with base classes and use case structure

### infrastructure-design

Infrastructure pattern guidance for DDD and hexagonal architecture applications.

- Event bus: in-memory, DB-backed, RabbitMQ with dead-letter exchanges
- Outbox and Inbox patterns for reliable event delivery
- Transactions: TransactionalDecorator, placement at use case boundary
- Cache-aside with Redis, cache key strategies
- Database views, materialized views, and MySQL trigger patterns

### tdd-best-practices

Test-Driven Development guidance for driving implementation from tests.

- Red-Green-Refactor cycle, the 3 Laws of TDD, FIRST properties
- Test doubles: Dummy, Fake, Stub, Spy, Mock (Meszaros taxonomy)
- London (outside-in) vs Chicago (inside-out) schools
- BDD (Given/When/Then) and ATDD
- James Carr's 15 anti-patterns + Ian Cooper's "TDD, Where Did It All Go Wrong"
- Examples in TypeScript, Java, Python, C#, Ruby, and PHP

## Usage

Skills activate automatically when a task matches their description. No explicit invocation needed.

Example prompts that trigger these skills:

```text
Improve this class design without overengineering it
Refactor this legacy service safely
Should this use Strategy or State?
Replace this type switch with a better object collaboration
Design the Bounded Contexts for this e-commerce domain
How should I structure my Aggregates?
Write tests first for this feature using TDD
What test double should I use here — mock or stub?
Should the event bus use in-memory or DB-backed delivery?
```

## Skill Structure

```
skills/<skill-name>/
  SKILL.md          # Main operating instructions and activation trigger (YAML frontmatter)
  references/       # Detailed guidance loaded on demand by the skill
  scripts/          # Optional deterministic automation
```

Each `SKILL.md` has a `description` field in its YAML frontmatter that acts as the activation trigger. The agent reads it to decide whether to load the full skill.

## Source Influences

Skills are synthesized from:

- *Domain-Driven Design* — Eric Evans
- *Implementing Domain-Driven Design* — Vaughn Vernon
- *Hexagonal Architecture Explained* — Cockburn & Garrido de Paz
- *Patterns of Enterprise Application Architecture* — Martin Fowler
- *Test Driven Development: By Example* — Kent Beck
- *Growing Object-Oriented Software, Guided by Tests* — Freeman & Pryce
- *Working Effectively with Legacy Code* — Michael Feathers
- *Practical Object-Oriented Design in Ruby* — Sandi Metz
- *Implementation Patterns* — Kent Beck
- CodelyTV repositories (TypeScript DDD skeleton, hexagonal architecture examples)
