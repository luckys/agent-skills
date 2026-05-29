# Go — Design Pattern Examples

Go has no classes, generics available since 1.18, and interfaces satisfied implicitly. Patterns look different but the same pressures apply.

---

## Strategy

```go
type PricingPolicy interface {
    Apply(subtotalCents int) int
}

type StandardPricing  struct{}
type PremiumPricing   struct{}
type PartnerPricing   struct{}

func (StandardPricing) Apply(s int) int  { return s }
func (PremiumPricing) Apply(s int) int   { return s * 8 / 10 }
func (PartnerPricing) Apply(s int) int   { return s * 85 / 100 }

type Cart struct{ policy PricingPolicy }

func (c Cart) Total(subtotal int) int {
    return c.policy.Apply(subtotal)
}
```

---

## State

```go
// State as an interface — each state struct implements it
type OrderState interface {
    Ship(o *Order) error
    Cancel(o *Order) error
    Status() string
}

type PendingState   struct{}
type ShippedState   struct{}
type CancelledState struct{}

func (PendingState) Ship(o *Order) error {
    o.state = ShippedState{}
    return nil
}
func (PendingState) Cancel(o *Order) error {
    o.state = CancelledState{}
    return nil
}
func (PendingState) Status() string { return "pending" }

func (ShippedState) Ship(*Order) error   { return errors.New("already shipped") }
func (ShippedState) Cancel(*Order) error { return errors.New("cannot cancel shipped order") }
func (ShippedState) Status() string      { return "shipped" }

func (CancelledState) Ship(*Order) error   { return errors.New("order cancelled") }
func (CancelledState) Cancel(*Order) error { return errors.New("already cancelled") }
func (CancelledState) Status() string      { return "cancelled" }

type Order struct{ state OrderState }

func NewOrder() *Order        { return &Order{state: PendingState{}} }
func (o *Order) Ship() error  { return o.state.Ship(o) }
func (o *Order) Cancel() error{ return o.state.Cancel(o) }
func (o *Order) Status() string{ return o.state.Status() }
```

---

## Observer

```go
// Idiomatic Go: callbacks or channels

// Callback-based observer
type EventHandler func(event OrderEvent)

type OrderEventPublisher struct {
    handlers []EventHandler
}

func (p *OrderEventPublisher) Subscribe(h EventHandler) {
    p.handlers = append(p.handlers, h)
}

func (p *OrderEventPublisher) Publish(event OrderEvent) {
    for _, h := range p.handlers {
        h(event)
    }
}

// Channel-based observer (fan-out)
type OrderEvent struct{ OrderID string; Kind string }

func NewOrderBus() (chan<- OrderEvent, <-chan OrderEvent) {
    ch := make(chan OrderEvent, 16)
    return ch, ch
}
```

---

## Command

```go
// Command as a function value — simplest Go approach
type Command func() error

func NewShipOrderCommand(repo OrderRepository, id string) Command {
    return func() error {
        order, err := repo.Find(id)
        if err != nil { return err }
        return repo.Save(order.Ship())
    }
}

// Command as an interface — when undo is needed
type UndoableCommand interface {
    Execute() error
    Undo() error
}

type CommandBus struct{ queue []Command }

func (b *CommandBus) Dispatch(cmd Command) { b.queue = append(b.queue, cmd) }
func (b *CommandBus) Run() error {
    for _, cmd := range b.queue {
        if err := cmd(); err != nil { return err }
    }
    return nil
}
```

---

## Factory Method

```go
// No classes: constructor functions are the factory

type Notification interface {
    Send(to, body string) error
}

type EmailNotification struct{ smtpHost string }
type SMSNotification   struct{ apiKey string }

func (e EmailNotification) Send(to, body string) error { /* smtp */ return nil }
func (s SMSNotification) Send(to, body string) error   { /* sms api */ return nil }

// Factory function — returns the interface
func NewNotification(channel string, cfg Config) (Notification, error) {
    switch channel {
    case "email": return EmailNotification{smtpHost: cfg.SMTPHost}, nil
    case "sms":   return SMSNotification{apiKey: cfg.SMSKey}, nil
    default:      return nil, fmt.Errorf("unknown channel: %s", channel)
    }
}
```

---

## Builder (Functional Options)

```go
// Functional options — idiomatic Go builder pattern
type Server struct {
    host    string
    port    int
    timeout time.Duration
    tls     bool
}

type Option func(*Server)

func WithHost(h string) Option        { return func(s *Server) { s.host = h } }
func WithPort(p int) Option           { return func(s *Server) { s.port = p } }
func WithTimeout(d time.Duration) Option { return func(s *Server) { s.timeout = d } }
func WithTLS() Option                 { return func(s *Server) { s.tls = true } }

func NewServer(opts ...Option) *Server {
    s := &Server{host: "localhost", port: 8080, timeout: 30 * time.Second}
    for _, o := range opts {
        o(s)
    }
    return s
}

// Usage
srv := NewServer(WithHost("0.0.0.0"), WithPort(9000), WithTLS())
```

---

## Decorator

```go
// Decorator: wrapper struct implements the same interface

type Logger interface {
    Log(msg string)
}

type ConsoleLogger struct{}
func (ConsoleLogger) Log(msg string) { fmt.Println(msg) }

// Decorated with timestamps — same interface, no inheritance
type TimestampLogger struct{ inner Logger }

func (t TimestampLogger) Log(msg string) {
    t.inner.Log(fmt.Sprintf("[%s] %s", time.Now().Format(time.RFC3339), msg))
}

// Stacked decoration
func NewProductionLogger() Logger {
    return TimestampLogger{inner: ConsoleLogger{}}
}
```

---

## Adapter

```go
// Adapter: translate an external interface into the one the domain expects

// Domain interface
type PaymentGateway interface {
    Charge(customerID string, cents int) error
}

// External Stripe SDK (we don't own this)
type StripeClient struct{}
func (s StripeClient) CreateCharge(params StripeParams) (*StripeCharge, error) { return nil, nil }

// Adapter — bridges Stripe to PaymentGateway
type StripeAdapter struct{ client StripeClient }

func (a StripeAdapter) Charge(customerID string, cents int) error {
    _, err := a.client.CreateCharge(StripeParams{
        Customer: customerID,
        Amount:   cents,
        Currency: "eur",
    })
    return err
}
```

---

## Composite

```go
// Composite: leaf and group both implement the same interface

type FileSystemNode interface {
    Name() string
    Size() int64
}

type File struct {
    name string
    size int64
}
func (f File) Name() string { return f.name }
func (f File) Size() int64  { return f.size }

type Directory struct {
    name     string
    children []FileSystemNode
}
func (d Directory) Name() string { return d.name }
func (d Directory) Size() int64 {
    var total int64
    for _, child := range d.children {
        total += child.Size()
    }
    return total
}
func (d *Directory) Add(node FileSystemNode) { d.children = append(d.children, node) }
```

---

## Proxy

```go
// Proxy: same interface, adds behaviour (lazy loading, cache, auth)

type UserRepository interface {
    FindByID(id string) (*User, error)
}

// Caching proxy
type CachedUserRepository struct {
    inner UserRepository
    cache map[string]*User
}

func (c *CachedUserRepository) FindByID(id string) (*User, error) {
    if u, ok := c.cache[id]; ok {
        return u, nil
    }
    u, err := c.inner.FindByID(id)
    if err != nil { return nil, err }
    c.cache[id] = u
    return u, nil
}
```

---

## Template Method

```go
// Go has no abstract methods; use embedding + function fields instead

type ReportGenerator struct {
    FetchData  func() ([]Row, error)
    FormatRows func(rows []Row) string
}

func (r ReportGenerator) Generate() (string, error) {
    rows, err := r.FetchData()
    if err != nil { return "", err }
    return r.FormatRows(rows), nil
}

// "Subclass" by injecting concrete steps
csvReport := ReportGenerator{
    FetchData:  fetchFromDB,
    FormatRows: formatAsCSV,
}
htmlReport := ReportGenerator{
    FetchData:  fetchFromDB,
    FormatRows: formatAsHTML,
}
```

---

## Chain of Responsibility

```go
type Middleware func(ctx context.Context, req Request) (Response, error)

type Handler func(Middleware) Middleware

func Chain(h func(context.Context, Request) (Response, error), middlewares ...Handler) Middleware {
    wrapped := Middleware(h)
    for i := len(middlewares) - 1; i >= 0; i-- {
        wrapped = middlewares[i](wrapped)
    }
    return wrapped
}

func AuthMiddleware(next Middleware) Middleware {
    return func(ctx context.Context, req Request) (Response, error) {
        if req.Token == "" { return Response{}, errors.New("unauthorized") }
        return next(ctx, req)
    }
}

func LoggingMiddleware(next Middleware) Middleware {
    return func(ctx context.Context, req Request) (Response, error) {
        log.Printf("→ %s", req.Path)
        resp, err := next(ctx, req)
        log.Printf("← %d", resp.Status)
        return resp, err
    }
}
```

---

## Result Pattern — `(value, error)`

```go
// Go's idiomatic result: multiple return values
// error = Left, value = Right

func ParseAge(s string) (int, error) {
    n, err := strconv.Atoi(s)
    if err != nil { return 0, fmt.Errorf("not a number: %w", err) }
    if n < 0 || n > 150 { return 0, fmt.Errorf("age out of range: %d", n) }
    return n, nil
}

// Chain with early return
func ProcessUser(emailStr, ageStr string) (User, error) {
    email, err := ParseEmail(emailStr)
    if err != nil { return User{}, err }
    age, err := ParseAge(ageStr)
    if err != nil { return User{}, err }
    return User{Email: email, Age: age}, nil
}
```

---

## Command + CommandHandler (CQRS write side)

```go
// Immutable command value object
type RegisterUserCommand struct {
    Email string
    Name  string
}

// Typed handler
type RegisterUserHandler struct {
    repo    UserRepository
    eventBus EventBus
}

func (h RegisterUserHandler) Handle(cmd RegisterUserCommand) error {
    user, err := NewUser(cmd.Email, cmd.Name)
    if err != nil { return err }
    if err := h.repo.Save(user); err != nil { return err }
    return h.eventBus.Publish(user.Events()...)
}
```

---

## Entity and Aggregate Root

```go
type UserID string

type User struct {
    id     UserID
    email  string
    events []DomainEvent
}

func NewUser(id UserID, email string) (*User, error) {
    if !strings.Contains(email, "@") {
        return nil, errors.New("invalid email")
    }
    u := &User{id: id, email: email}
    u.record(UserRegistered{UserID: string(id), Email: email})
    return u, nil
}

func (u *User) ID() UserID          { return u.id }
func (u *User) Email() string        { return u.email }
func (u *User) Events() []DomainEvent{ return u.events }
func (u *User) ClearEvents()         { u.events = nil }

func (u *User) record(e DomainEvent) { u.events = append(u.events, e) }
```

---

## Value Object (Money)

```go
type Money struct {
    amount   int64
    currency string
}

func NewMoney(amount int64, currency string) (Money, error) {
    if amount < 0 { return Money{}, errors.New("amount must be non-negative") }
    if currency == "" { return Money{}, errors.New("currency required") }
    return Money{amount: amount, currency: currency}, nil
}

func (m Money) Add(other Money) (Money, error) {
    if m.currency != other.currency {
        return Money{}, errors.New("currency mismatch")
    }
    return Money{amount: m.amount + other.amount, currency: m.currency}, nil
}

func (m Money) Equals(other Money) bool {
    return m.amount == other.amount && m.currency == other.currency
}
```

---

## Specification

```go
type Specification[T any] interface {
    IsSatisfiedBy(T) bool
}

type AndSpec[T any] struct{ left, right Specification[T] }
type OrSpec[T any]  struct{ left, right Specification[T] }
type NotSpec[T any] struct{ inner Specification[T] }

func (a AndSpec[T]) IsSatisfiedBy(v T) bool { return a.left.IsSatisfiedBy(v) && a.right.IsSatisfiedBy(v) }
func (o OrSpec[T]) IsSatisfiedBy(v T) bool  { return o.left.IsSatisfiedBy(v) || o.right.IsSatisfiedBy(v) }
func (n NotSpec[T]) IsSatisfiedBy(v T) bool { return !n.inner.IsSatisfiedBy(v) }

type ActiveUserSpec struct{}
func (ActiveUserSpec) IsSatisfiedBy(u User) bool { return u.Active }

type PremiumUserSpec struct{}
func (PremiumUserSpec) IsSatisfiedBy(u User) bool { return u.Plan == "premium" }

activePremium := AndSpec[User]{ActiveUserSpec{}, PremiumUserSpec{}}
```

---

## Domain Event

```go
type DomainEvent interface {
    EventName() string
    OccurredAt() time.Time
}

type UserRegistered struct {
    UserID     string
    Email      string
    occurredAt time.Time
}

func NewUserRegistered(userID, email string) UserRegistered {
    return UserRegistered{UserID: userID, Email: email, occurredAt: time.Now()}
}

func (e UserRegistered) EventName() string      { return "user.registered" }
func (e UserRegistered) OccurredAt() time.Time  { return e.occurredAt }
```
