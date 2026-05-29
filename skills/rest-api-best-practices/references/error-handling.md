# Error Handling

## Core Rule

An error response is part of the API contract — as important as a success response. Every error must be:

1. Signaled by the **correct HTTP status code** (never 200 for a failure).
2. Described by a **consistent, machine-readable body**.
3. **Free of internal implementation details** (no stack traces, no SQL errors).

## RFC 7807 — Problem Details

The IETF standard for HTTP API error responses. Preferred when clients are diverse, when tooling (OpenAPI, Postman) should generate error documentation, or when the team needs an interoperable format.

```json
{
  "type": "https://api.example.com/errors/validation-failed",
  "title": "Validation Failed",
  "status": 422,
  "detail": "The request body contains fields that failed validation.",
  "instance": "/orders",
  "errors": [
    { "field": "email", "message": "Must be a valid email address" },
    { "field": "quantity", "message": "Must be greater than 0" }
  ]
}
```

| Field | Purpose |
|-------|---------|
| `type` | URI identifying the problem type. Ideally dereferenceable to documentation. |
| `title` | Short, stable human-readable summary. Does not change between occurrences. |
| `status` | HTTP status code (useful for logging when the HTTP response is not available). |
| `detail` | Human-readable explanation specific to this occurrence. May change. |
| `instance` | URI referencing the specific occurrence (optional). |

Extensions like `errors` for field-level details are allowed and common.

## Custom Error Envelope

When RFC 7807 is too formal or the team has an existing convention, a simpler envelope is acceptable — as long as it is consistent.

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "The request body contains fields that failed validation.",
    "errors": [
      { "field": "email", "message": "Must be a valid email address" },
      { "field": "quantity", "message": "Must be greater than 0" }
    ]
  }
}
```

Rules for custom envelopes:
- `code` is **machine-readable** — clients branch on `code`, not on `message`.
- `message` is **human-readable** — it can be reworded without breaking clients.
- `errors` is optional — include only for field-level or item-level validation details.
- The same envelope must be used across all endpoints and error types.

## Status Code to Error Type Mapping

| Situation | Status | Code example |
|-----------|--------|--------------|
| Malformed JSON or request syntax | 400 | `MALFORMED_REQUEST` |
| Missing required field | 400 | `MISSING_REQUIRED_FIELD` |
| Field value fails validation | 422 | `VALIDATION_FAILED` |
| Missing or invalid authentication token | 401 | `UNAUTHORIZED` |
| Authenticated but not authorized | 403 | `FORBIDDEN` |
| Resource does not exist | 404 | `NOT_FOUND` |
| Duplicate create (unique constraint) | 409 | `CONFLICT` |
| Illegal state transition | 409 | `INVALID_STATE_TRANSITION` |
| Business rule violated | 422 | `BUSINESS_RULE_VIOLATED` |
| Rate limit exceeded | 429 | `RATE_LIMIT_EXCEEDED` |
| Unexpected server error | 500 | `INTERNAL_ERROR` |

## Domain Error Translation

Domain errors must be translated to HTTP at the API layer. The domain must not know about HTTP.

```typescript
// Domain layer — no HTTP knowledge
class OrderNotFound extends DomainError {
  constructor(id: string) { super(`Order ${id} not found`); }
}
class OrderAlreadyCancelled extends DomainError {}
class InsufficientStock extends DomainError {
  constructor(public readonly shortfall: number) { super(); }
}

// API layer — translates domain → HTTP
function toProblemDetails(error: DomainError): ProblemDetails {
  if (error instanceof OrderNotFound)
    return problem(404, "ORDER_NOT_FOUND", error.message);
  if (error instanceof OrderAlreadyCancelled)
    return problem(409, "ORDER_ALREADY_CANCELLED", "This order has already been cancelled.");
  if (error instanceof InsufficientStock)
    return problem(422, "INSUFFICIENT_STOCK", `Stock is short by ${error.shortfall} units.`);

  // Unknown domain error — log it, return generic 500
  logger.error("Unhandled domain error", { error });
  return problem(500, "INTERNAL_ERROR", "An unexpected error occurred.");
}
```

## Validation Errors

Return all validation errors at once — not just the first one. A client that must correct errors one by one per round trip has a frustrating experience.

```json
{
  "type": "https://api.example.com/errors/validation-failed",
  "title": "Validation Failed",
  "status": 422,
  "errors": [
    { "field": "email",     "message": "Required" },
    { "field": "name",      "message": "Must be at least 2 characters" },
    { "field": "birthDate", "message": "Must be a past date" }
  ]
}
```

## What Must Never Appear in Error Responses

| Never expose | Because |
|-------------|---------|
| Stack traces | Reveals internal architecture and file paths |
| SQL error messages | Reveals schema, table names, database engine |
| Raw exception messages from libraries | Unpredictable, may contain sensitive data |
| Internal service names or host names | Reveals infrastructure topology |
| Database row IDs or sequence numbers | Leaks internal data model |

Log all of these server-side. Return a generic, stable message to the client.

## Consistent Error Middleware

Implement a single error-handling middleware or filter that catches all exceptions and transforms them into the error format. Never construct error responses ad-hoc in individual controllers.

```typescript
// Express — one place handles all errors
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  if (err instanceof DomainError) {
    const problem = toProblemDetails(err);
    return res.status(problem.status).json(problem);
  }
  if (err instanceof ZodError) {
    return res.status(422).json(validationProblem(err));
  }
  logger.error("Unhandled error", { err, path: req.path });
  return res.status(500).json(problem(500, "INTERNAL_ERROR", "An unexpected error occurred."));
});
```
