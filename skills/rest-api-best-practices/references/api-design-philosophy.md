# API Design Philosophy

## REST Architectural Constraints

REST (Representational State Transfer) is defined by six architectural constraints. Breaking them does not make an API wrong, but it does forfeit the guarantees REST provides.

### 1. Uniform Interface

The most important constraint. It has four sub-constraints:

1. **Resource identification** — resources are identified by URI, independent of their representation.
2. **Manipulation through representations** — clients interact with resources via representations (JSON, XML), not directly with the resource.
3. **Self-descriptive messages** — each message includes enough information to describe how to process it (Content-Type, status codes, Cache-Control).
4. **HATEOAS** — representations include links to available next actions.

### 2. Statelessness

Each request must contain all information needed to process it. The server holds no client session state between requests.

- Benefits: horizontal scalability, fault tolerance, simplicity.
- Implication: authentication credentials must be sent with every request.
- Never store "current user state" on the server to resume across requests.

### 3. Cacheability

Responses must explicitly declare whether they are cacheable. GET responses are cacheable by default unless told otherwise. Proper caching reduces load and improves perceived latency.

### 4. Client–Server Separation

The client and server are decoupled and can evolve independently. The only coupling is the API contract (URLs, methods, response shapes). The server should not know or care about the client's rendering or state.

### 5. Layered System

A client cannot tell whether it is talking to the origin server or an intermediary (load balancer, CDN, API gateway, caching proxy). APIs must behave identically regardless of intermediaries.

### 6. Code on Demand (optional)

Servers may optionally send executable code to clients (JavaScript). Rarely used in practice.

---

## CRUD APIs Are Poor Design

Exposing a direct CRUD interface over domain entities is the most common REST anti-pattern.

> "CRUD APIs and CRUD-driven systems — meaning systems built around Create, Read, Update, and Delete operations — are, in the long run, the hardest to change and evolve." — Derek Comartin

Problems with pure CRUD APIs:

**Couples clients to data structure.** A schema change (renaming a field, splitting a table) immediately breaks consumers. The API leaks the database model.

**Hides business intent.** `PATCH /orders/{id}` with `{ "status": "cancelled" }` and `{ "status": "shipped" }` look identical. The consumer must know what transitions are legal and what side effects they trigger (email sent? stock updated?).

**Misses invariants.** A rule like "an order cannot be cancelled after it ships" is invisible in a raw PATCH. The client must implement the guard — and different clients will implement it differently.

**Forces multi-step choreography.** A single business operation (place an order: validate stock, charge payment, send confirmation) becomes a sequence of CRUD calls that the client must orchestrate correctly.

**When pure CRUD is acceptable:**
- Truly data-centric resources with no business logic: configuration entries, reference data, admin panels on lookup tables.
- Internal tooling where the consumer controls both sides of the contract.

---

## Task-Based API Design

Design endpoints around business capabilities, not data rows.

```
# CRUD (poor for domain operations)
PATCH /orders/{id}        { "status": "cancelled" }
PATCH /orders/{id}        { "status": "shipped" }
PATCH /accounts/{id}      { "active": false }

# Task-based (expresses domain intent)
POST /orders/{id}/cancel
POST /orders/{id}/ship
POST /accounts/{id}/deactivate
```

Benefits:
- The URL reads like the domain's ubiquitous language.
- Business rules live on the server: `cancel` enforces that you cannot cancel a shipped order.
- Clients express **intent**, not internal state mutations.
- Each action is independently versioned, documented, and tested.
- Side effects (events, notifications, stock updates) are encapsulated behind the action.

### Naming task URLs

Use the domain's verb in past tense or imperative:

```
POST /invoices/{id}/send
POST /invoices/{id}/void
POST /subscriptions/{id}/pause
POST /subscriptions/{id}/resume
POST /users/{id}/verify-email
POST /users/{id}/request-password-reset
```

---

## HATEOAS

Hypermedia As The Engine Of Application State: responses include links that guide the client to available next actions. The client discovers state transitions from the response rather than hard-coding them.

```json
{
  "id": "ord_01J8X",
  "status": "pending",
  "total": { "amount": 120.00, "currency": "EUR" },
  "_links": {
    "self":   { "href": "/orders/ord_01J8X" },
    "cancel": { "href": "/orders/ord_01J8X/cancel", "method": "POST" },
    "items":  { "href": "/orders/ord_01J8X/items" },
    "customer": { "href": "/users/usr_42" }
  }
}
```

When the order is shipped, `cancel` disappears from `_links` — the client does not need to know the cancellation business rule; it just checks whether the link is present.

Full HATEOAS is rarely implemented in practice (the tooling and discipline cost is high). A pragmatic middle ground: include `_links` for navigation and action discovery without requiring full hypermedia compliance.

---

## API as a Product

- **Design for the consumer**, not for the implementation. The right surface is discovered by talking to consumers, not by mirroring the database.
- **Provide documentation before shipping** — an undocumented API is a broken API.
- **Treat breaking changes like database migrations**: they require coordination, a migration path, and a deadline.
- **Gather consumer feedback** early and continuously. The API surface you ship first is not the right one.
- **A stable contract is more valuable than an internally "correct" one.** Once consumers depend on a shape, stability trumps elegance.
- **Version proactively** — add versioning before the first consumer, not after the first breaking change.
