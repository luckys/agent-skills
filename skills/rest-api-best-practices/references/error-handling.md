# HTTP Error Handling

## Core Contract

An error response is an API contract. It must use the correct status, a consistent machine-readable body, explicit safe details, and no stack trace, SQL text, vendor message, hostname, secret, or unauthorized identifier.

## Problem Details (RFC 9457)

RFC 9457 obsoletes RFC 7807 while retaining the familiar Problem Details shape. Return it with:

```http
Content-Type: application/problem+json
```

```json
{
  "type": "https://api.example.com/problems/validation-failed",
  "title": "Validation failed",
  "status": 422,
  "detail": "The request contains invalid fields.",
  "instance": "/orders/requests/req-123",
  "errors": [{ "field": "quantity", "code": "must_be_positive" }]
}
```

- `type`: stable public problem identifier, ideally documented.
- `title`: stable human summary for the type.
- `status`: repeated HTTP status.
- `detail`: occurrence-specific but explicitly safe text.
- `instance`: occurrence/resource URI without secrets.
- extensions: namespaced/defined fields such as validation errors or correlation ID.

The public `type` is owned by the API. Do not expose an internal class name or domain code automatically.

## Central Boundary Mapper

Use one framework-level middleware/filter/advice for ordinary formatting. Endpoint-local handling is reserved for endpoint-specific recovery.

```typescript
function toProblem(error: unknown, requestId: string): ProblemDetails {
  if (error instanceof OrderNotFound) {
    return problem(404, "order-not-found", "Order not found", requestId);
  }
  if (error instanceof OrderAlreadyCancelled) {
    return problem(409, "order-already-cancelled", "Order is already cancelled", requestId);
  }

  safeExceptionLogger.capture(error, { requestId }); // non-throwing redaction adapter
  return problem(500, "internal-error", "An unexpected error occurred", requestId);
}
```

The mapper must receive `unknown`, recognize known variants with real runtime guards/stable discriminants, and treat unmatched failures as unknown. Never cast a caught base error to a caller-selected union to manufacture exhaustiveness.

## Redaction

Construct public details from an allow-list. `error.message`, `Throwable.getMessage()`, and Go `err.Error()` are diagnostic by default, not public copy.

Do not reflect over all enumerable error properties. A future password, token, rejected content body, internal ID, SQL fragment, or provider response can otherwise become public silently.

Log unknown details server-side with redaction and correlation/trace ID. Return only a generic 500 body.

## Status Policy

Status selection depends on endpoint semantics and must be consistent:

| Situation | Common choice | Notes |
|---|---|---|
| Malformed JSON/syntax | 400 | Parse failure at delivery boundary |
| Semantically invalid fields | 400 or 422 | Choose and document one policy |
| Missing/invalid authentication | 401 | Include appropriate challenge where required |
| Authenticated but forbidden | 403 | May intentionally hide resource existence |
| Target resource absent | 404 | Enumeration policy may alter response |
| Current-state/version conflict | 409 | Include safe recovery hints when useful |
| Rate limited | 429 | Include `Retry-After` when known |
| Unexpected failure | 500 | Generic body; log/trace internally |
| Dependency temporarily unavailable | 503 | Use only when the API can identify temporary unavailability |

A unique-constraint violation becomes 409 only after the adapter recognizes and translates the intended business conflict. Never expose raw constraint text.

## Validation

Parse and validate untrusted JSON before domain construction. Distinguish malformed syntax from schema/semantic validation, cap body/list sizes, and derive actor identity from authentication rather than caller-supplied IDs.

Return field-level errors only when safe. Prefer stable field codes over internal validator messages. Aggregate multiple independent field issues when it improves client correction; domain commands may still fail fast on invariant violations.

## Exhaustiveness and Evolution

Every declared application failure should have a contract test for its public mapping. Adding a variant should fail compilation/static analysis where possible or fail a mapping test.

Version public problem types deliberately. Internal class renames must not alter the API. Document Problem Details schemas in OpenAPI and test `application/problem+json`.

## Checklist

- Correct status and `application/problem+json`?
- Stable API-owned `type`, not a class name?
- Public message/details explicitly allow-listed?
- Unknown failure logged with correlation ID and generic 500?
- Malformed JSON and validation mapped separately?
- Authentication-derived identity and authorization applied?
- Every expected application failure mapped and tested?
- No raw library/vendor messages or reflected error fields?
