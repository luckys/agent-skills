---
name: infrastructure-design
description: Infrastructure pattern guidance for DDD and hexagonal architecture applications. Use when implementing an event bus or broker relay, applying Outbox, Inbox, retry, dead-letter, ordering, or Change Data Capture patterns, managing database transactions or optimistic Aggregate concurrency, designing cache-aside strategies with Redis, building database views or materialized views, or choosing between synchronous and asynchronous event delivery.
license: MIT
metadata:
  author: luckys
  version: "1.0.0"
---

# Infrastructure Design

Practical infrastructure patterns for layered (hexagonal/DDD) applications. The domain defines business consistency requirements, the application defines unit-of-work boundaries and capability ports, and infrastructure implements transaction and delivery mechanics.

## Workflow

1. **Identify the concern** — is this about event delivery, data consistency, read performance, or query simplification?
2. **Choose the right reference** — load the relevant file from `references/`.
3. **Apply at the right layer** — domain owns business meaning, application owns orchestration contracts, and infrastructure provides technical adapters.
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
| Consumers must tolerate duplicate delivery | Idempotent handler / Inbox | `references/event-bus.md` |
| Legacy writer cannot emit messages | Change Data Capture translator | `references/event-bus.md` |
| Stale Aggregate writes must not overwrite newer decisions | Optimistic version check | `references/transactions.md` |

## Core Principles

- **Core contracts first** — define required ports in the domain or application core; implement adapters in infrastructure. DDD owns Repository semantics; infrastructure owns mapping, transactions, locking, caching, and Outbox mechanics.
- **Transactions wrap units of work** — application code or a typed decorator owns the business boundary; repositories join the scoped transaction and do not commit it independently.
- **Cache is a patch** — add it only when you have a measured performance problem. Remove it when the root cause is fixed.
- **Views abstract queries, not business logic** — a view is a saved SELECT, not a substitute for a domain model.
- **Durability is designed, not implied** — asynchronous delivery is reliable only with durable handoff, idempotent consumers, retries, dead-letter handling, and observability.

## Related Skills

- `ddd-best-practices` — bounded context design and aggregate boundaries
- `design-patterns-best-practices` — Decorator for transparent transaction/cache wrapping
- `oop-best-practices` — domain interface design and dependency inversion
- `tdd-best-practices` — real-database transaction, rollback, concurrency, and delivery tests
- `refactoring-best-practices` — incremental migration of controller/repository transaction boundaries

## References

- `references/event-bus.md` — synchronous failure policy, transactional Outbox, relay claiming, fan-out, Inbox/idempotency, ordering, retries, dead-letter/replay, brokers, and CDC
- `references/transactions.md` — transaction placement, Aggregate consistency boundaries, optimistic concurrency, decorator pattern, unit of work
- `references/cache.md` — cache-aside, write-through, write-behind, where to cache in DDD layers
- `references/database-views.md` — views vs materialized views, triggers for MySQL materialized views, CQRS read side
