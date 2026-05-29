# Event Bus

Source: CodelyTV/infrastructure_design-eventbus-db-course

## In-Memory Event Bus

**Intent:** Dispatch domain events synchronously within the same process.

**How it works:** On `publish()`, the bus iterates registered subscribers and calls each handler directly. Events are delivered immediately but are lost if the process crashes before all handlers complete. No persistence, no retry.

**When to use:**
- Development and testing environments
- Simple CRUD applications where event loss is acceptable
- Events that represent notifications with no side effects

**When NOT to use:**
- Production systems where event delivery must survive crashes
- Events that trigger writes in other bounded contexts
- Any case where a subscriber can fail without retrying

**Practical heuristic:** If losing an event would cause data inconsistency or a missed business action, do not use an in-memory bus.

**Example:**
```typescript
export class InMemoryEventBus implements EventBus {
  constructor(private readonly subscribers: DomainEventSubscriber<DomainEvent>[]) {}

  async publish(events: DomainEvent[]): Promise<void> {
    await Promise.all(
      events.flatMap((event) =>
        this.subscribersFor(event).map((sub) => sub.on(event))
      )
    );
  }
}
```

---

## DB-Backed Event Bus (Outbox Pattern)

**Intent:** Persist domain events to the same database as the aggregate, guaranteeing that events are never lost even if the application crashes after writing but before dispatching.

**How it works:** On `publish()`, the bus writes events to a `domain_events_to_consume` table inside the same database transaction that saved the aggregate. A background worker (consumer) polls the table, delivers events to subscribers, and marks them as consumed. Event delivery is decoupled from the write path.

**When to use:**
- Production systems where event loss causes inconsistency
- Cross-context event propagation (e.g., mooc context publishing, retention context consuming)
- Any scenario where the aggregate write and the event dispatch must be atomic

**When NOT to use:**
- Simple read-only events or analytics (overhead is not worth it)
- When you already have a reliable external message broker (RabbitMQ, Kafka) and prefer not to add a DB table

**Practical heuristic:** If your aggregate saves and your event bus publishes in the same transaction, you cannot lose the event. Implement this pattern whenever domain events drive downstream writes.

**Example:**
```typescript
// PostgresEventBus.ts — saves events in the same DB transaction
@Service()
export class PostgresEventBus implements EventBus {
  constructor(private readonly connection: PostgresConnection) {}

  async publish(events: DomainEvent[]): Promise<void> {
    if (events.length === 0) return;

    await this.connection.sql.begin(async (tx) => {
      await Promise.all(events.map((event) => this.insertEvent(event, tx)));
    });
  }

  private async insertEvent(event: DomainEvent, tx: TransactionSql) {
    return tx`
      INSERT INTO public.domain_events_to_consume (id, name, attributes, occurred_at)
      VALUES (
        ${event.eventId},
        ${event.eventName},
        ${tx.json(event.toPrimitives())},
        ${event.occurredAt}
      )
    `;
  }
}
```

---

## Consumer per Subscriber

**Intent:** Give each subscriber its own queue/cursor so that a slow or failing subscriber does not block others.

**How it works:** When the event bus publishes to the DB table, a separate row (or cursor) is created per subscriber. Each consumer independently reads and processes its own rows. Failure in subscriber A does not prevent subscriber B from advancing.

**When to use:**
- Multiple independent bounded contexts consuming the same events
- Subscribers with different processing speeds or reliability requirements
- When partial failure isolation is required

**When NOT to use:**
- Only one subscriber exists (unnecessary overhead)
- Subscribers must all succeed or all fail (use a saga instead)

**Practical heuristic:** One consumer per subscriber table entry. When you add a new subscriber, create a new consumer — never share one.

---

## Retries and Dead Letter

**Intent:** Automatically retry failed event deliveries and move permanently failing events to a dead-letter store for manual inspection.

**How it works:** The consumer tracks `retry_count` on each event row. On failure it increments the count and schedules a re-attempt with backoff. After a maximum retry threshold (e.g., 3–5), the event is moved to a `domain_events_dead_letter` table and no longer retried automatically.

**When to use:**
- Any production event bus — retries are not optional
- Transient infrastructure failures (network timeout, DB lock, third-party API unavailable)

**When NOT to use:**
- Do not retry on domain validation errors (the event will never succeed — fix the code, not the retry count)

**Practical heuristic:** Log every dead-letter event with its full payload. Set up an alert on dead-letter table growth — it signals a code bug or a broken external dependency.

---

## Retries and Dead Letter — Concrete Table Schema

**Schema for the outbox table with retry tracking:**
```sql
-- Events pending delivery
CREATE TABLE domain_events_to_consume (
  id           UUID        PRIMARY KEY,
  name         VARCHAR(255) NOT NULL,
  attributes   JSONB        NOT NULL,
  occurred_at  TIMESTAMPTZ  NOT NULL,
  retry_count  INT          NOT NULL DEFAULT 0
);

-- Events that exceeded max retries — for manual inspection
CREATE TABLE domain_events_dead_letter (
  id           UUID        PRIMARY KEY,
  name         VARCHAR(255) NOT NULL,
  attributes   JSONB        NOT NULL,
  occurred_at  TIMESTAMPTZ  NOT NULL,
  failed_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  last_error   TEXT
);
```

**Consumer loop with retry and dead letter (TypeScript):**
```typescript
// PostgresDomainEventsConsumer.ts
const MAX_RETRIES = 5;

export class PostgresDomainEventsConsumer {
  constructor(
    private readonly connection: PostgresConnection,
    private readonly subscribers: Map<string, DomainEventSubscriber<DomainEvent>>,
  ) {}

  async consume(): Promise<void> {
    const events = await this.connection.sql<DomainEventRow[]>`
      SELECT id, name, attributes, retry_count
      FROM domain_events_to_consume
      ORDER BY occurred_at ASC
      LIMIT 100
    `;

    await Promise.all(events.map((row) => this.processEvent(row)));
  }

  private async processEvent(row: DomainEventRow): Promise<void> {
    const subscriber = this.subscribers.get(row.name);
    if (!subscriber) return;

    try {
      await subscriber.on(this.toDomainEvent(row));
      // success: remove from queue
      await this.connection.sql`
        DELETE FROM domain_events_to_consume WHERE id = ${row.id}
      `;
    } catch (error) {
      if (row.retry_count >= MAX_RETRIES) {
        // move to dead letter
        await this.connection.sql`
          INSERT INTO domain_events_dead_letter (id, name, attributes, occurred_at, last_error)
          VALUES (${row.id}, ${row.name}, ${row.attributes}, ${row.occurred_at}, ${String(error)})
        `;
        await this.connection.sql`
          DELETE FROM domain_events_to_consume WHERE id = ${row.id}
        `;
      } else {
        // increment retry count — exponential backoff handled by consumer scheduling
        await this.connection.sql`
          UPDATE domain_events_to_consume
          SET retry_count = retry_count + 1
          WHERE id = ${row.id}
        `;
      }
    }
  }
}
```

**Practical heuristic:** Run the consumer on a short polling interval (1–5 seconds) during normal operation. Alert when `domain_events_dead_letter` table has rows — any row there is a guaranteed bug or broken external dependency.

---

## RabbitMQ Integration (Production Event Bus)

**Intent:** Replace the DB-backed polling consumer with a message broker for lower latency, fan-out across multiple services, and operations tooling (queues, DLQ, admin UI).

**How it works:** The DB outbox remains as the write-side guarantee (same transaction as the aggregate save). A separate "relay" process reads from the outbox and publishes to RabbitMQ exchanges. Consumers subscribe to queues bound to the exchange. RabbitMQ handles delivery, retry, and dead-lettering natively via queue arguments.

**When to use:**
- Multiple services or bounded contexts consuming the same events
- High event volume where polling latency is unacceptable
- When you need fan-out (one event → N queues) without writing N database rows

**When NOT to use:**
- Single-service architectures — the DB outbox alone is sufficient
- When you cannot afford the operational overhead of a RabbitMQ cluster

**RabbitMQ queue setup with DLQ (TypeScript / amqplib):**
```typescript
// Declare exchange + queue + dead-letter queue
await channel.assertExchange("domain_events", "topic", { durable: true });

// Dead-letter exchange and queue
await channel.assertExchange("domain_events.dead_letter", "topic", { durable: true });
await channel.assertQueue("retention.on_user_registered.dead_letter", { durable: true });
await channel.bindQueue(
  "retention.on_user_registered.dead_letter",
  "domain_events.dead_letter",
  "user.registered",
);

// Main consumer queue configured to DLQ on rejection
await channel.assertQueue("retention.on_user_registered", {
  durable: true,
  arguments: {
    "x-dead-letter-exchange": "domain_events.dead_letter",
    "x-message-ttl": 60_000,         // optional: per-message TTL
    "x-dead-letter-routing-key": "user.registered",
  },
});

await channel.bindQueue(
  "retention.on_user_registered",
  "domain_events",
  "user.registered",
);
```

**Consumer with explicit ack/nack:**
```typescript
channel.consume("retention.on_user_registered", async (msg) => {
  if (!msg) return;
  try {
    const event = JSON.parse(msg.content.toString());
    await subscriber.on(event);
    channel.ack(msg);                       // success: remove from queue
  } catch (error) {
    const retries = (msg.properties.headers?.["x-death"]?.[0]?.count ?? 0) as number;
    if (retries >= MAX_RETRIES) {
      channel.ack(msg);                     // give up — already in DLQ via x-death routing
    } else {
      channel.nack(msg, false, false);      // reject without requeue → routes to DLQ exchange
    }
  }
});
```

**Practical heuristic:** One queue per subscriber (not per event type). Name queues as `<context>.<subscriber>` (e.g., `retention.on_user_registered`). Bind multiple routing keys to the same queue if one subscriber handles multiple event types.

---

## Sync vs Async Publishing Decision

| Factor | Synchronous (In-Memory) | Asynchronous (DB-Backed) |
|---|---|---|
| Delivery guarantee | None (process crash = lost) | At-least-once |
| Latency | Immediate | Near-real-time (polling interval) |
| Complexity | Low | Medium |
| Failure isolation | None | Full (per subscriber) |
| Suitable for prod | No (non-critical only) | Yes |
