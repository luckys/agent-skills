# Domain Failure Modeling

Source: principles and counterexamples reviewed from [CodelyTV/domain_modeling-errors-course](https://github.com/CodelyTV/domain_modeling-errors-course), corrected and generalized for production use.

Use this reference to define failure vocabulary, ownership, expected control flow, composition, and safe boundary translation. HTTP formatting and operational retry mechanics are separate concerns.

## Failure Taxonomy

Classify by meaning, owner, and recovery rather than by wording:

| Category | Example | Owner | Typical channel |
|---|---|---|---|
| Intrinsic validation/invariant | `PostContentTooLong` | Value Object/Aggregate | typed error value or exception |
| Use-case outcome | `PostNotFound`, `EmailAlreadyRegistered` | Application/domain capability | `Result`/`Either` or typed exception |
| Port-level recoverable failure | `VersionConflict`, `DependencyUnavailable` | Application port contract | typed result when caller can recover |
| Vendor/technical failure | SQL syntax, socket reset | Infrastructure | exception/defect with preserved cause |
| Request/auth failure | malformed JSON, unauthenticated caller | Delivery | protocol-specific response |
| Programmer defect | impossible branch, broken invariant implementation | Code/runtime | fail fast, log, generic boundary response |

Do not convert an infrastructure failure into absence. A database outage is not `UserNotFound`. Do not relabel a business rejection as a SQL or HTTP concept.

## Ownership

Place a failure next to the rule or capability that gives it meaning:

- An invalid email belongs with `EmailAddress`.
- `OrderCannotBeCancelled` belongs with the cancellation rule.
- `PostNotFound` may belong to the application finder/use case because absence becomes failure only for that operation.
- A repository normally returns `null`/`Option` for ordinary absence; the caller decides whether absence is acceptable.
- Infrastructure translates vendor errors into stable port-level categories only when callers can act on them. Otherwise preserve the technical exception and cause for operational handling.

A use case's public failure type includes expected failures from its collaborators. Composition must preserve that union rather than hiding it behind `Error`.

## Stable Internal Codes

Represent distinguishable failures with a stable bounded-context code independent of class names and messages:

```typescript
abstract class DomainFailure extends Error {
  abstract readonly code: string;

  protected constructor(message: string, options?: ErrorOptions) {
    super(message, options);
  }
}

class UserNotFound extends DomainFailure {
  readonly code = "users.user_not_found";

  constructor(readonly userId: UserId) {
    super("Required user was not found");
  }
}
```

The code is internal application/domain vocabulary. The HTTP API may map it to a different public Problem Details type. Neither `constructor.name` nor raw `message` is a stable external contract.

Inheritance is optional. A language-native enum, sealed hierarchy, tagged union, checked exception, or error value is equally valid when it preserves identity and exhaustiveness.

## Option, Result, or Exception

| Situation | Prefer |
|---|---|
| Absence is normal and needs no reason | `Option<T>` / nullable search result |
| Expected failure changes caller behavior | `Result<T, E>` / `Either<E, T>` |
| Trusted domain command rejects an invalid transition | typed exception or `Result`, consistently |
| Parsing untrusted input is normal control flow | `Result<Value, ParseFailure>` |
| Technical defect/unavailable dependency is not recoverable here | exception/defect with cause |

`Option` cannot explain why a value is absent. Do not force the delivery layer to invent a domain failure after information has been discarded.

Exceptions and Results can coexist at different boundaries: expected domain outcomes in the typed channel, unexpected defects in the exception/defect channel. Avoid mixing both channels for the same expected failure within one capability.

## Discriminated Result

Prefer a proven language/library implementation when available. A minimal TypeScript shape illustrates the domain contract:

```typescript
type Result<T, E> =
  | { readonly kind: "ok"; readonly value: T }
  | { readonly kind: "error"; readonly error: E };

type LikePostFailure = PostNotFound | UserNotFound | AlreadyLiked;

declare function likePost(command: LikePost): Promise<Result<void, LikePostFailure>>;
```

Eliminate Results through exhaustive `match`/`fold` or narrowing. Avoid partial extraction methods that throw on the wrong branch; they recreate the hidden failure channel the type was meant to remove.

Do not constrain a generic `Result` implementation to `DomainFailure`: parsers, ports, and infrastructure adapters may need other typed error values.

## Exhaustive Handling

Use discriminated unions, sealed hierarchies, checked exceptions where appropriate, or library matchers so adding a failure forces callers to update:

```typescript
function describeFailure(error: LikePostFailure): string {
  if (error instanceof PostNotFound) return "post missing";
  if (error instanceof UserNotFound) return "user missing";
  if (error instanceof AlreadyLiked) return "already liked";
  return assertNever(error);
}
```

TypeScript does not track thrown exception sets. A type alias beside a throwing function is documentation, not enforcement. Never catch any base error and cast it to caller-selected `T`; require runtime guards or explicit constructor/code maps, and treat unmatched errors as unknown.

`instanceof` is useful within one runtime but can fail across realms, package copies, or serialization. Use stable discriminants at process/module boundaries.

## State Atomicity

A rejected domain operation must leave state and pending events unchanged. Validate before mutation, or stage changes and commit them only after every rule passes.

If a use case performs irreversible work before a later expected failure, returning `Result.error` does not undo that work. Order side effects deliberately and use transactions, Outbox, idempotency, or compensation according to the boundary.

## Boundary Translation and Redaction

Delivery maps known internal failures to protocol semantics. It must explicitly allow-list public code/message/details; never serialize every enumerable field or return `Error.message` by default.

```typescript
type PublicProblem = {
  type: string;
  title: string;
  status: number;
  detail?: string;
};

function presentFailure(error: LikePostFailure): PublicProblem {
  if (error instanceof PostNotFound) {
    return { type: "https://api.example.com/problems/post-not-found", title: "Post not found", status: 404 };
  }
  if (error instanceof UserNotFound) {
    return { type: "https://api.example.com/problems/actor-not-found", title: "Actor not found", status: 404 };
  }
  if (error instanceof AlreadyLiked) {
    return { type: "https://api.example.com/problems/already-liked", title: "Post already liked", status: 409 };
  }
  return assertNever(error);
}
```

Unknown failures are logged server-side with cause and correlation/trace ID, then returned as a generic 500. Ordinary formatting belongs in one framework-level error boundary; endpoint-local handling is for endpoint-specific recovery.

Whether a missing resource returns 404, 403, or a deliberately indistinguishable response can depend on authorization and enumeration policy. HTTP status is not part of the Domain Failure.

## Language Guidance

- TypeScript: discriminated unions and Result libraries make expected sets enforceable; thrown sets are not checked.
- Java: checked exceptions expose failure propagation but can become noisy; sealed result types are another option.
- Scala/Rust/F#/Elm: native sum types and exhaustive pattern matching are the default fit.
- PHP: `@throws` documents but does not enforce; static analysis and explicit result variants improve feedback.
- Effect systems: execute effects with their runtime (`runPromise`, etc.); awaiting an Effect value does not run it.

## Review Checklist

- Is the failure classified by domain/application/infrastructure/delivery ownership?
- Is normal absence distinct from failure and from outage?
- Can callers distinguish every outcome they recover from without parsing messages?
- Is the internal code stable and independent from class names?
- Is the expected failure set enforceable and exhaustive where the language permits?
- Are Results composed without unchecked extraction?
- Does rejection leave state/events unchanged?
- Are public details allow-listed and safe for this caller?
- Are unknown failures logged with a correlation ID and returned generically?
- Are vendor causes preserved without leaking through the public response?

## Course Caveats

Use the course for its progression from generic exceptions through Optional, Either, Result, language types, fp-ts, Effect, and exhaustivity. Do not copy snapshots wholesale: reviewed examples include swallowed database failures, invalid Optional adapters, ignored Results, broken Effect composition/tests, unsound generic catch casts, reflective public serialization, SQL injection, stale acceptance tests, shared self-asserting mocks, and incomplete runtime input validation.
