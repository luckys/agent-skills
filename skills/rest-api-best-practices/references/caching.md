# Caching

Caching is the highest-leverage performance tool in a REST API. Done well, it reduces latency, server load, and bandwidth. Done wrong, it serves stale or wrong data to the wrong users.

## Cache-Control Directives

The `Cache-Control` response header tells clients and intermediaries how to cache.

```
# Public — any cache (CDN, proxy, browser) may store it
Cache-Control: public, max-age=3600

# Private — only the end client may cache (user-specific data)
Cache-Control: private, max-age=60

# Never store (sensitive or always-fresh data)
Cache-Control: no-store

# Store but revalidate with the server before every use
Cache-Control: no-cache

# Allow stale while revalidating in the background
Cache-Control: max-age=600, stale-while-revalidate=60
```

| Directive | Meaning |
|-----------|---------|
| `public` | Any cache may store the response |
| `private` | Only the browser/client may store it — never shared caches |
| `no-store` | Do not store anywhere (most restrictive) |
| `no-cache` | May store, but must revalidate before serving |
| `max-age=N` | Fresh for N seconds |
| `s-maxage=N` | Fresh for N seconds in shared caches (overrides max-age there) |
| `must-revalidate` | Once stale, must revalidate — never serve stale |
| `stale-while-revalidate=N` | Serve stale up to N seconds while refreshing in background |

Rule of thumb:
- User-specific data → `private`.
- Public reference data → `public` with a sensible `max-age`.
- Anything with auth or PII → `no-store` unless you are certain.

## Validation: ETag and Last-Modified

Validation lets a client confirm its cached copy is still good without re-downloading the body.

### ETag (strong validator)

```
# First response — server provides an opaque version token
HTTP/1.1 200 OK
ETag: "a1b2c3d4"
Cache-Control: private, max-age=0, must-revalidate

{ "id": "usr_01", "name": "Ana García" }

# Next request — client asks "is my copy still valid?"
GET /users/usr_01
If-None-Match: "a1b2c3d4"

# Unchanged → 304, no body (saves bandwidth)
HTTP/1.1 304 Not Modified
ETag: "a1b2c3d4"

# Changed → 200 with new body and new ETag
HTTP/1.1 200 OK
ETag: "e5f6g7h8"
{ "id": "usr_01", "name": "Ana López" }
```

The ETag is an opaque token — typically a hash of the representation or a version number. Clients must treat it as opaque and not parse it.

### Last-Modified (weak validator)

```
HTTP/1.1 200 OK
Last-Modified: Wed, 21 Oct 2024 07:28:00 GMT

# Client revalidates by date
GET /users/usr_01
If-Modified-Since: Wed, 21 Oct 2024 07:28:00 GMT

# → 304 Not Modified if unchanged
```

Prefer ETag over Last-Modified when you can: it is precise to the byte, while Last-Modified has one-second granularity and breaks for sub-second updates.

## Conditional Writes (Optimistic Concurrency)

ETags also prevent lost updates. The client sends the ETag it last saw; the server rejects the write if the resource changed in the meantime.

```
PUT /users/usr_01
If-Match: "a1b2c3d4"
{ "name": "Ana López" }

# Resource unchanged since a1b2c3d4 → write succeeds
HTTP/1.1 200 OK
ETag: "e5f6g7h8"

# Resource changed since a1b2c3d4 → reject (someone else wrote first)
HTTP/1.1 412 Precondition Failed
```

This turns "last write wins" into "first write wins, others must refetch" — eliminating silent overwrites.

## Where to Cache

| Layer | What it caches | TTL guidance |
|-------|----------------|--------------|
| Browser / client | Per-user responses | Short (seconds–minutes) |
| CDN / edge | Public, cacheable GETs | Medium–long (minutes–hours) |
| Reverse proxy (Varnish, nginx) | Public responses near origin | Medium |
| Application cache (Redis) | Expensive computed results, read models | Domain-dependent |
| Database query cache | Hot queries | Short |

Push caching as close to the client as the data sensitivity allows. Public reference data belongs on the CDN; user-specific data stays private/in-app.

## Cache Invalidation

The hard part. Strategies, simplest to strongest:

1. **TTL expiry** — let entries expire naturally. Simple, but serves stale data within the window. Good for data that tolerates slight staleness.
2. **Write-through** — update the cache when you update the source. Keeps cache fresh, adds write latency.
3. **Explicit invalidation** — delete/purge cache keys on mutation. Precise, but you must track every key a change affects.
4. **Versioned keys** — embed a version in the cache key (`user:usr_01:v3`); a new version makes old entries unreachable and they expire naturally.

For CDN-cached public endpoints, trigger a purge on the relevant paths when the underlying resource changes.

## What Not to Cache

- Responses to authenticated requests, unless explicitly marked `private` and safe.
- Anything containing PII, tokens, or payment data → `no-store`.
- Non-idempotent responses (POST results) unless using an idempotency key mechanism.
- Error responses (4xx/5xx) beyond very short windows, to avoid pinning a transient failure.

## Vary Header

When a response depends on a request header (content negotiation, auth, encoding), tell caches so they key correctly:

```
Vary: Accept, Accept-Encoding, Authorization
```

Without `Vary: Authorization`, a shared cache could serve one user's response to another. Always set `Vary` (or `Cache-Control: private`) when responses differ per user.

## Related References

- `http-semantics.md` — status codes (304, 412), conditional request headers, idempotency.
- `observability.md` — measuring cache hit rates and their effect on latency.
