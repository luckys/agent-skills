# Event Delivery Infrastructure

Sources: CodelyTV event-bus courses, [inbox_outbox_pattern-course](https://github.com/CodelyTV/inbox_outbox_pattern-course), [infrastructure_design-eventbus-db-course](https://github.com/CodelyTV/infrastructure_design-eventbus-db-course), [infrastructure_design-eventbus-rabbitmq-course](https://github.com/CodelyTV/infrastructure_design-eventbus-rabbitmq-course), [infrastructure_design-eventbus-aws-course](https://github.com/CodelyTV/infrastructure_design-eventbus-aws-course), [domain_modeling-domain_events-course](https://github.com/CodelyTV/domain_modeling-domain_events-course), and [ddd_problems-domain_events_errors_handling-course](https://github.com/CodelyTV/ddd_problems-domain_events_errors_handling-course), corrected for transaction, retry, ordering, and consumer semantics.

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

Names and callback nesting do not prove atomicity. Verify that Aggregate repositories and Outbox adapters execute through the exact transaction-scoped handle. Likewise, an Inbox transaction around `subscriber.on()` is insufficient when subscriber repositories keep using a root pool/connection; propagate the same transaction context to every local effect.

Do not irreversibly lose pulled events before durable handoff. The Unit of Work must append them before commit and retain/recover them on rollback, or inspect without draining until the transaction succeeds.

A singleton deferred in-memory bus is not an Outbox. Buffering events and dispatching them just before commit can mix concurrent requests, expose effects for a transaction that later fails, and lose everything on process crash. Dispatching after commit avoids rolled-back publication but recreates the dual-write crash gap. Same-process handlers may join only when all their writes use the same scoped database transaction; external effects require durable handoff.

## Relay Claiming and Completion

Relays are at-least-once. Claim rows with database-supported locking/leases (`FOR UPDATE SKIP LOCKED`, claim token plus expiry, etc.), publish outside long locks where appropriate, and mark completion conditionally.

A crash after broker publish but before marking completion causes redelivery. Preserve message identity and require consumer idempotency. Do not generate a new ID from the payload on each attempt.

Keep claim transactions short. Running arbitrary handlers or remote I/O while a batch remains locked holds connections, amplifies rollback, and can replay every earlier side effect if a later row aborts the transaction. Prefer a committed lease (`claimed_by`, `claimed_until`) followed by conditional acknowledgement, or process one delivery in a short transaction only when its local effect can join that same transaction. `SKIP LOCKED` prevents workers from claiming the same currently locked row; it does not prevent sequential redelivery after rollback, lease expiry, or an ambiguous commit.

## Fan-Out and Delivery State

Independent subscribers need independent delivery state. Use one broker queue per subscriber, a per-subscriber Inbox/cursor, or an Outbox delivery table keyed by `(message_id, subscriber_id)`.

One queue row deleted by the first handler cannot represent fan-out. A `Map<eventName, subscriber>` also loses additional subscribers; use a collection per event type.

Unknown event types must have an explicit policy: quarantine/dead-letter, retain for later deployment, or intentionally ignore with metrics. Never leave them stuck silently.

Choose the persistence model deliberately:

- a **fan-out queue** stores one pending delivery per `(message_id, subscriber_id)` and usually deletes or archives it after acknowledgement; it is simple to claim but does not provide replay offsets or successful-delivery history;
- an **append-only log** retains messages and stores a cursor per subscriber and partition; it supports replay, lag, and late subscribers but requires offset and partition-ordering semantics.

Do not describe a pending-row queue as an offset-based log. Decide how new subscribers receive history and how removed subscribers' pending work is retained, reassigned, archived, or discarded.

When publishers and subscribers deploy separately, a durable routing registry can materialize fan-out without loading every subscriber into the publisher. Give one component ownership of atomic reconciliation; remove stale routes as well as adding new ones, use stable subscriber IDs, and define behavior during rolling deployments. An insert-only synchronization script leaves renamed or removed subscribers receiving permanent poison deliveries.

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

An Outbox can store capability-specific intents as well as Integration Events. For example, an email port may append a versioned email intent in the caller's transaction, then a worker sends it with a provider idempotency key. Do not hold database locks across the network send; claim briefly, execute remotely, and complete conditionally. A remote success followed by a crash remains ambiguous and may be retried.

Transport deduplication and semantic idempotency are different. An Inbox rejects the same message ID, while a business rule may require uniqueness by another key, such as one course creation per course ID. Use both when needed. Protect semantic uniqueness with a database constraint, atomic upsert, or conditional write; check-then-insert alone races under concurrent consumers.

## Ordering and Versioning

Brokers may provide ordering only within documented scopes such as a partition or queue. Define the partition key and required order explicitly.

Use aggregate version/source sequence or stream position for causal ordering. Wall-clock `occurredAt` is not reliable across machines. Consumers can reject stale versions, buffer gaps, rebuild a projection, or use commutative operations according to business semantics.

Persist a consumer's last applied source version with the projection and advance both atomically using an expected-version conditional update or transactional lock. Merely storing the version still lets replicas race and commit stale effects. An in-process map keyed by Aggregate ID loses its ordering guard on restart, is not shared by replicas, and can advance even if the projection write fails. Comparing timestamps in such a map does not repair these faults.

Do not treat a missing predecessor as a permanent invalid message. A later event may have arrived first. Buffer it durably, retry with a bounded policy, or rebuild from an authoritative ordered stream; acknowledge it only after the chosen policy has durably recorded the outcome.

Do not solve ordering by dumping the entire Aggregate into every message without a consumer and compatibility reason.

## Retries and Dead Letters

Classify failures:

- retry transient timeouts, unavailable dependencies, and lock conflicts with bounded exponential backoff plus jitter;
- do not endlessly retry invalid schemas, unknown versions, or permanent domain rejection;
- quarantine/dead-letter permanent failures with payload, stable ID, error, attempt count, and timestamps;
- alert on age, retry volume, and dead-letter growth;
- provide controlled replay that keeps identity and audit history.

Dead-letter insert and source completion should be atomic where possible. A broker DLQ route is not itself a multi-attempt retry topology; configure delayed retry queues/policies explicitly.

Republishing to a retry exchange and then acknowledging the original is another dual write. Require durable messages/queues, publisher confirms, unroutable-message detection such as mandatory returns, and a documented at-least-once retry/dead-letter mechanism; a positive confirm alone may still describe an unroutable message. Acknowledge the source only after the retry copy is durably accepted. Preserve headers without mutating a shared message object, cap header growth, and derive attempts from trusted broker/application metadata.

## Broker Relay

Use a broker for lower latency, service fan-out, partitioning, and operational tooling when its complexity is justified. The relay publishes versioned Integration Events from the Outbox. Consumers acknowledge only after their effect and Inbox commit.

One durable queue per subscriber is a useful default. Bind multiple event types to it when one subscriber intentionally handles them.

For RabbitMQ, durability is a conjunction: declare durable exchanges and queues, publish persistent messages, and choose a replicated queue type such as quorum queues when node-loss tolerance requires it. Durable topology alone does not make transient messages survive broker restart. Publisher confirms report broker acceptance, not successful routing or consumer completion; combine confirms with `mandatory` returns or a monitored alternate exchange for critical messages.

Treat topology as versioned infrastructure. Assert exchange types, queues, bindings, retry TTL/DLX routes, queue type, and compatible arguments idempotently during a controlled startup or migration step. Redeclaring an existing queue with incompatible arguments closes the channel with `PRECONDITION_FAILED`; prefer operator policies for settings that must change independently. Stable subscriber/queue IDs must not derive solely from refactorable class names.

Use one long-lived connection per process and separate channels by role: topology, confirmed publishing, and consumption, often one consumer channel per worker/group. Set explicit prefetch from handler latency, memory, downstream capacity, and fairness; `prefetch(1)` bounds in-flight work but does not create global ordering. Consumer adapters must observe every asynchronous handler promise and withhold ack until processing or confirmed retry/dead-letter publication settles.

### AWS EventBridge to SQS

Treat `PutEvents` as a per-entry result, not a request-level Boolean. The SDK call may resolve successfully while `FailedEntryCount` and individual `ErrorCode`/`ErrorMessage` values report rejected entries. Mark only successful entries dispatched; retry or retain each failed/ambiguous entry with its original stable ID. Validate payload size before publication and do not call an unversioned serializer a schema registry.

For each EventBridge rule targeting SQS, create a least-privilege queue resource policy allowing `events.amazonaws.com` to call `sqs:SendMessage`, restricted by the expected rule `aws:SourceArn` and account where appropriate. Configure account, region, partition, bus, queue URLs, and ARNs from deployment outputs rather than hard-coded literals. Scope producer, consumer, redrive, KMS, and topology IAM permissions separately; encrypt sensitive payloads and minimize logged event detail.

Separate the failure planes:

- EventBridge target retry policy and target DLQ cover failure to deliver from EventBridge to SQS;
- SQS visibility timeout, receive count, and redrive policy cover consumer processing failures;
- an SQS DLQ needs retention, inspection, authorization, alarms, and controlled redrive that preserves message identity.

SQS message deletion is acknowledgement. Delete only after the effect and Inbox transaction commit. Size visibility above normal processing or renew it with bounded `ChangeMessageVisibility` heartbeats; stop renewal on shutdown so unfinished work becomes visible again. Standard queues provide at-least-once best-effort ordering. Use FIFO only when its throughput, deduplication window, `MessageGroupId`, and head-of-line blocking match the business ordering requirement; consumer idempotency remains necessary.

A database-backed queue also needs per-delivery state. Selecting the oldest rows in a loop without claiming and marking/deleting them replays the same batch forever; clearing the ORM session changes no queue state. Define pending, claimed, completed, retry, and dead-letter transitions, including lease recovery after worker crashes.

## Backlog and Consumer Lifecycle

Bound batch size and concurrency according to downstream capacity. Back off empty polling, expose queue depth and oldest-message age, and alert on lag rather than only failures. A poison message must not block every later partition indefinitely; quarantine it according to the ordering policy. Define retention/archival, graceful shutdown that stops new claims and finishes or releases leases, and overload behavior before production traffic.

For HTTP/serverless pollers, fail closed when scheduler credentials are absent, use an authenticated mutation endpoint, validate subscriber scope, cap batch size server-side, prevent overlapping invocations where required, and leave enough execution budget to release or expire claims safely. For continuous workers, use adaptive idle backoff and treat `LISTEN/NOTIFY` only as a wake-up hint, not as the durable source of truth.

High-churn database queues also need retention, bounded cleanup, and index maintenance. Build partial composite indexes around the real eligibility/filter/order query, verify them with production-shaped `EXPLAIN (ANALYZE, BUFFERS)`, and monitor vacuum lag and table/index bloat rather than adding isolated indexes by intuition.

Handle broker connection/channel `error`, `close`, and consumer cancellation as lifecycle transitions rather than throwing from asynchronous callbacks. Mark publishers unready, reconnect with bounded backoff and jitter, recreate role-specific channels, reapply QoS, redeclare compatible topology, and restore consumers. Any publication without an observed confirm has an ambiguous outcome and must retain the same message ID on retry.

On shutdown, cancel consumers first, stop new deliveries, await in-flight handlers and confirmed replacement publications within a deadline, then close channels and the connection. If the deadline expires, leave unfinished deliveries unacknowledged for broker redelivery. Monitor confirms, returns, redeliveries, unacked count, connection churn, retry age, DLQ depth, and Outbox lag.

## Broker-First Fallback Is Not an Outbox

Do not publish to a broker and write to a database only when the client throws. A timeout has an ambiguous outcome, a send without confirms may not be durable, and an accepted but unroutable message may still disappear. The fallback is also not atomic with the Aggregate write and can create duplicates or gaps. Write the message to an Outbox in the Aggregate transaction, then relay it; reconcile ambiguous broker outcomes with the same stable message ID.

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
- Do Inbox and every local subscriber repository share one real transaction context?
- Is message identity stable across retries?
- Does each subscriber have independent delivery state?
- Is this explicitly a fan-out queue or an append-only log with offsets?
- Are consumer effect and Inbox atomic?
- Is ordering scope defined with a source sequence/version?
- Are retryable and permanent failures classified?
- Are dead-letter replay and observability operationally defined?
- Is retry republishing confirmed before the original delivery is acknowledged?
- Is ordering/deduplication state durable and committed with the projection?
- Does CDC translate row changes rather than pretending they are Domain Events?
- Are routing reconciliation and poller authentication safe during deployment and misconfiguration?
- Are topology durability, message persistence, routing returns, channels, prefetch, recovery, and shutdown explicit?
- For AWS, are per-entry publication results, queue policies, both retry planes, visibility leases, IAM, and real-service validation explicit?
