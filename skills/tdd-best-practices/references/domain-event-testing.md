# Testing Domain Events

Source: lessons and counterexamples from [CodelyTV/domain_modeling-domain_events-course](https://github.com/CodelyTV/domain_modeling-domain_events-course), corrected for behavior-focused tests.

## Aggregate Event Tests

Drive one public command and assert the exact resulting facts:

- event type/name;
- aggregate identity;
- complete business payload;
- exact event count and order when order is contractual;
- controlled metadata through injected clock/ID generation.

Also prove creation records its fact, reconstitution records none, rejected commands leave state and events unchanged, no-op commands follow their stated policy, pulling drains once, and a second pull is empty.

## Application Handoff Tests

Use a stub for reads and recording spies/fakes for writes and publication. Assert after Act:

```typescript
await registrar.execute(command);

expect(repository.save).toHaveBeenCalledTimes(1);
expect(eventBus.publish).toHaveBeenCalledTimes(1);
expect(eventBus.publish).toHaveBeenCalledWith([expectedEvent]);
```

Never call `shouldPublish(expected)` during Arrange if that helper invokes the mock. Never keep the only assertion inside `publish()` or `save()`: if the System Under Test omits the call, no assertion executes. Recreate or reset doubles per test.

## Subscriber Tests

Test handler logic directly with a concrete event and assert its outgoing effect. Separately test registration through the real dispatcher so a wrong `subscribedTo()` declaration cannot hide behind direct `on(event)` tests.

For a multi-event subscriber, use one isolated case per accepted event. Add negative assertions for ignored/stale events: zero saves, sends, and publications.

## Event Bus Contract Tests

Run focused tests against the real in-process bus:

- routes an event only to matching subscribers;
- invokes every registered subscriber exactly once;
- awaits asynchronous handlers;
- defines duplicate-registration behavior;
- handles no-subscriber publication;
- applies its documented failure policy without silently succeeding by accident.

For a synchronous consistency policy, subscriber failure should reject publication. Best-effort logging must be an explicit non-critical contract, not an accidental `catch`.

## Durable Delivery Tests

Use real disposable infrastructure to prove:

- Aggregate state and Outbox rows commit or roll back together;
- relay claiming prevents concurrent duplicate work where intended;
- broker success followed by relay crash remains safely retryable;
- Inbox/deduplication and business effect share one transaction;
- stale source versions are rejected or ignored according to policy;
- retries classify transient vs permanent failures;
- dead-letter replay preserves message identity.

At-least-once delivery requires duplicate-delivery tests. A single happy-path consumer test is insufficient.

## Integration Event Contract Tests

Test translation separately from transport. Assert stable type, schema version, envelope metadata, redaction, and payload. Keep compatibility fixtures for supported historical versions.

## CDC Tests

CDC mapping needs contract tests for each table/action pair, old/new row shape, unsupported mutations, schema changes, stable event identity across retries, empty batches, locking, duplicate delivery, and poison rows. CDC proves observed persistence changes, not domain intent.

## Course Caveats

The course contains many copied tests and self-asserting doubles. Several positive tests can remain green if save, publish, or send is removed; the concrete Event Bus and external-event filter have no direct tests. Treat its fixtures as modeling examples, not evidence of TDD discipline.
