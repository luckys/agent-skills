# HTTP Semantics

REST is not a framework — it is a set of constraints on how to use HTTP. Using HTTP correctly means its built-in semantics do work for you: caching, intermediaries, clients, and tooling all understand the protocol.

## HTTP Methods

| Method | Safe | Idempotent | Cacheable | Use for |
|--------|------|------------|-----------|---------|
| GET | ✅ | ✅ | ✅ | Retrieve a resource or collection |
| HEAD | ✅ | ✅ | ✅ | Check resource existence or metadata without body |
| OPTIONS | ✅ | ✅ | ❌ | Discover allowed methods (CORS preflight) |
| POST | ❌ | ❌ | ❌ | Create a resource; trigger a non-idempotent action |
| PUT | ❌ | ✅ | ❌ | Full replacement of a resource |
| PATCH | ❌ | ❌* | ❌ | Partial update of a resource |
| DELETE | ❌ | ✅ | ❌ | Remove a resource |

**Safe** = the operation must not change server state — clients can call it freely without side effects.  
**Idempotent** = calling it N times has the same effect as calling it once — safe to retry on network failure.  
*PATCH can be made idempotent by design (e.g., `{ "set": { "status": "active" } }`), but is not idempotent by default.

## Status Codes

### 2xx — Success

| Code | Name | When to use |
|------|------|-------------|
| 200 | OK | Successful GET, PUT, PATCH; DELETE with a response body |
| 201 | Created | Successful POST that created a resource. Always include `Location` header. |
| 202 | Accepted | Request accepted for async processing; result not yet available |
| 204 | No Content | Successful operation with no response body (DELETE, PUT/PATCH when body is not useful) |

### 3xx — Redirection

| Code | Name | When to use |
|------|------|-------------|
| 301 | Moved Permanently | Resource URL has permanently changed; include `Location` |
| 304 | Not Modified | Conditional GET; the cached version is still valid (ETag or Last-Modified match) |

### 4xx — Client Error

| Code | Name | When to use |
|------|------|-------------|
| 400 | Bad Request | Malformed request syntax, invalid JSON, unrecognized parameters |
| 401 | Unauthorized | No credentials provided, or credentials are invalid/expired |
| 403 | Forbidden | Credentials are valid but access to this resource is denied |
| 404 | Not Found | Resource does not exist |
| 405 | Method Not Allowed | HTTP method is not supported for this resource. Include `Allow` header. |
| 406 | Not Acceptable | Server cannot produce a response matching the `Accept` header |
| 409 | Conflict | State conflict: duplicate create, optimistic lock failure, illegal state transition |
| 410 | Gone | Resource existed but has been permanently deleted |
| 415 | Unsupported Media Type | Server cannot process the `Content-Type` of the request body |
| 422 | Unprocessable Entity | Request is syntactically valid but semantically invalid (domain/validation error) |
| 429 | Too Many Requests | Rate limit exceeded. Always include `Retry-After`. |

### 5xx — Server Error

| Code | Name | When to use |
|------|------|-------------|
| 500 | Internal Server Error | Unexpected server-side failure. Never leak internal details. |
| 502 | Bad Gateway | Upstream service returned an invalid response |
| 503 | Service Unavailable | Server temporarily unable to handle requests; include `Retry-After` |
| 504 | Gateway Timeout | Upstream service did not respond in time |

## Key Request Headers

| Header | Purpose | Example |
|--------|---------|---------|
| `Accept` | Content types the client can handle | `application/json` |
| `Authorization` | Credentials | `Bearer <token>` |
| `Content-Type` | Media type of the request body | `application/json` |
| `If-None-Match` | Conditional GET by ETag | `"abc123"` |
| `If-Modified-Since` | Conditional GET by date | `Wed, 21 Oct 2015 07:28:00 GMT` |
| `Idempotency-Key` | Retry safety for POST operations | `a1b2-c3d4-e5f6` |

## Key Response Headers

| Header | Purpose |
|--------|---------|
| `Content-Type` | Media type of the response body |
| `Location` | URL of the created resource (after 201) or redirect target |
| `Link` | Related resource URLs; pagination navigation |
| `ETag` | Opaque identifier for caching and conditional requests |
| `Last-Modified` | Timestamp for caching and conditional requests |
| `Cache-Control` | Caching directives |
| `X-RateLimit-Limit` | Max requests allowed in current window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Epoch seconds when the window resets |
| `Retry-After` | Seconds to wait before retrying (429, 503) |
| `Allow` | Methods allowed on this resource (405 responses) |
| `Deprecation` | Date this endpoint version is deprecated |
| `Sunset` | Date this endpoint version will be removed |

## Idempotency Keys

For non-idempotent POST operations where the client needs retry safety (e.g., payment creation):

```
POST /payments
Idempotency-Key: a1b2c3d4-e5f6-7890-abcd-ef1234567890
Content-Type: application/json

{ "amount": 99.90, "currency": "EUR" }
```

The server stores the result keyed by the idempotency key. Retries with the same key return the stored result without re-executing the operation. Use UUIDs generated by the client.

## Caching

```
# Public, cacheable for 5 minutes (CDN + browser)
Cache-Control: public, max-age=300

# Private (user-specific), not shared-cacheable
Cache-Control: private, max-age=60

# No caching at all
Cache-Control: no-store

# Revalidate with server before using cached copy
Cache-Control: no-cache
```

### ETag Validation

```
# Server sends ETag with initial response
HTTP/1.1 200 OK
ETag: "d3b07384"
Content-Type: application/json

{ ... }

# Client sends ETag on next request
GET /users/123
If-None-Match: "d3b07384"

# Server: unchanged → 304, no body
HTTP/1.1 304 Not Modified

# Server: changed → 200 with new ETag
HTTP/1.1 200 OK
ETag: "b026324c"
```

Use ETags for GET responses on resources that change infrequently. They reduce bandwidth and server load significantly.

## Content Negotiation

The client requests a format; the server confirms or rejects it:

```
# Client requests JSON
GET /users/123
Accept: application/json

# Server responds with JSON
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8

# Client requests a format the server does not support
GET /users/123
Accept: application/xml

# Server cannot comply
HTTP/1.1 406 Not Acceptable
```

Default to `application/json`. Only add other formats (`text/csv`, `application/xml`) if there is a clear consumer requirement.
