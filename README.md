# Agent Skills

[![skills.sh](https://skills.sh/b/luckys/agent-skills)](https://skills.sh/luckys/agent-skills)

A curated collection of reusable agent skills for software design, refactoring, and implementation work. Skills activate automatically when a task matches their description — no explicit invocation needed.

## Installation

Install all skills into your project using the [skills CLI](https://www.skills.sh):

```bash
npx skills add luckys/agent-skills
```

Install a single skill:

```bash
npx skills add luckys/agent-skills --skill oop-best-practices
npx skills add luckys/agent-skills --skill refactoring-best-practices
npx skills add luckys/agent-skills --skill design-patterns-best-practices
npx skills add luckys/agent-skills --skill ddd-best-practices
npx skills add luckys/agent-skills --skill infrastructure-design
npx skills add luckys/agent-skills --skill tdd-best-practices
npx skills add luckys/agent-skills --skill fp-best-practices
npx skills add luckys/agent-skills --skill rest-api-best-practices
```

Run the command from your project root. Claude Code and other supported agents pick up `SKILL.md` files automatically on the next session.

> Supported agents: Claude Code, Cursor, Codex, GitHub Copilot, Windsurf, Gemini, Cline, and [more](https://www.skills.sh).

## Available Skills

### oop-best-practices

Day-to-day OOP guidance for writing and reviewing clean, maintainable code.

- Naming, object boundaries, and encapsulation
- Tell Don't Ask, Law of Demeter, Object Calisthenics
- Value objects, first-class collections, and primitive obsession
- Value equality/hashing, deep immutability, parsing/normalization, optionality, and persistence mapping
- Message-based design and role-oriented objects
- SOLID principles in practice
- Examples in TypeScript, Java, Python, C#, Ruby, PHP, Go, and Rust

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
- Examples in TypeScript, Java, Python, C#, Ruby, PHP, Go, and Rust

### ddd-best-practices

Domain-Driven Design guidance for modeling complex domains.

- Bounded Contexts, Subdomains (Core/Supporting/Generic), Ubiquitous Language
- Aggregates, Entities, Value Objects, Domain Services, Factories
- Aggregate discovery from invariants, lifecycle, cardinality, contention, and transaction boundaries
- Cross-Aggregate consistency, optimistic concurrency, creation vs. reconstitution
- Repository contracts, Repository vs DAO/query service/gateway, mapping, absence, and adapter testing
- Domain Event semantics, granularity, payloads, lifecycle recording, and Integration Event translation
- Typed domain failure ownership, Option vs Result/Either vs exceptions, and exhaustive handling
- Context Mapping (ACL, Open Host Service, Partnership, Shared Kernel, and more)
- CQRS, Event Sourcing, Event Storming, Saga, Outbox/Inbox
- Hexagonal Architecture (Ports & Adapters)
- TypeScript DDD skeleton with base classes and use case structure

### infrastructure-design

Infrastructure pattern guidance for DDD and hexagonal architecture applications.

- Event bus: in-memory, DB-backed, RabbitMQ with dead-letter exchanges
- Outbox and Inbox patterns for reliable event delivery
- Ordering/versioning, retries, dead-letter replay, idempotency, and Change Data Capture
- Transactions: TransactionalDecorator, placement at use case boundary
- Aggregate optimistic versioning and stale-write conflict handling
- Cache-aside with Redis, cache key strategies
- Database views, materialized views, and MySQL trigger patterns

### tdd-best-practices

Test-Driven Development guidance for driving implementation from tests.

- Red-Green-Refactor cycle, the 3 Laws of TDD, FIRST properties
- Test doubles: Dummy, Fake, Stub, Spy, Mock (Meszaros taxonomy)
- London (outside-in) vs Chicago (inside-out) schools
- BDD (Given/When/Then) and ATDD
- James Carr's 15 anti-patterns + Ian Cooper's "TDD, Where Did It All Go Wrong"
- Invariant-first Aggregate tests, atomic failure assertions, deterministic Mothers, concurrency tests
- Value Object contract tests: equality laws, defensive copies, normalization, and round trips
- Domain Event, subscriber, Event Bus, Outbox/Inbox, and CDC contract tests
- Typed error/Result composition, exhaustive mapping, redaction, and unknown-failure tests
- Examples in TypeScript, Java, Python, C#, Ruby, PHP, Go, and Rust

### fp-best-practices

Functional Programming guidance for writing clean, composable, and predictable code.

- Pure functions, immutability, and referential transparency
- Function composition with `pipe`/`compose`, currying, and partial application
- Algebraic data types: Maybe/Option, Either/Result, sum types (tagged unions)
- Making illegal states unrepresentable with branded types
- Separating pure core from impure shell; dependency injection via function parameters
- Higher-order functions: map, filter, reduce, flatMap, transducers, functors, monads
- Examples in JavaScript, TypeScript, Python, Haskell, Elm, Clojure, F#, Elixir, Go, and Rust

### rest-api-best-practices

REST API design guidance for building clean, consistent, and consumer-friendly APIs.

- URL naming conventions, resource nesting, and versioning strategy
- HTTP method semantics (safe, idempotent, cacheable) and status code selection
- Request and response design: filtering, sorting, cursor and offset pagination, content negotiation
- Error response formats: RFC 9457 Problem Details and consistent custom envelopes
- Security: JWT, API keys, OAuth 2.0, rate limiting, CORS, and HTTPS enforcement
- CRUD anti-pattern: why task-based APIs (`POST /orders/{id}/cancel`) are more expressive than raw CRUD
- HATEOAS, REST architectural constraints, and API-as-a-product thinking
- Examples in TypeScript (Express, NestJS), Python (FastAPI, DRF), Go (Chi), PHP (Laravel), and Java (Spring Boot)

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
How do I replace this null check with a Maybe type?
Should I use Either or throw an exception here?
Refactor this loop to use map/filter/reduce
Design a REST API for this e-commerce domain
What status code should I return when a business rule fails?
Should I use PATCH or a task-based endpoint here?
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
- CodelyTV repositories (TypeScript DDD skeleton, hexagonal architecture examples, Aggregates, Value Objects, and Repository Pattern courses)
- *Mostly Adequate Guide to Functional Programming* — Brian Lonsdorf (Professor Frisby)
- *Domain Modeling Made Functional* — Scott Wlaschin
- *Grokking Simplicity* — Eric Normand
- *Structure and Interpretation of Computer Programs* — Abelson & Sussman
- fp-ts, Effect-TS, and Ramda library documentation
- *REST API Design Rulebook* — Mark Masse
- *RESTful Web APIs* — Leonard Richardson & Mike Amundsen
- RFC 9457 (Problem Details), RFC 9110 (HTTP Semantics)
- Fran Iglesias — API REST series (franiglesias.github.io)
- Derek Comartin — "CRUD APIs are Poor Design" (codeopinion.com)
