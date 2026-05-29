---
name: infrastructure-design
description: Guidance for designing infrastructure components in layered applications. Use when implementing event buses, managing database transactions, designing caching strategies, building database views, or choosing between synchronous and asynchronous messaging patterns.
---

# Infrastructure Design

Practical infrastructure patterns for layered (hexagonal/DDD) applications. Each pattern lives in the infrastructure layer but has clear contracts defined in the domain.

## Workflow

1. **Identify the concern** — is this about event delivery, data consistency, read performance, or query simplification?
2. **Choose the right reference** — load the relevant file from `references/`.
3. **Apply at the right layer** — domain defines the interface, infrastructure provides the implementation.
4. **Validate the tradeoff** — every infrastructure decision trades something (complexity, consistency, latency). Make the tradeoff explicit.

## Quick Decision Map

| Concern | Pattern | Reference |
|---|---|---|
| Publishing domain events reliably without losing them | DB-backed Event Bus / Outbox | `references/event-bus.md` |
| Ensuring multiple writes succeed or fail together | Transactions in use case | `references/transactions.md` |
| Slow read queries on frequently accessed data | Cache-Aside at repository | `references/cache.md` |
| Complex JOIN queries repeated across the codebase | Database View / Materialized View | `references/database-views.md` |
| Read model needs pre-computed aggregates | Materialized view with triggers | `references/database-views.md` |
| Events must survive application crashes | Outbox pattern | `references/event-bus.md` |

## Core Principles

- **Domain contracts first** — define `EventBus`, `Cache`, `Repository` interfaces in domain; implement them in infrastructure.
- **Transactions wrap use cases, not repositories** — repositories stay unaware of transactions; the use case or a decorator manages the boundary.
- **Cache is a patch** — add it only when you have a measured performance problem. Remove it when the root cause is fixed.
- **Views abstract queries, not business logic** — a view is a saved SELECT, not a substitute for a domain model.
- **Async beats sync at scale** — prefer publishing events to a DB table and consuming them asynchronously over synchronous in-process dispatch when reliability matters.

## Related Skills

- `ddd-architecture` — bounded context design and aggregate boundaries
- `design-patterns-best-practices` — Decorator for transparent transaction/cache wrapping
- `oop-best-practices` — domain interface design and dependency inversion

## References

- `references/event-bus.md` — DB-backed event bus, outbox pattern, consumer-per-subscriber, retries and dead-letter
- `references/transactions.md` — transaction placement (repo vs use case vs entry point), decorator pattern, unit of work
- `references/cache.md` — cache-aside, write-through, write-behind, where to cache in DDD layers
- `references/database-views.md` — views vs materialized views, triggers for MySQL materialized views, CQRS read side
