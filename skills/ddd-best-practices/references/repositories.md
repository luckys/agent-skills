# Repositories in DDD

Source: principles and counterexamples reviewed from [CodelyTV/repository_pattern-course](https://github.com/CodelyTV/repository_pattern-course), corrected and generalized for production use.

Use this reference to design or review repository contracts, distinguish repositories from DAOs and gateways, and choose the right persistence and query boundaries.

## Decision Summary

- Give a repository only to an Aggregate Root that needs global access.
- Define the contract in the core using domain types; implement it in infrastructure.
- Model a repository as a collection of complete Aggregates, not as a table-shaped CRUD service.
- Use a dedicated query service or read model for reporting, projections, joins, and partial records.
- Use a gateway for external capabilities such as email, payments, LLMs, or remote APIs.
- Keep transaction control outside individual repository methods and propagate one real transaction context through the whole use case.
- Test application orchestration with a double and test each production adapter against real infrastructure.

Do not introduce a repository automatically for simple CRUD. Transaction Script, Active Record, or a small Data Mapper can be clearer when there is no meaningful Aggregate behavior to protect.

## Repository Semantics

A DDD repository represents the conceptual collection of all instances of one Aggregate Root. It controls which domain objects are globally accessible and hides storage, mapping, caching, and query technology.

```typescript
export interface UserRepository {
  save(user: User): Promise<void>;
  search(id: UserId): Promise<User | null>;
}
```

The contract should expose domain capabilities and domain types. It should not expose ORM entities, query builders, database rows, SQL fragments, transaction handles, or generic maps of fields to update.

One repository per Aggregate Root is a default design rule. Child entities are loaded and changed through the root so callers cannot bypass its invariants. Multiple tables may still store one Aggregate; table count does not determine repository count.

## Contract Ownership and Dependency Direction

The application or domain core owns the port because it defines what persistence capability the model needs. The infrastructure adapter depends inward on that contract.

An Aggregate repository may legitimately be named `UserRepository`: its collection semantics are part of the domain model. Intention-oriented names such as `ForPersistingUsers` are another hexagonal convention, not a universal requirement. Prefer the name that makes the contract's role clearest and use it consistently.

Interfaces are not mandatory. In a structurally typed or functional design, a narrow function can be the port:

```typescript
type SaveUser = (user: User) => Promise<void>;
```

Use a repository object when its operations form one cohesive collection abstraction. Do not create a broad interface solely to make mocking possible.

## Repository, DAO, Query Service, and Gateway

| Abstraction | Purpose | Typical shape |
|---|---|---|
| Repository | Load and persist Aggregate Roots in domain terms | `save(order)`, `search(orderId)` |
| DAO | Expose persistence-oriented access operations | `insert(row)`, `updateColumns(id, data)` |
| Data Mapper | Translate between stored representation and domain objects | `toAggregate(row)`, `toRow(order)` |
| Query service/read model | Return consumer-specific projections efficiently | `latestActiveUsers(): UserReport[]` |
| Gateway | Translate access to an external system or resource | `send(message)`, `charge(payment)`, `generate(prompt)` |

A repository adapter may compose several DAOs or mappers. That persistence detail must not leak into application services.

Do not return a partially hydrated Aggregate to optimize a query. Partial state cannot safely enforce invariants. Return a projection DTO from a query port instead.

## Designing the Contract

Prefer the smallest stable contract needed by current use cases. Avoid generic base repositories with universal CRUD methods unless every Aggregate genuinely shares those semantics.

Use explicit methods when the query has stable domain meaning:

```typescript
interface ShipmentRepository {
  save(shipment: Shipment): Promise<void>;
  search(id: ShipmentId): Promise<Shipment | null>;
  pendingForRoute(route: RouteId): Promise<Shipment[]>;
}
```

Use Criteria or Specification when filters, ordering, and pagination combine dynamically. Generic technical Criteria normally belongs to an application query/read-model port; put it in an Aggregate repository contract only when selectors use genuine domain vocabulary. Keep field/operator mappings in the adapter and bind all values as query parameters. Use a dedicated read model when the result crosses Aggregates, computes reports, or has a consumer-specific shape.

Make hidden query policy explicit. Page size, ordering, similarity semantics, and cursor behavior belong in named parameters/value objects or result types, not as undocumented adapter constants.

## Absence and Errors

Keep repository lookup absence explicit:

- `search(id): Aggregate | null` (or `Option<Aggregate>`) lets the caller decide what absence means.
- An application/domain finder can translate absence into a typed error when the use case requires existence.
- Use `Result`/`Either` at a boundary when callers must recover differently from known operational failures.

The repository should normally report persistence facts, not decide business policy. For example, a unique database collision can be translated to a stable application/domain conflict, while whether duplicate registration is permitted remains a business decision.

Do not catch every infrastructure failure and return `null`; that makes an outage indistinguishable from absence.

## Mapping and Reconstitution

Separate new creation from stored-state reconstitution:

- `create(...)` establishes a new valid identity and may record creation events.
- `fromPrimitives(...)`, `rehydrate(...)`, or a mapper restores state and records no new events.
- `toPrimitives()` is optional; a dedicated mapper is preferable when serialization would pollute the model.

Validate the boundary between untrusted stored data and the domain. Type assertions do not validate nullable columns, malformed JSON, stale enum values, or driver-specific date/number representations. Keep schema constraints and mapper assumptions aligned.

Persist the Aggregate as one consistency unit. Whole-Aggregate upserts without an expected version can silently overwrite concurrent decisions; use optimistic version checks when lost updates matter.

## Transactions and Concurrency

Repository methods should not independently begin and commit transactions. The use case or a transaction decorator owns the unit of work, and every participating repository must use the same transaction-scoped connection.

Opening a transaction at the entry point is not sufficient if repositories continue using a pooled/global connection. Prove propagation with rollback integration tests.

Do not implement business numbering as `MAX(number) + 1`. Use a database sequence, locked counter, serializable allocation with retry, or another atomic allocator. Back global uniqueness with a database constraint and translate collisions deliberately.

For events that require reliable delivery, persist state and Outbox messages in the same transaction. A sequential `save -> publish` flow has a dual-write failure window.

## Caching and Pagination

A cache decorator must preserve repository semantics:

- key Value Objects by canonical value, not object identity;
- define TTL, invalidation, capacity, and multi-process consistency;
- avoid exposing shared mutable Aggregate instances;
- test misses, stale entries, equivalent IDs, and stampede behavior relevant to the system.

Cursor pagination requires a stable total order. If timestamps can tie, use a compound order and cursor such as `(publishedAt, id)`. Return enough metadata for the caller to continue safely, and test ties, deletion of cursor records, and concurrent inserts.

## Testing Strategy

Split tests by responsibility:

| Test | Proves |
|---|---|
| Application unit | load, orchestration, save intent, and error choice |
| Shared repository contract | behavior common to every implementation |
| Adapter integration | queries, mapping, reconstitution, constraints, transactions |
| Concurrency integration | stale-write rejection, uniqueness, and atomic allocation |
| Outbox integration | Aggregate state and messages commit or roll back together |

Arrange stubs before Act and assert recorded calls afterward. Never hide assertions inside `save()` or `publish()` on a self-asserting double: if the System Under Test omits the call, the assertion never executes. Reset or recreate doubles per test.

An in-memory fake is useful for application tests, but it is not proof that SQL, constraints, isolation, mapping, or transaction propagation work. A fake should compare Value Object identities by value and should not accidentally grant semantics the real adapter lacks.

## Refactoring a Legacy System

Introduce the boundary incrementally:

1. Characterize visible behavior and database side effects.
2. Extract the narrow capability the current use case needs.
3. Move SQL and hydration into an adapter without changing behavior.
4. Change the application service to depend on the port.
5. Add focused application tests with a double.
6. Retain adapter integration tests against the real database.
7. Only then improve naming, mapping, errors, or query design in separate steps.

Use parameterized queries throughout the migration. A repository abstraction does not make interpolated SQL safe.

## Review Checklist

- Does the repository belong to an Aggregate Root rather than a table or child Entity?
- Does the contract use domain types and current use-case language?
- Are reporting and partial projections separated from write repositories?
- Are remote capabilities named as gateways rather than repositories?
- Is absence distinguishable from infrastructure failure?
- Does reconstitution avoid creation events and validate stored data?
- Do writes protect against lost updates where required?
- Does one real transaction context reach every participating adapter?
- Are query values bound and fields/operators allow-listed?
- Is pagination deterministic under ties and concurrent changes?
- Are adapter behavior, constraints, rollback, and concurrency tested on real infrastructure?

## Course Caveats

Use the CodelyTV course for its progression and design discussions, not as production-ready source code. Reviewed snapshots include interpolated SQL, incomplete DAO examples, an unused transaction connection, race-prone invoice allocation, identity-keyed caching, unstable cursor pagination, unwired gateway stubs, and mocks that can pass without observing the intended call.
