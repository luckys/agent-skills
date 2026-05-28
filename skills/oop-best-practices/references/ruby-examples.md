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

## SOLID — Open/Closed Principle

### Before (case on type string)

```ruby
class ShippingCalculator
  def cost(order)
    case order.type
    when 'standard' then 500
    when 'express'  then 1200
    when 'overnight' then 2500
    else raise ArgumentError, "Unknown order type: #{order.type}"
    end
  end
end
```

### After (open to new policies, closed to modification)

```ruby
class StandardShipping
  def cost(_order)
    500
  end
end

class ExpressShipping
  def cost(_order)
    1200
  end
end

class OvernightShipping
  def cost(_order)
    2500
  end
end

class ShippingCalculator
  def initialize(policy)
    @policy = policy
  end

  def cost(order)
    @policy.cost(order)
  end
end
```

## SOLID — Liskov Substitution Principle

### Before (LSP violation — subclass breaks the contract)

```ruby
class Collection
  def initialize
    @items = []
  end

  def add(item)
    @items << item
  end

  def all
    @items
  end
end

class ReadOnlyCollection < Collection
  def add(_item)
    raise 'Cannot modify a read-only collection'
  end
end
```

### After (independent classes, no broken inheritance)

```ruby
class MutableCollection
  def initialize
    @items = []
  end

  def add(item)
    @items << item
  end

  def all
    @items
  end
end

class ReadOnlyCollection
  def initialize(items)
    @items = items.freeze
  end

  def all
    @items
  end
end
```

## SOLID — Interface Segregation Principle

### Before (fat module forces unrelated implementations)

```ruby
module Worker
  def work
    raise NotImplementedError
  end

  def eat
    raise NotImplementedError
  end

  def sleep
    raise NotImplementedError
  end
end

class RobotWorker
  include Worker

  def work
    'working'
  end

  def eat
    raise 'Robots do not eat'
  end

  def sleep
    raise 'Robots do not sleep'
  end
end
```

### After (narrow modules included only where needed)

```ruby
module Workable
  def work
    raise NotImplementedError
  end
end

module Eatable
  def eat
    raise NotImplementedError
  end
end

module Sleepable
  def sleep
    raise NotImplementedError
  end
end

class HumanWorker
  include Workable
  include Eatable
  include Sleepable

  def work  = 'working'
  def eat   = 'eating'
  def sleep = 'sleeping'
end

class RobotWorker
  include Workable

  def work = 'working'
end
```

## SOLID — Dependency Inversion Principle

### Before (depends on a concrete class)

```ruby
class OrderProcessor
  def process(order)
    db = PostgresDatabase.new
    db.save(order)
  end
end
```

### After (depends on any object that responds to `save`)

```ruby
class OrderProcessor
  def initialize(storage)
    @storage = storage   # duck-typed: any object responding to #save(order)
  end

  def process(order)
    @storage.save(order)
  end
end
```

## Object Calisthenics — One Level of Indentation

### Before (nested loops and conditionals)

```ruby
def generate_report(orders)
  result = []
  orders.each do |order|
    if order.complete?
      order.items.each do |item|
        if item.price > 100
          result << "#{item.name}: #{item.price}"
        end
      end
    end
  end
  result
end
```

### After (extracted private methods, functional style)

```ruby
def generate_report(orders)
  complete_orders(orders)
    .flat_map { |order| expensive_items(order.items) }
    .map { |item| format_item(item) }
end

private

def complete_orders(orders)
  orders.select(&:complete?)
end

def expensive_items(items)
  items.select { |item| item.price > 100 }
end

def format_item(item)
  "#{item.name}: #{item.price}"
end
```

## Object Calisthenics — No Getters/Setters

### Before (callers compute behaviour from exposed data)

```ruby
class Rectangle
  attr_reader :width, :height

  def initialize(width, height)
    @width  = width
    @height = height
  end
end

# Caller computes what the object should know:
area      = rect.width * rect.height
perimeter = 2 * (rect.width + rect.height)
square    = rect.width == rect.height
```

### After (behaviour lives on the object)

```ruby
class Rectangle
  def initialize(width, height)
    @width  = width
    @height = height
  end

  def area
    @width * @height
  end

  def perimeter
    2 * (@width + @height)
  end

  def square?
    @width == @height
  end
end
```

## Object Calisthenics — Don't Abbreviate

### Before (cryptic class and method names)

```ruby
class OrdMgr
  def calc(o)
    o.items.sum(&:price)
  end

  def proc(o)
    calc(o)
    o.mark_processed
  end
end
```

### After (names reveal intent)

```ruby
class OrderManager
  def calculate_total(order)
    order.items.sum(&:price)
  end

  def process_order(order)
    calculate_total(order)
    order.mark_processed
  end
end
```

## Explaining Message

### Before (inline computation obscures intent)

```ruby
class Subscription
  def initialize(started_at, duration_days)
    @started_at    = started_at
    @duration_days = duration_days
  end

  def expired?
    Time.now > @started_at + (@duration_days * 24 * 60 * 60)
  end
end
```

### After (private method names the concept)

```ruby
class Subscription
  def initialize(started_at, duration_days)
    @started_at    = started_at
    @duration_days = duration_days
  end

  def expired?
    Time.now > expiration_date
  end

  private

  def expiration_date
    @started_at + (@duration_days * 24 * 60 * 60)
  end
end
```

## What to Notice

- Rich models and clear object responsibilities help keep knowledge close to the concept.
- Ruby makes message-based design and duck typing feel natural.
- Explicit interfaces can still be made visible through narrow modules and roles.
- Composition and delegation stay easier to evolve than large inheritance hierarchies.
- Wrapping primitives and splitting responsibilities keep each class focused on one reason to change.
- SOLID principles, Object Calisthenics rules, and extracted explaining messages each reduce a different kind of coupling or noise.
