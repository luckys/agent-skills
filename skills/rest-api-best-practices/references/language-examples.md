# Language Examples

Use this file as an index to language-specific REST API example files.

## Covered Languages

- `references/typescript-examples.md` — TypeScript with Express and NestJS

## Shared Concept Set

Each language file covers the same set of implementation patterns:

- Route definition and URL structure
- HTTP method handlers (GET, POST, PUT, PATCH, DELETE)
- Status code responses (200, 201, 204, 4xx, 5xx)
- Request body validation
- Error response format (RFC 7807 or custom envelope)
- Pagination (offset-based with Link header)
- Filtering and sorting via query parameters
- Authentication middleware (JWT Bearer)
- Domain error translation at the API boundary
- Task-based endpoints
- Request ID middleware (`X-Request-ID`)

## How to Use

- Start with the language file that matches the user's stack.
- For deeper design questions, consult:
  - `url-design.md` — URL naming, versioning, task-based URLs
  - `http-semantics.md` — method semantics, status codes, headers
  - `request-response-design.md` — filtering, pagination, response shape
  - `error-handling.md` — error formats, domain error mapping
  - `security.md` — auth, rate limiting, CORS
  - `api-design-philosophy.md` — REST constraints, CRUD anti-pattern, HATEOAS

## Quick Reference

| Language | Framework | Validation | Auth |
|----------|-----------|------------|------|
| TypeScript | Express, NestJS | Zod, class-validator | jsonwebtoken, Passport |
