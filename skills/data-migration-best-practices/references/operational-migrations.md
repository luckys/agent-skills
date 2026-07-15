# Operational Data Migrations

Source: lessons and counterexamples from [CodelyTV/data_migration-course](https://github.com/CodelyTV/data_migration-course), corrected for resumability, concurrency, reconciliation, and cutover safety.

## Snapshot and Live Deltas

When writes continue, establish a high-water mark and durable delta capture before scanning. Valid strategies include a database snapshot plus WAL/binlog position, an Outbox sequence, or CDC offset. Replay deltas after or alongside the snapshot with a source version, timestamp plus tie-breaker, or monotonic compare-and-set rule so stale snapshot rows cannot overwrite newer target state.

Document the boundary precisely: capture start, snapshot position, inclusive/exclusive semantics, replay start, and completion watermark. A replica disconnected at an approximate wall-clock time is not a reliable boundary unless its log position and lag are recorded.

## Resumable Backfills

Use deterministic keyset/range batches:

```sql
SELECT id, source_version, ...
FROM source
WHERE id > :last_committed_id
ORDER BY id
LIMIT :batch_size;
```

Transform and write idempotently, then commit the target batch and checkpoint atomically where possible. Store migration name/version, range, source watermark, status, attempts, counts, checksum, timestamps, and last error. If source and checkpoint cannot share a transaction, make reprocessing safe and advance only after confirmed writes.

Do not repeatedly select arbitrary `LIMIT` rows without ordering or a claim. Do not launch asynchronous writes from a backpressure stream without awaiting them; stream completion must mean target writes completed. Tune batch and concurrency against measured source/target latency, replication lag, lock time, transaction-log growth, and live SLOs.

## Expand and Contract

1. Add nullable/new fields, tables, or indexes without breaking old code.
2. Deploy readers tolerant of old and new shapes.
3. Start maintaining the new shape for live writes with version conflict protection.
4. Backfill historical rows.
5. Reconcile and validate constraints without blocking production unexpectedly.
6. Switch reads/authority behind a reversible flag or routing change.
7. Enforce `NOT NULL`, uniqueness, or foreign keys only after an explicit zero-violation gate.
8. Remove old writes and schema after the rollback window closes.

Dual writes are not atomic across stores. Prefer one authoritative write plus durable change capture. If temporary dual writing is unavoidable, record divergence, make both paths idempotent, define precedence, and reconcile continuously.

## Reconciliation Ladder

Run comparisons over half-open indexed ranges such as `[day_start, next_day_start)`, not `DATE(column)` or hand-built `23:59:59.999` bounds.

Check in increasing strength:

1. both systems and comparison dependencies are healthy;
2. counts by stable partition and migration status;
3. source and target identity sets, including extras and duplicates;
4. canonical field hashes or complete value comparison;
5. referential and domain invariants;
6. freshness/lag relative to the recorded watermark;
7. repaired rows converge after an idempotent rerun.

Never translate a source/query outage into count zero. Report comparison failure separately from data mismatch. Keep reconciliation queries parameterized, index-friendly, bounded, and reproducible from retained artifacts.

## Cutover and Recovery

Define go/no-go thresholds before execution: maximum lag, discrepancy count, quarantine count, error rate, load, and duration. Pause or throttle automatically when live SLOs or replication health degrade. Use canary cohorts or partitions before global cutover.

Rollback is safe only while old readers/writers can represent every new mutation and required deltas are retained. Otherwise prefer forward repair: stop cutover, restore authoritative routing, correct transformation/code, rerun affected ranges, replay deltas, and reconcile again. Never delete source data or migration evidence during the initial cutover window.

## Observability

Expose rows scanned/written/skipped/quarantined, committed checkpoint, remaining estimate, throughput, batch latency, retries, age/lag, source/target errors, constraint failures, and reconciliation differences. Counters must distinguish attempts from committed rows. Logs and quarantine records need migration/range/record identifiers without leaking sensitive values.

## Course Caveats

The course demonstrates useful progression through SQL copy, lazy import, cross-store export, live-event maintenance, backpressure, reconciliation, and replica snapshots. Do not copy count-only validation, unordered `LIMIT` loops, N+1 updates, check-then-insert lazy imports, discarded asynchronous database futures, hard-coded credentials, approximate wall-clock snapshot boundaries, or comparators that turn dependency errors into zero records.
