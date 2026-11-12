---
name: infrastructure-design
description: Use when designing event buses or broker relays, Outbox/Inbox and CDC delivery, retries, ordering, dead-letter replay, crash recovery, concurrent workers, transaction boundaries, optimistic Aggregate concurrency, Redis caching, or database views in layered applications. Focuses on real adapter guarantees and coordination; use DDD for aggregate and context ownership.
license: MIT
metadata:
  author: luckys
  version: "1.2.0"
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
| Repeated measured reads with acceptable staleness | Cache-Aside at the narrowest reusable layer | `references/cache.md` |
| Complex JOIN queries repeated across the codebase | Database View / Materialized View | `references/database-views.md` |
| Read model needs pre-computed aggregates | Materialized view, trigger, or event-driven projection | `references/database-views.md` |
| Events must survive application crashes | Outbox pattern | `references/event-bus.md` |
| Consumers must tolerate duplicate delivery | Idempotent handler / Inbox | `references/event-bus.md` |
| Legacy writer cannot emit messages | Change Data Capture translator | `references/event-bus.md` |
| Stale Aggregate writes must not overwrite newer decisions | Optimistic version check | `references/transactions.md` |

## Core Principles

- **Core contracts first** — define required ports in the domain or application core; implement adapters in infrastructure. DDD owns Repository semantics; infrastructure owns mapping, transactions, locking, caching, and Outbox mechanics.
- **Transactions wrap units of work** — application code or a typed decorator owns the business boundary; repositories join the scoped transaction and do not commit it independently.
- **Cache is a derived copy** — add it only for a measured problem, with explicit freshness, invalidation, privacy, failure, and removal policies.
- **Views abstract queries, not business logic** — a view is a saved SELECT, not a substitute for a domain model.
- **Durability is designed, not implied** — persist critical events with their writes; asynchronous delivery needs durable handoff, idempotent consumers, retries, dead-letter handling, and observability. Synchronous versus asynchronous delivery is a separate latency and coupling decision.

## Related Skills

- `ddd-best-practices` — bounded context design and aggregate boundaries
- `design-patterns-best-practices` — Decorator for transparent transaction/cache wrapping
- `oop-best-practices` — domain interface design and dependency inversion
- `tdd-best-practices` — real-database transaction, rollback, concurrency, and delivery tests
- `refactoring-best-practices` — incremental migration of controller/repository transaction boundaries
- `data-migration-best-practices` — snapshot/backfill, live-delta handoff, reconciliation, cutover, and repair workflow

## References

Code examples are in TypeScript, each followed by a Kotlin twin (FP style: Arrow `Either`, coroutines).

- Read `references/retry-and-concurrency.md` when an operation can be retried, resumed, or executed by concurrent workers.

- `references/event-bus.md` — synchronous failure policy, transactional Outbox, relay claiming, fan-out, Inbox/idempotency, ordering, retries, dead-letter/replay, RabbitMQ and AWS EventBridge/SQS semantics, brokers, and CDC
- `references/transactions.md` — transaction placement, Aggregate consistency boundaries, optimistic concurrency, decorator pattern, unit of work
- `references/cache.md` — cache placement, keys, invalidation, failures, stampede, capacity, Redis operations, and observability
- `references/database-views.md` — views vs materialized views, trigger-maintained tables, event-driven projections, and workload-based selection
