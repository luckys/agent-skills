# Rust — Design Pattern Examples

Rust has no classes or inheritance. Patterns use structs + traits + enums. Enums with `match` are the natural home for State and Visitor. Traits are the interface mechanism.

---

## Strategy

```rust
pub trait PricingPolicy {
    fn apply(&self, subtotal_cents: i64) -> i64;
}

pub struct StandardPricing;
pub struct PremiumPricing;
pub struct PartnerPricing;

impl PricingPolicy for StandardPricing { fn apply(&self, s: i64) -> i64 { s } }
impl PricingPolicy for PremiumPricing  { fn apply(&self, s: i64) -> i64 { s * 8 / 10 } }
impl PricingPolicy for PartnerPricing  { fn apply(&self, s: i64) -> i64 { s * 85 / 100 } }

pub struct Cart<P: PricingPolicy> { policy: P }

impl<P: PricingPolicy> Cart<P> {
    pub fn total(&self, subtotal: i64) -> i64 {
        self.policy.apply(subtotal)
    }
}

// With trait objects (dynamic dispatch)
pub struct DynCart { policy: Box<dyn PricingPolicy> }

impl DynCart {
    pub fn total(&self, subtotal: i64) -> i64 {
        self.policy.apply(subtotal)
    }
}
```

---

## State (enum — idiomatic Rust)

```rust
// State as enum — exhaustive match prevents missing transitions
#[derive(Debug)]
pub enum OrderStatus {
    Pending,
    Shipped { tracking_code: String },
    Delivered { delivered_at: chrono::DateTime<chrono::Utc> },
    Cancelled { reason: String },
}

pub struct Order {
    id: String,
    status: OrderStatus,
}

impl Order {
    pub fn ship(&mut self, tracking_code: String) -> Result<(), &'static str> {
        match &self.status {
            OrderStatus::Pending => {
                self.status = OrderStatus::Shipped { tracking_code };
                Ok(())
            }
            _ => Err("can only ship pending orders"),
        }
    }

    pub fn cancel(&mut self, reason: String) -> Result<(), &'static str> {
        match &self.status {
            OrderStatus::Pending => {
                self.status = OrderStatus::Cancelled { reason };
                Ok(())
            }
            OrderStatus::Shipped { .. } => Err("cannot cancel shipped order"),
            _ => Err("order already resolved"),
        }
    }
}
```

---

## Observer

```rust
pub trait EventHandler<E> {
    fn handle(&self, event: &E);
}

pub struct EventPublisher<E> {
    handlers: Vec<Box<dyn EventHandler<E>>>,
}

impl<E> EventPublisher<E> {
    pub fn subscribe(&mut self, handler: Box<dyn EventHandler<E>>) {
        self.handlers.push(handler);
    }

    pub fn publish(&self, event: &E) {
        for handler in &self.handlers {
            handler.handle(event);
        }
    }
}

// Closure-based (simpler for most cases)
pub struct ClosurePublisher<E> {
    handlers: Vec<Box<dyn Fn(&E)>>,
}

impl<E> ClosurePublisher<E> {
    pub fn subscribe(&mut self, f: impl Fn(&E) + 'static) {
        self.handlers.push(Box::new(f));
    }

    pub fn publish(&self, event: &E) {
        for h in &self.handlers { h(event); }
    }
}
```

---

## Command

```rust
// Command as closure (simple case)
type Command = Box<dyn FnOnce() -> Result<(), Box<dyn std::error::Error>>>;

pub struct CommandBus { queue: Vec<Command> }

impl CommandBus {
    pub fn dispatch(&mut self, cmd: Command) { self.queue.push(cmd); }

    pub fn run(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        for cmd in self.queue.drain(..) { cmd()?; }
        Ok(())
    }
}

// Command as trait (when undo is needed)
pub trait UndoableCommand {
    fn execute(&mut self) -> Result<(), String>;
    fn undo(&mut self) -> Result<(), String>;
}
```

---

## Factory Method

```rust
pub trait Notification {
    fn send(&self, to: &str, body: &str) -> Result<(), String>;
}

pub struct EmailNotification { smtp_host: String }
pub struct SmsNotification   { api_key: String }

impl Notification for EmailNotification {
    fn send(&self, to: &str, body: &str) -> Result<(), String> { Ok(()) }
}
impl Notification for SmsNotification {
    fn send(&self, to: &str, body: &str) -> Result<(), String> { Ok(()) }
}

pub fn create_notification(channel: &str, cfg: &Config) -> Result<Box<dyn Notification>, String> {
    match channel {
        "email" => Ok(Box::new(EmailNotification { smtp_host: cfg.smtp_host.clone() })),
        "sms"   => Ok(Box::new(SmsNotification   { api_key: cfg.sms_key.clone() })),
        other   => Err(format!("unknown channel: {}", other)),
    }
}
```

---

## Builder

```rust
// Builder pattern — fluent method chaining
#[derive(Debug)]
pub struct ServerConfig {
    host:    String,
    port:    u16,
    timeout: u64,
    tls:     bool,
}

pub struct ServerConfigBuilder {
    host:    String,
    port:    u16,
    timeout: u64,
    tls:     bool,
}

impl ServerConfigBuilder {
    pub fn new() -> Self {
        Self { host: "localhost".into(), port: 8080, timeout: 30, tls: false }
    }

    pub fn host(mut self, h: impl Into<String>) -> Self { self.host = h.into(); self }
    pub fn port(mut self, p: u16) -> Self               { self.port = p; self }
    pub fn timeout(mut self, t: u64) -> Self            { self.timeout = t; self }
    pub fn tls(mut self) -> Self                        { self.tls = true; self }

    pub fn build(self) -> ServerConfig {
        ServerConfig { host: self.host, port: self.port, timeout: self.timeout, tls: self.tls }
    }
}

// Usage
let config = ServerConfigBuilder::new()
    .host("0.0.0.0")
    .port(9000)
    .tls()
    .build();
```

---

## Decorator

```rust
pub trait Logger { fn log(&self, msg: &str); }

pub struct ConsoleLogger;
impl Logger for ConsoleLogger { fn log(&self, msg: &str) { println!("{}", msg); } }

// Decorator: wraps inner logger, same trait
pub struct TimestampLogger<L: Logger> { inner: L }

impl<L: Logger> Logger for TimestampLogger<L> {
    fn log(&self, msg: &str) {
        let ts = chrono::Utc::now().to_rfc3339();
        self.inner.log(&format!("[{}] {}", ts, msg));
    }
}

pub struct PrefixLogger<L: Logger> { inner: L, prefix: String }

impl<L: Logger> Logger for PrefixLogger<L> {
    fn log(&self, msg: &str) {
        self.inner.log(&format!("{}: {}", self.prefix, msg));
    }
}

// Stack decorators
let logger = TimestampLogger {
    inner: PrefixLogger { inner: ConsoleLogger, prefix: "APP".into() }
};
```

---

## Adapter

```rust
// Domain interface
pub trait PaymentGateway {
    fn charge(&self, customer_id: &str, cents: i64) -> Result<(), String>;
}

// External SDK we don't control
pub struct StripeClient;
impl StripeClient {
    pub fn create_charge(&self, params: StripeParams) -> Result<StripeCharge, StripeError> {
        todo!()
    }
}

// Adapter: implements domain interface, delegates to Stripe
pub struct StripeAdapter { client: StripeClient }

impl PaymentGateway for StripeAdapter {
    fn charge(&self, customer_id: &str, cents: i64) -> Result<(), String> {
        self.client.create_charge(StripeParams {
            customer: customer_id.to_string(),
            amount: cents,
            currency: "eur".into(),
        })
        .map(|_| ())
        .map_err(|e| e.to_string())
    }
}
```

---

## Composite

```rust
pub trait FileSystemNode {
    fn name(&self) -> &str;
    fn size(&self) -> u64;
}

pub struct File { name: String, size: u64 }
impl FileSystemNode for File {
    fn name(&self) -> &str { &self.name }
    fn size(&self) -> u64  { self.size }
}

pub struct Directory { name: String, children: Vec<Box<dyn FileSystemNode>> }
impl FileSystemNode for Directory {
    fn name(&self) -> &str { &self.name }
    fn size(&self) -> u64  { self.children.iter().map(|c| c.size()).sum() }
}

impl Directory {
    pub fn add(&mut self, node: Box<dyn FileSystemNode>) {
        self.children.push(node);
    }
}
```

---

## Proxy

```rust
pub trait UserRepository {
    fn find_by_id(&self, id: &str) -> Option<User>;
}

pub struct DatabaseUserRepository { /* db connection */ }
impl UserRepository for DatabaseUserRepository {
    fn find_by_id(&self, id: &str) -> Option<User> { todo!() }
}

// Caching proxy — same interface
use std::collections::HashMap;

pub struct CachedUserRepository<R: UserRepository> {
    inner: R,
    cache: HashMap<String, User>,
}

impl<R: UserRepository> UserRepository for CachedUserRepository<R> {
    fn find_by_id(&self, id: &str) -> Option<User> {
        if let Some(u) = self.cache.get(id) {
            return Some(u.clone());
        }
        self.inner.find_by_id(id)
    }
}
```

---

## Visitor (enum + match — idiomatic Rust)

```rust
// Rust's enum + match IS the visitor pattern — no double dispatch needed

#[derive(Debug)]
pub enum Expr {
    Number(f64),
    Add(Box<Expr>, Box<Expr>),
    Multiply(Box<Expr>, Box<Expr>),
    Negate(Box<Expr>),
}

// Different "visitors" are just functions pattern-matching on the enum
fn evaluate(expr: &Expr) -> f64 {
    match expr {
        Expr::Number(n)      => *n,
        Expr::Add(l, r)      => evaluate(l) + evaluate(r),
        Expr::Multiply(l, r) => evaluate(l) * evaluate(r),
        Expr::Negate(e)      => -evaluate(e),
    }
}

fn to_string(expr: &Expr) -> String {
    match expr {
        Expr::Number(n)      => n.to_string(),
        Expr::Add(l, r)      => format!("({} + {})", to_string(l), to_string(r)),
        Expr::Multiply(l, r) => format!("({} * {})", to_string(l), to_string(r)),
        Expr::Negate(e)      => format!("(-{})", to_string(e)),
    }
}
```

---

## Result Pattern — `Result<T, E>`

```rust
#[derive(Debug, thiserror::Error)]
pub enum ParseError {
    #[error("not a number: {0}")]
    NotANumber(String),
    #[error("age out of range: {0}")]
    OutOfRange(i32),
}

pub fn parse_age(s: &str) -> Result<i32, ParseError> {
    let n: i32 = s.parse().map_err(|_| ParseError::NotANumber(s.to_string()))?;
    if !(0..=150).contains(&n) { return Err(ParseError::OutOfRange(n)); }
    Ok(n)
}

// ? operator chains Results
pub fn process_user(email: &str, age_str: &str) -> Result<User, ParseError> {
    let email = parse_email(email)?;
    let age   = parse_age(age_str)?;
    Ok(User { email, age })
}
```

---

## Command + CommandHandler (CQRS)

```rust
// Immutable command value object
#[derive(Debug)]
pub struct RegisterUserCommand {
    pub email: String,
    pub name: String,
}

// Typed handler as a struct with dependencies
pub struct RegisterUserHandler {
    repo: Box<dyn UserRepository>,
    bus:  Box<dyn EventBus>,
}

impl RegisterUserHandler {
    pub fn handle(&self, cmd: RegisterUserCommand) -> Result<(), String> {
        let user = User::new(&cmd.email, &cmd.name)?;
        self.repo.save(&user)?;
        self.bus.publish(user.events())
    }
}
```

---

## Entity and Aggregate Root

```rust
use uuid::Uuid;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct UserId(Uuid);

impl UserId {
    pub fn new() -> Self { Self(Uuid::new_v4()) }
}

pub struct User {
    id: UserId,
    email: String,
    events: Vec<DomainEvent>,
}

impl User {
    pub fn new(email: &str) -> Result<Self, &'static str> {
        if !email.contains('@') { return Err("invalid email"); }
        let id = UserId::new();
        let mut user = Self { id: id.clone(), email: email.to_string(), events: vec![] };
        user.record(DomainEvent::UserRegistered { user_id: id, email: email.to_string() });
        Ok(user)
    }

    pub fn id(&self) -> &UserId           { &self.id }
    pub fn email(&self) -> &str           { &self.email }
    pub fn pull_events(&mut self) -> Vec<DomainEvent> {
        std::mem::take(&mut self.events)
    }

    fn record(&mut self, event: DomainEvent) { self.events.push(event); }
}
```

---

## Value Object (Money)

```rust
#[derive(Debug, Clone, PartialEq)]
pub struct Money {
    amount: i64,
    currency: String,
}

impl Money {
    pub fn new(amount: i64, currency: impl Into<String>) -> Result<Self, &'static str> {
        if amount < 0 { return Err("amount must be non-negative"); }
        Ok(Self { amount, currency: currency.into() })
    }

    pub fn add(&self, other: &Money) -> Result<Money, &'static str> {
        if self.currency != other.currency { return Err("currency mismatch"); }
        Ok(Money { amount: self.amount + other.amount, currency: self.currency.clone() })
    }
}
```

---

## Specification

```rust
pub trait Specification<T> {
    fn is_satisfied_by(&self, value: &T) -> bool;
}

pub struct AndSpec<T> { left: Box<dyn Specification<T>>, right: Box<dyn Specification<T>> }
pub struct OrSpec<T>  { left: Box<dyn Specification<T>>, right: Box<dyn Specification<T>> }
pub struct NotSpec<T> { inner: Box<dyn Specification<T>> }

impl<T> Specification<T> for AndSpec<T> {
    fn is_satisfied_by(&self, v: &T) -> bool {
        self.left.is_satisfied_by(v) && self.right.is_satisfied_by(v)
    }
}

pub struct ActiveUserSpec;
impl Specification<User> for ActiveUserSpec {
    fn is_satisfied_by(&self, u: &User) -> bool { u.active }
}
```
