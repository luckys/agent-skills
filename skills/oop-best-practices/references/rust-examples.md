# Rust Examples

Rust has no classes or inheritance. OOP concepts are expressed through structs + `impl` blocks, traits, and composition. Ownership makes immutability and encapsulation the natural defaults rather than discipline to enforce.

## Concepts Covered

- Value Objects and Invariants
- First-Class Collections
- Tell, Don't Ask
- Role-Based Collaboration
- Dependency Injection
- Explicit Interfaces (traits)
- Composition over Inheritance
- Message-Based Design
- Law of Demeter Violation and Fix
- Immutable Objects (ownership and `let`)
- Absence without null (Option<T>)
- Anemic versus Rich Model
- SOLID — Single Responsibility
- SOLID — Open/Closed
- SOLID — Interface Segregation
- SOLID — Dependency Inversion
- Object Calisthenics — Wrap Primitive (Newtype)
- Object Calisthenics — No Else Rule
- Object Calisthenics — No Getters
- Object Calisthenics — Don't Abbreviate
- Composed Method
- Explaining Message

---

## Value Objects and Invariants

```rust
// Newtype pattern — a wrapper that enforces invariants
// Private field: external code cannot construct Money directly
pub struct Money {
    cents: i64,
}

impl Money {
    pub fn new(cents: i64) -> Result<Self, &'static str> {
        if cents < 0 {
            return Err("money cannot be negative");
        }
        Ok(Self { cents })
    }

    pub fn add(&self, other: &Money) -> Money {
        Money { cents: self.cents + other.cents }
    }

    pub fn multiply_by_percent(&self, percent: u8) -> Money {
        Money { cents: self.cents * percent as i64 / 100 }
    }

    pub fn cents(&self) -> i64 {
        self.cents
    }
}
```

---

## First-Class Collections

```rust
pub struct OrderLine {
    subtotal: Money,
}

impl OrderLine {
    pub fn subtotal(&self) -> &Money {
        &self.subtotal
    }
}

// The collection owns its invariants
pub struct OrderLines {
    items: Vec<OrderLine>,
}

impl OrderLines {
    pub fn total(&self) -> Money {
        self.items
            .iter()
            .fold(Money::new(0).unwrap(), |acc, item| acc.add(item.subtotal()))
    }

    pub fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
}
```

---

## Tell, Don't Ask

```rust
pub struct Address {
    country_code: String,
}

impl Address {
    // Tell the address — don't ask for the string and decide outside
    pub fn is_domestic(&self) -> bool {
        self.country_code == "ES"
    }
}

pub struct Shipment {
    address: Address,
}

impl Shipment {
    pub fn dispatch_window_in_days(&self) -> u32 {
        if self.address.is_domestic() { 2 } else { 5 }
    }
}
```

---

## Role-Based Collaboration

```rust
// Trait = role — defines what behavior a collaborator must provide
pub trait CurrencyFormatter {
    fn format(&self, amount: &Money) -> String;
}

pub struct OrderSummary<F: CurrencyFormatter> {
    formatter: F,
}

impl<F: CurrencyFormatter> OrderSummary<F> {
    pub fn total_label(&self, lines: &OrderLines) -> String {
        self.formatter.format(&lines.total())
    }
}
```

---

## Dependency Injection

```rust
pub trait Mailer {
    fn send(&self, to: &str, body: &str) -> Result<(), Box<dyn std::error::Error>>;
}

pub struct Invoice {
    recipient: String,
    body: String,
}

impl Invoice {
    pub fn recipient_email(&self) -> &str { &self.recipient }
    pub fn body(&self) -> &str           { &self.body }
}

// Collaborator injected — not created inside the struct
pub struct InvoiceSender<M: Mailer> {
    mailer: M,
}

impl<M: Mailer> InvoiceSender<M> {
    pub fn new(mailer: M) -> Self {
        Self { mailer }
    }

    pub fn send(&self, invoice: &Invoice) -> Result<(), Box<dyn std::error::Error>> {
        self.mailer.send(invoice.recipient_email(), invoice.body())
    }
}
```

---

## Explicit Interfaces (Traits)

```rust
pub trait PaymentGateway {
    fn charge(&self, customer_id: &str, amount: &Money) -> Result<(), String>;
}

pub struct SubscriptionActivator<G: PaymentGateway> {
    gateway: G,
}

impl<G: PaymentGateway> SubscriptionActivator<G> {
    pub fn activate(&self, customer_id: &str, fee: &Money) -> Result<(), String> {
        self.gateway.charge(customer_id, fee)
    }
}

// StripeGateway satisfies PaymentGateway by implementing the trait
pub struct StripeGateway;

impl PaymentGateway for StripeGateway {
    fn charge(&self, _customer_id: &str, _amount: &Money) -> Result<(), String> {
        Ok(()) // call Stripe API
    }
}
```

---

## Composition over Inheritance

Rust has no inheritance. Behavior is shared through traits and delegation.

```rust
pub trait DiscountPolicy {
    fn apply(&self, total: &Money) -> Money;
}

pub trait TaxPolicy {
    fn apply(&self, total: &Money) -> Money;
}

pub struct CartPricing<D: DiscountPolicy, T: TaxPolicy> {
    discount: D,
    tax: T,
}

impl<D: DiscountPolicy, T: TaxPolicy> CartPricing<D, T> {
    pub fn total(&self, subtotal: &Money) -> Money {
        let discounted = self.discount.apply(subtotal);
        self.tax.apply(&discounted)
    }
}
```

---

## Message-Based Design

```rust
pub trait SeatInventory {
    fn reserve(&mut self, seat_count: u32) -> Result<(), String>;
}

pub trait PaymentService {
    fn charge(&self, amount: &Money) -> Result<(), String>;
}

pub struct Booking<I: SeatInventory, P: PaymentService> {
    seats: u32,
    amount: Money,
    inventory: I,
    payments: P,
}

impl<I: SeatInventory, P: PaymentService> Booking<I, P> {
    pub fn confirm(&mut self) -> Result<(), String> {
        self.inventory.reserve(self.seats)?;
        self.payments.charge(&self.amount)
    }
}
```

---

## Law of Demeter Violation and Fix

### Before

```rust
// Caller traverses the chain — coupled to intermediate structure
let domestic = order.customer().shipping_address().is_domestic();
```

### After

```rust
pub struct Customer {
    address: Address,
}

impl Customer {
    // Customer answers questions about itself
    pub fn ships_domestically(&self) -> bool {
        self.address.is_domestic()
    }
}

pub struct Order {
    customer: Customer,
}

impl Order {
    // Order delegates — no chain traversal at the call site
    pub fn ships_domestically(&self) -> bool {
        self.customer.ships_domestically()
    }
}

let domestic = order.ships_domestically();
```

---

## Immutable Objects (Ownership and `let`)

```rust
// let is immutable by default — mutation requires `mut`
pub struct Rooms {
    items: Vec<String>,
}

impl Rooms {
    // Returns a new Rooms — original unchanged
    pub fn add(&self, room: &str) -> Rooms {
        let mut new_items = self.items.clone();
        new_items.push(room.to_string());
        Rooms { items: new_items }
    }

    pub fn count(&self) -> usize {
        self.items.len()
    }
}
```

---

## Absence without Null (Option<T>)

```rust
// Rust has no null — Option<T> = Some(T) | None
// The compiler forces callers to handle the missing case

pub struct UserRepository {
    users: std::collections::HashMap<String, User>,
}

impl UserRepository {
    pub fn find(&self, id: &str) -> Option<&User> {
        self.users.get(id)
    }
}

// Null Object equivalent — default implementation via Option methods
let name = repo.find("123")
    .map(|u| u.name())
    .unwrap_or("Anonymous");

// Or pattern match explicitly
match repo.find("123") {
    Some(user) => println!("Found: {}", user.name()),
    None       => println!("Not found"),
}
```

---

## Anemic versus Rich Model

### Anemic

```rust
pub struct ScoreData {
    pub value: i32, // public mutable field — no protection
}

// Logic lives outside
fn increase_score(score: &mut ScoreData, points: i32) {
    score.value += points;
}
```

### Rich

```rust
pub struct Score {
    points: i32, // private — callers cannot bypass the rule
}

impl Score {
    pub fn new(points: i32) -> Self {
        Self { points }
    }

    // Returns a new Score — immutable increment
    pub fn increase(&self, extra: i32) -> Score {
        Score { points: self.points + extra }
    }

    pub fn value(&self) -> i32 {
        self.points
    }
}
```

---

## SOLID — Single Responsibility

### Before

```rust
// Report formats and persists — two unrelated responsibilities
impl Report {
    pub fn save(&self, conn: &mut PgConnection) -> QueryResult<usize> {
        diesel::insert_into(reports::table)
            .values((reports::title.eq(&self.title), reports::content.eq(&self.content)))
            .execute(conn)
    }
}
```

### After

```rust
pub struct Report {
    title: String,
    content: String,
}

impl Report {
    pub fn title(&self) -> &str   { &self.title }
    pub fn content(&self) -> &str { &self.content }
}

pub struct ReportRepository {
    conn: PgConnection,
}

impl ReportRepository {
    pub fn save(&mut self, report: &Report) -> QueryResult<usize> {
        diesel::insert_into(reports::table)
            .values((reports::title.eq(report.title()), reports::content.eq(report.content())))
            .execute(&mut self.conn)
    }
}
```

---

## SOLID — Open/Closed

### Before

```rust
fn shipping_cost(order_type: &str) -> u32 {
    match order_type {
        "standard"  => 5,
        "express"   => 15,
        "overnight" => 25,
        _           => 0,
    }
}
```

### After

```rust
pub trait ShippingPolicy {
    fn cost(&self) -> u32;
}

pub struct StandardShipping;
pub struct ExpressShipping;
pub struct OvernightShipping;

impl ShippingPolicy for StandardShipping  { fn cost(&self) -> u32 { 5 } }
impl ShippingPolicy for ExpressShipping   { fn cost(&self) -> u32 { 15 } }
impl ShippingPolicy for OvernightShipping { fn cost(&self) -> u32 { 25 } }

// Adding a new variant does not touch this function
fn shipping_cost(policy: &dyn ShippingPolicy) -> u32 {
    policy.cost()
}
```

---

## SOLID — Interface Segregation

```rust
pub trait Workable { fn work(&self); }
pub trait Eatable  { fn eat(&self); }
pub trait Sleepable{ fn sleep(&self); }

pub struct HumanWorker;

impl Workable  for HumanWorker { fn work(&self)  {} }
impl Eatable   for HumanWorker { fn eat(&self)   {} }
impl Sleepable for HumanWorker { fn sleep(&self) {} }

pub struct Robot;

// Robot only implements what it needs — compiler enforces it
impl Workable for Robot { fn work(&self) {} }
```

---

## SOLID — Dependency Inversion

### Before

```rust
use postgres::Client;

pub struct OrderProcessor {
    db: Client, // depends on concrete infrastructure
}

impl OrderProcessor {
    pub fn process(&mut self, order: &Order) -> Result<(), postgres::Error> {
        self.db.execute("INSERT INTO orders ...", &[&order.id])
            .map(|_| ())
    }
}
```

### After

```rust
// Interface owned by the domain
pub trait OrderStore {
    fn save(&mut self, order: &Order) -> Result<(), Box<dyn std::error::Error>>;
}

pub struct OrderProcessor<S: OrderStore> {
    store: S, // depends on abstraction
}

impl<S: OrderStore> OrderProcessor<S> {
    pub fn new(store: S) -> Self { Self { store } }

    pub fn process(&mut self, order: &Order) -> Result<(), Box<dyn std::error::Error>> {
        self.store.save(order)
    }
}

pub struct PostgresOrderStore { /* db connection */ }

impl OrderStore for PostgresOrderStore {
    fn save(&mut self, order: &Order) -> Result<(), Box<dyn std::error::Error>> {
        // persist to Postgres
        Ok(())
    }
}
```

---

## Object Calisthenics — Wrap Primitive (Newtype)

### Before

```rust
fn apply_discount(price_in_cents: i64, discount_percent: u8) -> i64 {
    assert!(discount_percent <= 100, "invalid discount");
    price_in_cents - (price_in_cents * discount_percent as i64 / 100)
}
```

### After

```rust
pub struct Percentage(u8);

impl Percentage {
    pub fn new(value: u8) -> Result<Self, &'static str> {
        if value > 100 {
            return Err("percentage must be between 0 and 100");
        }
        Ok(Self(value))
    }

    pub fn of(&self, amount: i64) -> i64 {
        amount * self.0 as i64 / 100
    }
}

pub struct Price(i64);

impl Price {
    pub fn apply_discount(&self, discount: &Percentage) -> Price {
        Price(self.0 - discount.of(self.0))
    }

    pub fn value(&self) -> i64 { self.0 }
}
```

---

## Object Calisthenics — No Else Rule

### Before

```rust
fn shipping_cost(order: &Order) -> u32 {
    if order.is_express() {
        return 15;
    } else {
        if order.total_weight() > 10 {
            return 8;
        } else {
            return 3;
        }
    }
}
```

### After

```rust
fn shipping_cost(order: &Order) -> u32 {
    if order.is_express()        { return 15; }
    if order.total_weight() > 10 { return 8; }
    3
}
```

---

## Object Calisthenics — No Getters

### Before

```rust
pub struct Rectangle {
    pub width: u32,
    pub height: u32,
}

let area      = rect.width * rect.height;
let perimeter = 2 * (rect.width + rect.height);
```

### After

```rust
pub struct Rectangle {
    width: u32,
    height: u32,
}

impl Rectangle {
    pub fn new(width: u32, height: u32) -> Self { Self { width, height } }

    pub fn area(&self) -> u32      { self.width * self.height }
    pub fn perimeter(&self) -> u32 { 2 * (self.width + self.height) }
    pub fn is_square(&self) -> bool{ self.width == self.height }
}
```

---

## Object Calisthenics — Don't Abbreviate

### Before

```rust
struct OrdMgr;

impl OrdMgr {
    fn calc(&self, o: &Order) -> i64 {
        o.itms().iter().map(|i| i.prc()).sum()
    }
}
```

### After

```rust
struct OrderManager;

impl OrderManager {
    fn calculate_total(&self, order: &Order) -> i64 {
        order.items().iter().map(|item| item.price()).sum()
    }
}
```

---

## Composed Method

### Before

```rust
impl RegistrationService {
    pub fn register(&self, email: &str, password: &str) -> Result<(), String> {
        if !email.contains('@') { return Err("invalid email".into()); }
        if password.len() < 8  { return Err("password too short".into()); }
        let hashed = hash_password(password);
        self.repo.save(&User::new(email, &hashed))?;
        self.mailer.send(email, "Welcome!").map_err(|e| e.to_string())
    }
}
```

### After

```rust
impl RegistrationService {
    pub fn register(&self, email: &str, password: &str) -> Result<(), String> {
        self.validate(email, password)?;
        let user = self.build_user(email, password);
        self.persist(&user)?;
        self.welcome(&user)
    }

    fn validate(&self, email: &str, password: &str) -> Result<(), String> {
        if !email.contains('@') { return Err("invalid email".into()); }
        if password.len() < 8  { return Err("password too short".into()); }
        Ok(())
    }

    fn build_user(&self, email: &str, password: &str) -> User {
        User::new(email, &hash_password(password))
    }

    fn persist(&self, user: &User) -> Result<(), String> {
        self.repo.save(user)
    }

    fn welcome(&self, user: &User) -> Result<(), String> {
        self.mailer.send(user.email(), "Welcome!").map_err(|e| e.to_string())
    }
}
```

---

## Explaining Message

### Before

```rust
impl Subscription {
    pub fn is_expired(&self) -> bool {
        std::time::SystemTime::now()
            > self.start_date + std::time::Duration::from_secs(self.duration_days * 86400)
    }
}
```

### After

```rust
impl Subscription {
    pub fn is_expired(&self) -> bool {
        std::time::SystemTime::now() > self.expiration_date()
    }

    fn expiration_date(&self) -> std::time::SystemTime {
        self.start_date + std::time::Duration::from_secs(self.duration_days * 86400)
    }
}
```

---

## What to Notice

- Rust has no classes — structs with private fields and `impl` blocks replace them. The constructor (`new`) is the single entry point that enforces invariants.
- Traits are the interface mechanism. They are explicit, named, and implemented intentionally — no accidental satisfaction.
- Ownership enforces immutability by default: `let` bindings cannot be reassigned; methods taking `&self` cannot mutate.
- There is no null. `Option<T>` forces callers to handle absence at compile time — the Null Object pattern becomes `Option::unwrap_or_default()` or `Option::map`.
- There is no inheritance. Reuse is achieved through traits (shared behavior) and composition (explicit delegation). LSP applies at the trait level.
- The newtype pattern (`struct Percentage(u8)`) is the idiomatic way to wrap primitives and enforce domain invariants with zero runtime cost.
