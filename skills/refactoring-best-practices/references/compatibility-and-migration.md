# Compatibility and Migration During Refactoring

Use when consolidating APIs, deleting a compatibility path, moving a persisted shape, or simplifying a path with hidden consumers.

## Establish what must remain observable

Record outputs, errors, side effects, ordering, identity, serialization, and resource cleanup. For a suspect abstraction, inspect callers, neighboring conventions, and relevant history before removing it. A behavior-preserving change can still break timing-sensitive or wire-format consumers that symbol search misses.

Keep a failing-before regression check for a bug fix and a current-behavior baseline for refactoring. Change tests only when their assumptions concern obsolete internal structure or the authorized contract changes. A failing test is first evidence to investigate, not permission to weaken its assertion.

## Decide which migration you own

- **Internal, coordinated change:** when all consumers deploy together and no external compatibility promise exists, migrate callers and remove the old path in the same coherent change. Include tests, scripts, serialized configuration, and generated clients in the inventory.
- **Public or independently deployed consumers:** introduce the replacement compatibly, migrate in stages, measure remaining usage where possible, and remove only after the agreed compatibility window. An additive field or new enum value is not automatically compatible with strict readers.

Temporary adapters need a purpose and a removal condition. They are useful for an actual rollout constraint, not permanent insurance against imaginary consumers.

## Persisted data needs an additional plan

Expand the schema, deploy compatible writes, backfill in bounded restartable batches, switch reads, then contract in a later step. Explain compatibility between old/new code and old/new data at each phase, including concurrency during backfill.

A code revert is not a data rollback. Specify whether recovery uses a tested down migration, restoring data, or a forward repair; do not label destructive loss reversible. Test the important transformation and failure/restart cases with the actual adapter.

## Keep the change reviewable

Separate behavior changes from structural moves where that helps review and rollback. Automate repetitive edits when their size or error risk justifies it; neither a fixed line limit nor one PR per extraction is mandatory. Remove replaced tests only after their meaningful behavior is covered at the surviving interface.

## Sources and adaptation

Adapted from Addy Osmani's `code-simplification` and `deprecation-and-migration`, Matt Pocock's `codebase-design/DEEPENING.md`, and pstack's `blast-radius` and `principle-migrate-callers-then-delete-legacy-apis`. Staged compatibility remains necessary for external consumers. See [third-party-notices.md](third-party-notices.md).
