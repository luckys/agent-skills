# Domain Event Design

Source: principles and counterexamples reviewed from [CodelyTV/domain_modeling-domain_events-course](https://github.com/CodelyTV/domain_modeling-domain_events-course), corrected and generalized for production use.

Use this reference to decide what a Domain Event means, where it originates, what it contains, and how it differs from an Integration Event. Delivery infrastructure is a separate concern.

## Domain Facts, Not Commands

A Domain Event is an immutable record of a meaningful fact that already happened inside one Bounded Context. Name it in past tense using the Ubiquitous Language:

- `UserRegistered`, not `RegisterUserEvent`.
- `UserArchived`, not `UserStatusUpdated(status = archived)`.
- `OrderPaymentFailed`, not `HandlePaymentFailure`.

Do not emit an event for every setter or database update. A direct method call inside one Aggregate is clearer when no independent reaction or historical fact exists.

## Granularity and Semantics

Prefer the narrowest event that preserves the business meaning:

- `UserEmailUpdated(userId, email)` is clearer than `UserUpdated(fullUser)`.
- `UserArchived(userId)` communicates intent better than a generic status transition.
- Separate facts when consumers, lifecycle, authorization, or evolution differ.

Avoid generic `EntityUpdated` events. They force consumers to inspect before/after data, couple them to the producer's full shape, and hide why the change matters.

No-op command policy must be explicit. If setting the same email twice is not a new domain fact, do not record a second event. If repeated confirmation is meaningful, name and test that fact deliberately.

## Aggregate Records, Application Delivers

The Aggregate decides which facts occurred because it owns the transition and invariants. It records events in memory; it does not publish them.

```typescript
abstract class AggregateRoot {
  private pendingEvents: DomainEvent[] = [];

  protected record(event: DomainEvent): void {
    this.pendingEvents.push(event);
  }

  pullDomainEvents(): readonly DomainEvent[] {
    const events = this.pendingEvents;
    this.pendingEvents = [];
    return events;
  }

  pendingDomainEvents(): readonly DomainEvent[] {
    return [...this.pendingEvents];
  }

  clearDomainEvents(handedOff: readonly DomainEvent[]): void {
    const ids = new Set(handedOff.map((event) => event.eventId));
    this.pendingEvents = this.pendingEvents.filter((event) => !ids.has(event.eventId));
  }
}

class User extends AggregateRoot {
  static create(id: UserId, email: UserEmail): User {
    const user = new User(id, email);
    user.record(UserRegistered.now(id, email));
    return user;
  }
}
```

Keep `record` protected. A public method lets external callers forge facts the Aggregate did not establish. Use destructive `pullDomainEvents()` only for best-effort local dispatch. Durable handoff takes a non-destructive snapshot and selectively clears those stable event IDs after commit, preserving facts recorded later.

The application coordinates persistence and handoff. Never inject an Event Bus or Repository into an Entity, call a static bus from a constructor, or make construction asynchronous for publication.

## Creation and Reconstitution

Creation and loading are different lifecycle operations:

- `create(...)` establishes new state and may record `Created`/`Registered`.
- `fromPrimitives(...)`, `rehydrate(...)`, or a mapper restores existing state and records nothing.
- named commands record only facts caused by successful transitions.

Never load through the creation path. Reconstitution must not resend welcome emails, analytics, or other creation reactions.

## Payload and Envelope

Separate business payload from transport envelope.

Business payload should contain the identity and values required to understand the fact. Prefer immutable primitives at serialization boundaries. Do not embed a live Aggregate or dump its complete state by default.

A durable envelope commonly contains:

- stable event/message ID;
- aggregate ID and optional aggregate version/source sequence;
- event type and schema version;
- occurrence time represented as an immutable instant/string;
- correlation and causation IDs;
- producer/Bounded Context and tenant when applicable;
- payload.

Metadata belongs to the envelope unless it is itself domain meaning. An occurrence timestamp is not a reliable causal ordering mechanism across machines; use an aggregate version or source position when ordering matters.

## Domain Events and Integration Events

A Domain Event is an internal model fact. An Integration Event is a stable published contract for another Bounded Context or external consumer.

Translate explicitly at the boundary:

```text
internal UserEmailUpdated
  -> publication policy/translator
  -> shop.user-email-updated.v2 integration message
```

The integration message may need more data than the internal event to avoid synchronous callbacks, but enrichment is deliberate and versioned. Do not move a producer-owned event class into a generic shared-domain folder or add `isExternal()` to every internal event as a substitute for translation.

Not every Domain Event must be public. Publication policy can filter, combine, redact, enrich, or suppress internal facts.

## Subscribers

Subscribers are application handlers in the consuming context. Name them as policies, such as `SendWelcomeEmailOnUserRegistered`, and keep them thin: translate the event into a focused use-case call.

A subscriber may handle multiple events only when they represent the same reaction. Test each accepted event independently. Consumers of durable messages must be idempotent and define behavior for duplicates, retries, and out-of-order delivery.

Do not make primary Aggregate persistence an ordinary subscriber-derived action. The command should not report success before its source-of-truth state is durable. Event-sourced systems are different because appending the event stream is the primary persistence operation.

## Delivery Boundary

`save -> pull -> publish` is acceptable only for explicitly best-effort, in-process reactions. It has a crash window, and destructive pulling can lose events when publication fails.

For durable delivery:

1. Persist Aggregate state and Outbox messages in one database transaction using the same transaction-scoped connection.
2. Commit both or neither.
3. Relay messages asynchronously.
4. Require idempotent consumers. For local database effects, commit the Inbox record and effect in the same transaction. For remote effects, use provider idempotency keys or a durable intent plus reconciliation.

The Event Bus, Outbox, retries, ordering, dead letters, and CDC belong to infrastructure design, not the Aggregate.

## Review Checklist

- Is the event a completed business fact rather than a command or CRUD notification?
- Is its name part of the Ubiquitous Language?
- Does the Aggregate record it only after a successful transition?
- Does a rejected/no-op command avoid misleading events?
- Is creation separate from reconstitution?
- Is `record` inaccessible to arbitrary callers?
- Does the payload avoid unnecessary full-Aggregate coupling?
- Are durable identity, schema version, and source ordering available where needed?
- Are cross-context messages explicitly translated and versioned?
- Is primary persistence independent from ordinary subscribers?
- Is reliable delivery handled by one real transaction plus idempotent consumption?

## Course Caveats

Use the course for its design progression, not as production-ready code. Reviewed snapshots include static publication from constructors, infrastructure passed into Entities, non-atomic save/publish flows, a synchronous bus that swallows failures, unwired subscribers, generic shared external events, SQL injection, and tests whose self-asserting doubles can pass when collaborators are never called.
