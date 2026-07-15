---
name: data-migration-best-practices
description: Operational data migration guidance. Use when moving or transforming persisted data between schemas, databases, services, or storage technologies; running large backfills; applying expand-and-contract schema changes; combining snapshots with live CDC/events; designing resumable batches and checkpoints; reconciling source and target; or planning cutover, rollback, and repair.
---

# Data Migration Best Practices

Treat migration as a temporary production system with explicit correctness, capacity, observability, and retirement criteria. It changes persisted behavior and is not automatically a refactoring.

## Workflow

1. Define source authority, target contract, transformations, invariants, data classification, and tolerated downtime/staleness.
2. Choose a stable snapshot boundary or high-water mark and start durable capture of live changes before they can escape the snapshot.
3. Expand the target schema compatibly; keep old and new application versions interoperable during rolling deployment.
4. Backfill in bounded, idempotent, resumable batches with deterministic progress and explicit bad-row handling.
5. Apply captured deltas without allowing stale snapshot data to overwrite newer writes.
6. Reconcile availability, counts, identities, values, and domain invariants against a declared watermark.
7. Cut over only when freshness and discrepancy gates pass; monitor and retain a reversal or forward-repair path.
8. Contract old fields, code paths, capture infrastructure, and temporary permissions only after an observation window.

## Decision Rules

- Prefer direct transactional SQL for small same-database transformations that fit the lock and deployment budget.
- Prefer an offline bulk importer for heterogeneous stores or transformations that need application code.
- Prefer lazy/on-read migration only when incomplete migration is acceptable indefinitely and concurrent misses use atomic upsert.
- Combine a bounded snapshot with Outbox, CDC, or event capture when writes must continue during a long migration.
- Use expand-and-contract for online schema changes: add compatible shape, deploy tolerant readers/writers, populate, validate, switch authority, then remove legacy shape.
- Use forward repair rather than destructive rollback once new writes cannot be losslessly represented by the old model.

## Safety Invariants

- Preserve a stable source identity and transformation version for every target row.
- Make reruns harmless through upserts, compare-and-set/version guards, or processed-range records.
- Advance checkpoints only after the batch transaction commits; never use offset pagination over a changing source.
- Order by an immutable key and use keyset/range batches. Multiple workers need disjoint ranges or durable claims.
- Bound reads, writes, concurrency, retries, memory, and lock time against live-traffic capacity.
- Quarantine malformed or constraint-violating rows with redacted diagnostics; never convert infrastructure failure into valid empty data.
- Parameterize queries and keep credentials out of commands, source files, logs, and process arguments.
- Record who approved cutover, the exact watermark, artifacts, checksums, code/schema versions, and repair decisions.

## Gates

Do not cut over on row-count equality alone. Require:

- source and target dependencies are healthy;
- migration lag is within the agreed threshold at the watermark;
- missing, extra, duplicate, and changed identities are measured separately;
- value checksums or full comparisons pass for critical fields;
- target constraints and domain invariants pass;
- quarantined rows are resolved or explicitly accepted;
- rollback/forward-repair and operator runbooks have been rehearsed.

## Related Skills

- Use `infrastructure-design` for Outbox, Inbox, CDC, broker delivery, transactions, locking, and capacity mechanics.
- Use `tdd-best-practices` and its `references/migration-testing.md` for failure, restart, race, reconciliation, and cutover verification.
- Use `refactoring-best-practices` only for introducing code seams and compatibility paths without changing existing behavior.
- Use `ddd-best-practices` to decide whether transformed data changes domain meaning or bounded-context ownership.

## Reference

Read `references/operational-migrations.md` for snapshot/delta handoff, batching, reconciliation, observability, cutover, repair, and course caveats.
