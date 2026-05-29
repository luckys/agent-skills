# Go Examples

Go has no classes or inheritance. OOP concepts are expressed through structs + methods, implicit interfaces, and composition via embedding. The same design pressures apply — the mechanisms differ.

## Concepts Covered

- Value Objects and Invariants
- First-Class Collections
- Tell, Don't Ask
- Role-Based Collaboration
- Dependency Injection
- Explicit Interfaces (implicit satisfaction)
- Composition over Inheritance
- Message-Based Design
- Law of Demeter Violation and Fix
- Immutable Objects (value semantics)
- Null Object
- Anemic versus Rich Model
- SOLID — Single Responsibility
- SOLID — Open/Closed
- SOLID — Interface Segregation
- SOLID — Dependency Inversion
- Object Calisthenics — Wrap Primitive
- Object Calisthenics — No Else Rule
- Object Calisthenics — No Getters
- Object Calisthenics — Don't Abbreviate
- Composed Method
- Explaining Message

---

## Value Objects and Invariants

```go
// Unexported fields — callers cannot bypass invariants
type Money struct {
    cents int
}

func NewMoney(cents int) (Money, error) {
    if cents < 0 {
        return Money{}, errors.New("money cannot be negative")
    }
    return Money{cents: cents}, nil
}

func (m Money) Add(other Money) Money {
    return Money{cents: m.cents + other.cents}
}

func (m Money) MultiplyByPercent(percent int) Money {
    return Money{cents: m.cents * percent / 100}
}

func (m Money) Cents() int {
    return m.cents
}
```

---

## First-Class Collections

```go
type OrderLine struct {
    subtotal Money
}

func (ol OrderLine) Subtotal() Money {
    return ol.subtotal
}

// The collection owns its rules
type OrderLines struct {
    items []OrderLine
}

func (ol OrderLines) Total() Money {
    total := Money{}
    for _, item := range ol.items {
        total = total.Add(item.Subtotal())
    }
    return total
}

func (ol OrderLines) IsEmpty() bool {
    return len(ol.items) == 0
}
```

---

## Tell, Don't Ask

```go
type Address struct {
    countryCode string
}

// Tell the address — don't ask for the country and decide outside
func (a Address) IsDomestic() bool {
    return a.countryCode == "ES"
}

type Shipment struct {
    address Address
}

func (s Shipment) DispatchWindowInDays() int {
    if s.address.IsDomestic() {
        return 2
    }
    return 5
}
```

---

## Role-Based Collaboration

```go
// The role — what behavior the collaborator must provide
type CurrencyFormatter interface {
    Format(amount Money) string
}

type OrderSummary struct {
    formatter CurrencyFormatter
}

func (os OrderSummary) TotalLabel(lines OrderLines) string {
    return os.formatter.Format(lines.Total())
}
```

---

## Dependency Injection

```go
type Mailer interface {
    Send(to, body string) error
}

type Invoice struct {
    recipient string
    body      string
}

func (i Invoice) RecipientEmail() string { return i.recipient }
func (i Invoice) Body() string           { return i.body }

// Collaborator injected — not created internally
type InvoiceSender struct {
    mailer Mailer
}

func NewInvoiceSender(mailer Mailer) InvoiceSender {
    return InvoiceSender{mailer: mailer}
}

func (is InvoiceSender) Send(invoice Invoice) error {
    return is.mailer.Send(invoice.RecipientEmail(), invoice.Body())
}
```

---

## Explicit Interfaces (Implicit Satisfaction)

```go
// Interface is defined by the consumer, not the implementor
// Any struct with a Charge method satisfies PaymentGateway automatically

type PaymentGateway interface {
    Charge(customerID string, amount Money) error
}

type SubscriptionActivator struct {
    gateway PaymentGateway
}

func (sa SubscriptionActivator) Activate(customerID string, fee Money) error {
    return sa.gateway.Charge(customerID, fee)
}

// Stripe, Paypal — both satisfy the interface without importing it
type StripeGateway struct{}

func (g StripeGateway) Charge(customerID string, amount Money) error {
    // call Stripe API
    return nil
}
```

---

## Composition over Inheritance

Go has no inheritance. Behavior is shared through interfaces and embedding.

```go
type DiscountPolicy interface {
    Apply(total Money) Money
}

type TaxPolicy interface {
    Apply(total Money) Money
}

// CartPricing is composed from two collaborating policies
type CartPricing struct {
    discount DiscountPolicy
    tax      TaxPolicy
}

func (cp CartPricing) Total(subtotal Money) Money {
    return cp.tax.Apply(cp.discount.Apply(subtotal))
}

// Embedding — structural reuse without inheritance
type TimestampedEntity struct {
    CreatedAt time.Time
    UpdatedAt time.Time
}

type Order struct {
    TimestampedEntity        // embedded — Order gains CreatedAt/UpdatedAt fields
    ID                string
    lines             OrderLines
}
```

---

## Message-Based Design

```go
type SeatInventory interface {
    Reserve(seatCount int) error
}

type PaymentService interface {
    Charge(amount Money) error
}

type Booking struct {
    seats    int
    amount   Money
    inventory SeatInventory
    payments  PaymentService
}

func (b Booking) Confirm() error {
    if err := b.inventory.Reserve(b.seats); err != nil {
        return err
    }
    return b.payments.Charge(b.amount)
}
```

---

## Law of Demeter Violation and Fix

### Before

```go
// Caller navigates through internals — coupled to the chain
domestic := order.Customer().ShippingAddress().IsDomestic()
```

### After

```go
type Customer struct {
    address Address
}

// Customer answers questions about itself
func (c Customer) ShipsDomestically() bool {
    return c.address.IsDomestic()
}

type Order struct {
    customer Customer
}

// Order delegates to Customer — no chain traversal
func (o Order) ShipsDomestically() bool {
    return o.customer.ShipsDomestically()
}

domestic := order.ShipsDomestically()
```

---

## Immutable Objects (Value Semantics)

```go
// Struct is passed by value — each copy is independent
// Value receiver methods do not mutate the receiver

type Rooms struct {
    items []string
}

// Returns a new Rooms — original unchanged
func (r Rooms) Add(room string) Rooms {
    newItems := make([]string, len(r.items)+1)
    copy(newItems, r.items)
    newItems[len(r.items)] = room
    return Rooms{items: newItems}
}

func (r Rooms) Count() int {
    return len(r.items)
}
```

---

## Null Object

```go
// Go has no null objects but interfaces fill the same role — no-op implementation

type Logger interface {
    Info(message string)
}

// NullLogger satisfies Logger — does nothing
type NullLogger struct{}

func (NullLogger) Info(_ string) {}

// RealLogger — used in production
type RealLogger struct{}

func (RealLogger) Info(message string) {
    log.Println(message)
}

// Service accepts either — callers never check for nil
type OrderProcessor struct {
    logger Logger
}
```

---

## Anemic versus Rich Model

### Anemic

```go
type ScoreData struct {
    Value int
}

// Logic lives outside the data — external function mutates
func IncreaseScore(score *ScoreData, points int) {
    score.Value += points
}
```

### Rich

```go
type Score struct {
    points int
}

// Behavior lives on the type — returns a new value
func (s Score) Increase(extra int) Score {
    return Score{points: s.points + extra}
}

func (s Score) Value() int {
    return s.points
}
```

---

## SOLID — Single Responsibility

### Before

```go
type Report struct {
    title   string
    content string
}

// Report formats and persists — two unrelated responsibilities
func (r Report) Save(db *sql.DB) error {
    _, err := db.Exec("INSERT INTO reports (title, content) VALUES (?, ?)", r.title, r.content)
    return err
}
```

### After

```go
type Report struct {
    title   string
    content string
}

func (r Report) Title() string   { return r.title }
func (r Report) Content() string { return r.content }

type ReportRepository struct {
    db *sql.DB
}

func (rr ReportRepository) Save(r Report) error {
    _, err := rr.db.Exec("INSERT INTO reports (title, content) VALUES (?, ?)", r.Title(), r.Content())
    return err
}
```

---

## SOLID — Open/Closed

### Before

```go
func ShippingCost(orderType string) int {
    switch orderType {
    case "standard":  return 5
    case "express":   return 15
    case "overnight": return 25
    default:          return 0
    }
}
```

### After

```go
type ShippingPolicy interface {
    Cost() int
}

type StandardShipping  struct{}
type ExpressShipping   struct{}
type OvernightShipping struct{}

func (StandardShipping) Cost() int  { return 5 }
func (ExpressShipping) Cost() int   { return 15 }
func (OvernightShipping) Cost() int { return 25 }

// Adding a new type does not touch ShippingCalculator
func ShippingCost(policy ShippingPolicy) int {
    return policy.Cost()
}
```

---

## SOLID — Interface Segregation

```go
// Prefer many small interfaces over one large one
// Callers depend only on what they use

type Worker interface {
    Work()
}

type Eater interface {
    Eat()
}

type Sleeper interface {
    Sleep()
}

type HumanWorker struct{}

func (HumanWorker) Work()  {}
func (HumanWorker) Eat()   {}
func (HumanWorker) Sleep() {}

type Robot struct{}

// Robot only needs to satisfy Worker — not forced to implement Eat/Sleep
func (Robot) Work() {}
```

---

## SOLID — Dependency Inversion

### Before

```go
type OrderProcessor struct {
    db *postgres.DB  // depends on concrete infrastructure
}

func (op *OrderProcessor) Process(order Order) error {
    return op.db.Save(order)
}
```

### After

```go
// Interface owned by the domain — not by infrastructure
type OrderStore interface {
    Save(order Order) error
}

type OrderProcessor struct {
    store OrderStore  // depends on abstraction
}

func NewOrderProcessor(store OrderStore) OrderProcessor {
    return OrderProcessor{store: store}
}

func (op OrderProcessor) Process(order Order) error {
    return op.store.Save(order)
}

// Infrastructure adapts to the domain interface
type PostgresOrderStore struct{ db *sql.DB }

func (s PostgresOrderStore) Save(order Order) error {
    _, err := s.db.Exec("INSERT INTO orders ...", order.ID)
    return err
}
```

---

## Object Calisthenics — Wrap Primitive

### Before

```go
func ApplyDiscount(priceInCents int, discountPercent int) int {
    if discountPercent < 0 || discountPercent > 100 {
        panic("invalid discount")
    }
    return priceInCents - (priceInCents * discountPercent / 100)
}
```

### After

```go
type Percentage struct {
    value int
}

func NewPercentage(v int) (Percentage, error) {
    if v < 0 || v > 100 {
        return Percentage{}, fmt.Errorf("percentage must be between 0 and 100, got %d", v)
    }
    return Percentage{value: v}, nil
}

func (p Percentage) Of(amount int) int {
    return amount * p.value / 100
}

type Price struct {
    cents int
}

func (pr Price) ApplyDiscount(discount Percentage) Price {
    return Price{cents: pr.cents - discount.Of(pr.cents)}
}
```

---

## Object Calisthenics — No Else Rule

### Before

```go
func ShippingCost(order Order) int {
    if order.IsExpress() {
        return 15
    } else {
        if order.TotalWeight() > 10 {
            return 8
        } else {
            return 3
        }
    }
}
```

### After

```go
func ShippingCost(order Order) int {
    if order.IsExpress()        { return 15 }
    if order.TotalWeight() > 10 { return 8 }
    return 3
}
```

---

## Object Calisthenics — No Getters

### Before

```go
type Rectangle struct {
    Width  int
    Height int
}

area      := rect.Width * rect.Height
perimeter := 2 * (rect.Width + rect.Height)
```

### After

```go
type Rectangle struct {
    width  int
    height int
}

func NewRectangle(width, height int) Rectangle {
    return Rectangle{width: width, height: height}
}

func (r Rectangle) Area() int      { return r.width * r.height }
func (r Rectangle) Perimeter() int { return 2 * (r.width + r.height) }
func (r Rectangle) IsSquare() bool { return r.width == r.height }
```

---

## Object Calisthenics — Don't Abbreviate

### Before

```go
type OrdMgr struct{}

func (m OrdMgr) Calc(o Order) int {
    s := 0
    for _, i := range o.Itms() {
        s += i.Prc()
    }
    return s
}
```

### After

```go
type OrderManager struct{}

func (m OrderManager) CalculateTotal(order Order) int {
    total := 0
    for _, item := range order.Items() {
        total += item.Price()
    }
    return total
}
```

---

## Composed Method

### Before

```go
func (s RegistrationService) Register(email, password string) error {
    if !strings.Contains(email, "@") { return errors.New("invalid email") }
    if len(password) < 8            { return errors.New("password too short") }
    hashed := hashPassword(password)
    if err := s.repo.Save(NewUser(email, hashed)); err != nil { return err }
    return s.mailer.Send(email, "Welcome!")
}
```

### After

```go
func (s RegistrationService) Register(email, password string) error {
    if err := s.validate(email, password); err != nil { return err }
    user, err := s.buildUser(email, password)
    if err != nil { return err }
    if err := s.persist(user); err != nil { return err }
    return s.welcome(user)
}

func (s RegistrationService) validate(email, password string) error {
    if !strings.Contains(email, "@") { return errors.New("invalid email") }
    if len(password) < 8            { return errors.New("password too short") }
    return nil
}

func (s RegistrationService) buildUser(email, password string) (User, error) {
    return NewUser(email, hashPassword(password))
}

func (s RegistrationService) persist(user User) error {
    return s.repo.Save(user)
}

func (s RegistrationService) welcome(user User) error {
    return s.mailer.Send(user.Email(), "Welcome!")
}
```

---

## Explaining Message

### Before

```go
func (s Subscription) IsExpired() bool {
    return time.Now().After(s.startDate.Add(time.Duration(s.durationDays) * 24 * time.Hour))
}
```

### After

```go
func (s Subscription) IsExpired() bool {
    return time.Now().After(s.expirationDate())
}

func (s Subscription) expirationDate() time.Time {
    return s.startDate.Add(time.Duration(s.durationDays) * 24 * time.Hour)
}
```

---

## What to Notice

- Go has no classes — structs with unexported fields and methods replace them.
- Interfaces are satisfied implicitly: any struct with the right methods qualifies. Callers define the interface; implementors do not import it.
- There is no inheritance. Variation is expressed through interfaces (OCP) and embedding (reuse). Delegation is explicit.
- Value receivers return new values — the natural way to model immutability.
- LSP applies at the interface level: any implementation must honor the contract, not just the method signature.
- The same design pressures (cohesion, coupling, naming, encapsulation) appear in Go exactly as they do in class-based languages.
