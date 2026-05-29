# Python Examples

Examples using FastAPI (primary) and Django REST Framework (secondary).

## Route Definition and URL Structure

```python
from fastapi import APIRouter

router = APIRouter(prefix="/v1")

# Collection and resource routes
router.get("/orders")(list_orders)
router.post("/orders")(create_order)
router.get("/orders/{order_id}")(get_order)
router.patch("/orders/{order_id}")(update_order)
router.delete("/orders/{order_id}")(delete_order)

# Sub-collection
router.get("/orders/{order_id}/items")(list_order_items)

# Task-based URLs — domain operations
router.post("/orders/{order_id}/cancel")(cancel_order)
router.post("/orders/{order_id}/ship")(ship_order)


# Django REST Framework — ViewSet
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import action

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="order")

class OrderViewSet(ViewSet):
    def list(self, request): ...
    def create(self, request): ...
    def retrieve(self, request, pk): ...
    def partial_update(self, request, pk): ...
    def destroy(self, request, pk): ...

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk): ...
```

## Status Codes in Responses

```python
from fastapi import status
from fastapi.responses import JSONResponse, Response

# 200 OK — default for GET
@router.get("/orders/{order_id}")
async def get_order(order_id: str) -> OrderResponse:
    return order  # FastAPI serializes and returns 200

# 201 Created — POST that creates a resource
@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order(
    body: CreateOrderRequest,
    response: Response,
) -> OrderResponse:
    order = await order_service.create(body)
    response.headers["Location"] = f"/v1/orders/{order.id}"
    return order

# 204 No Content — DELETE with no body
@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: str) -> None:
    await order_service.delete(order_id)

# 202 Accepted — async operation
@router.post("/orders/{order_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_order(order_id: str) -> dict:
    job = await order_service.queue_cancel(order_id)
    return {"jobId": job.id, "message": "Cancellation queued."}
```

## Request Validation (Pydantic)

```python
from pydantic import BaseModel, EmailStr, field_validator, UUID4
from typing import list

class OrderItemRequest(BaseModel):
    product_id: UUID4
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("must be greater than 0")
        return v

class ShippingAddressRequest(BaseModel):
    street: str
    city: str
    postal_code: str
    country: str  # ISO 3166-1 alpha-2

class CreateOrderRequest(BaseModel):
    customer_id: UUID4
    items: list[OrderItemRequest]
    shipping_address: ShippingAddressRequest

    @field_validator("items")
    @classmethod
    def items_must_not_be_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("must contain at least one item")
        return v


# FastAPI validates automatically — 422 returned on failure
@router.post("/orders", status_code=201)
async def create_order(body: CreateOrderRequest) -> OrderResponse:
    ...
```

## Error Response Format (RFC 7807)

```python
from pydantic import BaseModel
from typing import list, Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

class ErrorDetail(BaseModel):
    field: str
    message: str

class ProblemDetails(BaseModel):
    type: str
    title: str
    status: int
    detail: str
    errors: Optional[list[ErrorDetail]] = None

def problem(status: int, code: str, detail: str) -> ProblemDetails:
    slug = code.lower().replace("_", "-")
    return ProblemDetails(
        type=f"https://api.example.com/errors/{slug}",
        title=code.replace("_", " ").title(),
        status=status,
        detail=detail,
    )

# Override FastAPI's default 422 handler to use RFC 7807 format
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        ErrorDetail(field=".".join(str(loc) for loc in e["loc"][1:]), message=e["msg"])
        for e in exc.errors()
    ]
    body = ProblemDetails(
        type="https://api.example.com/errors/validation-failed",
        title="Validation Failed",
        status=422,
        detail="The request body contains fields that failed validation.",
        errors=errors,
    )
    return JSONResponse(status_code=422, content=body.model_dump())
```

## Domain Error Translation

```python
from fastapi import Request
from fastapi.responses import JSONResponse

# Domain errors — no HTTP knowledge
class OrderNotFound(Exception):
    def __init__(self, order_id: str):
        self.order_id = order_id

class OrderAlreadyCancelled(Exception): ...
class InsufficientStock(Exception):
    def __init__(self, shortfall: int):
        self.shortfall = shortfall

# Global exception handlers — one place, all errors
@app.exception_handler(OrderNotFound)
async def order_not_found_handler(request: Request, exc: OrderNotFound) -> JSONResponse:
    body = problem(404, "ORDER_NOT_FOUND", f"Order {exc.order_id} not found.")
    return JSONResponse(status_code=404, content=body.model_dump())

@app.exception_handler(OrderAlreadyCancelled)
async def order_already_cancelled_handler(request: Request, exc: OrderAlreadyCancelled) -> JSONResponse:
    body = problem(409, "ORDER_ALREADY_CANCELLED", "This order has already been cancelled.")
    return JSONResponse(status_code=409, content=body.model_dump())

@app.exception_handler(InsufficientStock)
async def insufficient_stock_handler(request: Request, exc: InsufficientStock) -> JSONResponse:
    body = problem(422, "INSUFFICIENT_STOCK", f"Stock is short by {exc.shortfall} units.")
    return JSONResponse(status_code=422, content=body.model_dump())
```

## Pagination

```python
from pydantic import BaseModel, Field
from typing import TypeVar, Generic, list

T = TypeVar("T")

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=25, ge=1, le=100)

class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: dict

@router.get("/orders")
async def list_orders(
    pagination: Annotated[PaginationParams, Query()],
    response: Response,
) -> PaginatedResponse[OrderSummary]:
    offset = (pagination.page - 1) * pagination.per_page
    orders, total = await order_repo.find_many(offset=offset, limit=pagination.per_page)
    total_pages = math.ceil(total / pagination.per_page)
    base = "/v1/orders"

    links = [f'<{base}?page=1&per_page={pagination.per_page}>; rel="first"']
    links.append(f'<{base}?page={total_pages}&per_page={pagination.per_page}>; rel="last"')
    if pagination.page > 1:
        links.append(f'<{base}?page={pagination.page - 1}&per_page={pagination.per_page}>; rel="prev"')
    if pagination.page < total_pages:
        links.append(f'<{base}?page={pagination.page + 1}&per_page={pagination.per_page}>; rel="next"')

    response.headers["Link"] = ", ".join(links)
    response.headers["X-Total-Count"] = str(total)

    return PaginatedResponse(
        data=orders,
        meta={"total": total, "page": pagination.page, "perPage": pagination.per_page},
    )
```

## Filtering and Sorting

```python
from enum import Enum
from typing import Optional
from fastapi import Query

class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    cancelled = "cancelled"

class OrderSortField(str, Enum):
    created_at = "created_at"
    total = "total"
    status = "status"

@router.get("/orders")
async def list_orders(
    status: Optional[OrderStatus] = Query(None),
    customer_id: Optional[UUID4] = Query(None),
    sort: OrderSortField = Query(OrderSortField.created_at),
    order: Literal["asc", "desc"] = Query("desc"),
    pagination: Annotated[PaginationParams, Query()] = ...,
) -> PaginatedResponse[OrderSummary]:
    filters = OrderFilters(status=status, customer_id=customer_id)
    ...
```

## Authentication Middleware (JWT)

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthenticatedUser:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_PUBLIC_KEY,
            algorithms=["RS256"],
            audience=settings.JWT_AUDIENCE,
        )
        return AuthenticatedUser(id=payload["sub"], roles=payload.get("roles", []))
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")

# Apply to protected routes
@router.get("/orders")
async def list_orders(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PaginatedResponse[OrderSummary]:
    ...
```

## Request ID Middleware

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

app.add_middleware(RequestIdMiddleware)
```

## Task-Based Endpoint

```python
@router.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> OrderResponse:
    # Raises domain exceptions → caught by exception handlers above
    order = await order_service.cancel(order_id, requested_by=current_user.id)
    return OrderResponse.from_domain(order)
```
