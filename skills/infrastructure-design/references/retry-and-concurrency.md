# Retry, Crash Recovery, and Shared State

Use when a command, worker, scheduler, or event consumer can run concurrently or resume after a crash.

## Separate before coordinating

Identify the mutable state each actor owns. Independent facts can use independent keys or files. A genuinely shared invariant, such as available balance or uniqueness, needs atomic database constraints, compare-and-swap, a transaction, or another real coordination mechanism. An instruction to run sequentially is not concurrency control.

For distributed workers, a process-local lock or PID check is insufficient. If leases are needed, specify expiry, renewal, ownership checks, and protection against a late worker committing after ownership changed. Use the database/broker's real atomic capabilities rather than an in-memory approximation.

## Protect a logical operation

Choose one stable operation identity and bind it to the authorized scope and request content. Claim work atomically; concurrent workers must not both observe absence and perform the effect. Persist local changes and their outbox records in the same unit of work. Commit consumer deduplication with its local effect.

For a remote effect, a local transaction alone cannot close the crash window. Persist intent, reuse a supported provider idempotency key, and reconcile an uncertain result. A timeout or lost acknowledgement is an unknown outcome, not proof the effect failed.

A relay marks delivery only after broker acknowledgement. A crash after publish but before marking may duplicate delivery, so consumers still need idempotency. Retain deduplication evidence for the actual retry/replay horizon, including manual dead-letter replay. Retention expiry is part of the guarantee.

## Verify every important crash window

For each operation, exercise two sequential runs, concurrent duplicates, and restart after its important steps. Check failures before commit, after commit but before acknowledgement, and after remote success but before local confirmation. Verify convergence or an explicit pending reconciliation state; no second logical effect should be created silently.

Use the real adapter for uniqueness, rollback, isolation, locking, and serialization claims. Deterministic fakes are useful for orchestration but cannot establish a database's guarantee. Report omitted integration checks separately from passing tests.

## Sources and adaptation

Adapted from Addy Osmani's `api-and-interface-design` and pstack's `principle-make-operations-idempotent` and `principle-separate-before-serializing-shared-state`. PID-based cleanup is not promoted to distributed lock safety. See [third-party-notices.md](third-party-notices.md).
