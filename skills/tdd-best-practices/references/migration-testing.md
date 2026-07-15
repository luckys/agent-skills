# Testing Data Migrations

Source: testing gaps and counterexamples from [CodelyTV/data_migration-course](https://github.com/CodelyTV/data_migration-course).

Use disposable production-compatible stores and representative dirty data. Unit tests for a transformer do not prove batching, locking, constraints, restart, or cutover behavior.

## Core Matrix

| Scenario | Required assertion |
|---|---|
| Representative and boundary rows | Every field, type, precision, timezone, encoding, and null policy transforms exactly |
| Malformed, duplicate, orphaned, or oversized row | The declared reject, quarantine, repair, or abort policy is observable |
| Same migration runs twice | Row count and canonical values remain stable; newly eligible rows still migrate |
| Process dies mid-batch | Only committed checkpoint progress survives; restart has no gap or destructive duplicate |
| 0, 1, batch-1, batch, batch+1, and many batches | Boundaries, final partial batch, ordering, and termination are correct |
| Two workers or lazy imports race | Claim/range ownership or atomic upsert prevents lost data and unique-key failures |
| Live write races with snapshot row | Source version/watermark policy prevents stale overwrite |
| Delta consumer stops and restarts | Backlog drains from the recorded position without loss; duplicates are harmless |
| Middle row repeatedly fails | It is bounded and quarantined or blocks by explicit policy, never loops invisibly |
| Source/target dependency fails | Job pauses/fails distinctly; outage is not reported as empty data |
| Equal counts but changed identities/values | Reconciliation detects missing, extra, duplicate, and corrupted records |
| Constraint cutover with residual violations | Gate prevents contraction and leaves old reads/writes operational |
| Cutover and rollback/forward repair | Routing, retained deltas, and rerun restore a reconciled state |

## Performance and Operations

- Benchmark production-shaped volume and skew with live-traffic load, not only an empty database.
- Assert bounded concurrency, memory, transaction size, locks, replication lag, and write amplification.
- Verify stream/job completion awaits every target write and checkpoint.
- Inspect query plans for scan, keyset pagination, update, and reconciliation paths.
- Fault-inject deadlocks, timeouts, connection loss, disk/constraint errors, and operator cancellation.
- Verify metrics distinguish scanned, attempted, committed, skipped, quarantined, retried, and remaining rows.

Avoid sleeps and count-only assertions. Persist exact migration artifacts and compare canonical values at a declared watermark.
