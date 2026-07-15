# Value Objects: Design, Implementation, and Evolution

Source: corrected synthesis of [CodelyTV/value_objects-course](https://github.com/CodelyTV/value_objects-course), with DDD, language, and production-safety caveats.

Use this as the canonical detailed Value Object reference. The course is valuable as a progression of refactorings, but several snapshots are intentionally intermediate or technically unsafe. Follow the contracts below rather than copying its implementations verbatim.

## Core Contract

A Value Object represents a domain concept whose identity does not matter. Two instances are interchangeable when all semantically defining values are equal.

A robust Value Object should provide:

- **Value semantics:** equality depends on meaning, not allocation identity.
- **Complete construction:** every public construction path returns a valid value or fails explicitly.
- **Immutable observation:** callers cannot change the value through aliases or exposed internals.
- **Cohesive behavior:** parsing, normalization, comparison, formatting, or operations live with the value when they use its knowledge.
- **Stable representation:** persistence and transport mappings preserve meaning and absence without leaking mutable domain internals.

Make Value Objects immutable from creation. If measured performance requires mutable storage, model it as an exclusively owned implementation detail rather than exposing a mutable Value Object contract.

## When to Introduce One

Use a Value Object when one or more signals are present:

- The term exists in the Ubiquitous Language: `EmailAddress`, `Money`, `DateRange`, `CourseId`.
- The value has intrinsic invariants, normalization, comparison, formatting, or operations.
- Two same-typed primitives can be swapped accidentally, such as `UserId` and `CourseId`.
- Validation or interpretation is duplicated across callers.
- Several attributes form one conceptual whole.
- An API becomes clearer by asking for a domain value instead of raw representation details.

A Value Object can be useful even without validation. Semantic type safety and intention-revealing APIs may justify `UserId` over `string`.

Do not introduce one merely because:

- every primitive must be wrapped
- a DTO groups transport fields but has no domain meaning
- unrelated parameters often travel together
- a type alias, enum, branded scalar, record, or discriminated union already provides sufficient guarantees
- the rule depends on current user, time, tenant, repository state, or workflow rather than the value itself
- the abstraction is speculative and has no stable name or behavior

## Value Object vs. Related Types

| Type | Distinguishing question |
|---|---|
| Entity | Must two instances with equal attributes still be distinguished over time? |
| DTO | Is the shape primarily for transport between boundaries? |
| Parameter Object | Are fields grouped for call convenience without shared domain semantics? |
| Branded scalar | Is compile-time distinction enough, with no runtime behavior or validation? |
| Enum or sum type | Is the concept only a closed set of alternatives? |
| First-class collection | Does the collection own rules, regardless of whether the collection itself has value semantics? |

The same concept can be an Entity in one Bounded Context and a Value Object in another. Let domain meaning decide, not the class shape.

## Put Only Intrinsic Rules Inside

Keep rules in the narrowest concept that owns them:

| Rule | Owner |
|---|---|
| Parseable calendar date, rating from 0 to 5 | Value Object |
| Rule involving Aggregate state | Aggregate Root |
| Rule requiring an explicit policy, tenant, role, or current date | Aggregate or named policy/service |
| Existence checks and workflow orchestration | Application Service |
| Global uniqueness and concurrent allocation | Persistence constraint plus application handling |

Do not hide ambient context in a Value Object constructor. A `BirthDate` can guarantee a real calendar date. Whether a person is old enough must use an explicit reference date and policy; otherwise loading the same stored date can change behavior as the clock advances.

Use `ddd-best-practices` when deciding whether a rule belongs to a Value Object, Aggregate, policy, application service, or persistence constraint.

## Construction, Parsing, and Normalization

Enforce every intrinsic invariant through one canonical implementation shared by all public construction paths. The public API may use:

- a constructor that throws for programmer-oriented domain construction
- a named factory such as `EmailAddress.create(...)`
- `parse(...)` or `tryParse(...)` for untrusted text
- `Result<Value, ParseError>` when invalid input is expected control flow

Normalize before validating when canonical representation is part of the concept:

```typescript
class EmailAddress {
  private constructor(private readonly canonical: string) {}

  static parse(raw: string): Result<EmailAddress, InvalidEmailAddress> {
    const trimmed = raw.trim();
    const separator = trimmed.lastIndexOf("@");
    const canonical = separator < 0
      ? trimmed
      : `${trimmed.slice(0, separator)}@${trimmed.slice(separator + 1).toLowerCase()}`;
    if (!isSyntacticallyValidEmail(canonical)) {
      return Result.err(new InvalidEmailAddress(raw));
    }
    return Result.ok(new EmailAddress(canonical));
  }

  equals(other: EmailAddress): boolean {
    return this.canonical === other.canonical;
  }
}
```

This example normalizes only the domain part. Lowercasing the local part is a bounded-context/provider policy, not universally safe SMTP behavior. Decide explicitly whether any normalization changes meaning. Email provider allowlists, tenant policies, and global uniqueness are not email syntax and should not be hidden in a generic `EmailAddress`.

Reject invalid runtime representations even in typed code:

- `NaN`, positive/negative infinity, and overflow for numbers
- `Invalid Date` (`!Number.isFinite(date.getTime())`) for JavaScript dates
- malformed Unicode or unsupported normalization where relevant
- impossible ranges such as end before start

TypeScript types disappear at runtime. Parsing untrusted values still requires runtime checks.

## Equality and Hashing

Define equality from all and only the attributes that determine the value.

An equality implementation must be:

- reflexive: `a == a`
- symmetric: `a == b` implies `b == a`
- transitive: `a == b` and `b == c` imply `a == c`
- stable while the values are observable
- consistent with hashing: equal values produce equal hashes

Use semantic comparison for each component:

- strings after the concept's chosen normalization
- dates by epoch or canonical date-only representation, not object reference
- decimals by exact representation and scale policy
- composite values by recursively comparing their defining components
- collections according to domain order: sequence equality, set equality, or multiset equality

Do not use JavaScript `===` for separately allocated `Date`, array, or object values. Do not use `constructor.name` as a domain type discriminator; minification and bundling can change it. Prefer explicit per-type equality or a base class deliberately restricted to safe scalar representations.

Languages with hash-based collections require the matching hash contract (`hashCode`, `GetHashCode`, `__hash__`, etc.). Never override equality without reviewing hashing.

## Deep Immutability and Aliasing

`readonly`, `final`, and a read-only interface can still hold mutable objects. Protect invariants at both input and output boundaries:

- Store immutable scalars where practical, such as epoch milliseconds or a date-only string.
- Defensively copy arrays, dates, maps, sets, buffers, and mutable nested objects.
- Keep collections private and expose iterators, immutable snapshots, or domain queries.
- Freeze/copy nested data where runtime immutability matters; shallow freeze is not deep freeze.
- Return a new value from transformation operations rather than mutating the receiver.

```typescript
class DateRange {
  private readonly startMs: number;
  private readonly endMs: number;

  constructor(start: Date, end: Date) {
    const startMs = start.getTime();
    const endMs = end.getTime();
    if (!Number.isFinite(startMs) || !Number.isFinite(endMs) || endMs < startMs) {
      throw new InvalidDateRange();
    }
    this.startMs = startMs;
    this.endMs = endMs;
  }

  start(): Date {
    return new Date(this.startMs);
  }

  equals(other: DateRange): boolean {
    return this.startMs === other.startMs && this.endMs === other.endMs;
  }
}
```

The defensive copy returned by `start()` prevents callers from mutating internal state with `setDate()`.

## Behavior and Domain Algebra

Prefer asking the value for meaningful behavior over extracting primitives and deciding elsewhere:

```typescript
const total = subtotal.add(tax);
if (period.overlaps(existingPeriod)) { /* ... */ }
const normalized = phoneNumber.inInternationalFormat();
```

For operations, define:

- compatibility rules, such as matching currencies or units
- precision and rounding policy
- overflow behavior
- ordering and comparison semantics
- whether the operation is closed over the type (`Money + Money -> Money`)

Do not assume money can never be negative; debts, refunds, and adjustments may require signed values. Avoid binary floating point for exact decimal money unless the domain accepts its error model.

## Composite Values

A Value Object may contain several fields or other Value Objects when they form one value:

```typescript
class Address {
  constructor(
    readonly street: Street,
    readonly city: City,
    readonly postalCode: PostalCode,
    readonly country: CountryCode,
  ) {}

  equals(other: Address): boolean {
    return this.street.equals(other.street)
      && this.city.equals(other.city)
      && this.postalCode.equals(other.postalCode)
      && this.country.equals(other.country);
  }
}
```

Composition does not remove the need for deep immutability or explicit equality. If the object has a lifecycle and identity independent of these attributes, it is an Entity instead.

## First-Class Collections

Introduce a first-class collection when membership, uniqueness, ordering, overlap, cardinality, or aggregation has domain meaning.

```typescript
class JobExperiences {
  private readonly items: ReadonlyArray<JobExperience>;

  private constructor(items: ReadonlyArray<JobExperience>) {
    this.items = Object.freeze([...items]);
  }

  static create(items: ReadonlyArray<JobExperience>): JobExperiences {
    ensureNoOverlappingRanges(items);
    return new JobExperiences(items);
  }

  add(experience: JobExperience): JobExperiences {
    return JobExperiences.create([...this.items, experience]);
  }
}
```

Validate every construction path, including initial factories and update operations. Define open-ended range behavior rather than skipping validation. Require immutable `JobExperience` members; if members are mutable Entities, store immutable snapshots or keep the collection exclusively behind its Aggregate Root.

A first-class collection is not automatically a Value Object. A collection of mutable Entities may be Aggregate-owned state or an immutable snapshot. Use Entity identity for Entity membership and value equality for Value Object membership. Do not expose mutable child Entities from an Aggregate merely because the array is read-only.

## Optional Values

Choose the least powerful representation that preserves meaning:

| Representation | Use when |
|---|---|
| `T | null` | Absence is simple and one meaning is sufficient |
| `Option<T>` / `Maybe<T>` | Repeated composition should force explicit handling |
| Tagged union | Missing, unknown, not applicable, or withheld are distinct states |
| Null Object | Absence has genuinely neutral, substitutable behavior under the same protocol |

A real Option distinguishes only nullish absence, not falsiness:

```typescript
type Option<T> =
  | { readonly kind: "some"; readonly value: T }
  | { readonly kind: "none" };

const fromNullable = <T>(value: T | null | undefined): Option<T> =>
  value === null || value === undefined
    ? { kind: "none" }
    : { kind: "some", value };
```

Values such as `0`, `false`, and `""` remain present. Do not use `if (!value)` to detect absence.

Use Null Object only when substitutability is honest. Never invent a birthday, identifier, or monetary value to stand for missing data. Preserve absence through equality, serialization, and reconstitution.

## Persistence and Boundary Mapping

Domain values and serialized representations have different responsibilities:

- Delivery DTOs and messages normally carry JSON-safe primitives.
- Application/domain boundaries convert primitives into domain values deliberately.
- Domain APIs may accept Value Objects when that makes invalid calls impossible.
- Infrastructure maps storage values without exposing public mutable fields.
- Value Objects normally do not have repositories; they persist as parts of Entities or Aggregates.

Use explicit representations for dates and decimals:

- `YYYY-MM-DD` for a date without time or timezone
- ISO instant or epoch for an instant
- integer minor units plus currency, or an exact decimal type, for money

Do not call a structure "primitives" if it contains `Date`, `Maybe`, or domain classes. Ensure JSON round trips preserve the type's meaning.

Creation and reconstitution may need different paths when creation emits events or historical data predates current validation. Prefer a mapper when public `toPrimitives()` methods would weaken encapsulation. Translate equivalent-looking values across Bounded Contexts instead of sharing model classes by default.

## Construction Failures and Domain Errors

Choose the failure shape by caller needs:

- Throw a typed domain error when invalid construction is exceptional in trusted domain code.
- Return `Result`/`Either` from parsers when invalid external input is expected.
- Use structured error details when callers map, recover, or display specific failures.
- Use a simple assertion/error for programmer-only impossible states when no recovery contract exists.

Do not create a dedicated class for every throw automatically. Do not enforce global uniqueness with only `searchByEmail` followed by `save`; concurrent requests can race. Back uniqueness with a persistence constraint and translate the collision.

Use `ddd-best-practices` for the full domain error taxonomy and boundary translation guidance.

## Testing Contract

Test the behaviors the Value Object actually exposes: construction boundaries, semantic equality, normalization, immutable observation, operations, hashing, and serialization only when each is part of its contract. Use deterministic fixtures and explicit policy inputs.

Use `tdd-best-practices` for the complete Value Object test matrix, property-based test guidance, and deterministic fixture strategy.

## Safe Evolution

Introduce Value Objects incrementally beside primitive APIs, migrate one boundary at a time, preserve serialization, and remove duplicated validation only after feedback is green.

Use `refactoring-best-practices` for the complete safe migration sequence.

## TypeScript-Specific Guardrails

- `readonly` is shallow; copy mutable values and collections.
- Avoid a generic equality base for `Date`, arrays, objects, and composites unless it defines semantic comparison explicitly.
- Avoid `constructor.name` as a stable type identifier.
- Structural typing may make two wrappers assignable; use private fields, brands, or opaque types when distinction matters.
- Test transpilation with SWC/Babel does not perform semantic typechecking; run `tsc --noEmit` separately.
- Inherited static factories can accidentally return the base class; test the concrete return type or prefer explicit factories.
- Keep localized display formatting separate from stable machine serialization.
- Redact secrets and sensitive values from `toString()`, logs, and error messages.

## Course Lessons to Retain

The course demonstrates these useful progressions:

- Move duplicated email and identifier knowledge out of `User` and application services.
- Prefer Tell Don't Ask by moving value-specific decisions to the value.
- Extract a policy when behavior gains context or an independent reason to change.
- Introduce composite values and collection objects when rules span several components.
- Use Object Mothers to keep valid defaults readable while overriding relevant values.
- Model domain failures with stable names when callers need to distinguish them.

## Course Examples Not to Copy

- Equality implemented as `constructor.name` plus `===`.
- A mutable `Date` stored behind `readonly`.
- Age eligibility hidden behind `new Date()` in a birthdate constructor.
- `Maybe.some()` or `map()` treating `0`, `false`, or `""` as absent.
- A Null Object that substitutes a real birthday for missing data.
- Public mutable arrays or collection constructors that bypass invariants.
- Open-ended date ranges that skip overlap checks.
- "Primitive" persistence shapes containing `Date`, `Maybe`, or domain classes.
- Uniqueness enforced only by check-then-save.
- Unseeded Faker/`Math.random` in fixtures that must be reproducible.
- Assuming the course commit history demonstrates strict Red-Green-Refactor.
