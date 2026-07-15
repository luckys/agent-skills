# Test Doubles

A *test double* is any object that replaces a real collaborator in a test. The term comes from film stunt doubles — they stand in for the real thing.

Gerard Meszaros defined five types in *xUnit Test Patterns*. Martin Fowler codified the same taxonomy. Most frameworks collapse some categories (e.g., Jest's `jest.fn()` covers Stub, Spy, and Mock).

---

## The Five Types (Meszaros)

### Dummy

An object passed to the SUT but never actually used. Satisfies a parameter that the code path under test doesn't exercise.

```typescript
// Dummy: the logger is required but the test doesn't care about it
const logger = null as unknown as Logger;
const service = new OrderService(repo, logger);
service.process(order); // logger never called in this path
```

**Use when:** A constructor or method signature requires a collaborator that the specific behavior under test never touches.

---

### Fake

A working implementation that is not suitable for production. The canonical example is an in-memory repository or in-memory event bus.

```typescript
class FakeUserRepository implements UserRepository {
  private users: Map<string, User> = new Map();

  async save(user: User): Promise<void> {
    this.users.set(user.id.value, user);
  }

  async findById(id: UserId): Promise<User | null> {
    return this.users.get(id.value) ?? null;
  }
}
```

**Use when:** The real collaborator is too slow or has external dependencies (database, email server), but you need realistic behavior (not just canned responses).

---

### Stub

Returns canned answers to calls made during the test. Stubs don't verify how they were called — they only control what the SUT receives.

```typescript
// Stub: always returns a fixed user
const userRepository = {
  findById: async (_id: UserId) =>
    User.create({ id: "123", name: "Alice", email: "alice@example.com" }),
} as UserRepository;
```

```python
# pytest-mock
mock_repo = Mock()
mock_repo.find_by_id.return_value = User(id="123", name="Alice")
```

**Use when:** The test depends on a collaborator returning specific data, and you want to control that data without caring about how often or how the method was called.

---

### Spy

A real object (or wrapper) that records its interactions for later verification. Unlike a Mock, the assertion comes after the fact.

```typescript
// Manual spy
class SpyEventBus implements EventBus {
  publishedEvents: DomainEvent[] = [];

  async publish(events: DomainEvent[]): Promise<void> {
    this.publishedEvents.push(...events);
  }
}

// In test
const bus = new SpyEventBus();
await useCase.execute(command);
expect(bus.publishedEvents).toHaveLength(1);
expect(bus.publishedEvents[0]).toBeInstanceOf(UserRegistered);
```

**Use when:** You need to assert that a side effect happened (event published, email sent) but want to capture real data rather than set up expectations upfront.

---

### Mock

Pre-programmed with expectations. The mock verifies that the SUT called it correctly. If the expectation isn't met, the test fails — even if no assertion runs.

```typescript
// Jest mock — expectation set upfront
const sendEmail = jest.fn();
const service = new NotificationService(sendEmail);

await service.notifyUser(user);

expect(sendEmail).toHaveBeenCalledTimes(1);
expect(sendEmail).toHaveBeenCalledWith(user.email, expect.stringContaining("Welcome"));
```

```java
// Mockito
UserRepository repo = mock(UserRepository.class);
when(repo.findById(userId)).thenReturn(Optional.of(user));

service.process(command);

verify(repo, times(1)).save(any(User.class));
```

**Use when:** The interaction itself is the behavior under test — not just the result, but the fact that a specific message was sent to a collaborator.

---

## Mocks vs Stubs — The Key Distinction (Fowler)

| | Stub | Mock |
|---|---|---|
| Purpose | Provide inputs to the SUT | Verify outputs from the SUT |
| Assertion style | State-based (assert result) | Behavior-based (assert call) |
| Verification | After — you check the SUT's state | Built into the double (fails if call didn't happen) |

**Principle:** One test, one reason to fail. Either assert on state *or* on interactions — rarely both.

---

## Classicist vs Mockist

Two schools of thought on how aggressively to use test doubles:

### Classicist (Chicago/Detroit school)

- Use real collaborators when they are deterministic and fast.
- Only replace external dependencies (DB, network, clock).
- Assert on state: did the object end up in the right state?
- Result: tests are more integration-like, less coupled to implementation.

### Mockist (London school)

- Replace all collaborators with mocks, even domain objects.
- Assert on interactions: did the SUT send the right messages?
- Result: fine-grained isolation; design pressure to keep objects small.

**When to choose:**
- Classicist → domain logic, pure functions, value-heavy code.
- Mockist → infrastructure adapters, use cases with external side effects.

---

## Common Mistakes

### Over-mocking

Mocking everything — including objects you own — means you're testing the mocks, not the system. If the mock reproduces the logic of the real object, you get false confidence.

```typescript
// Over-mocked — this test proves nothing
const pricing = { calculate: jest.fn().mockReturnValue(100) };
const result = pricing.calculate(cart);
expect(result).toBe(100); // trivially true
```

### Coupling tests to implementation

Mocking private methods or internal details breaks on every refactor. Mock at the boundary — the interface your production code depends on.

### Shared mocks across tests

Global `beforeAll` that sets up mocks used by many tests creates hidden coupling. Keep test doubles local to each test unless they truly represent a fixed test context.

---

## Test Double Selection Guide

```
Does the collaborator have I/O or non-determinism?
  YES → Replace with Fake, Stub, or Mock
  NO  → Use the real object

Is the interaction itself (how it was called) the behavior under test?
  YES → Mock
  NO  → Stub or Fake

Do you need realistic behavior (not just canned responses)?
  YES → Fake
  NO  → Stub

Do you need to assert after the fact what calls were made?
  YES → Spy
```

---

## Sources

- Gerard Meszaros, *xUnit Test Patterns* — Chap. 5: Test Doubles
- Martin Fowler, "Mocks Aren't Stubs" (martinfowler.com)
- Steve Freeman & Nat Pryce, *Growing Object-Oriented Software, Guided by Tests*
