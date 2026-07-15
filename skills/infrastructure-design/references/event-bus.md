# Event Delivery Infrastructure

Sources: CodelyTV event-bus courses and [domain_modeling-domain_events-course](https://github.com/CodelyTV/domain_modeling-domain_events-course), corrected for transaction, retry, and consumer semantics.

This reference owns transport and reliability. The domain owns which facts occurred; the application translates public contracts; infrastructure delivers them.

## Message Contract Assumptions

Local in-process dispatch may carry internal Domain Events. Cross-process or cross-context transport should carry explicitly translated, versioned Integration Events.

A durable envelope needs a stable message ID, type, schema version, aggregate/source identity, occurrence time, correlation/causation metadata where relevant, and immutable payload. Preserve the same ID across every retry and relay attempt.

## Synchronous In-Process Bus

Use an in-memory bus for simple same-process reactions when process-crash loss is acceptable or the caller's transaction explicitly includes all effects.

```typescript
type EventHandler = (event: DomainEvent) => Promise<void>;

export class InMemoryEventBus implements EventBus {
  private readonly subscriptions = new Map<string, EventHandler[]>();

  constructor(subscribers: readonly DomainEventSubscriber<DomainEvent>[]) {
    for (const subscriber of subscribers) {
      for (const eventType of subscriber.subscribedTo()) {
        const handlers = this.subscriptions.get(eventType.eventName) ?? [];
        handlers.push(subscriber.on.bind(subscriber));
        this.subscriptions.set(eventType.eventName, handlers);
      }
    }
  }

  async publish(events: readonly DomainEvent[]): Promise<void> {
    for (const event of events) {
      // Sequential dispatch avoids sibling work outliving a rejected publication.
      for (const handler of this.subscriptions.get(event.eventName) ?? []) {
        await handler(event);
      }
    }
  }
}
```

Choose and document one failure policy:

- **Fail-fast/propagate:** publication rejects if a synchronous handler fails.
- **Collect-all:** run all handlers, then reject with all failures.
- **Best-effort:** log and continue only for explicitly non-critical reactions.

Never catch and log by default while returning success. Test routing, awaiting, no-subscriber behavior, multiple subscribers, and the selected failure policy.

## Transactional Outbox

The Outbox guarantee exists only when Aggregate state and messages use the same database transaction and transaction-scoped connection.

```typescript
const pending = user.pendingDomainEvents(); // non-destructive snapshot with stable IDs
await transactionManager.run(async (tx) => {
  await userRepository.with(tx).save(user);
  await outbox.with(tx).append(toIntegrationMessages(pending));
});
user.clearDomainEvents(pending); // only after commit succeeds
```

An Event Bus that opens a separate transaction around only its inserts does not solve the dual-write problem. An external broker cannot participate atomically in a normal database transaction; retain the Outbox even when the relay publishes to RabbitMQ or Kafka.

Do not irreversibly lose pulled events before durable handoff. The Unit of Work must append them before commit and retain/recover them on rollback, or inspect without draining until the transaction succeeds.

## Relay Claiming and Completion

Relays are at-least-once. Claim rows with database-supported locking/leases (`FOR UPDATE SKIP LOCKED`, claim token plus expiry, etc.), publish outside long locks where appropriate, and mark completion conditionally.

A crash after broker publish but before marking completion causes redelivery. Preserve message identity and require consumer idempotency. Do not generate a new ID from the payload on each attempt.

## Fan-Out and Delivery State

Independent subscribers need independent delivery state. Use one broker queue per subscriber, a per-subscriber Inbox/cursor, or an Outbox delivery table keyed by `(message_id, subscriber_id)`.

One queue row deleted by the first handler cannot represent fan-out. A `Map<eventName, subscriber>` also loses additional subscribers; use a collection per event type.

Unknown event types must have an explicit policy: quarantine/dead-letter, retain for later deployment, or intentionally ignore with metrics. Never leave them stuck silently.

## Inbox and Idempotency

At-least-once transport means duplicates are normal. Prefer naturally idempotent effects; otherwise record the message ID in an Inbox in the same transaction as the business effect:

```sql
BEGIN;
WITH accepted AS (
  INSERT INTO inbox(message_id, consumer) VALUES ($1, $2)
  ON CONFLICT DO NOTHING
  RETURNING 1
)
UPDATE projection SET ...
WHERE EXISTS (SELECT 1 FROM accepted);
COMMIT;
```

Back this with `UNIQUE (message_id, consumer)`. An Inbox committed before a local effect can lose work; committed after it can duplicate work. Both can be atomic only when the effect uses the same transactional database. For email, payment, or another remote system, use a provider idempotency key or persist a durable intent/outbox and reconcile uncertain outcomes.

## Ordering and Versioning

Brokers may provide ordering only within documented scopes such as a partition or queue. Define the partition key and required order explicitly.

Use aggregate version/source sequence or stream position for causal ordering. Wall-clock `occurredAt` is not reliable across machines. Consumers can reject stale versions, buffer gaps, rebuild a projection, or use commutative operations according to business semantics.

Do not solve ordering by dumping the entire Aggregate into every message without a consumer and compatibility reason.

## Retries and Dead Letters

Classify failures:

- retry transient timeouts, unavailable dependencies, and lock conflicts with bounded exponential backoff plus jitter;
- do not endlessly retry invalid schemas, unknown versions, or permanent domain rejection;
- quarantine/dead-letter permanent failures with payload, stable ID, error, attempt count, and timestamps;
- alert on age, retry volume, and dead-letter growth;
- provide controlled replay that keeps identity and audit history.

Dead-letter insert and source completion should be atomic where possible. A broker DLQ route is not itself a multi-attempt retry topology; configure delayed retry queues/policies explicitly.

## Broker Relay

Use a broker for lower latency, service fan-out, partitioning, and operational tooling when its complexity is justified. The relay publishes versioned Integration Events from the Outbox. Consumers acknowledge only after their effect and Inbox commit.

One durable queue per subscriber is a useful default. Bind multiple event types to it when one subscriber intentionally handles them.

## Change Data Capture

CDC is appropriate when a legacy writer cannot record an Outbox. Capture stable mutation IDs and old/new row data, then map an allow-listed `(table, operation)` to a versioned Integration Event.

CDC limitations:

- database mutation is not necessarily domain intent;
- schema changes can break contracts;
- the same application write may already publish an event, causing duplicates;
- retries must reuse the captured mutation ID;
- concurrent consumers need claiming/locking;
- unsupported or poison mutations need quarantine, not deletion.

Prefer an application Outbox once the writer can change.

## Decision Table

| Need | Approach |
|---|---|
| Non-critical local reaction | In-process bus with explicit failure policy |
| Durable state-to-message handoff | Transactional Outbox on the same connection |
| Cross-service fan-out | Outbox relay plus broker queues |
| Duplicate-safe consumer | Idempotent operation or transactional Inbox |
| Ordered Aggregate stream | Partition by Aggregate and carry source version |
| Legacy writer cannot change | CDC translated to Integration Events |

## Review Checklist

- Do state and Outbox append share one real transaction context?
- Is message identity stable across retries?
- Does each subscriber have independent delivery state?
- Are consumer effect and Inbox atomic?
- Is ordering scope defined with a source sequence/version?
- Are retryable and permanent failures classified?
- Are dead-letter replay and observability operationally defined?
- Does CDC translate row changes rather than pretending they are Domain Events?
