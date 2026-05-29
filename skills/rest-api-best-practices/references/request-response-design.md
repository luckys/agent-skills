# Request and Response Design

## Response Shape

Choose one field naming convention and never mix:
- **camelCase**: `userId`, `createdAt` — standard for JavaScript/TypeScript APIs
- **snake_case**: `user_id`, `created_at` — standard for Python APIs

Return only what the consumer needs. Do not leak internal identifiers, database columns, or null fields that carry no meaning for the caller.

```json
// Good — clean, purposeful shape
{
  "id": "usr_01J8X",
  "name": "Ana García",
  "email": "ana@example.com",
  "createdAt": "2024-01-15T10:30:00Z"
}

// Bad — leaks internals, inconsistent naming, null noise
{
  "user_id": 42,
  "internal_ref": "SQL_123",
  "userName": "Ana García",
  "email": "ana@example.com",
  "deletedAt": null,
  "updated_at": null,
  "v": 3
}
```

## Collection Responses

Two valid approaches — pick one and apply it consistently:

### Envelope wrapper (preferred when metadata is needed)

```json
{
  "data": [
    { "id": "usr_01", "name": "Ana García" },
    { "id": "usr_02", "name": "Carlos López" }
  ],
  "meta": {
    "total": 142,
    "page": 2,
    "perPage": 25
  }
}
```

### Bare array + headers (simpler for clients that don't need metadata)

```
HTTP/1.1 200 OK
Content-Type: application/json
X-Total-Count: 142
Link: <...>; rel="next", <...>; rel="prev"

[
  { "id": "usr_01", "name": "Ana García" },
  { "id": "usr_02", "name": "Carlos López" }
]
```

## Filtering

Use query parameters. Document exactly which filters are supported and reject unknown ones with `400 Bad Request`.

```
GET /articles?status=published
GET /articles?authorId=usr_01&status=published
GET /articles?publishedAfter=2024-01-01&publishedBefore=2024-12-31
GET /articles?tags=ddd,architecture
```

Do not silently ignore unknown filters — the caller expects them to work, and silent failure leads to incorrect results.

## Sorting

```
# Explicit direction parameter
GET /articles?sort=publishedAt&order=asc
GET /articles?sort=publishedAt&order=desc

# Prefix convention (- = descending)
GET /articles?sort=-publishedAt
GET /articles?sort=-publishedAt,title   ← multiple fields
```

Always document:
- Which fields are sortable (not all fields should be sortable)
- What the default sort order is when `sort` is omitted

## Pagination

### Offset-based (page number)

```
GET /articles?page=2&perPage=25
GET /articles?offset=25&limit=25
```

Good for: small bounded collections, random access (jump to page 5), stable sorted results.  
Bad for: large datasets, real-time data (page boundaries shift as new items are inserted).

Response headers:
```
Link: <https://api.example.com/articles?page=1&perPage=25>; rel="first",
      <https://api.example.com/articles?page=1&perPage=25>; rel="prev",
      <https://api.example.com/articles?page=3&perPage=25>; rel="next",
      <https://api.example.com/articles?page=6&perPage=25>; rel="last"
X-Total-Count: 142
```

The `Link` header with `rel=first|prev|next|last` lets clients navigate without constructing URLs. Consumers should use these links rather than building pagination URLs themselves.

### Cursor-based (keyset pagination)

```
GET /articles?limit=25                              ← first page
GET /articles?cursor=eyJpZCI6MTI1fQ&limit=25       ← subsequent pages
```

Good for: large datasets, infinite scroll, real-time feeds, high-write collections.  
Bad for: random access, jumping to arbitrary pages.

Response:
```json
{
  "data": [...],
  "nextCursor": "eyJpZCI6MTUwfQ",
  "hasMore": true
}
```

The cursor encodes the position in the result set (typically the ID or a composite key of the last item). It is opaque to the client — never document its format as part of the contract.

### Rules for both approaches

- Never return an unbounded collection. Always require a limit.
- Define and document the maximum page size (e.g., max `perPage=100`).
- Apply the same pagination shape consistently across all collection endpoints.
- Return an empty array (not 404) when a collection exists but has no items.

## Timestamps

Always use ISO 8601 in UTC:

```json
{
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-03-22T14:00:00Z"
}
```

Never use Unix timestamps (ambiguous), locale-formatted dates, or dates without timezone information.

## Null vs. Absent Fields

Choose one strategy and apply it everywhere:

| Strategy | Payload | Consumer impact |
|----------|---------|----------------|
| Omit absent fields | Smaller | Must handle missing keys |
| Include null explicitly | Predictable shape | Easier deserialization |

Document the chosen strategy. Never mix both randomly — a client cannot know whether a missing field means null or an API bug.

## Partial Responses (Field Selection)

Allow clients to request only the fields they need:

```
GET /users?fields=id,name,email
GET /orders/{id}?fields=id,status,total
```

Reduces payload size. Especially valuable for mobile clients or aggregation layers that call many APIs. Not required for all APIs — add only when there is clear consumer demand.

## Identifiers

Use opaque string IDs (`usr_01J8X`, `ord_abc123`) rather than raw database integer IDs:
- Hides internal sequencing and scale signals
- Makes IDs non-guessable
- Decouples the API from the storage implementation

When exposing UUIDs, use the standard dashed format: `f47ac10b-58cc-4372-a567-0e02b2c3d479`.
