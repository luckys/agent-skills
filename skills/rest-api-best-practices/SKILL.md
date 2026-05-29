---
name: rest-api-best-practices
description: REST API design guidance. Use when designing or reviewing REST endpoints, choosing HTTP methods and status codes, defining URL structure and naming conventions, formatting error responses, implementing pagination or filtering, versioning an API, securing endpoints with authentication or rate limiting, or reviewing whether an API exposes domain capabilities rather than raw CRUD operations.
license: MIT
metadata:
  author: luckys
  version: "1.0.0"
---

# REST API Best Practices

Use this skill when the main question is how to design, review, or improve a REST API — from URL structure to error formats to security.

## Working Style

1. Start from what the consumer needs, not from what the database looks like.
2. Use HTTP as designed — methods, status codes, and headers carry meaning.
3. Express domain capabilities, not data operations.
4. Make errors as informative as successes.
5. Design for change: version early, break compatibility deliberately.

## Design Workflow

1. **Define the resources.**
   - What are the concepts the consumer needs to interact with?
   - Name them with nouns, in plural form.
   - Avoid verbs in URLs — the HTTP method is the verb.

2. **Choose the right HTTP method.**
   - GET for retrieval (safe, idempotent, cacheable)
   - POST for creation or non-idempotent operations
   - PUT for full replacement (idempotent)
   - PATCH for partial update
   - DELETE for removal (idempotent)

3. **Design the URL.**
   - Keep paths flat where possible — at most two levels of nesting.
   - Use query parameters for filtering, sorting, and pagination.
   - Use task URLs (`POST /orders/{id}/cancel`) for domain operations that aren't simple CRUD.

4. **Define response shapes.**
   - Choose a consistent field naming convention (camelCase or snake_case) and stick to it.
   - Return only what the consumer needs.
   - Use HTTP headers for metadata (pagination, rate limits).

5. **Define error responses.**
   - Use the right 4xx or 5xx status code — never return 200 for errors.
   - Return a structured error body with a machine-readable code and a human-readable message.
   - Follow RFC 7807 (Problem Details) when the team needs a standard.

6. **Add versioning.**
   - Default to URL versioning (`/v1/`).
   - Treat a breaking change as a reason to bump the version, not to patch silently.

## Heuristics

### Resource Naming
Nouns, plural, lowercase, kebab-case for multi-word: `/user-profiles`, `/order-items`.

### HTTP Method Semantics
GET is safe and must never change state. POST creates or triggers actions. PUT replaces the entire resource. PATCH patches specific fields. DELETE removes.

### Status Code Choice
2xx = success. 4xx = client error. 5xx = server error. Never return 200 for a failed operation.

### Error Format
One consistent error envelope for all failures. Machine-readable `code` field, human-readable `message`, optional `errors` array for field-level validation details.

### Pagination
Default to cursor-based for large or real-time datasets. Offset-based is fine for small, bounded collections. Always include a `Link` header with navigation links.

### CRUD vs. Task-Based Design
Avoid exposing raw CRUD when the domain has real business operations. Prefer `POST /orders/{id}/cancel` over `PATCH /orders/{id}` with `{ "status": "cancelled" }`.

## Day-to-Day Rules

- Use plural nouns for collection endpoints.
- Never put verbs in URL paths — the HTTP method is the verb.
- Return 201 Created (not 200) after a successful POST that creates a resource.
- Include a `Location` header pointing to the new resource after 201.
- Return 204 No Content when there is nothing meaningful to return in the body.
- Never expose stack traces, SQL errors, or internal paths in error responses.
- Paginate every collection endpoint — never return an unbounded list.
- Use `Accept` and `Content-Type` headers for content negotiation.
- Put secrets in headers, never in query parameters.
- Always use HTTPS — never plain HTTP for API traffic.

## Good Signals

- URL paths read like a sentence: `GET /orders/{id}/items`.
- Every status code is intentional and precise.
- Errors have a machine-readable code the client can branch on.
- Pagination is consistent across all collection endpoints.
- Breaking changes require a version bump.
- The API surface reflects domain language, not table names.

## Warning Signs

- Verbs in URL paths: `/getUser`, `/createOrder`, `/deleteItem`.
- 200 OK returned for validation errors or business failures.
- Error bodies expose stack traces or raw SQL.
- Collections returned without pagination.
- Inconsistent field naming: sometimes `userId`, sometimes `user_id`.
- Every endpoint maps directly to a database table with full CRUD.
- No versioning strategy — breaking changes deployed silently.
- API key or token passed as a query parameter.
- Response objects nested more than two levels deep.
- No request ID header — errors cannot be correlated in logs.
- No documentation or documentation that doesn't match reality.

## References

- Read `references/url-design.md` for URL structure, naming conventions, nesting rules, versioning, and task-based URLs.
- Read `references/http-semantics.md` for HTTP method semantics, idempotency, safety, status code selection, and key headers.
- Read `references/request-response-design.md` for filtering, sorting, pagination (offset and cursor), content negotiation, and response shape.
- Read `references/error-handling.md` for error response formats (RFC 7807 and custom envelope), status code mapping, domain error translation, and validation errors.
- Read `references/security.md` for authentication (JWT, API keys, OAuth 2.0), authorization, rate limiting, CORS, and HTTPS enforcement.
- Read `references/api-design-philosophy.md` for REST architectural constraints, the CRUD anti-pattern, task-based API design, and HATEOAS.
- Read `references/observability.md` for request IDs, structured logging, metrics, distributed tracing, health endpoints, and alerting.
- Read `references/documentation.md` for what to document per endpoint, working examples, OpenAPI 3.x spec structure, keeping docs executable with contract testing, and changelog practices.
- Read `references/language-examples.md` for an index of language-specific implementation examples.
- Read `references/typescript-examples.md` for REST API implementation in TypeScript (Express, NestJS).

## Related Skills

- Use `ddd-best-practices` when the API surface should reflect a Bounded Context or align with domain language.
- Use `design-patterns-best-practices` for internal patterns within the API implementation (Repository, Service Layer, etc.).
- Use `oop-best-practices` for controller and service design within the API layer.

## Source Influences

This skill is synthesized from:

- *REST API Design Rulebook* by Mark Masse
- *RESTful Web APIs* by Leonard Richardson & Mike Amundsen
- RFC 7807 — Problem Details for HTTP APIs
- RFC 9110 — HTTP Semantics
- Fran Iglesias — API REST series (franiglesias.github.io)
- Derek Comartin — "CRUD APIs are Poor Design" (codeopinion.com)
- Postman REST API Best Practices
- *Building Microservices* by Sam Newman
