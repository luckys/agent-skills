# Rust — Functional Programming Examples

Concepts covered: pure functions, iterators (map/filter/fold/flat_map), closures, `Option<T>`, `Result<T, E>`, pattern matching, algebraic data types (enums), immutability by default, `?` operator, function composition.

Rust's ownership system makes pure functions the natural default — mutation is explicit and visible. The iterator trait provides a rich functional pipeline API.

---

## Pure Functions and Immutability by Default

```rust
// let bindings are immutable by default — mutation requires `mut`
let x = 5;          // immutable
let mut y = 5;      // explicit mutation

// Pure function — no hidden state, no side effects
fn apply_discount(rate: f64, price: f64) -> f64 {
    price * (1.0 - rate)
}

// Structs implement value semantics with ownership
#[derive(Debug, Clone)]
struct Cart {
    items: Vec<Item>,
}

// Returns a new Cart — original is moved or cloned, never mutated
fn add_item(mut cart: Cart, item: Item) -> Cart {
    cart.items.push(item);
    cart  // returns the modified owned value
}

// If you need to keep the original, clone first
fn add_item_pure(cart: &Cart, item: Item) -> Cart {
    let mut new_items = cart.items.clone();
    new_items.push(item);
    Cart { items: new_items }
}
```

---

## Closures and First-Class Functions

```rust
// Closures are anonymous functions that capture their environment
let double = |x: i32| x * 2;
let add_n  = |n: i32| move |x: i32| x + n;  // move captures n by value

let add5 = add_n(5);
add5(10)  // 15

// Function pointers for zero-cost abstractions
fn apply(f: fn(i32) -> i32, x: i32) -> i32 {
    f(x)
}

// Generic higher-order function
fn apply_twice<F: Fn(i32) -> i32>(f: F, x: i32) -> i32 {
    f(f(x))
}

apply_twice(|x| x + 3, 10)  // 16
apply_twice(double, 5)       // 20
```

---

## Iterator — Functional Pipelines

```rust
// The Iterator trait is Rust's primary FP tool
// Iterators are lazy — no intermediate allocations until .collect()

let orders = vec![
    Order { id: 1, active: true,  total: 150.0 },
    Order { id: 2, active: false, total:  80.0 },
    Order { id: 3, active: true,  total: 200.0 },
];

// map — transform
let totals: Vec<f64> = orders.iter().map(|o| o.total).collect();

// filter — select
let active: Vec<&Order> = orders.iter().filter(|o| o.active).collect();

// fold (= reduce) — aggregate
let grand_total: f64 = orders.iter()
    .filter(|o| o.active)
    .map(|o| o.total)
    .fold(0.0, |acc, t| acc + t);

// sum/product — convenience reducers
let total: f64 = orders.iter().map(|o| o.total).sum();

// flat_map — expand nested
let all_items: Vec<&Item> = orders.iter()
    .flat_map(|o| o.items.iter())
    .collect();

// chain — concatenate iterators
let combined = first.iter().chain(second.iter());

// zip — pair two iterators
let pairs: Vec<_> = names.iter().zip(scores.iter()).collect();

// enumerate — add index
for (i, order) in orders.iter().enumerate() {
    println!("{}: {:?}", i, order);
}

// any / all — boolean aggregation
let has_active = orders.iter().any(|o| o.active);
let all_active = orders.iter().all(|o| o.active);

// find — first matching
let first_active = orders.iter().find(|o| o.active);

// take_while / skip_while
let until_cancelled: Vec<_> = orders.iter()
    .take_while(|o| o.active)
    .collect();
```

---

## Option<T> — Explicit Absence

```rust
// Option<T> = Some(T) | None
// The compiler forces you to handle both cases

fn find_user(id: &str, db: &HashMap<String, User>) -> Option<&User> {
    db.get(id)
}

// Pattern matching — exhaustive
match find_user("123", &db) {
    None       => println!("Not found"),
    Some(user) => println!("Found: {}", user.name),
}

// if let — match only the Some case
if let Some(user) = find_user("123", &db) {
    println!("Found: {}", user.name);
}

// map — transform the value inside Some
let email: Option<String> = find_user("123", &db)
    .map(|u| u.email.clone());

// and_then — chain Option computations (flatMap)
let city: Option<&str> = find_user("123", &db)
    .and_then(|u| u.address.as_ref())
    .and_then(|a| a.city.as_deref());

// unwrap_or — provide a default
let city = get_city(&user).unwrap_or("Unknown");

// unwrap_or_else — lazy default (only evaluated if None)
let city = get_city(&user).unwrap_or_else(|| fetch_default_city());

// ? operator in functions returning Option
fn get_city(user: &User) -> Option<&str> {
    let address = user.address.as_ref()?;  // returns None if None
    address.city.as_deref()
}
```

---

## Result<T, E> — Explicit Failure

```rust
use std::fmt;

#[derive(Debug)]
enum ValidationError {
    InvalidEmail(String),
    InvalidAge(i32),
}

impl fmt::Display for ValidationError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Self::InvalidEmail(e) => write!(f, "Invalid email: {e}"),
            Self::InvalidAge(a)   => write!(f, "Invalid age: {a}"),
        }
    }
}

fn validate_email(email: &str) -> Result<String, ValidationError> {
    if email.contains('@') {
        Ok(email.to_lowercase().trim().to_string())
    } else {
        Err(ValidationError::InvalidEmail(email.to_string()))
    }
}

fn validate_age(age: i32) -> Result<i32, ValidationError> {
    if (0..=150).contains(&age) {
        Ok(age)
    } else {
        Err(ValidationError::InvalidAge(age))
    }
}

#[derive(Debug)]
struct User { email: String, age: i32 }

// ? operator — propagates Err automatically
fn parse_user(email: &str, age: i32) -> Result<User, ValidationError> {
    let valid_email = validate_email(email)?;  // returns Err if Err
    let valid_age   = validate_age(age)?;
    Ok(User { email: valid_email, age: valid_age })
}

// map / and_then for pipeline style
fn process_email(raw: &str) -> Result<String, ValidationError> {
    validate_email(raw)
        .map(|e| e.to_uppercase())
        .and_then(|e| if e.len() > 5 { Ok(e) } else { Err(ValidationError::InvalidEmail(e)) })
}

// Pattern match at call site
match parse_user("alice@example.com", 30) {
    Ok(user)  => println!("User: {:?}", user),
    Err(e)    => eprintln!("Error: {}", e),
}
```

---

## Algebraic Data Types — Enums

```rust
// Rust enums are full algebraic data types — each variant can carry data

#[derive(Debug)]
enum OrderStatus {
    Pending,
    Shipped { tracking_code: String },
    Delivered { delivered_at: chrono::DateTime<chrono::Utc> },
    Cancelled { reason: String },
}

// Exhaustive pattern matching — compiler error if a case is missing
fn describe_status(status: &OrderStatus) -> String {
    match status {
        OrderStatus::Pending                  => "Awaiting shipment".to_string(),
        OrderStatus::Shipped { tracking_code } => format!("Shipped — {tracking_code}"),
        OrderStatus::Delivered { delivered_at } => format!("Delivered on {delivered_at}"),
        OrderStatus::Cancelled { reason }      => format!("Cancelled: {reason}"),
    }
}

// Recursive enum (Box needed for size known at compile time)
#[derive(Debug)]
enum Tree<A> {
    Leaf,
    Node { value: A, left: Box<Tree<A>>, right: Box<Tree<A>> },
}

fn depth<A>(tree: &Tree<A>) -> usize {
    match tree {
        Tree::Leaf => 0,
        Tree::Node { left, right, .. } => 1 + depth(left).max(depth(right)),
    }
}
```

---

## Function Composition

```rust
// Rust has no built-in compose/pipe operator, but closures compose naturally

fn compose<A, B, C>(f: impl Fn(A) -> B, g: impl Fn(B) -> C) -> impl Fn(A) -> C {
    move |x| g(f(x))
}

let normalize = |s: &str| s.trim().to_lowercase();
let validate  = |s: String| if s.contains('@') { Some(s) } else { None };

// Iterator chains ARE the pipeline
let result = raw_emails.iter()
    .map(|e| e.trim().to_lowercase())
    .filter(|e| e.contains('@'))
    .map(|e| format!("<{e}>"))
    .collect::<Vec<_>>();
```

---

## Newtype Pattern — Nominal Typing

```rust
// Wrapping primitives prevents mixing up different domain concepts

struct UserId(String);
struct OrderId(String);
struct Email(String);

impl UserId {
    fn new(id: impl Into<String>) -> Self { Self(id.into()) }
    fn as_str(&self) -> &str { &self.0 }
}

fn get_user(id: &UserId) -> Option<User> {
    db.find_user(id.as_str())
}

let order_id = OrderId::new("order-123");
// get_user(&order_id)  — compile error! OrderId is not UserId
```

---

## Side Effect Boundary

```rust
// Pure core — no I/O, fully testable
fn process_registration(
    existing_emails: &std::collections::HashSet<String>,
    email: &str,
    name: &str,
    id: &str,
) -> Result<User, String> {
    let email = email.trim().to_lowercase();
    if !email.contains('@') {
        return Err("Invalid email".to_string());
    }
    if existing_emails.contains(&email) {
        return Err("Email already registered".to_string());
    }
    Ok(User { id: id.to_string(), email, name: name.to_string() })
}

// Impure shell — coordinates I/O
async fn register_user(
    db: &Database,
    email: &str,
    name: &str,
) -> Result<User, Box<dyn std::error::Error>> {
    let existing = db.all_emails().await?;                         // I/O
    let id = uuid::Uuid::new_v4().to_string();                     // I/O
    let user = process_registration(&existing, email, name, &id)   // pure
        .map_err(|e| Box::<dyn std::error::Error>::from(e))?;
    db.save_user(&user).await?;                                    // I/O
    Ok(user)
}
```
