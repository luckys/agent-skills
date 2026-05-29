# Language Examples

These examples show a refactoring move from branching logic toward role-based collaboration.

## Before

```typescript
function discountAmount(customerType: string, subtotalInCents: number): number {
  if (customerType === 'premium') {
    return Math.round(subtotalInCents * 0.8)
  }

  if (customerType === 'partner') {
    return Math.round(subtotalInCents * 0.85)
  }

  return subtotalInCents
}
```

## After in TypeScript

```typescript
interface PricingPolicy {
  apply(subtotalInCents: number): number
}

class StandardPricing implements PricingPolicy {
  apply(subtotalInCents: number): number {
    return subtotalInCents
  }
}

class PremiumPricing implements PricingPolicy {
  apply(subtotalInCents: number): number {
    return Math.round(subtotalInCents * 0.8)
  }
}

class PartnerPricing implements PricingPolicy {
  apply(subtotalInCents: number): number {
    return Math.round(subtotalInCents * 0.85)
  }
}
```

## After in Go

```go
type PricingPolicy interface {
    Apply(subtotalInCents int) int
}

type StandardPricing struct{}
type PremiumPricing  struct{}
type PartnerPricing  struct{}

func (StandardPricing) Apply(s int) int { return s }
func (PremiumPricing) Apply(s int) int  { return s * 8 / 10 }
func (PartnerPricing) Apply(s int) int  { return s * 85 / 100 }
```

## After in Rust

```rust
pub trait PricingPolicy { fn apply(&self, subtotal_in_cents: i64) -> i64; }

pub struct StandardPricing;
pub struct PremiumPricing;
pub struct PartnerPricing;

impl PricingPolicy for StandardPricing { fn apply(&self, s: i64) -> i64 { s } }
impl PricingPolicy for PremiumPricing  { fn apply(&self, s: i64) -> i64 { s * 8 / 10 } }
impl PricingPolicy for PartnerPricing  { fn apply(&self, s: i64) -> i64 { s * 85 / 100 } }
```

## After in Java

```java
public interface PricingPolicy {
    int apply(int subtotalInCents);
}

public final class StandardPricing implements PricingPolicy {
    public int apply(int subtotalInCents) {
        return subtotalInCents;
    }
}

public final class PremiumPricing implements PricingPolicy {
    public int apply(int subtotalInCents) {
        return Math.round(subtotalInCents * 0.8f);
    }
}
```

## After in Python

```python
class PricingPolicy:
    def apply(self, subtotal_in_cents: int) -> int:
        raise NotImplementedError


class StandardPricing(PricingPolicy):
    def apply(self, subtotal_in_cents: int) -> int:
        return subtotal_in_cents


class PremiumPricing(PricingPolicy):
    def apply(self, subtotal_in_cents: int) -> int:
        return round(subtotal_in_cents * 0.8)
```

## After in C#

```csharp
public interface IPricingPolicy
{
    int Apply(int subtotalInCents);
}

public sealed class StandardPricing : IPricingPolicy
{
    public int Apply(int subtotalInCents)
    {
        return subtotalInCents;
    }
}

public sealed class PremiumPricing : IPricingPolicy
{
    public int Apply(int subtotalInCents)
    {
        return (int)Math.Round(subtotalInCents * 0.8);
    }
}
```

## After in Ruby

```ruby
class StandardPricing
  def apply(subtotal_in_cents)
    subtotal_in_cents
  end
end

class PremiumPricing
  def apply(subtotal_in_cents)
    (subtotal_in_cents * 0.8).round
  end
end
```

## After in PHP

```php
interface PricingPolicy
{
    public function apply(int $subtotalInCents): int;
}

final class StandardPricing implements PricingPolicy
{
    public function apply(int $subtotalInCents): int
    {
        return $subtotalInCents;
    }
}

final class PremiumPricing implements PricingPolicy
{
    public function apply(int $subtotalInCents): int
    {
        return (int) round($subtotalInCents * 0.8);
    }
}
```

## Extract Method

Use this move when a method mixes several levels of abstraction or contains a block whose purpose can be captured in a single clear name.

### Before

```typescript
function printOrderSummary(order: Order): void {
  console.log(`Order: ${order.id()}`)
  console.log(`Date: ${order.date()}`)

  for (const item of order.items()) {
    console.log(`  ${item.name()}: ${item.price().value()}`)
  }

  console.log(`Total: ${order.items().total().value()}`)
}
```

### After in TypeScript

```typescript
function printOrderSummary(order: Order): void {
  printHeader(order)
  printItems(order)
  printTotal(order)
}

function printHeader(order: Order): void {
  console.log(`Order: ${order.id()}`)
  console.log(`Date: ${order.date()}`)
}

function printItems(order: Order): void {
  for (const item of order.items()) {
    console.log(`  ${item.name()}: ${item.price().value()}`)
  }
}

function printTotal(order: Order): void {
  console.log(`Total: ${order.items().total().value()}`)
}
```

### After in Go

```go
func printOrderSummary(order Order) {
    printHeader(order)
    printItems(order)
    printTotal(order)
}

func printHeader(order Order) {
    fmt.Printf("Order: %s\n", order.ID())
    fmt.Printf("Date: %s\n", order.Date())
}

func printItems(order Order) {
    for _, item := range order.Items() {
        fmt.Printf("  %s: %d\n", item.Name(), item.Price().Value())
    }
}

func printTotal(order Order) {
    fmt.Printf("Total: %d\n", order.Items().Total().Value())
}
```

### After in Rust

```rust
fn print_order_summary(order: &Order) {
    print_header(order);
    print_items(order);
    print_total(order);
}

fn print_header(order: &Order) {
    println!("Order: {}", order.id());
    println!("Date: {}", order.date());
}

fn print_items(order: &Order) {
    for item in order.items() {
        println!("  {}: {}", item.name(), item.price().value());
    }
}

fn print_total(order: &Order) {
    println!("Total: {}", order.items().total().value());
}
```

### After in Java

```java
void printOrderSummary(Order order) {
    printHeader(order);
    printItems(order);
    printTotal(order);
}

private void printHeader(Order order) {
    System.out.printf("Order: %s%n", order.id());
    System.out.printf("Date: %s%n", order.date());
}

private void printItems(Order order) {
    for (OrderItem item : order.items()) {
        System.out.printf("  %s: %s%n", item.name(), item.price().value());
    }
}

private void printTotal(Order order) {
    System.out.printf("Total: %s%n", order.items().total().value());
}
```

### After in Python

```python
def print_order_summary(order: Order) -> None:
    print_header(order)
    print_items(order)
    print_total(order)


def print_header(order: Order) -> None:
    print(f"Order: {order.id()}")
    print(f"Date: {order.date()}")


def print_items(order: Order) -> None:
    for item in order.items():
        print(f"  {item.name()}: {item.price().value()}")


def print_total(order: Order) -> None:
    print(f"Total: {order.items().total().value()}")
```

### After in C#

```csharp
void PrintOrderSummary(Order order)
{
    PrintHeader(order);
    PrintItems(order);
    PrintTotal(order);
}

private void PrintHeader(Order order)
{
    Console.WriteLine($"Order: {order.Id()}");
    Console.WriteLine($"Date: {order.Date()}");
}

private void PrintItems(Order order)
{
    foreach (var item in order.Items())
    {
        Console.WriteLine($"  {item.Name()}: {item.Price().Value()}");
    }
}

private void PrintTotal(Order order)
{
    Console.WriteLine($"Total: {order.Items().Total().Value()}");
}
```

### After in Ruby

```ruby
def print_order_summary(order)
  print_header(order)
  print_items(order)
  print_total(order)
end

def print_header(order)
  puts "Order: #{order.id}"
  puts "Date: #{order.date}"
end

def print_items(order)
  order.items.each do |item|
    puts "  #{item.name}: #{item.price.value}"
  end
end

def print_total(order)
  puts "Total: #{order.items.total.value}"
end
```

### After in PHP

```php
function printOrderSummary(Order $order): void
{
    printHeader($order);
    printItems($order);
    printTotal($order);
}

function printHeader(Order $order): void
{
    echo "Order: {$order->id()}\n";
    echo "Date: {$order->date()}\n";
}

function printItems(Order $order): void
{
    foreach ($order->items() as $item) {
        echo "  {$item->name()}: {$item->price()->value()}\n";
    }
}

function printTotal(Order $order): void
{
    echo "Total: {$order->items()->total()->value()}\n";
}
```

---

## Extract Class

Use this move when a class carries two distinct clusters of data and behavior that have different reasons to change.

### Before

```typescript
class Order {
  constructor(
    private readonly orderId: string,
    private readonly customerName: string,
    private readonly customerEmail: string,
    private readonly items: OrderItem[],
  ) {}

  id(): string { return this.orderId }
  customerName(): string { return this.customerName }
  customerEmail(): string { return this.customerEmail }
  itemCount(): number { return this.items.length }
}
```

### After in TypeScript

```typescript
class Customer {
  constructor(
    private readonly _name: string,
    private readonly _email: string,
  ) {}

  name(): string { return this._name }
  email(): string { return this._email }
}

class Order {
  constructor(
    private readonly orderId: string,
    private readonly _customer: Customer,
    private readonly items: OrderItem[],
  ) {}

  id(): string { return this.orderId }
  customer(): Customer { return this._customer }
  itemCount(): number { return this.items.length }
}
```

### After in Go

```go
type Customer struct {
    name  string
    email string
}

func (c Customer) Name() string  { return c.name }
func (c Customer) Email() string { return c.email }

type Order struct {
    id       string
    customer Customer
    items    []OrderItem
}

func (o Order) ID() string           { return o.id }
func (o Order) Customer() Customer   { return o.customer }
func (o Order) ItemCount() int       { return len(o.items) }
```

### After in Rust

```rust
pub struct Customer { name: String, email: String }

impl Customer {
    pub fn name(&self) -> &str  { &self.name }
    pub fn email(&self) -> &str { &self.email }
}

pub struct Order { id: String, customer: Customer, items: Vec<OrderItem> }

impl Order {
    pub fn id(&self) -> &str           { &self.id }
    pub fn customer(&self) -> &Customer { &self.customer }
    pub fn item_count(&self) -> usize  { self.items.len() }
}
```

### After in Java

```java
public final class Customer {
    private final String name;
    private final String email;

    public Customer(String name, String email) {
        this.name = name;
        this.email = email;
    }

    public String name() { return name; }
    public String email() { return email; }
}

public final class Order {
    private final String orderId;
    private final Customer customer;
    private final List<OrderItem> items;

    public Order(String orderId, Customer customer, List<OrderItem> items) {
        this.orderId = orderId;
        this.customer = customer;
        this.items = items;
    }

    public String id() { return orderId; }
    public Customer customer() { return customer; }
    public int itemCount() { return items.size(); }
}
```

### After in Python

```python
class Customer:
    def __init__(self, name: str, email: str) -> None:
        self._name = name
        self._email = email

    def name(self) -> str:
        return self._name

    def email(self) -> str:
        return self._email


class Order:
    def __init__(self, order_id: str, customer: Customer, items: list[OrderItem]) -> None:
        self._order_id = order_id
        self._customer = customer
        self._items = items

    def id(self) -> str:
        return self._order_id

    def customer(self) -> Customer:
        return self._customer

    def item_count(self) -> int:
        return len(self._items)
```

### After in C#

```csharp
public sealed class Customer
{
    public Customer(string name, string email)
    {
        Name = name;
        Email = email;
    }

    public string Name { get; }
    public string Email { get; }
}

public sealed class Order
{
    public Order(string orderId, Customer customer, IReadOnlyList<OrderItem> items)
    {
        Id = orderId;
        Customer = customer;
        Items = items;
    }

    public string Id { get; }
    public Customer Customer { get; }
    public int ItemCount => Items.Count;
    private IReadOnlyList<OrderItem> Items { get; }
}
```

### After in Ruby

```ruby
class Customer
  attr_reader :name, :email

  def initialize(name, email)
    @name = name
    @email = email
  end
end

class Order
  attr_reader :id, :customer

  def initialize(order_id, customer, items)
    @id = order_id
    @customer = customer
    @items = items
  end

  def item_count
    @items.length
  end
end
```

### After in PHP

```php
final class Customer
{
    public function __construct(
        private readonly string $name,
        private readonly string $email,
    ) {}

    public function name(): string { return $this->name; }
    public function email(): string { return $this->email; }
}

final class Order
{
    public function __construct(
        private readonly string $orderId,
        private readonly Customer $customer,
        private readonly array $items,
    ) {}

    public function id(): string { return $this->orderId; }
    public function customer(): Customer { return $this->customer; }
    public function itemCount(): int { return count($this->items); }
}
```

---

## Introduce Value Object

Use this move when validation logic for a domain concept is duplicated across multiple callers.

### Before

```typescript
function registerUser(email: string): void {
  if (!email.includes('@')) throw new Error('Invalid email')
  userRepository.save(new User(email))
}

function sendNewsletter(email: string): void {
  if (!email.includes('@')) throw new Error('Invalid email')
  mailer.send(email, 'Newsletter content')
}
```

### After in TypeScript

```typescript
class EmailAddress {
  constructor(private readonly value: string) {
    if (!value.includes('@')) throw new Error('Invalid email address')
  }

  toString(): string {
    return this.value
  }
}

function registerUser(email: EmailAddress): void {
  userRepository.save(new User(email))
}

function sendNewsletter(email: EmailAddress): void {
  mailer.send(email.toString(), 'Newsletter content')
}
```

### After in Go

```go
type EmailAddress struct{ value string }

func NewEmailAddress(value string) (EmailAddress, error) {
    if !strings.Contains(value, "@") {
        return EmailAddress{}, errors.New("invalid email address")
    }
    return EmailAddress{value: value}, nil
}

func (e EmailAddress) String() string { return e.value }

func registerUser(email EmailAddress) { userRepository.save(NewUser(email)) }
func sendNewsletter(email EmailAddress) { mailer.send(email.String(), "Newsletter content") }
```

### After in Rust

```rust
pub struct EmailAddress(String);

impl EmailAddress {
    pub fn new(value: impl Into<String>) -> Result<Self, &'static str> {
        let v = value.into();
        if !v.contains('@') { return Err("invalid email address"); }
        Ok(Self(v))
    }
}

impl std::fmt::Display for EmailAddress {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result { write!(f, "{}", self.0) }
}

fn register_user(email: EmailAddress) { user_repository.save(User::new(email)); }
fn send_newsletter(email: EmailAddress) { mailer.send(&email.to_string(), "Newsletter content"); }
```

### After in Java

```java
public final class EmailAddress {
    private final String value;

    public EmailAddress(String value) {
        if (!value.contains("@")) throw new IllegalArgumentException("Invalid email address");
        this.value = value;
    }

    @Override
    public String toString() { return value; }
}

void registerUser(EmailAddress email) {
    userRepository.save(new User(email));
}

void sendNewsletter(EmailAddress email) {
    mailer.send(email.toString(), "Newsletter content");
}
```

### After in Python

```python
class EmailAddress:
    def __init__(self, value: str) -> None:
        if '@' not in value:
            raise ValueError("Invalid email address")
        self._value = value

    def __str__(self) -> str:
        return self._value


def register_user(email: EmailAddress) -> None:
    user_repository.save(User(email))


def send_newsletter(email: EmailAddress) -> None:
    mailer.send(str(email), "Newsletter content")
```

### After in C#

```csharp
public sealed class EmailAddress
{
    private readonly string _value;

    public EmailAddress(string value)
    {
        if (!value.Contains('@')) throw new ArgumentException("Invalid email address");
        _value = value;
    }

    public override string ToString() => _value;
}

void RegisterUser(EmailAddress email)
{
    userRepository.Save(new User(email));
}

void SendNewsletter(EmailAddress email)
{
    mailer.Send(email.ToString(), "Newsletter content");
}
```

### After in Ruby

```ruby
class EmailAddress
  def initialize(value)
    raise ArgumentError, 'Invalid email address' unless value.include?('@')
    @value = value
  end

  def to_s
    @value
  end
end

def register_user(email)
  user_repository.save(User.new(email))
end

def send_newsletter(email)
  mailer.send(email.to_s, 'Newsletter content')
end
```

### After in PHP

```php
final class EmailAddress
{
    private string $value;

    public function __construct(string $value)
    {
        if (!str_contains($value, '@')) {
            throw new InvalidArgumentException('Invalid email address');
        }
        $this->value = $value;
    }

    public function __toString(): string
    {
        return $this->value;
    }
}

function registerUser(EmailAddress $email): void
{
    $userRepository->save(new User($email));
}

function sendNewsletter(EmailAddress $email): void
{
    $mailer->send((string) $email, 'Newsletter content');
}
```

---

## Move Method

Use this move when a method uses more data from another object than from its own class.

### Before

```typescript
class Rental {
  constructor(
    private readonly movie: Movie,
    private readonly daysRented: number,
  ) {}

  charge(): number {
    if (this.movie.isPremium()) {
      return this.daysRented * 3.5
    }
    return this.daysRented * 2
  }
}
```

### After in TypeScript

```typescript
class Movie {
  constructor(private readonly premium: boolean) {}

  dailyRate(): number {
    return this.premium ? 3.5 : 2
  }
}

class Rental {
  constructor(
    private readonly movie: Movie,
    private readonly daysRented: number,
  ) {}

  charge(): number {
    return this.movie.dailyRate() * this.daysRented
  }
}
```

### After in Go

```go
type Movie struct{ premium bool }
func (m Movie) DailyRate() float64 { if m.premium { return 3.5 }; return 2.0 }

type Rental struct { movie Movie; daysRented int }
func (r Rental) Charge() float64 { return r.movie.DailyRate() * float64(r.daysRented) }
```

### After in Rust

```rust
pub struct Movie { premium: bool }
impl Movie { pub fn daily_rate(&self) -> f64 { if self.premium { 3.5 } else { 2.0 } } }

pub struct Rental { movie: Movie, days_rented: u32 }
impl Rental { pub fn charge(&self) -> f64 { self.movie.daily_rate() * self.days_rented as f64 } }
```

### After in Java

```java
public final class Movie {
    private final boolean premium;

    public Movie(boolean premium) {
        this.premium = premium;
    }

    public double dailyRate() {
        return premium ? 3.5 : 2.0;
    }
}

public final class Rental {
    private final Movie movie;
    private final int daysRented;

    public Rental(Movie movie, int daysRented) {
        this.movie = movie;
        this.daysRented = daysRented;
    }

    public double charge() {
        return movie.dailyRate() * daysRented;
    }
}
```

### After in Python

```python
class Movie:
    def __init__(self, premium: bool) -> None:
        self._premium = premium

    def daily_rate(self) -> float:
        return 3.5 if self._premium else 2.0


class Rental:
    def __init__(self, movie: Movie, days_rented: int) -> None:
        self._movie = movie
        self._days_rented = days_rented

    def charge(self) -> float:
        return self._movie.daily_rate() * self._days_rented
```

### After in C#

```csharp
public sealed class Movie
{
    private readonly bool _premium;

    public Movie(bool premium) => _premium = premium;

    public double DailyRate() => _premium ? 3.5 : 2.0;
}

public sealed class Rental
{
    private readonly Movie _movie;
    private readonly int _daysRented;

    public Rental(Movie movie, int daysRented)
    {
        _movie = movie;
        _daysRented = daysRented;
    }

    public double Charge() => _movie.DailyRate() * _daysRented;
}
```

### After in Ruby

```ruby
class Movie
  def initialize(premium)
    @premium = premium
  end

  def daily_rate
    @premium ? 3.5 : 2.0
  end
end

class Rental
  def initialize(movie, days_rented)
    @movie = movie
    @days_rented = days_rented
  end

  def charge
    @movie.daily_rate * @days_rented
  end
end
```

### After in PHP

```php
final class Movie
{
    public function __construct(private readonly bool $premium) {}

    public function dailyRate(): float
    {
        return $this->premium ? 3.5 : 2.0;
    }
}

final class Rental
{
    public function __construct(
        private readonly Movie $movie,
        private readonly int $daysRented,
    ) {}

    public function charge(): float
    {
        return $this->movie->dailyRate() * $this->daysRented;
    }
}
```

---

## Replace Temp with Query

Use this move when a temporary variable stores a computation that can be extracted into a named method, making the intent readable without comments.

### Before

```typescript
class Cart {
  calculateTotal(): number {
    const base = this.items.reduce((sum, item) => sum + item.price(), 0)
    const discount = base > 100 ? base * 0.1 : 0
    return base - discount
  }
}
```

### After in TypeScript

```typescript
class Cart {
  calculateTotal(): number {
    return this.baseAmount() - this.discount()
  }

  private baseAmount(): number {
    return this.items.reduce((sum, item) => sum + item.price(), 0)
  }

  private discount(): number {
    return this.baseAmount() > 100 ? this.baseAmount() * 0.1 : 0
  }
}
```

### After in Go

```go
type Cart struct{ items []CartItem }

func (c Cart) CalculateTotal() float64 { return c.baseAmount() - c.discount() }
func (c Cart) baseAmount() float64     { s := 0.0; for _, i := range c.items { s += i.Price() }; return s }
func (c Cart) discount() float64       { if c.baseAmount() > 100 { return c.baseAmount() * 0.1 }; return 0 }
```

### After in Rust

```rust
pub struct Cart { items: Vec<CartItem> }

impl Cart {
    pub fn calculate_total(&self) -> f64 { self.base_amount() - self.discount() }
    fn base_amount(&self) -> f64 { self.items.iter().map(|i| i.price()).sum() }
    fn discount(&self) -> f64 { if self.base_amount() > 100.0 { self.base_amount() * 0.1 } else { 0.0 } }
}
```

### After in Java

```java
public class Cart {
    private final List<CartItem> items;

    public Cart(List<CartItem> items) {
        this.items = items;
    }

    public double calculateTotal() {
        return baseAmount() - discount();
    }

    private double baseAmount() {
        return items.stream().mapToDouble(CartItem::price).sum();
    }

    private double discount() {
        return baseAmount() > 100 ? baseAmount() * 0.1 : 0;
    }
}
```

### After in Python

```python
class Cart:
    def __init__(self, items: list[CartItem]) -> None:
        self._items = items

    def calculate_total(self) -> float:
        return self._base_amount() - self._discount()

    def _base_amount(self) -> float:
        return sum(item.price() for item in self._items)

    def _discount(self) -> float:
        return self._base_amount() * 0.1 if self._base_amount() > 100 else 0
```

### After in C#

```csharp
public class Cart
{
    private readonly IReadOnlyList<CartItem> _items;

    public Cart(IReadOnlyList<CartItem> items) => _items = items;

    public double CalculateTotal() => BaseAmount() - Discount();

    private double BaseAmount() => _items.Sum(item => item.Price());

    private double Discount() => BaseAmount() > 100 ? BaseAmount() * 0.1 : 0;
}
```

### After in Ruby

```ruby
class Cart
  def initialize(items)
    @items = items
  end

  def calculate_total
    base_amount - discount
  end

  private

  def base_amount
    @items.sum(&:price)
  end

  def discount
    base_amount > 100 ? base_amount * 0.1 : 0
  end
end
```

### After in PHP

```php
class Cart
{
    public function __construct(private readonly array $items) {}

    public function calculateTotal(): float
    {
        return $this->baseAmount() - $this->discount();
    }

    private function baseAmount(): float
    {
        return array_sum(array_map(fn($item) => $item->price(), $this->items));
    }

    private function discount(): float
    {
        return $this->baseAmount() > 100 ? $this->baseAmount() * 0.1 : 0;
    }
}
```

---

## What to Notice

- The variation becomes explicit.
- Adding a new pricing rule no longer requires editing a central conditional.
- The refactor is safest when protected by tests that captured the old behavior first.
- The same refactoring move works across mainstream object-oriented languages.
- Each move addresses a specific structural problem — match the smell to the move before refactoring.
