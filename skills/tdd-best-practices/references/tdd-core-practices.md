# TDD Core Practices

## Red-Green-Refactor in Detail

### Red — Write a failing test

- Write only enough test to fail.
- The failure should be an assertion failure, not a compilation or setup error.
- The test name describes a behavior: `"should reject negative amounts"`, not `"test_amount"`.
- Run the test and confirm it fails for the right reason.

### Green — Make it pass

- Write the absolute minimum production code to pass the test.
- Fake it if you must: return a hard-coded value. Triangulation will force you to generalize later.
- Resist the urge to solve the general case before the test demands it.
- Do not refactor here — only add behavior.

### Refactor — Improve without changing behavior

- Remove duplication between test and production code.
- Improve names to reveal intent.
- Extract methods, eliminate magic numbers, simplify conditionals.
- All tests must stay green throughout refactoring.
- Refactor the test code too — tests are first-class code.

---

## The 3 Laws of TDD (Uncle Bob)

1. Write no production code unless it makes a failing test pass.
2. Write no more of a unit test than is sufficient to fail (compilation failure counts as failure).
3. Write no more production code than sufficient to pass the currently failing test.

These laws enforce small steps. Each loop is measured in seconds, not hours.

---

## FIRST Properties

Good tests are:

| Property | Meaning |
|---|---|
| **F**ast | Run in milliseconds; the full suite in under a minute. |
| **I**solated | No shared state between tests; each test can run alone. |
| **R**epeatable | Same result every run — no dependency on network, clock, or filesystem. |
| **S**elf-validating | Pass or fail without manual inspection of output. |
| **T**imely | Written before or immediately with the production code. |

A test that violates any of these becomes a liability. Slow tests get skipped. Tests with shared state give false confidence.

---

## The Test Pyramid

```
         /\
        /  \
       / E2E \         ← Few: slow, expensive, fragile
      /--------\
     /Integration\     ← Some: test module seams
    /--------------\
   /   Unit Tests   \  ← Many: fast, isolated, focused
  /------------------\
```

**Martin Fowler's guidance:**
- Most tests should be unit tests — fast feedback, easy to maintain.
- Integration tests verify that components work together at boundaries.
- E2E tests verify user-facing behavior but are expensive to maintain.

**Google's sizing (alternative framing):**
- Small: no I/O, no threads, < 1 ms.
- Medium: may use file system, database, but not external services.
- Large: uses full environment, network, production-like config.

---

## Triangulation

When the right implementation isn't obvious, use triangulation:

1. First test: return a hard-coded value.
2. Second test: different input, different expected output.
3. The production code must now generalize to satisfy both.

```python
# Test 1: hard-code passes
def test_add_two_numbers():
    assert add(2, 3) == 5

# Production: return 5 — passes but wrong

# Test 2: forces generalization
def test_add_different_numbers():
    assert add(1, 4) == 5  # same value, still passes!

# Test 3: actually forces the general solution
def test_add_zero():
    assert add(0, 3) == 3
```

After three tests, the production code must implement real addition.

---

## Baby Steps

Take the smallest possible step forward. If a test is too hard to make pass in one go, break it into smaller tests. The cost of a too-small step is a few seconds. The cost of a too-large step can be hours of debugging a failing test.

Indicators that a step is too large:
- You need to change more than one class to make the test pass.
- The test setup is longer than the assertion.
- You're not sure where the failure is.

---

## Tests as Specification

A well-written test reads like a specification:

```
GIVEN a shopping cart with two items
WHEN the user checks out
THEN the total price reflects both items plus tax
```

- Name tests after behaviors, not method names.
- Use `describe`/`context`/`it` or equivalent to group by scenario.
- Avoid asserting on internal state — assert on observable behavior.

---

## Test Coverage

Coverage is a negative indicator, not a positive one:

- Low coverage → definite gaps.
- High coverage → not necessarily good tests.

100% coverage with tests that don't assert anything is worse than 70% coverage with meaningful assertions. Use mutation testing (Stryker, PIT, mutmut) to measure whether tests actually detect changes.

---

## Continuous Testing

- Run the test suite on every file save.
- Fix a failing test before writing new code.
- Never commit broken tests to shared branches.
- A red CI build is a production-level emergency for the team.

---

## Sources

- Kent Beck, *Test Driven Development: By Example*
- Tim Ottinger & Jeff Langr, "Unit Tests Are FIRST" (Pragmatic Bookshelf)
- Martin Fowler, "Test Pyramid" (martinfowler.com)
- Robert C. Martin (Uncle Bob), "The Three Laws of TDD"
