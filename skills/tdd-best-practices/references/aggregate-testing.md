# Testing DDD Aggregates

Source: lessons and counterexamples from [CodelyTV/aggregates-course](https://github.com/CodelyTV/aggregates-course), corrected and generalized for behavior-focused tests.

Use this reference when driving or reviewing an aggregate with tests. Keep pure aggregate tests fast and classicist; use integration tests only where persistence, constraints, isolation, or concurrency are the behavior.

## Test Through Public Commands

Construct or reconstitute the root, invoke one named command, and observe state or recorded domain facts through its public API. Use real value objects and child entities. Do not mock objects inside the aggregate or inspect private fields.

```typescript
it("rejects a line that exceeds the approved limit", () => {
  const order = OrderMother.approved({ limit: Money.euros(100) });

  expect(() => order.addLine(ProductId.of("p1"), Money.euros(101)))
    .toThrow(OrderLimitExceeded);
});
```

Prefer one behavior per test. Let test names describe business rules rather than method names.

## Drive Invariants with Boundary Cases

For every invariant, cover:

- lowest and highest valid values
- one value immediately outside each boundary
- duplicate or missing members
- invalid transition from the current state
- sequence-sensitive behavior after earlier commands

Start with the simplest failing example, implement the minimum behavior, then triangulate with the opposite boundary. Avoid reproducing the production algorithm in test data builders.

## Prove Rejected Commands Are Atomic

A rejected command must not partially mutate state or record events. Capture observations before the command and compare them afterward:

```typescript
it("keeps state and events unchanged when adding a duplicate category", () => {
  const course = CourseMother.reconstituted({ categories: [Category.of("ddd")] });
  const before = course.snapshot();
  expect(course.pullDomainEvents()).toEqual([]); // known-clean baseline

  expect(() => course.addCategory(Category.of("ddd")))
    .toThrow(CategoryAlreadyAdded);

  expect(course.snapshot()).toEqual(before);
  expect(course.pullDomainEvents()).toEqual([]);
});
```

If validation happens after mutation or after recording an event, this test exposes the ordering defect.

## Separate Creation from Reconstitution

Test lifecycle paths independently:

- `create(...)` establishes valid state and records exactly the intended creation event.
- `fromPrimitives(...)` or repository loading restores state and records no new event.
- each named transition records only the facts caused by that transition.

Also test event draining semantics when the model exposes them: pulling events returns each pending event once and leaves the queue empty afterward. Do not mistake this in-memory behavior for reliable delivery; outbox reliability belongs in an integration test.

## Assert Domain Events by Meaning

Compare event name, aggregate identity, and business payload. Control or ignore generated metadata such as event ID and timestamp unless that metadata is the behavior under test.

Prefer injecting a clock or ID generator when ordering or timestamps matter. Avoid broad snapshots that hide which part of the domain fact is important.

## Use Deterministic Mothers and Builders

Make the default fixture valid and allow focused overrides:

```typescript
const order = OrderMother.approved({
  limit: Money.euros(100),
});
```

- Use explicit values for fields involved in the invariant.
- Seed random generators and print the seed on failure.
- Keep Mothers in test code; do not turn them into an alternate production construction API.
- Prefer a Builder when the order of setup steps communicates a scenario.
- Do not let defaults make the important condition invisible.

## Choose Doubles at Architectural Boundaries

Pure aggregate tests need no repository or Event Bus. Application-service tests may stub reads and spy on outgoing writes or messages.

Use conventional Arrange-Act-Assert:

```typescript
repository.search.mockResolvedValue(order);

await useCase.execute(command);

expect(repository.save).toHaveBeenCalledTimes(1);
expect(repository.save).toHaveBeenCalledWith(order);
expect(eventBus.publish).toHaveBeenCalledWith(expectedEvents);
```

Avoid self-asserting doubles whose `save()` or `publish()` method contains the assertion. If the System Under Test never calls that method, the assertion never runs and the test can pass falsely. Assert recorded calls after Act, or use a stateful fake and inspect its state.

Do not call a helper such as `shouldSave(expected)` during Arrange if that helper invokes the mock itself. Arrangement configures input; only the System Under Test should produce the interaction being verified.

## Split Tests by Responsibility

| Test level | Prove |
|---|---|
| Value Object unit | intrinsic validity and value equality |
| Aggregate unit | invariants, transitions, child ownership, recorded facts |
| Application unit | loading, orchestration, save intent, message handoff |
| Shared repository contract | collection behavior common to every implementation |
| Repository integration | mapping, reconstitution, version checks, constraints, transaction propagation |
| Outbox integration | state and outgoing message commit atomically |
| API/acceptance | boundary translation and user-visible capability |

Do not mock a database in a test named as repository integration. Use the real database engine or a faithful disposable instance for SQL constraints, transactions, and isolation behavior.

Run shared contract cases against in-memory and production implementations only for semantics they truly share, such as save/search round trips and absence. Keep SQL mapping, rollback, locking, indexes, and database constraints in adapter-specific integration tests. A fake is not a substitute for the real engine.

## Test Collection Semantics by Value

First-class collections need tests for membership, duplicate handling, ordering, and removal. In JavaScript and similar languages, object collection operations may use reference identity:

```typescript
// Wrong for equivalent Value Objects:
categories.includes(new Category("ddd"));

// Compare explicitly by domain value:
categories.some((category) => category.equals(Category.of("ddd")));
```

Include two distinct Value Object instances with equal attributes in the test. This prevents an identity-based implementation from passing accidentally.

## Test Global Rules Under Real Concurrency

An aggregate unit test cannot prove cross-aggregate uniqueness or sequence allocation. Add integration tests that run concurrent attempts and assert the database-backed guarantee:

- duplicate emails produce one success and one translated uniqueness conflict
- optimistic version conflicts reject a stale writer
- business sequence allocation does not duplicate numbers
- outbox records survive a crash between commit and relay

Do not accept a single-threaded test of `MAX(number) + 1` as evidence of safe allocation.

## Aggregate Test Matrix

- Minimum and maximum valid Value Object values.
- Values immediately outside each boundary.
- Valid creation state and one creation event.
- Reconstitution with no event.
- Valid named transition and expected state.
- Invalid transition with unchanged state and events.
- Duplicate child or collection member behavior.
- Removal of an absent child according to the stated policy.
- Value equality using distinct instances.
- Event payload with controlled nondeterministic metadata.
- Event drain behavior.
- Persistence round trip.
- Stale-version conflict.
- Database uniqueness and concurrent allocation.

## What Not to Test

- Private fields or helper methods.
- The exact internal call sequence of pure domain objects.
- Framework or ORM behavior already covered by the framework.
- Getters with no domain behavior.
- Random fixture values without a reproducible seed.
- Event publication infrastructure in a pure aggregate test.

Use `domain-event-testing.md` for subscriber registration, Event Bus contracts, durable delivery, and CDC tests.

## Course Caveats

Use the course for modeling examples, not as proof of testing discipline:

- Several aggregate lessons contain only placeholder tests.
- Some mocks assert inside fake methods and can pass when the expected call never occurs.
- The Domain Events course repeats self-asserting doubles and does not directly test its concrete Event Bus or external-event filtering.
- The commit history does not consistently show tests preceding implementation.
- Event metadata matchers are useful, but assertions still need to prove the System Under Test published the event.
