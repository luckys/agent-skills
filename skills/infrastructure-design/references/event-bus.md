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

## Sync vs Async Publishing Decision

| Factor | Synchronous (In-Memory) | Asynchronous (DB-Backed) |
|---|---|---|
| Delivery guarantee | None (process crash = lost) | At-least-once |
| Latency | Immediate | Near-real-time (polling interval) |
| Complexity | Low | Medium |
| Failure isolation | None | Full (per subscriber) |
| Suitable for prod | No (non-critical only) | Yes |
