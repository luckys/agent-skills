---
name: tdd-best-practices
description: Test-Driven Development guidance. Use when writing tests before implementation, applying Red-Green-Refactor, testing Value Object contracts, typed domain failures/Results, DDD Aggregates, Domain Events/subscribers, repository contracts or persistence adapters, choosing between test doubles, deciding test granularity, practicing outside-in or inside-out TDD, reviewing test suite quality, or diagnosing brittle tests.
license: MIT
metadata:
  author: luckys
  version: "1.0.0"
---

# TDD Best Practices

Use this skill when the main question is how to drive implementation from tests, how to structure a test suite, or how to recover discipline in a codebase where tests were written after the fact.

## Working Style

1. Write one failing test, then make it pass with the minimum code needed.
2. Refactor only when all tests are green.
3. Test behaviors, not implementations — the public API, not private methods.
4. Keep tests as simple as the production code they verify.
5. A test suite that is hard to change is as expensive as production code that is hard to change.

## The Red-Green-Refactor Cycle

```
RED    → Write a failing test that describes the next behavior.
GREEN  → Write the minimum code to make it pass.
REFACTOR → Clean up both the code and the test — no new behavior.
```

The discipline is in the order. Never refactor on Red. Never add behavior on Green.

### The 3 Laws (Uncle Bob)

1. You may not write production code unless you have a failing unit test.
2. You may not write more of a unit test than is sufficient to fail (including compilation failures).
3. You may not write more production code than is sufficient to make the currently failing test pass.

## Design Workflow

1. **Describe the behavior** — what should the system do? Write the test name first.
2. **Write a failing test** — make it fail for the right reason (assertion, not setup error).
3. **Make it pass** — take the simplest path; you can clean up after.
4. **Refactor** — remove duplication, improve names, reduce complexity.
5. **Repeat** — the next test should be the smallest step forward.

## Choosing Test Granularity

| Level | Tests | Speed | Confidence |
|---|---|---|---|
| Unit | Single class/function in isolation | Milliseconds | Behavior of one unit |
| Integration | Multiple real collaborators | Seconds | Module boundaries work |
| Acceptance / E2E | Full system from user perspective | Minutes | Feature works end-to-end |

Start with units for logic-heavy code. Start with acceptance tests when following outside-in TDD. Integration tests fill the seams.

## Heuristics

### When to mock
Mock when the collaborator has I/O, non-determinism, or a slow/external dependency. Use real objects when collaborators are pure domain logic.

### When testing an Aggregate
Use real Value Objects and child Entities. Test commands through the root, including the rule that a rejected command leaves both state and pending events unchanged.

### When testing Domain Events
Assert exact facts after Act: type/name, aggregate identity, business payload, count, and controlled metadata. Test subscriber handling separately from real-bus registration and prove durable duplicate/retry behavior with integration tests.

### When testing a Value Object
Test the applicable public contract: semantic equality with distinct instances, exact invariant boundaries, and any exposed normalization, hashing, defensive-copy, operation, or serialization behavior. Inject clocks or policies instead of reading ambient context.

### When a test is too big
If setup takes longer than the assertion, the test is covering too much. Split by behavior.

### When tests break on every refactor
Tests are coupled to implementation, not behavior. Move the assertion to the public API surface.

### When you can't write a test first
The design is too coupled. A class that is hard to test is a design problem, not a testing problem.

## Warning Signs

- Tests that only pass in a specific execution order.
- Mocks that reproduce the production logic (over-mocking).
- Tests with no assertion (`assertTrue(true)`).
- Tests named after methods, not behaviors.
- A test suite that takes more than 10 minutes to run on CI.
- Tests that break when internal details change, not when behavior changes.

## References

- Read `references/tdd-core-practices.md` for Red-Green-Refactor detail, FIRST properties, the test pyramid, triangulation, and baby steps.
- Read `references/test-doubles.md` for the Meszaros taxonomy (Dummy, Fake, Stub, Spy, Mock), when to use each, and the classicist vs mockist distinction.
- Read `references/tdd-schools.md` for the London (outside-in/mockist) vs Chicago (inside-out/classicist) schools, BDD, and ATDD.
- Read `references/tdd-anti-patterns.md` for James Carr's 15 anti-patterns, Ian Cooper's "TDD, Where Did It All Go Wrong" insights, and recovery strategies.
- Read `references/tdd-language-examples.md` for Red-Green-Refactor walkthroughs in TypeScript, Java, Python, C#, Ruby, and PHP with their respective test frameworks.
- Read `references/value-object-testing.md` for semantic equality, invariant boundaries, deep immutability, normalization, optionality, serialization, and property-based Value Object tests.
- Read `references/aggregate-testing.md` for invariant-first Aggregate tests, repository contract and adapter tests, including atomic failures, deterministic Mothers, collection equality, transaction propagation, and concurrency integration tests.
- Read `references/domain-event-testing.md` for Aggregate event assertions, application handoff, subscriber and real-bus tests, Outbox/Inbox delivery tests, Integration Event contracts, and CDC mapping tests.
- Read `references/domain-error-testing.md` for typed failure assertions, Result short-circuit tests, exhaustive boundary mappings, public redaction, unknown 500 behavior, Effect execution, and error-test-double caveats.

## Related Skills

- Use `oop-best-practices` when a class is hard to test — the design needs improvement first.
- Use `refactoring-best-practices` when adding tests to untested legacy code (characterization tests).
- Use `ddd-best-practices` to decide Aggregate boundaries and invariant ownership before testing them.

## Source Influences

This skill is synthesized from:

- *Test Driven Development: By Example* by Kent Beck
- *Growing Object-Oriented Software, Guided by Tests* (GOOS) by Steve Freeman & Nat Pryce
- *Working Effectively with Legacy Code* by Michael Feathers
- *xUnit Test Patterns* by Gerard Meszaros
- Ian Cooper — "TDD, Where Did It All Go Wrong" (talk, Vimeo)
- James Carr — "TDD Anti-Patterns" (blog)
- Tim Ottinger & Jeff Langr — "Unit Tests Are FIRST" (Pragmatic Bookshelf)
- Dan North — "Introducing BDD"
- [CodelyTV Aggregates course](https://github.com/CodelyTV/aggregates-course) (including testing counterexamples)
- [CodelyTV Value Objects course](https://github.com/CodelyTV/value_objects-course) (including testing and TypeScript counterexamples)
- [CodelyTV Repository Pattern course](https://github.com/CodelyTV/repository_pattern-course) (including repository-double and integration-test counterexamples)
- [CodelyTV Domain Events course](https://github.com/CodelyTV/domain_modeling-domain_events-course) (including self-asserting-double and Event Bus coverage counterexamples)
- [CodelyTV Domain Modeling Errors course](https://github.com/CodelyTV/domain_modeling-errors-course) (including Result, Effect, stale-contract, and mock counterexamples)
