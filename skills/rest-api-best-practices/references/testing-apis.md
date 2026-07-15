# Testing APIs

A REST API is a contract. Tests exist to prove the contract holds — across happy paths, failures, edge cases, and changes over time. Test at multiple levels; do not rely on manual checks or end-to-end tests alone.

## The API Test Pyramid

```
        /\        E2E / Journey tests  (few)
       /  \       — full flows across multiple endpoints
      /----\      Integration / Contract tests (some)
     /      \     — real HTTP, real routing, mocked externals
    /--------\    Unit tests (many)
                  — handlers, validators, mappers, domain logic
```

- **Unit (many, fast)**: validators, error mappers, serializers, domain services. No HTTP, no DB.
- **Integration / contract (some)**: spin up the app, hit real routes over HTTP, assert status codes, headers, and body shapes. Mock third-party services.
- **E2E / journey (few)**: exercise complete business flows (register → create order → cancel) against a running system.

Most coverage lives in the bottom two layers. E2E tests are valuable but slow and brittle — keep them few and focused on critical journeys.

## What to Test Beyond the Happy Path

The happy path is the easy 20%. Reliability comes from testing the rest:

| Category | Examples |
|----------|----------|
| Validation | Missing required fields, wrong types, out-of-range values, all errors returned at once |
| Authentication | No token, expired token, malformed token → 401 |
| Authorization | Valid token but no permission → 403; accessing another user's resource |
| Not found | Unknown ID → 404 |
| Conflict | Duplicate create → 409; stale `If-Match` → 412 |
| Business rules | Cancelling a shipped order → 409/422 |
| Rate limiting | Exceeding the limit → 429 with `Retry-After` |
| Idempotency | Same `Idempotency-Key` twice → one effect, same response |
| Pagination | First/last page, empty collection, over-max page size |
| Content negotiation | Unsupported `Accept` → 406; wrong `Content-Type` → 415 |

## Status Code and Header Assertions

Assert the full response contract, not just the body:

```typescript
const res = await request(app)
  .post("/v1/orders")
  .set("Authorization", `Bearer ${token}`)
  .send(validOrderPayload);

expect(res.status).toBe(201);
expect(res.headers.location).toMatch(/^\/v1\/orders\/ord_/);
expect(res.body).toMatchObject({ status: "pending" });

// Error case — assert the RFC 9457 Problem Details envelope
const bad = await request(app).post("/v1/orders").send({});
expect(bad.status).toBe(422);
expect(bad.headers["content-type"]).toMatch(/^application\/problem\+json/);
expect(bad.body.type).toContain("validation-failed");
expect(bad.body.errors).toEqual(
  expect.arrayContaining([expect.objectContaining({ field: "items" })]),
);
```

For every declared application failure, test status, `application/problem+json`, stable API-owned `type`, and explicitly safe details. Add an unknown-failure case that proves a generic 500 is returned and the failure is logged with a correlation ID. Include negative assertions that raw exception messages, IDs, rejected content, SQL, and stack traces are absent.

## Contract Testing

A contract test verifies the API conforms to its published specification (OpenAPI). It catches drift between the spec, the docs, and the implementation.

- **Schema validation**: validate every response against the OpenAPI schema in CI. Tools: Schemathesis (Python), Dredd, openapi-backend, express-openapi-validator.
- **Property-based / fuzz**: Schemathesis generates inputs from the spec and asserts the server never violates it (no 500s, responses match declared schemas).
- **Consumer-driven contracts (Pact)**: when other teams consume your API, the consumer publishes the interactions it relies on; the provider verifies it satisfies them before deploy. This prevents breaking changes that the provider's own tests would miss.

```bash
# Example: fuzz the API against its OpenAPI spec
schemathesis run openapi.yaml --base-url http://localhost:3000 --checks all
```

## Tooling

| Tool | Use |
|------|-----|
| Postman / Newman | Manual exploration + automated collection runs in CI |
| supertest (Node), httpx (Python), RestAssured (Java) | In-process integration tests |
| Schemathesis, Dredd | OpenAPI contract / fuzz testing |
| Pact | Consumer-driven contracts across teams |
| k6, Locust, Gatling | Load and performance testing |

## Test Data and Isolation

- Each test sets up and tears down its own data — never depend on test execution order.
- Use a dedicated test database; reset state between runs (transactional rollback or truncation).
- Mock third-party HTTP (payment, email) at the boundary — never call real external services in tests.
- Make tests deterministic: freeze time, seed randomness, use fixed IDs (Object Mother / factory helpers).

## Keep Tests Aligned with the Contract

- Generate request/response examples in docs from the same fixtures the tests use, so docs cannot drift from reality.
- Run contract validation in CI and fail the build on drift.
- When you intentionally change the contract, the failing contract test is the signal to bump the version.

## Related References

- `documentation.md` — OpenAPI spec as the source of truth for contract tests.
- `error-handling.md` — the error shapes your tests assert against.
- `http-semantics.md` — status codes and headers to verify.
