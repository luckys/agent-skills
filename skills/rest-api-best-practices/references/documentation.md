# Documentation

An undocumented API is a broken API. Clients cannot safely use what they cannot understand, and undocumented behavior becomes accidental contracts that are impossible to change.

## What to Document for Every Endpoint

For each endpoint, document:

| Section | Content |
|---------|---------|
| **Method + URL** | `POST /v1/orders` |
| **Description** | What this endpoint does in domain terms |
| **Authentication** | Required auth method and scope |
| **Request headers** | Required and optional headers |
| **Path parameters** | Name, type, constraints |
| **Query parameters** | Name, type, default, constraints |
| **Request body** | Schema with field descriptions and constraints |
| **Response body** | Schema for each success response |
| **Status codes** | All possible codes with meaning |
| **Error responses** | Error codes, messages, and when each occurs |

## Working Examples

Every endpoint should have at least one complete request/response example — not a schema, but actual content a developer can copy and run.

```
# Create an order
POST /v1/orders
Content-Type: application/json
Authorization: Bearer eyJhbGci...

{
  "customerId": "usr_01J8X",
  "items": [
    { "productId": "prod_abc", "quantity": 2 }
  ],
  "shippingAddress": {
    "street": "Calle Mayor 10",
    "city": "Madrid",
    "postalCode": "28001",
    "country": "ES"
  }
}

# → 201 Created
Location: /v1/orders/ord_xyz789

{
  "id": "ord_xyz789",
  "status": "pending",
  "customerId": "usr_01J8X",
  "total": { "amount": 59.90, "currency": "EUR" },
  "createdAt": "2024-01-15T10:30:00Z"
}
```

Include examples for the most common error cases too:

```
# → 422 Unprocessable Entity (validation error)
{
  "type": "https://api.example.com/errors/validation-failed",
  "title": "Validation Failed",
  "status": 422,
  "errors": [
    { "field": "items", "message": "Must contain at least one item" }
  ]
}
```

## OpenAPI Specification

Use OpenAPI 3.x as the machine-readable contract. It generates:
- Interactive documentation (Swagger UI, Redoc)
- Client SDKs in any language
- Server stubs
- Automated contract tests

Keep the spec in the repository alongside the code. Treat spec drift (spec out of sync with implementation) as a bug.

```yaml
# openapi.yaml skeleton
openapi: "3.1.0"
info:
  title: Orders API
  version: "1.0.0"
paths:
  /v1/orders:
    post:
      summary: Create an order
      operationId: createOrder
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CreateOrderRequest"
      responses:
        "201":
          description: Order created
          headers:
            Location:
              schema:
                type: string
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Order"
        "422":
          $ref: "#/components/responses/ValidationError"
```

## Keeping Documentation Executable

Documentation that cannot be verified against the real API will drift. Strategies to keep it current:

- **Contract testing**: use the OpenAPI spec to generate tests that run against the real server (Schemathesis, Dredd, Spectral).
- **Example-driven testing**: use the examples in the spec as test inputs and verify the outputs match the documented schemas.
- **CI gate**: fail the pipeline if the spec fails linting or contract tests.
- **One source of truth**: generate both docs and validation from the same spec — never maintain parallel copies.

## Documenting Deprecations

When an endpoint or field is deprecated, document it prominently:
- Mark it as deprecated in the OpenAPI spec (`deprecated: true`).
- Include the removal date and the migration path.
- Link to the replacement endpoint or field.

```yaml
/v1/users/{id}:
  get:
    deprecated: true
    summary: "[Deprecated - removed 2025-12-01] Use /v2/users/{id} instead"
```

## Changelog

Maintain a public changelog that documents:
- New endpoints and fields (non-breaking)
- Deprecated endpoints with removal dates
- Breaking changes with migration guides (per major version)

A changelog is the first place an API consumer checks when something breaks after an upgrade.
