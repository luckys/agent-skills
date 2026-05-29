# Go — Functional Programming Examples

Concepts covered: pure functions, first-class functions, closures, error handling (`error` return), functional options, generics (1.18+), immutable value types, higher-order functions, iterator pattern.

Go is not a functional language, but it supports pure functions, first-class functions, closures, and immutable value types. FP idioms in Go stay idiomatic — avoid over-abstracting.

---

## Pure Functions and Value Semantics

```go
package pricing

// Pure — same input always gives same output, no side effects
func ApplyDiscount(rate, price float64) float64 {
    return price * (1 - rate)
}

// Pure — structs are value types; assignment copies, not references
type Cart struct {
    Items []Item
}

// Returns a new Cart — original is unchanged because we copy the struct
// NOTE: the Items slice still shares underlying array; use append for safety
func AddItem(cart Cart, item Item) Cart {
    newItems := make([]Item, len(cart.Items)+1)
    copy(newItems, cart.Items)
    newItems[len(cart.Items)] = item
    return Cart{Items: newItems}
}
```

---

## First-Class Functions and Closures

```go
package main

// Functions as values
type Predicate[T any] func(T) bool
type Transform[A, B any] func(A) B

// Closure — captures surrounding scope
func MakeAdder(n int) func(int) int {
    return func(x int) int {
        return x + n
    }
}

add5 := MakeAdder(5)
add5(10)  // 15

// Closure for dependency injection
func MakeUserService(db Database) func(id string) (User, error) {
    return func(id string) (User, error) {
        return db.FindUser(id)
    }
}

// Partial application via closure
func MakeDiscountFn(rate float64) func(float64) float64 {
    return func(price float64) float64 {
        return price * (1 - rate)
    }
}

applyTenPercent := MakeDiscountFn(0.1)
applyTenPercent(200)  // 180.0
```

---

## Error Handling — Go's Either

```go
package validation

import (
    "fmt"
    "strings"
)

// Go's idiomatic (value, error) is the Either pattern
// error = Left, value = Right

func ValidateEmail(email string) (string, error) {
    email = strings.TrimSpace(strings.ToLower(email))
    if !strings.Contains(email, "@") {
        return "", fmt.Errorf("invalid email: %q", email)
    }
    return email, nil
}

func ValidateAge(age int) (int, error) {
    if age < 0 || age > 150 {
        return 0, fmt.Errorf("age must be between 0 and 150, got %d", age)
    }
    return age, nil
}

type User struct {
    Email string
    Age   int
}

// Chain validations — early return on first error
func ParseUser(email string, age int) (User, error) {
    validEmail, err := ValidateEmail(email)
    if err != nil {
        return User{}, err
    }
    validAge, err := ValidateAge(age)
    if err != nil {
        return User{}, err
    }
    return User{Email: validEmail, Age: validAge}, nil
}

// Usage
user, err := ParseUser("alice@example.com", 30)
if err != nil {
    log.Printf("validation failed: %v", err)
    return
}
fmt.Printf("Valid user: %+v\n", user)
```

---

## Functional Options Pattern

```go
package server

// Functional options: configure a struct without a bloated constructor
// Robert Pike's pattern — idiomatic Go FP

type Server struct {
    host    string
    port    int
    timeout time.Duration
    maxConn int
}

type Option func(*Server)

func WithHost(host string) Option {
    return func(s *Server) { s.host = host }
}

func WithPort(port int) Option {
    return func(s *Server) { s.port = port }
}

func WithTimeout(d time.Duration) Option {
    return func(s *Server) { s.timeout = d }
}

func NewServer(opts ...Option) *Server {
    s := &Server{
        host:    "localhost",
        port:    8080,
        timeout: 30 * time.Second,
        maxConn: 100,
    }
    for _, opt := range opts {
        opt(s)
    }
    return s
}

// Usage
srv := NewServer(
    WithHost("0.0.0.0"),
    WithPort(9000),
    WithTimeout(60 * time.Second),
)
```

---

## Generics and Higher-Order Functions (Go 1.18+)

```go
package slicefn

// Map :: (A -> B) -> []A -> []B
func Map[A, B any](slice []A, fn func(A) B) []B {
    result := make([]B, len(slice))
    for i, v := range slice {
        result[i] = fn(v)
    }
    return result
}

// Filter :: (A -> bool) -> []A -> []A
func Filter[A any](slice []A, pred func(A) bool) []A {
    var result []A
    for _, v := range slice {
        if pred(v) {
            result = append(result, v)
        }
    }
    return result
}

// Reduce :: (B -> A -> B) -> B -> []A -> B
func Reduce[A, B any](slice []A, init B, fn func(B, A) B) B {
    acc := init
    for _, v := range slice {
        acc = fn(acc, v)
    }
    return acc
}

// FlatMap :: (A -> []B) -> []A -> []B
func FlatMap[A, B any](slice []A, fn func(A) []B) []B {
    var result []B
    for _, v := range slice {
        result = append(result, fn(v)...)
    }
    return result
}

// Usage
type Order struct {
    ID     string
    Active bool
    Total  float64
    Items  []Item
}

orders := []Order{...}

activeOrders := Filter(orders, func(o Order) bool { return o.Active })
totals       := Map(activeOrders, func(o Order) float64 { return o.Total })
grandTotal   := Reduce(totals, 0.0, func(acc, t float64) float64 { return acc + t })
allItems     := FlatMap(orders, func(o Order) []Item { return o.Items })
```

---

## Standard Library — `slices` and `maps` (Go 1.21+)

```go
import (
    "cmp"
    "slices"
    "maps"
)

type Order struct {
    ID     string
    Total  float64
    Status string
}

orders := []Order{...}

// Sort by field
slices.SortFunc(orders, func(a, b Order) int {
    return cmp.Compare(a.Total, b.Total)
})

// Check if any/all satisfy a predicate
hasActive := slices.ContainsFunc(orders, func(o Order) bool { return o.Status == "active" })

// Collect map keys
keys := slices.Collect(maps.Keys(myMap))
```

---

## Immutability via Value Types

```go
// Structs are value types — assignment copies
type Point struct {
    X, Y float64
}

p1 := Point{1.0, 2.0}
p2 := p1        // p2 is a copy — changing p2 does not affect p1
p2.X = 99.0
fmt.Println(p1) // {1 2} — unchanged

// For immutable domain values, avoid pointer receivers in pure functions
func (p Point) Translate(dx, dy float64) Point {
    return Point{p.X + dx, p.Y + dy}  // new Point — p unchanged
}

// Use pointer only for mutation or performance with large structs
// For domain value objects, prefer value receivers
type Money struct {
    Amount   int64
    Currency string
}

func (m Money) Add(other Money) Money {
    if m.Currency != other.Currency {
        panic("currency mismatch")
    }
    return Money{Amount: m.Amount + other.Amount, Currency: m.Currency}
}
```

---

## Function Pipelines with Variadic Functions

```go
// Pipeline via slice of functions (when types align)
type Middleware func(http.Handler) http.Handler

func Chain(middlewares ...Middleware) Middleware {
    return func(final http.Handler) http.Handler {
        for i := len(middlewares) - 1; i >= 0; i-- {
            final = middlewares[i](final)
        }
        return final
    }
}

// Generic transform pipeline
type Step[T any] func(T) (T, error)

func Pipeline[T any](steps ...Step[T]) Step[T] {
    return func(input T) (T, error) {
        current := input
        for _, step := range steps {
            next, err := step(current)
            if err != nil {
                return current, err
            }
            current = next
        }
        return current, nil
    }
}

// Usage
process := Pipeline(
    normalizeInput,
    validateInput,
    enrichInput,
)
result, err := process(rawInput)
```

---

## Side Effect Boundary

```go
package registration

// Pure core — no I/O, returns (value, error)
func ProcessRegistration(
    existingEmails map[string]bool,
    email, name, id string,
) (User, error) {
    email = strings.TrimSpace(strings.ToLower(email))
    if !strings.Contains(email, "@") {
        return User{}, errors.New("invalid email")
    }
    if existingEmails[email] {
        return User{}, errors.New("email already registered")
    }
    return User{ID: id, Email: email, Name: name}, nil
}

// Impure shell — only coordinates I/O
func RegisterUser(ctx context.Context, db DB, email, name string) (User, error) {
    existing, err := db.AllEmails(ctx)       // I/O
    if err != nil {
        return User{}, err
    }
    id := uuid.New().String()                // I/O (randomness)
    user, err := ProcessRegistration(existing, email, name, id)  // pure
    if err != nil {
        return User{}, err
    }
    if err := db.SaveUser(ctx, user); err != nil {  // I/O
        return User{}, err
    }
    return user, nil
}
```

---

## Iterator Pattern (Go 1.23 range-over-func)

```go
// Go 1.23 — range over iterator functions
import "iter"

// Producer that yields values
func ActiveOrders(orders []Order) iter.Seq[Order] {
    return func(yield func(Order) bool) {
        for _, o := range orders {
            if o.Active {
                if !yield(o) {
                    return  // consumer stopped iteration
                }
            }
        }
    }
}

// Usage with range
for order := range ActiveOrders(orders) {
    fmt.Println(order.ID)
}
```
