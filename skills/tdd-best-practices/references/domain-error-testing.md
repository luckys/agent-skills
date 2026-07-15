# Testing Failure Contracts

Source: lessons and counterexamples from [CodelyTV/domain_modeling-errors-course](https://github.com/CodelyTV/domain_modeling-errors-course), corrected for behavior-focused tests.

## Domain and Application Tests

- Assert the typed class/variant/code first; assert message text only when copy is contractual.
- Cover every invariant boundary and every declared use-case failure.
- Prove rejection leaves state and pending events unchanged.
- Distinguish absence, expected conflict, and infrastructure exception.
- Verify composed Results short-circuit: later reads/writes are not called after the first error.
- Test success and every `flatMap`/async composition branch.
- Avoid `get()`/`getError()` in tests; match/fold exhaustively like production.

## Exception Tests

Catch only the expected type or use framework typed matchers. A broad `toThrow(Error)` can pass for setup bugs or unrelated exceptions. When causes matter, assert the public category and preserved cause without making vendor text contractual.

## Boundary Contract Tests

For each declared failure, assert status, media type, stable public Problem Details type, safe body, and correlation/instance behavior. Also test:

- malformed JSON and invalid schema;
- unmapped/unknown failure produces generic 500 and is logged;
- raw internal message, IDs, rejected content, stack, and SQL never appear;
- authorization policy does not leak resource existence;
- internal class renaming does not change public code.

## Exhaustiveness

Use compile-time type tests/static analysis where available. Add a table-driven mapping test listing every supported variant. Do not trust TypeScript aliases to constrain thrown exceptions, and do not use unchecked casts in catch wrappers.

## Test Doubles

Configure stubs without calling them, execute the System Under Test, then assert interactions. Recreate/reset doubles per test. Course helpers that call `shouldFind()` or `shouldSave()` during Arrange can create stale calls and false positives.

## Effect Systems

Run the effect with the library runtime and assert typed exits/causes. `await effect` does not execute a non-Promise Effect. Prove earlier failure prevents later effects.

## Course Caveats

The course contains useful Optional/Either/Result progression but also ignored Results, incomplete combinator tests, stale acceptance suites, broken Effect tests, and shared self-asserting mocks. Treat the snapshots as comparisons, not verified reference implementations.
