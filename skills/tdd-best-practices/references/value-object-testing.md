# Testing Value Objects

Source: lessons and counterexamples from [CodelyTV/value_objects-course](https://github.com/CodelyTV/value_objects-course), corrected for semantic equality, deep immutability, deterministic time, and reliable TypeScript validation.

Use this reference to drive or review the public contract of a Value Object. Test only capabilities the type actually exposes; a scalar identifier does not need date, normalization, serialization, or arithmetic tests unless those behaviors are part of its contract.

## Start from the Semantic Contract

List the observable promises before choosing examples:

- Which values define equality?
- Which inputs are valid, normalized, or rejected?
- Is construction trusted or parsing untrusted input?
- Which operations and comparisons exist?
- Does the type accept or return mutable representations?
- Is hashing, ordering, optionality, or serialization part of its use?

Test the public constructor/factory/parser and public operations. Do not inspect private representation.

## Test Construction Boundaries

Partition inputs into meaningful classes and cover exact edges:

- minimum and maximum valid values
- one value immediately outside each boundary
- empty, whitespace-only, malformed, and unsupported forms when relevant
- runtime-invalid values such as `NaN`, infinities, overflow, and `Invalid Date`
- normalized variants such as casing, whitespace, or Unicode forms when normalization is specified

Use an explicit clock or reference date for time-dependent policy. A test that relies on `new Date()` can change result tomorrow or in another timezone.

## Test Semantic Equality

Always compare separately allocated instances:

```typescript
it("compares by canonical value", () => {
  const first = EmailAddress.parse("Alice@example.COM").get();
  const second = EmailAddress.parse("Alice@example.com").get();

  expect(first).not.toBe(second);
  expect(first.equals(second)).toBe(true);
});
```

For composite values, vary each defining component independently. Add law tests when equality is custom or shared:

- reflexive: `a.equals(a)`
- symmetric: `a.equals(b) === b.equals(a)`
- transitive: if `a == b` and `b == c`, then `a == c`
- unequal semantic types do not compare equal merely because their scalar representation matches

Where the language uses hash collections, prove equal values produce equal hashes. Test collection membership using value equality rather than object reference identity.

## Test Immutability and Aliasing

When the API accepts or returns mutable data, prove callers cannot mutate the stored value:

```typescript
it("defensively copies dates", () => {
  const input = new Date("2026-01-01T00:00:00.000Z");
  const range = DateRange.startingAt(input);

  input.setUTCFullYear(2030);
  const returned = range.start();
  returned.setUTCFullYear(2040);

  expect(range.start().toISOString()).toBe("2026-01-01T00:00:00.000Z");
});
```

Apply this only to mutable representations such as arrays, dates, maps, sets, objects, and buffers. Primitive scalar Value Objects need no defensive-copy test.

## Test Normalization and Parsing

When normalization exists, verify:

- equivalent accepted forms produce equal canonical values
- normalization is idempotent
- normalization does not erase a distinction the domain preserves
- invalid input returns the documented typed error or result variant
- error messages are not the only machine-readable assertion

Do not assume an entire email address is case-insensitive. Test the exact bounded-context policy.

## Test Operations and Laws

For arithmetic, ranges, quantities, and collections, test domain laws where useful:

- operations leave operands unchanged
- closed operations return a valid value of the expected type
- identity element, associativity, or commutativity only when the domain promises it
- incompatible currencies, units, or ranges fail explicitly
- rounding and overflow follow the documented policy
- open-ended ranges participate in overlap rules rather than bypassing them

Property-based tests are valuable when generated examples explore more combinations than a small table. Keep explicit examples for named business boundaries.

## Test Optionality

If the type uses Option/Maybe or a tagged union, verify:

- `null`/`undefined` map to absence according to the contract
- `0`, `false`, and `""` remain present
- mapping a present value preserves legitimate falsy results
- distinct states such as unknown and not-applicable remain distinct
- serialization and reconstitution preserve absence exactly

For Null Object, test substitutability and neutral behavior. Reject designs that invent a real domain value to represent missing data.

## Test Serialization and Reconstitution

Add round-trip tests only when the value crosses a persistence or transport boundary:

```text
domain value -> JSON-safe representation -> domain value
```

Assert semantic equality after the round trip. Cover date-only versus instant semantics, exact decimal representation, optional values, and historical formats the mapper still supports.

Do not call shapes containing `Date`, Option objects, or domain classes "primitives." Run integration tests for ORM converters and database constraints rather than mocking the mapping layer.

## Deterministic Mothers and Builders

- Give each Mother one valid deterministic default.
- Override every value relevant to the behavior under test.
- Seed generated variation and include the seed in failure output.
- Keep invalid fixtures named after the violated rule.
- Do not duplicate production validation inside the Mother.

Unseeded Faker or `Math.random()` creates failures that cannot be reproduced and can accidentally generate an irrelevant boundary.

## TypeScript Verification

Jest/Vitest running through SWC or Babel may execute code that fails TypeScript semantic checks. Run `tsc --noEmit` as a separate CI gate.

Include runtime-invalid inputs through an `unknown` parsing boundary when the source is external. Type annotations alone do not prove parser safety.

## Course Caveats

Do not treat the course tests or history as proof of strict TDD:

- New Value Object abstractions often lack focused unit tests.
- Equality, defensive copying, Maybe laws, and JSON round trips are largely untested.
- Object Mothers use unseeded randomness.
- Several snapshots contain type errors that transpile-only test execution may miss.
- Some copied age tests contain date-boundary defects.
