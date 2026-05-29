# TDD Anti-Patterns

## James Carr's 15 Anti-Patterns

Originally documented in "TDD Anti-Patterns" (2006). These patterns describe tests that exist but provide false confidence or actively make the codebase harder to change.

---

### 1. The Liar

Tests that pass but don't actually verify anything meaningful.

```typescript
it("processes the order", () => {
  const result = service.process(order);
  expect(result).toBeDefined(); // always true
});
```

**Fix:** Assert on the specific behavior: what state changed? What was returned? What was published?

---

### 2. Excessive Setup

So much setup that you can't tell what is actually being tested.

```typescript
it("validates the email", () => {
  const db = new FakeDatabase();
  const cache = new FakeCache();
  const eventBus = new FakeEventBus();
  const logger = new FakeLogger();
  const metrics = new FakeMetrics();
  const validator = new EmailValidator(db, cache, eventBus, logger, metrics);
  // ... finally:
  expect(validator.isValid("bad-email")).toBe(false);
});
```

**Fix:** If setup is excessive, the object has too many dependencies. Redesign — extract a smaller object that handles only the validation.

---

### 3. The Giant

One test that verifies multiple behaviors at once.

```typescript
it("order processing", () => {
  // verifies validation, inventory check, payment, email, event publication...
  // 80 lines of assertions
});
```

**Fix:** One behavior per test. Name each test after the single thing it verifies.

---

### 4. The Mockery

Mocking so aggressively that the test only verifies the mock configuration, not real behavior.

```typescript
it("calls findById then save", () => {
  const repo = mock<UserRepository>();
  when(repo.findById).calledWith("123").mockResolvedValue(user);
  service.updateEmail("123", "new@example.com");
  verify(repo.findById).calledWith("123");
  verify(repo.save).calledWith(expect.objectContaining({ email: "new@example.com" }));
  // Test passes even if updateEmail does nothing to the user object
});
```

**Fix:** Prefer a Fake with state assertions. If an interaction is the actual behavior (event published, email sent), mock it — but not domain object collaborators.

---

### 5. The Inspector

Breaks encapsulation by accessing private fields or internal state to verify behavior.

```typescript
it("updates internal counter", () => {
  service.process(event);
  expect((service as any)._internalCounter).toBe(1); // private field access
});
```

**Fix:** Only test through the public API. If the internal state is important, expose a meaningful query method on the object.

---

### 6. Generous Leftovers

Tests that depend on state left behind by other tests. Usually caused by shared singletons, global state, or static variables.

```typescript
describe("UserService", () => {
  it("creates a user", () => {
    service.create({ name: "Alice" }); // leaves Alice in the database
  });

  it("counts users", () => {
    expect(service.count()).toBe(1); // depends on Alice from previous test!
  });
});
```

**Fix:** Each test must set up its own state and clean up after itself. Use `beforeEach`/`afterEach`. Never depend on test execution order.

---

### 7. The Local Hero

Tests that only pass in one specific environment (the original developer's machine, a specific OS, a specific timezone).

```typescript
it("formats the date", () => {
  expect(formatDate(new Date())).toBe("2024-01-15"); // hardcoded today
});
```

**Fix:** Control the clock in tests. Use a fixed `Date` or inject a clock collaborator. Test for format, not a specific date.

---

### 8. The Nitpicker

Tests implementation details rather than behavior. Breaks whenever the internal structure changes, even when behavior is identical.

```typescript
it("uses exactly 3 iterations", () => {
  const spy = jest.spyOn(array, "forEach");
  processor.process(items);
  expect(spy).toHaveBeenCalledTimes(3);
});
```

**Fix:** Test the output or state, not how many times internal methods were called.

---

### 9. The Secret Catcher

Relies on exceptions being silently caught, giving the impression of passing when actually hiding failures.

```typescript
it("handles errors gracefully", () => {
  try {
    service.process(invalidInput);
  } catch {
    // swallow — test passes regardless
  }
});
```

**Fix:** Assert explicitly on the exception: `expect(() => service.process(x)).toThrow(ValidationError)`.

---

### 10. The Dodger

Integration test that avoids the hard parts by mocking the exact things that should be tested together.

```typescript
// Claims to test the repository + DB
it("saves the user", () => {
  const db = mock<Database>(); // mocked — there's no actual DB integration
  const repo = new UserRepository(db);
  repo.save(user);
  expect(db.query).toHaveBeenCalled(); // only tested that query was called
});
```

**Fix:** Integration tests should use real infrastructure (test DB, in-memory DB). If you mock the DB, you're writing a unit test — name it accordingly.

---

### 11. The Loudmouth

Test output is so noisy (console logs, print statements) that failures are hidden in the noise.

**Fix:** Suppress output in tests unless it's relevant to the assertion. Use a NullLogger or configure log level to `ERROR`-only in test environments.

---

### 12. The Greedy Catcher

Catches all exceptions indiscriminately, masking unexpected failures.

```typescript
it("processes the request", async () => {
  try {
    await handler.handle(request);
    expect(true).toBe(true); // always passes
  } catch (e) {
    // swallowed
  }
});
```

**Fix:** Catch only the specific exception you expect. Let unexpected exceptions propagate and fail the test.

---

### 13. The Sequencer

Tests are written to run in a specific order and fail when run in isolation or in a different order.

**Fix:** Each test must be fully independent. Run tests in random order occasionally (`jest --randomize`) to detect sequencing dependencies.

---

### 14. The Enumerator

Test names are meaningless: `test1`, `test2`, `shouldWork`, `checkIt`.

**Fix:** Name tests after the behavior they verify: `"should reject negative amounts"`, `"returns null when user not found"`. The test name is the specification.

---

### 15. The Stranger

A test that tests something entirely unrelated to the class under test. Usually produced by copy-paste.

```typescript
describe("OrderService", () => {
  it("validates email format", () => {
    // this belongs in EmailValidator tests
    expect(isValidEmail("bad")).toBe(false);
  });
});
```

**Fix:** Keep test files focused on one subject. When a test belongs elsewhere, move it.

---

## Ian Cooper: "TDD, Where Did It All Go Wrong"

Key insights from Ian Cooper's widely-cited talk (Vimeo, 2013):

### The core mistake: testing implementations, not behaviors

Kent Beck's original intent was to test *behaviors* (what the system does from the outside), not *implementations* (how a specific method works internally).

The widespread practice of "one test per method" creates tests that:
- Break whenever internals are refactored.
- Give no useful documentation of intended behavior.
- Create a maintenance burden proportional to the number of methods, not the number of behaviors.

### The rule: test the public API, not private methods

A unit in TDD is a *behavior*, not a *method* or *class*. The unit under test is the public interface of a module. Internal classes and private methods are implementation details.

```
❌ One test class per production class
✓  One test suite per behavior (which may involve many collaborators)
```

### Adding a new class should not require new tests

If you're adding a supporting class that implements an existing behavior (extracting a helper, introducing a collaborator), existing tests should still pass. New tests are only needed for *new behaviors*.

### When to add tests

Add a test when you're specifying a new behavior, not when you're adding code. The test captures the *contract*, not the implementation.

### Implication for refactoring

If refactoring breaks tests, the tests are testing implementation. Tests should be stable through refactoring — that's the point of the safety net.

---

## Recovery Strategies

### When the test suite is too slow

1. Profile the suite — find the 20% of tests taking 80% of the time.
2. Replace slow integration tests with Fakes for the I/O.
3. Move slow tests to a separate suite run on CI but not on every save.

### When tests break on every refactor

1. Identify tests that assert on internal methods or structure.
2. Replace with tests on the public API.
3. Delete tests for internal helpers — test the observable behavior instead.

### When setup is excessive

1. The object has too many dependencies — split it.
2. Extract a Facade or use a Builder to simplify construction.
3. Use an Object Mother or Builder for complex test data.

### When you have no tests (legacy code)

1. Write characterization tests first (describe current behavior, not desired).
2. Add tests at the highest possible boundary (public API, HTTP endpoint).
3. Don't add unit tests until you have a seam to test through.
4. See `refactoring-best-practices` → `legacy-code-techniques.md`.

---

## Sources

- James Carr, "TDD Anti-Patterns" (2006, archived)
- Ian Cooper, "TDD, Where Did It All Go Wrong" (Vimeo, 2013)
- Michael Feathers, *Working Effectively with Legacy Code*
- Gerard Meszaros, *xUnit Test Patterns*
