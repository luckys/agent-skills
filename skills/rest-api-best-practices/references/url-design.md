# URL Design

## Core Rule

URLs identify resources. HTTP methods express what to do with them. Never mix both responsibilities into the URL.

```
# Wrong — verbs in URL
GET  /getUser/123
POST /createOrder
POST /deleteItem/5

# Right — method is the verb
GET    /users/123
POST   /orders
DELETE /items/5
```

## Naming Conventions

- **Nouns, plural**: `/users`, `/orders`, `/line-items`
- **Lowercase**: `/user-profiles` not `/UserProfiles`
- **Kebab-case** for multi-word: `/order-items` not `/orderItems` or `/order_items`
- **No trailing slash**: `/users` not `/users/`
- **No file extensions**: `/users` not `/users.json`
- **No version in resource name**: `/v1/users` not `/users-v1`

## URL Structure

```
/collection                     → all resources in a collection
/collection/{id}                → one specific resource
/collection/{id}/sub-collection → sub-collection belonging to one resource
```

Keep nesting at most two levels deep. Deeper nesting couples the URL to internal relationships and makes paths fragile.

```
# OK — two levels
GET /orders/{orderId}/items

# Avoid — three levels
GET /users/{userId}/orders/{orderId}/items/{itemId}

# Better — expose the resource directly
GET /items/{itemId}
```

When the sub-resource has its own identity and can be addressed independently, promote it to a top-level resource.

## Query Parameters

Use query parameters for everything that shapes the collection response but does not identify the resource:

| Purpose | Example |
|---------|---------|
| Filtering | `GET /articles?status=published&category=tech` |
| Sorting | `GET /articles?sort=publishedAt&order=desc` |
| Pagination | `GET /articles?page=2&perPage=25` |
| Search | `GET /articles?q=domain+driven+design` |
| Field selection | `GET /users?fields=id,name,email` |

Never put filter logic in the path segment: `/articles/published` is a smell if `published` is a filter — not a meaningful sub-resource that can be addressed independently.

## Versioning

### URL versioning (recommended default)

```
/v1/users
/v2/users
```

Visible, easy to route, easy to deprecate, testable directly in a browser. The most practical strategy for most teams.

### Header versioning

```
Accept: application/vnd.myapi.v1+json
```

Cleaner URLs, but harder to discover and test. Use when the team needs to shield clients from URL changes or when managing multiple representations of the same resource.

### What constitutes a breaking change

A breaking change requires a new version:
- Removing or renaming a field
- Changing a field's type (e.g., string → number)
- Changing the semantics of a status code
- Removing an endpoint
- Changing authentication requirements

**Adding optional fields or endpoints is not a breaking change.**

### Deprecation headers

Signal that a version is going away before removing it:

```
Deprecation: Tue, 01 Jan 2026 00:00:00 GMT
Sunset: Tue, 01 Jul 2026 00:00:00 GMT
Link: <https://api.example.com/v2/users>; rel="successor-version"
```

Support at least one prior major version during the deprecation window.

## Task-Based URLs

When a domain operation does not map cleanly to CRUD, use a task URL. The pattern is:

```
POST /collection/{id}/action
```

Examples:
```
POST /orders/{id}/cancel
POST /orders/{id}/ship
POST /accounts/{id}/activate
POST /accounts/{id}/deactivate
POST /invoices/{id}/send
POST /payments/{id}/refund
POST /users/{id}/verify-email
```

These are POST because they trigger a state transition — they are not safe or idempotent in the general case.

The URL names the business action in domain language, not the data field that changes.

```
# CRUD smell — encoding business action as a data mutation
PATCH /orders/{id}
{ "status": "cancelled" }

# Task-based — explicit domain operation
POST /orders/{id}/cancel
```

Benefits:
- Domain rules live on the server (`cancel` enforces that shipped orders cannot be cancelled).
- Clients express intent, not internal state changes.
- The API surface reads like the ubiquitous language.
- Each action can be versioned and evolved independently.
