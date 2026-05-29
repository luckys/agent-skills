# Security

## HTTPS

Every API must run over HTTPS. No exceptions.

- Redirect HTTP to HTTPS with 301.
- Enforce HSTS: `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- Never put secrets or tokens in URLs — they appear in server logs, browser history, and proxy caches.

## Authentication

### Bearer Token (JWT)

```
Authorization: Bearer eyJhbGciOiJSUzI1NiJ9...
```

- **Stateless** — the server validates the signature; no session lookup needed.
- Include only non-sensitive claims in the payload (`sub`, `iss`, `aud`, `exp`, `roles`).
- Set short expiry (`exp`) — typically 15 minutes for access tokens.
- Provide a refresh token flow for long sessions.
- Use **RS256** (asymmetric) over HS256 (symmetric) in multi-service environments — the public key can be distributed without sharing the secret.
- Always validate: `iss` (issuer), `aud` (audience), `exp` (expiry), `nbf` (not before).

### API Keys

```
X-API-Key: sk_live_abc123...
```

- Send in a **header**, never in a query parameter (query params appear in server logs and browser history).
- Scope keys to specific permissions (read-only, write, admin).
- Allow key rotation without downtime.
- **Hash keys at rest** using a slow hash (bcrypt, Argon2) — treat them as passwords.
- Log the key ID (not the key itself) in access logs.

### OAuth 2.0

Use for delegated access (third-party integrations, mobile apps, SPAs):

| Flow | When to use |
|------|-------------|
| **Client Credentials** | Machine-to-machine; no user involved |
| **Authorization Code + PKCE** | User-facing browser and mobile applications |
| ~~Implicit~~ | Deprecated — do not use |
| ~~Password~~ | Deprecated — do not use |

Store access tokens securely:
- **Browser**: `HttpOnly` cookies (not `localStorage` — XSS exposed)
- **Mobile**: OS secure storage (Keychain, Keystore)
- **Server**: memory or encrypted at-rest storage

## Authorization

- **Authenticate first, authorize second** — always in this order.
- Return `401 Unauthorized` when credentials are missing or invalid.
- Return `403 Forbidden` when credentials are valid but access is denied.
- Apply authorization at the **resource level**, not just at the route level. A user who can list orders should not necessarily be able to view another user's order.
- Avoid leaking resource existence to unauthorized callers: when a user is authenticated but not authorized, return `403` for protected resources — not `404`. Returning `404` to hide the resource is only appropriate for truly sensitive data where even the existence of the resource must be hidden.

## Rate Limiting

Return `429 Too Many Requests` when limits are exceeded:

```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1711929600
Retry-After: 60
Content-Type: application/json

{
  "type": "https://api.example.com/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "You have exceeded 1000 requests per hour. Retry after 60 seconds."
}
```

Rules:
- Apply limits per **API key** or **authenticated user**, not per IP alone (IPs can be shared or rotated).
- Use **sliding window** or **token bucket** algorithms for smooth enforcement.
- Include `Retry-After` so clients know when to retry rather than hammering the API.
- Document rate limits in API documentation.
- Use different limits for different tiers (free, pro, enterprise).

## CORS

For browser-facing APIs:

```
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, X-API-Key
Access-Control-Max-Age: 86400
```

- **Never set `Access-Control-Allow-Origin: *` for authenticated APIs** — this allows any site to make credentialed requests.
- Maintain an explicit allowlist of trusted origins.
- Respond to OPTIONS preflight requests with `204 No Content` and the CORS headers.
- Set `Access-Control-Max-Age` to cache preflight responses and reduce OPTIONS round trips.

## Input Validation

- Validate **all input at the API boundary** — never trust client data.
- Use **allowlists** for acceptable values, not denylists.
- Set a maximum request body size to prevent resource exhaustion: `Content-Length` checks or framework body size limits.
- Sanitize before logging — never log raw user input that could contain PII, passwords, or injection payloads.

## Sensitive Data in Responses

- Never return passwords, private keys, or full payment card numbers.
- Mask sensitive fields in logs (e.g., `"email": "a***@example.com"`).
- Remove or mask fields the caller is not authorized to see — do not rely on client-side filtering.

## Security Headers

Include these on all API responses:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'none'
Referrer-Policy: no-referrer
```
