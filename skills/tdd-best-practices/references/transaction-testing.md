# Testing Transaction Boundaries

Source: lessons and counterexamples from [CodelyTV/infrastructure_design-transactions-course](https://github.com/CodelyTV/infrastructure_design-transactions-course), corrected for concurrency and failure semantics.

## Unit Tests

Use a recording transaction fake to verify the application contract: begin before work, commit only after success, rollback after a work failure, rethrow the primary error, and return the wrapped result. Test explicit decorators through their public interface. A mock that only proves `beginTransaction()` was called does not prove atomicity.

Cover commit and rollback failures separately. Commit failure must not be reported as success. If work fails and rollback also fails, preserve the work failure and make the cleanup failure observable. Verify nested calls follow the declared join/savepoint/reject policy.

## Real-Database Integration Tests

Use disposable production-equivalent database infrastructure and force failure after each write. Assert all participating tables and Outbox rows commit together or all remain unchanged. This proves repositories use the same transaction-scoped connection; isolated repository mock tests cannot.

Add concurrent tests with barriers, not sleeps:

- two requests through the same singleton composition must not share an active connection;
- a stale Aggregate version produces exactly one winner;
- constraints, locks, or isolation prevent the specific invariant violation and write-skew scenario;
- connection count returns to baseline after success, work failure, commit failure, and cancellation.

## Side-Effect Tests

Prove no external effect occurs before database commit. For an Outbox, crash after commit and before relay, then verify eventual publication with the same message ID. A deferred in-memory bus test only proves process-local ordering; it cannot prove crash-safe delivery.

## Entry-Point Tests

If middleware/controller code owns the boundary, verify parsing or authorization failures do not open unnecessary transactions, every intended use case is inside the boundary, response serialization happens after commit where appropriate, and client cancellation releases the connection. Prefer use-case-level ownership when equivalent entry points must share semantics.

## Course Caveats

The course tests application and repository behavior but does not directly prove rollback atomicity, concurrent request isolation, connection release, decorator boundaries, or deferred-event crash safety. Its mutable connection field and singleton deferred-event buffer are educational snapshots, not safe production scopes.
