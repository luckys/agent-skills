# Language Examples

Use this file as an index to language-specific REST API example files.

## Covered Languages

- `references/typescript-examples.md` — TypeScript with Express and NestJS
- `references/python-examples.md`     — Python with FastAPI and Django REST Framework
- `references/go-examples.md`         — Go with net/http and Chi
- `references/php-examples.md`        — PHP with Laravel and Symfony
- `references/java-examples.md`       — Java with Spring Boot 3.x

## Shared Concept Set

Each language file covers the same set of implementation patterns:

- Route definition and URL structure
- HTTP method handlers (GET, POST, PATCH, DELETE)
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
  - `url-design.md` — URL naming, versioning, backward compatibility, task-based URLs
  - `http-semantics.md` — method semantics, status codes, headers
  - `request-response-design.md` — filtering, pagination, nested structure guidance
  - `error-handling.md` — error formats, domain error mapping
  - `security.md` — auth, rate limiting, CORS
  - `api-design-philosophy.md` — REST constraints, CRUD anti-pattern, HATEOAS
  - `observability.md` — request IDs, logging, metrics, health endpoints
  - `documentation.md` — OpenAPI, working examples, contract testing

## Quick Reference

| Language   | Framework            | Validation               | Auth                        |
|------------|----------------------|--------------------------|-----------------------------|
| TypeScript | Express, NestJS      | Zod, class-validator     | jsonwebtoken, Passport      |
| Python     | FastAPI, DRF         | Pydantic, DRF Serializer | python-jose, djangorestframework-simplejwt |
| Go         | net/http, Chi        | go-playground/validator  | golang-jwt/jwt              |
| PHP        | Laravel, Symfony     | Form Request, Assert     | Sanctum, LexikJWTBundle     |
| Java       | Spring Boot 3.x      | Bean Validation (Jakarta)| Spring Security + OAuth2    |
