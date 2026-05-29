# Go Examples

Examples using the standard `net/http` library and Chi router.

## Route Definition and URL Structure

```go
package main

import (
    "net/http"
    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
)

func NewRouter(h *OrderHandler) http.Handler {
    r := chi.NewRouter()
    r.Use(middleware.RequestID)
    r.Use(middleware.RealIP)
    r.Use(middleware.Logger)

    r.Route("/v1/orders", func(r chi.Router) {
        r.Use(AuthMiddleware)         // applied to all /v1/orders routes

        r.Get("/", h.List)            // collection
        r.Post("/", h.Create)         // create
        r.Get("/{id}", h.Get)         // one resource
        r.Patch("/{id}", h.Update)    // partial update
        r.Delete("/{id}", h.Delete)   // remove

        // Sub-collection
        r.Get("/{id}/items", h.ListItems)

        // Task-based URLs — domain operations
        r.Post("/{id}/cancel", h.Cancel)
        r.Post("/{id}/ship", h.Ship)
    })

    return r
}
```

## Status Codes in Responses

```go
package handler

import (
    "encoding/json"
    "net/http"
)

func (h *OrderHandler) Create(w http.ResponseWriter, r *http.Request) {
    var body CreateOrderRequest
    if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
        renderProblem(w, http.StatusBadRequest, "MALFORMED_REQUEST", "Invalid JSON body.")
        return
    }

    order, err := h.service.Create(r.Context(), body)
    if err != nil {
        renderDomainError(w, err)
        return
    }

    w.Header().Set("Location", "/v1/orders/"+order.ID)
    renderJSON(w, http.StatusCreated, order)
}

func (h *OrderHandler) Delete(w http.ResponseWriter, r *http.Request) {
    id := chi.URLParam(r, "id")
    if err := h.service.Delete(r.Context(), id); err != nil {
        renderDomainError(w, err)
        return
    }
    w.WriteHeader(http.StatusNoContent)
}
```

## Request Validation

```go
package handler

import (
    "errors"
    "github.com/go-playground/validator/v10"
)

var validate = validator.New()

type OrderItemRequest struct {
    ProductID string `json:"productId" validate:"required,uuid4"`
    Quantity  int    `json:"quantity"  validate:"required,gt=0"`
}

type ShippingAddressRequest struct {
    Street     string `json:"street"     validate:"required,min=1"`
    City       string `json:"city"       validate:"required,min=1"`
    PostalCode string `json:"postalCode" validate:"required"`
    Country    string `json:"country"    validate:"required,len=2"`
}

type CreateOrderRequest struct {
    CustomerID      string                 `json:"customerId"      validate:"required,uuid4"`
    Items           []OrderItemRequest     `json:"items"           validate:"required,min=1,dive"`
    ShippingAddress ShippingAddressRequest `json:"shippingAddress" validate:"required"`
}

func decodeAndValidate[T any](r *http.Request) (T, []ValidationError, error) {
    var body T
    if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
        return body, nil, err
    }
    if err := validate.Struct(body); err != nil {
        var ve validator.ValidationErrors
        if errors.As(err, &ve) {
            details := make([]ValidationError, len(ve))
            for i, e := range ve {
                details[i] = ValidationError{Field: e.Field(), Message: e.Tag()}
            }
            return body, details, nil
        }
    }
    return body, nil, nil
}
```

## Error Response Format (RFC 7807)

```go
package handler

import (
    "encoding/json"
    "fmt"
    "net/http"
    "strings"
)

type ProblemDetails struct {
    Type   string           `json:"type"`
    Title  string           `json:"title"`
    Status int              `json:"status"`
    Detail string           `json:"detail"`
    Errors []ValidationError `json:"errors,omitempty"`
}

type ValidationError struct {
    Field   string `json:"field"`
    Message string `json:"message"`
}

func renderProblem(w http.ResponseWriter, status int, code, detail string) {
    slug := strings.ToLower(strings.ReplaceAll(code, "_", "-"))
    p := ProblemDetails{
        Type:   fmt.Sprintf("https://api.example.com/errors/%s", slug),
        Title:  strings.ReplaceAll(code, "_", " "),
        Status: status,
        Detail: detail,
    }
    renderJSON(w, status, p)
}

func renderJSON(w http.ResponseWriter, status int, v any) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(v)
}
```

## Domain Error Translation

```go
package handler

import (
    "errors"
    "net/http"
    "your/module/domain"
)

func renderDomainError(w http.ResponseWriter, err error) {
    var notFound *domain.OrderNotFound
    var alreadyCancelled *domain.OrderAlreadyCancelled
    var insufficientStock *domain.InsufficientStock

    switch {
    case errors.As(err, &notFound):
        renderProblem(w, http.StatusNotFound, "ORDER_NOT_FOUND", err.Error())
    case errors.As(err, &alreadyCancelled):
        renderProblem(w, http.StatusConflict, "ORDER_ALREADY_CANCELLED", "This order has already been cancelled.")
    case errors.As(err, &insufficientStock):
        renderProblem(w, http.StatusUnprocessableEntity, "INSUFFICIENT_STOCK",
            fmt.Sprintf("Stock is short by %d units.", insufficientStock.Shortfall))
    default:
        slog.Error("unhandled error", "err", err)
        renderProblem(w, http.StatusInternalServerError, "INTERNAL_ERROR", "An unexpected error occurred.")
    }
}
```

## Pagination

```go
package handler

import (
    "math"
    "net/http"
    "strconv"
    "fmt"
)

type PaginationParams struct {
    Page    int
    PerPage int
}

func parsePagination(r *http.Request) (PaginationParams, error) {
    page, _ := strconv.Atoi(r.URL.Query().Get("page"))
    perPage, _ := strconv.Atoi(r.URL.Query().Get("per_page"))
    if page < 1 { page = 1 }
    if perPage < 1 { perPage = 25 }
    if perPage > 100 { perPage = 100 }
    return PaginationParams{Page: page, PerPage: perPage}, nil
}

func (h *OrderHandler) List(w http.ResponseWriter, r *http.Request) {
    p, _ := parsePagination(r)
    offset := (p.Page - 1) * p.PerPage

    orders, total, err := h.repo.FindMany(r.Context(), offset, p.PerPage)
    if err != nil {
        renderProblem(w, http.StatusInternalServerError, "INTERNAL_ERROR", "An unexpected error occurred.")
        return
    }

    totalPages := int(math.Ceil(float64(total) / float64(p.PerPage)))
    base := "/v1/orders"

    links := []string{
        fmt.Sprintf(`<%s?page=1&per_page=%d>; rel="first"`, base, p.PerPage),
        fmt.Sprintf(`<%s?page=%d&per_page=%d>; rel="last"`, base, totalPages, p.PerPage),
    }
    if p.Page > 1 {
        links = append(links, fmt.Sprintf(`<%s?page=%d&per_page=%d>; rel="prev"`, base, p.Page-1, p.PerPage))
    }
    if p.Page < totalPages {
        links = append(links, fmt.Sprintf(`<%s?page=%d&per_page=%d>; rel="next"`, base, p.Page+1, p.PerPage))
    }

    w.Header().Set("Link", strings.Join(links, ", "))
    w.Header().Set("X-Total-Count", strconv.Itoa(total))
    renderJSON(w, http.StatusOK, orders)
}
```

## Authentication Middleware (JWT)

```go
package middleware

import (
    "context"
    "net/http"
    "strings"
    "github.com/golang-jwt/jwt/v5"
)

type contextKey string
const userKey contextKey = "user"

func AuthMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        authHeader := r.Header.Get("Authorization")
        if !strings.HasPrefix(authHeader, "Bearer ") {
            renderProblem(w, http.StatusUnauthorized, "UNAUTHORIZED", "Bearer token required.")
            return
        }

        tokenStr := strings.TrimPrefix(authHeader, "Bearer ")
        token, err := jwt.Parse(tokenStr, keyFunc, jwt.WithValidMethods([]string{"RS256"}))
        if err != nil || !token.Valid {
            renderProblem(w, http.StatusUnauthorized, "UNAUTHORIZED", "Invalid or expired token.")
            return
        }

        claims := token.Claims.(jwt.MapClaims)
        user := AuthenticatedUser{ID: claims["sub"].(string)}
        ctx := context.WithValue(r.Context(), userKey, user)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

func CurrentUser(r *http.Request) AuthenticatedUser {
    return r.Context().Value(userKey).(AuthenticatedUser)
}
```

## Request ID Middleware

```go
package middleware

import (
    "net/http"
    "github.com/go-chi/chi/v5/middleware"
)

// chi/middleware.RequestID handles this automatically.
// Access it in handlers:
func requestIDFromContext(r *http.Request) string {
    return middleware.GetReqID(r.Context())
}

// Ensure it's echoed in all responses via a wrapper:
func RequestIDHeader(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("X-Request-ID", middleware.GetReqID(r.Context()))
        next.ServeHTTP(w, r)
    })
}
```

## Task-Based Endpoint

```go
func (h *OrderHandler) Cancel(w http.ResponseWriter, r *http.Request) {
    id := chi.URLParam(r, "id")
    user := middleware.CurrentUser(r)

    order, err := h.service.Cancel(r.Context(), id, user.ID)
    if err != nil {
        renderDomainError(w, err)
        return
    }
    renderJSON(w, http.StatusOK, order)
}
```
