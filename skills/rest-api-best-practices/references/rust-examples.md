# Rust Examples

Examples using axum (Tokio ecosystem), the most common modern Rust web framework.

## Route Definition and URL Structure

```rust
use axum::{Router, routing::{get, post, patch, delete}};

fn router(state: AppState) -> Router {
    Router::new()
        // collection + resource
        .route("/v1/orders", get(list_orders).post(create_order))
        .route("/v1/orders/:id", get(get_order).patch(update_order).delete(delete_order))
        // sub-collection
        .route("/v1/orders/:id/items", get(list_order_items))
        // task-based URLs — domain operations
        .route("/v1/orders/:id/cancel", post(cancel_order))
        .route("/v1/orders/:id/ship", post(ship_order))
        .with_state(state)
}
```

## Status Codes in Responses

```rust
use axum::{http::StatusCode, response::IntoResponse, Json};
use axum::http::header::LOCATION;

// 201 Created + Location header
async fn create_order(
    State(svc): State<OrderService>,
    Json(body): Json<CreateOrderRequest>,
) -> Result<impl IntoResponse, ApiError> {
    let order = svc.create(body).await?;
    let location = format!("/v1/orders/{}", order.id);
    Ok((
        StatusCode::CREATED,
        [(LOCATION, location)],
        Json(OrderResponse::from(order)),
    ))
}

// 204 No Content
async fn delete_order(
    State(svc): State<OrderService>,
    Path(id): Path<String>,
) -> Result<StatusCode, ApiError> {
    svc.delete(&id).await?;
    Ok(StatusCode::NO_CONTENT)
}
```

## Request Validation

```rust
use serde::Deserialize;
use validator::Validate; // `validator` crate

#[derive(Deserialize, Validate)]
struct OrderItemRequest {
    #[validate(length(equal = 36))]
    product_id: String,
    #[validate(range(min = 1))]
    quantity: u32,
}

#[derive(Deserialize, Validate)]
struct CreateOrderRequest {
    #[validate(length(equal = 36))]
    customer_id: String,
    #[validate(length(min = 1), nested)]
    items: Vec<OrderItemRequest>,
}

async fn create_order(
    Json(body): Json<CreateOrderRequest>,
) -> Result<impl IntoResponse, ApiError> {
    body.validate().map_err(ApiError::Validation)?; // -> 422
    // ...
    Ok(StatusCode::CREATED)
}
```

## Error Response Format (RFC 7807)

```rust
use axum::{http::StatusCode, response::{IntoResponse, Response}, Json};
use serde::Serialize;

#[derive(Serialize)]
struct ProblemDetails {
    #[serde(rename = "type")]
    type_: String,
    title: String,
    status: u16,
    detail: String,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    errors: Vec<FieldError>,
}

#[derive(Serialize)]
struct FieldError { field: String, message: String }

fn problem(status: StatusCode, code: &str, detail: &str) -> ProblemDetails {
    let slug = code.to_lowercase().replace('_', "-");
    ProblemDetails {
        type_: format!("https://api.example.com/errors/{slug}"),
        title: code.replace('_', " "),
        status: status.as_u16(),
        detail: detail.to_string(),
        errors: Vec::new(),
    }
}
```

## Domain Error Translation

```rust
// Domain errors as an enum — no HTTP knowledge
#[derive(thiserror::Error, Debug)]
enum DomainError {
    #[error("order {0} not found")]
    OrderNotFound(String),
    #[error("order already cancelled")]
    OrderAlreadyCancelled,
    #[error("stock short by {0}")]
    InsufficientStock(u32),
}

// API error wrapper that knows how to become an HTTP response
enum ApiError {
    Domain(DomainError),
    Validation(validator::ValidationErrors),
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let (status, code, detail) = match self {
            ApiError::Domain(DomainError::OrderNotFound(id)) =>
                (StatusCode::NOT_FOUND, "ORDER_NOT_FOUND", format!("Order {id} not found.")),
            ApiError::Domain(DomainError::OrderAlreadyCancelled) =>
                (StatusCode::CONFLICT, "ORDER_ALREADY_CANCELLED", "This order has already been cancelled.".into()),
            ApiError::Domain(DomainError::InsufficientStock(n)) =>
                (StatusCode::UNPROCESSABLE_ENTITY, "INSUFFICIENT_STOCK", format!("Stock is short by {n} units.")),
            ApiError::Validation(_) =>
                (StatusCode::UNPROCESSABLE_ENTITY, "VALIDATION_FAILED", "The request body failed validation.".into()),
        };
        let body = problem(status, code, &detail);
        (status, Json(body)).into_response()
    }
}

// Lets `?` convert domain errors automatically
impl From<DomainError> for ApiError {
    fn from(e: DomainError) -> Self { ApiError::Domain(e) }
}
```

## Pagination

```rust
use serde::Deserialize;

#[derive(Deserialize)]
struct Pagination {
    #[serde(default = "default_page")]
    page: u32,
    #[serde(default = "default_per_page")]
    per_page: u32,
}
fn default_page() -> u32 { 1 }
fn default_per_page() -> u32 { 25 }

async fn list_orders(
    State(repo): State<OrderRepo>,
    Query(p): Query<Pagination>,
) -> Result<impl IntoResponse, ApiError> {
    let per_page = p.per_page.min(100);
    let offset = (p.page.saturating_sub(1)) * per_page;

    let (orders, total) = repo.find_many(offset, per_page).await?;
    let total_pages = (total + per_page - 1) / per_page;
    let base = "/v1/orders";

    let mut links = vec![
        format!("<{base}?page=1&per_page={per_page}>; rel=\"first\""),
        format!("<{base}?page={total_pages}&per_page={per_page}>; rel=\"last\""),
    ];
    if p.page > 1 {
        links.push(format!("<{base}?page={}&per_page={per_page}>; rel=\"prev\"", p.page - 1));
    }
    if p.page < total_pages {
        links.push(format!("<{base}?page={}&per_page={per_page}>; rel=\"next\"", p.page + 1));
    }

    Ok((
        StatusCode::OK,
        [("Link", links.join(", ")), ("X-Total-Count", total.to_string())],
        Json(orders),
    ))
}
```

## Authentication Middleware (JWT)

```rust
use axum::{extract::Request, middleware::Next, response::Response};
use jsonwebtoken::{decode, DecodingKey, Validation, Algorithm};

async fn auth(mut req: Request, next: Next) -> Result<Response, ApiError> {
    let token = req
        .headers()
        .get("Authorization")
        .and_then(|h| h.to_str().ok())
        .and_then(|h| h.strip_prefix("Bearer "))
        .ok_or(ApiError::unauthorized("Bearer token required."))?;

    let data = decode::<Claims>(
        token,
        &DecodingKey::from_rsa_pem(JWT_PUBLIC_KEY).unwrap(),
        &Validation::new(Algorithm::RS256),
    ).map_err(|_| ApiError::unauthorized("Invalid or expired token."))?;

    req.extensions_mut().insert(AuthUser { id: data.claims.sub });
    Ok(next.run(req).await)
}

// Apply: Router::new().route(...).layer(middleware::from_fn(auth))
```

## Request ID Middleware

```rust
use axum::{extract::Request, middleware::Next, response::Response};
use uuid::Uuid;

async fn request_id(mut req: Request, next: Next) -> Response {
    let id = req
        .headers()
        .get("X-Request-ID")
        .and_then(|h| h.to_str().ok())
        .map(String::from)
        .unwrap_or_else(|| Uuid::new_v4().to_string());

    let mut res = next.run(req).await;
    res.headers_mut().insert("X-Request-ID", id.parse().unwrap());
    res
}
```

## Task-Based Endpoint

```rust
async fn cancel_order(
    State(svc): State<OrderService>,
    Extension(user): Extension<AuthUser>,
    Path(id): Path<String>,
) -> Result<impl IntoResponse, ApiError> {
    // svc.cancel returns Result<Order, DomainError>; `?` maps via From<DomainError>
    let order = svc.cancel(&id, &user.id).await?;
    Ok((StatusCode::OK, Json(OrderResponse::from(order))))
}
```

## What to Notice

- `Result<T, ApiError>` + `IntoResponse` centralizes error-to-HTTP translation — the domain stays HTTP-free.
- `?` propagates domain errors and converts them via `From`, mirroring the middleware error handler in other languages.
- The type system forces every error path to be handled — there is no unhandled-exception escape hatch.
