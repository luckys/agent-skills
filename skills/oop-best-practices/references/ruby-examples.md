# Ruby Examples

These examples cover the same core concepts as the other language-specific example files.

## Concepts Covered

- Value Objects and Invariants
- First-Class Collections
- Tell, Don't Ask
- Role-Based Collaboration
- Dependency Injection
- Explicit Interfaces
- Duck Typing / Protocol-Style Roles
- Composition over Inheritance
- Message-Based Design
- Law of Demeter Violation and Fix
- Immutable Objects
- Null Object
- Anemic versus Rich Model

## Value Objects and Invariants

```ruby
class Money
  def initialize(cents)
    raise ArgumentError, 'Money cannot be negative' if cents < 0

    @cents = cents
  end

  def add(other)
    Money.new(@cents + other.value)
  end

  def multiply_by(percent)
    Money.new((@cents * percent / 100.0).round)
  end

  def value
    @cents
  end
end
```

## First-Class Collections

```ruby
class OrderLine
  def initialize(subtotal_amount)
    @subtotal_amount = subtotal_amount
  end

  def subtotal
    @subtotal_amount
  end
end

class OrderLines
  def initialize(items)
    @items = items
  end

  def total
    @items.reduce(Money.new(0)) { |total, item| total.add(item.subtotal) }
  end

  def empty?
    @items.empty?
  end
end
```

## Tell, Don't Ask

```ruby
class Address
  def initialize(country_code)
    @country_code = country_code
  end

  def domestic?
    @country_code == 'ES'
  end
end

class Shipment
  def initialize(address)
    @address = address
  end

  def dispatch_window_in_days
    @address.domestic? ? 2 : 5
  end
end
```

## Role-Based Collaboration

```ruby
class OrderSummary
  def initialize(formatter)
    @formatter = formatter
  end

  def total_label(lines)
    @formatter.format(lines.total)
  end
end
```

## Dependency Injection

```ruby
class Invoice
  def initialize(recipient, body_text)
    @recipient = recipient
    @body_text = body_text
  end

  def recipient_email
    @recipient
  end

  def body
    @body_text
  end
end

class InvoiceSender
  def initialize(mailer)
    @mailer = mailer
  end

  def send(invoice)
    @mailer.send(invoice.recipient_email, invoice.body)
  end
end
```

## Explicit Interfaces

```ruby
module PaymentGateway
  def charge(_customer_id, _amount)
    raise NotImplementedError
  end
end

class SubscriptionActivator
  def initialize(payment_gateway)
    @payment_gateway = payment_gateway
  end

  def activate(customer_id, fee)
    @payment_gateway.charge(customer_id, fee)
  end
end
```

## Duck Typing / Protocol-Style Roles

```ruby
class InventoryReport
  def initialize(source)
    @source = source
  end

  def available?
    @source.available_units > 0
  end
end

class WarehouseBin
  def initialize(units)
    @units = units
  end

  def available_units
    @units
  end
end
```

## Composition over Inheritance

```ruby
class CartPricing
  def initialize(discount_policy, tax_policy)
    @discount_policy = discount_policy
    @tax_policy = tax_policy
  end

  def total(subtotal)
    discounted = @discount_policy.apply(subtotal)
    @tax_policy.apply(discounted)
  end
end
```

## Message-Based Design

```ruby
class Booking
  def initialize(seats, amount, inventory, payments)
    @seats = seats
    @amount = amount
    @inventory = inventory
    @payments = payments
  end

  def confirm
    @inventory.reserve(@seats)
    @payments.charge(@amount)
  end
end
```

## Law of Demeter Violation and Fix

### Before

```ruby
class CustomerRecord
  def initialize(address)
    @address = address
  end

  def shipping_address
    @address
  end
end

class Order
  def initialize(customer)
    @customer = customer
  end

  def customer_record
    @customer
  end
end

domestic = order.customer_record.shipping_address.domestic?
```

### After

```ruby
class Customer
  def initialize(address)
    @address = address
  end

  def ships_domestically?
    @address.domestic?
  end
end

class PurchaseOrder
  def initialize(customer)
    @customer = customer
  end

  def ships_domestically?
    @customer.ships_domestically?
  end
end

domestic = order.ships_domestically?
```

## Immutable Objects

```ruby
class Rooms
  def initialize(items)
    @items = items.freeze
  end

  def add(room)
    Rooms.new(@items + [room])
  end

  def count
    @items.length
  end
end
```

## Null Object

```ruby
class NullLogger
  def info(_message)
  end
end
```

## Anemic versus Rich Model

### Anemic

```ruby
class ScoreData
  attr_accessor :value

  def initialize(value)
    @value = value
  end
end

def increase_score(score, points)
  score.value = score.value + points
end
```

### Rich

```ruby
class Score
  def initialize(value)
    @value = value
  end

  def increase(points)
    Score.new(@value + points)
  end

  def value
    @value
  end
end
```

## SOLID — Single Responsibility Violation and Fix

### Before (Report does too much)

```ruby
class Report
  def initialize(title, body)
    @title = title
    @body  = body
  end

  def title
    @title
  end

  def body
    @body
  end

  def save_to_database(db_connection)
    db_connection.execute(
      'INSERT INTO reports (title, body) VALUES (?, ?)',
      @title, @body
    )
  end
end
```

### After (split responsibilities)

```ruby
class Report
  attr_reader :title, :body

  def initialize(title, body)
    @title = title.freeze
    @body  = body.freeze
  end
end

class ReportRepository
  def initialize(db_connection)
    @db = db_connection
  end

  def save(report)
    @db.execute(
      'INSERT INTO reports (title, body) VALUES (?, ?)',
      report.title, report.body
    )
  end
end
```

## Object Calisthenics — Wrap Primitive

```ruby
class Percentage
  def initialize(value)
    raise ArgumentError, 'Percentage must be between 0 and 100' unless (0..100).include?(value)

    @value = value.freeze
  end

  def of(amount)
    (amount * @value / 100.0).round
  end

  def value
    @value
  end
end

class Price
  def initialize(cents)
    raise ArgumentError, 'Price cannot be negative' if cents < 0

    @cents = cents.freeze
  end

  def apply_discount(discount)
    Price.new(@cents - discount.of(@cents))
  end

  def cents
    @cents
  end
end
```

## Object Calisthenics — No Else Rule

### Before (nested if/else)

```ruby
def shipping_cost(order)
  if order.domestic?
    if order.total_cents > 5000
      0
    else
      500
    end
  else
    1500
  end
end
```

### After (guard clauses, early return)

```ruby
def shipping_cost(order)
  return 1500 unless order.domestic?
  return 0    if order.total_cents > 5000

  500
end
```

## Dependency Direction

### Before (hard-wired dependency)

```ruby
class InvoiceExporter
  def export(invoice, path)
    fs = FileSystem.new
    fs.write(path, invoice.to_csv)
  end
end
```

### After (inject any collaborator that responds to `write`)

```ruby
class InvoiceExporter
  def initialize(storage)
    @storage = storage   # duck-typed: any object responding to #write(path, content)
  end

  def export(invoice, path)
    @storage.write(path, invoice.to_csv)
  end
end
```

## Composed Method

### Before (mixed concerns in one method)

```ruby
class RegistrationService
  def register(email, password)
    raise ArgumentError, 'Email is required'    if email.nil? || email.empty?
    raise ArgumentError, 'Password too short'   if password.length < 8

    hashed = BCrypt::Password.create(password)
    user   = User.new(email: email, password_hash: hashed)
    UserRepository.new.save(user)
    Mailer.new.send_welcome(email)
    user
  end
end
```

### After (composed sequence of private methods)

```ruby
class RegistrationService
  def register(email, password)
    validate(email, password)
    user = build_user(email, password)
    persist(user)
    welcome(user)
    user
  end

  private

  def validate(email, password)
    raise ArgumentError, 'Email is required'  if email.nil? || email.empty?
    raise ArgumentError, 'Password too short' if password.length < 8
  end

  def build_user(email, password)
    hashed = BCrypt::Password.create(password)
    User.new(email: email, password_hash: hashed)
  end

  def persist(user)
    @repository.save(user)
  end

  def welcome(user)
    @mailer.send_welcome(user.email)
  end
end
```

## What to Notice

- Rich models and clear object responsibilities help keep knowledge close to the concept.
- Ruby makes message-based design and duck typing feel natural.
- Explicit interfaces can still be made visible through narrow modules and roles.
- Composition and delegation stay easier to evolve than large inheritance hierarchies.
- Wrapping primitives and splitting responsibilities keep each class focused on one reason to change.
