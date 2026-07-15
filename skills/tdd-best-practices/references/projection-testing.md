# Testing Read Models and Projections

Source: lessons and counterexamples from [CodelyTV/domain_modeling-projections-course](https://github.com/CodelyTV/domain_modeling-projections-course), corrected for durable delivery, concurrency, versioning, and rebuild semantics.

## Test Layers

- Unit-test a projector's state transition with a fake repository and controlled event metadata.
- Contract-test event serialization with historical fixtures and runtime validation.
- Integration-test the real database constraints, Inbox, mutation, and checkpoint transaction.
- Process-test concurrent workers, crashes, restart recovery, replay, and shadow cutover.
- Acceptance-test query shape and the documented eventual-consistency behavior.

Calling `handler.on(event)` proves handler logic, not bus registration or durable delivery. Queue acknowledgement or row deletion does not prove the projection mutation committed.

## Core Matrix

| Scenario | Required assertion |
|---|---|
| Same event delivered twice | Final state and derived publications are unchanged after the first committed application |
| Two events update one key concurrently | No increment, list entry, or independent field update is lost |
| Event `N+1` arrives before `N` | The stated policy buffers, retries, rejects, or applies it without silently advancing past a gap |
| Prerequisite projection is missing | Delivery remains recoverable and does not starve unrelated keys |
| Projection write succeeds but checkpoint fails | Both roll back, or redelivery is harmless through the Inbox |
| Worker crashes before/after commit | A new worker resumes with neither loss nor an unbounded duplicate effect |
| Old event schema is replayed | Validation and upcasting produce the current internal representation |
| Unsupported/malformed event arrives | It is quarantined with diagnostics and later valid work can progress |
| Full history is rebuilt | Shadow projection equals the live projection under explicit reconciliation checks |
| Rebuild catches live traffic | High-water mark and tail handoff contain no gap or double application |
| Projection lags | Query/API follows its freshness, pending, or read-your-writes contract |

## Assertions That Prevent False Confidence

- Assert exact final rows, values, versions, and processed event IDs, not only collaborator calls.
- For fan-out, assert the exact subscriber set and each independent outcome.
- Execute real transaction callbacks; a mocked `begin()` that resolves without invoking its callback proves no persistence behavior.
- Round-trip every versioned event fixture through the actual serializer/deserializer. Constructor-only tests miss field swaps and incompatible payload changes.
- Use independent database connections or worker processes for lock and race tests; sequential promises do not reproduce concurrency.
- Recreate workers and clear process memory when testing checkpoints, ordering, and deduplication.

## Course Caveats

The course's isolated handler tests are useful interaction examples but do not prove idempotency, ordering, concurrency, durable acknowledgement, or rebuildability. Do not copy its catch-and-log in-memory bus, search-then-save creation guard, read-modify-save counters, unversioned deserialization, or tests whose event mothers produce fields the real Aggregate does not emit.
