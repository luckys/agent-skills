# Python Examples

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

```python
class Money:
    def __init__(self, cents: int) -> None:
        if cents < 0:
            raise ValueError("Money cannot be negative")
        self._cents = cents

    def add(self, other: "Money") -> "Money":
        return Money(self._cents + other._cents)

    def multiply_by(self, percent: int) -> "Money":
        return Money(round(self._cents * percent / 100))

    def value(self) -> int:
        return self._cents
```

## First-Class Collections

```python
class OrderLine:
    def __init__(self, subtotal_amount: Money) -> None:
        self._subtotal_amount = subtotal_amount

    def subtotal(self) -> Money:
        return self._subtotal_amount

class OrderLines:
    def __init__(self, items: list[OrderLine]) -> None:
        self._items = list(items)

    def total(self) -> Money:
        total = Money(0)
        for item in self._items:
            total = total.add(item.subtotal())
        return total

    def is_empty(self) -> bool:
        return len(self._items) == 0
```

## Tell, Don't Ask

```python
class Address:
    def __init__(self, country_code: str) -> None:
        self._country_code = country_code

    def is_domestic(self) -> bool:
        return self._country_code == "ES"

class Shipment:
    def __init__(self, address: Address) -> None:
        self._address = address

    def dispatch_window_in_days(self) -> int:
        return 2 if self._address.is_domestic() else 5
```

## Role-Based Collaboration

```python
class CurrencyFormatter:
    def format(self, amount: Money) -> str:
        raise NotImplementedError

class OrderSummary:
    def __init__(self, formatter: CurrencyFormatter) -> None:
        self._formatter = formatter

    def total_label(self, lines: OrderLines) -> str:
        return self._formatter.format(lines.total())
```

## Dependency Injection

```python
class Mailer:
    def send(self, to: str, body: str) -> None:
        raise NotImplementedError

class Invoice:
    def __init__(self, recipient: str, body_text: str) -> None:
        self._recipient = recipient
        self._body_text = body_text

    def recipient_email(self) -> str:
        return self._recipient

    def body(self) -> str:
        return self._body_text

class InvoiceSender:
    def __init__(self, mailer: Mailer) -> None:
        self._mailer = mailer

    def send(self, invoice: Invoice) -> None:
        self._mailer.send(invoice.recipient_email(), invoice.body())
```

## Explicit Interfaces

```python
from typing import Protocol

class PaymentGateway(Protocol):
    def charge(self, customer_id: str, amount: Money) -> None:
        pass

class SubscriptionActivator:
    def __init__(self, payment_gateway: PaymentGateway) -> None:
        self._payment_gateway = payment_gateway

    def activate(self, customer_id: str, fee: Money) -> None:
        self._payment_gateway.charge(customer_id, fee)
```

## Duck Typing / Protocol-Style Roles

```python
class InventoryReport:
    def __init__(self, source) -> None:
        self._source = source

    def is_available(self) -> bool:
        return self._source.available_units() > 0

class WarehouseBin:
    def __init__(self, units: int) -> None:
        self._units = units

    def available_units(self) -> int:
        return self._units
```

## Composition over Inheritance

```python
class DiscountPolicy:
    def apply(self, total: Money) -> Money:
        raise NotImplementedError

class TaxPolicy:
    def apply(self, total: Money) -> Money:
        raise NotImplementedError

class CartPricing:
    def __init__(self, discount_policy: DiscountPolicy, tax_policy: TaxPolicy) -> None:
        self._discount_policy = discount_policy
        self._tax_policy = tax_policy

    def total(self, subtotal: Money) -> Money:
        discounted = self._discount_policy.apply(subtotal)
        return self._tax_policy.apply(discounted)
```

## Message-Based Design

```python
class SeatInventory:
    def reserve(self, seat_count: int) -> None:
        raise NotImplementedError

class PaymentService:
    def charge(self, amount: Money) -> None:
        raise NotImplementedError

class Booking:
    def __init__(
        self,
        seats: int,
        amount: Money,
        inventory: SeatInventory,
        payments: PaymentService,
    ) -> None:
        self._seats = seats
        self._amount = amount
        self._inventory = inventory
        self._payments = payments

    def confirm(self) -> None:
        self._inventory.reserve(self._seats)
        self._payments.charge(self._amount)
```

## Law of Demeter Violation and Fix

### Before

```python
class CustomerRecord:
    def __init__(self, address: Address) -> None:
        self._address = address

    def shipping_address(self) -> Address:
        return self._address

class Order:
    def __init__(self, customer: CustomerRecord) -> None:
        self._customer = customer

    def customer_record(self) -> CustomerRecord:
        return self._customer

domestic = order.customer_record().shipping_address().is_domestic()
```

### After

```python
class Customer:
    def __init__(self, address: Address) -> None:
        self._address = address

    def ships_domestically(self) -> bool:
        return self._address.is_domestic()

class PurchaseOrder:
    def __init__(self, customer: Customer) -> None:
        self._customer = customer

    def ships_domestically(self) -> bool:
        return self._customer.ships_domestically()

domestic = order.ships_domestically()
```

## Immutable Objects

```python
class Rooms:
    def __init__(self, items: tuple[str, ...]) -> None:
        self._items = items

    def add(self, room: str) -> "Rooms":
        return Rooms(self._items + (room,))

    def count(self) -> int:
        return len(self._items)
```

## Null Object

```python
class Logger:
    def info(self, message: str) -> None:
        raise NotImplementedError

class NullLogger(Logger):
    def info(self, message: str) -> None:
        return None
```

## Anemic versus Rich Model

### Anemic

```python
class ScoreData:
    def __init__(self, value: int) -> None:
        self.value = value

def increase_score(score: ScoreData, points: int) -> None:
    score.value = score.value + points
```

### Rich

```python
class Score:
    def __init__(self, value: int) -> None:
        self._value = value

    def increase(self, points: int) -> "Score":
        return Score(self._value + points)

    def value(self) -> int:
        return self._value
```

## SOLID — Single Responsibility Violation and Fix

### Before — one class does too much

```python
from dataclasses import dataclass

@dataclass
class Report:
    title: str
    content: str

    def save(self, report_id: int) -> None:
        # mixes persistence logic into a data class
        db = Database()
        db.execute(
            "INSERT INTO reports (id, title, content) VALUES (?, ?, ?)",
            (report_id, self.title, self.content),
        )
```

### After — split by responsibility

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Report:
    title: str
    content: str

class ReportRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    def save(self, report_id: int, report: Report) -> None:
        self._db.execute(
            "INSERT INTO reports (id, title, content) VALUES (?, ?, ?)",
            (report_id, report.title, report.content),
        )
```

## Object Calisthenics — Wrap Primitive

### Before — raw int leaks the invariant everywhere

```python
def apply_discount(price: int, discount: int) -> int:
    # nothing stops discount=150 from being passed
    return round(price * (1 - discount / 100))
```

### After — encapsulate the concept and its rules

```python
class Percentage:
    def __init__(self, value: int) -> None:
        if not (0 <= value <= 100):
            raise ValueError(f"Percentage must be between 0 and 100, got {value}")
        self._value = value

    def of(self, amount: int) -> int:
        return round(amount * self._value / 100)

    def __repr__(self) -> str:
        return f"Percentage({self._value})"

class Price:
    def __init__(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("Price cannot be negative")
        self._amount = amount

    def apply_discount(self, discount: Percentage) -> "Price":
        return Price(self._amount - discount.of(self._amount))

    def value(self) -> int:
        return self._amount
```

## Object Calisthenics — No Else Rule

### Before — nested if/else blocks

```python
def shipping_cost(order) -> int:
    if order.is_member():
        if order.total() > 100:
            return 0
        else:
            return 3
    else:
        if order.total() > 50:
            return 5
        else:
            return 10
```

### After — guard clauses with early returns

```python
def shipping_cost(order) -> int:
    if order.is_member() and order.total() > 100:
        return 0
    if order.is_member():
        return 3
    if order.total() > 50:
        return 5
    return 10
```

## Dependency Direction

### Before — hardcoded volatile dependency

```python
class InvoiceExporter:
    def export(self, invoice_id: int, content: str) -> None:
        fs = FileSystem()                         # concrete, volatile
        fs.write(f"/invoices/{invoice_id}.pdf", content)
```

### After — depend on an abstraction via Protocol

```python
from typing import Protocol

class DocumentStorage(Protocol):
    def write(self, path: str, content: str) -> None:
        ...

class InvoiceExporter:
    def __init__(self, storage: DocumentStorage) -> None:
        self._storage = storage

    def export(self, invoice_id: int, content: str) -> None:
        self._storage.write(f"/invoices/{invoice_id}.pdf", content)

# Any object with a matching write() method satisfies DocumentStorage.
# The exporter never imports FileSystem — the direction of the dependency
# now points toward the abstraction, not the volatile implementation.
```

## Composed Method

### Before — one flat method doing everything

```python
import hashlib

class RegistrationService:
    def register(self, email: str, password: str) -> None:
        if not email or "@" not in email:
            raise ValueError("Invalid email")
        if len(password) < 8:
            raise ValueError("Password too short")
        hashed = hashlib.sha256(password.encode()).hexdigest()
        user = {"email": email, "password_hash": hashed}
        self._db.insert("users", user)
        self._mailer.send(email, "Welcome!", "Your account is ready.")
```

### After — register reads as a high-level sequence of steps

```python
import hashlib
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    email: str
    password_hash: str

class RegistrationService:
    def register(self, email: str, password: str) -> None:
        self._validate(email, password)
        user = self._build_user(email, password)
        self._persist(user)
        self._welcome(user)

    def _validate(self, email: str, password: str) -> None:
        if not email or "@" not in email:
            raise ValueError("Invalid email")
        if len(password) < 8:
            raise ValueError("Password too short")

    def _build_user(self, email: str, password: str) -> User:
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return User(email=email, password_hash=hashed)

    def _persist(self, user: User) -> None:
        self._db.insert("users", {"email": user.email, "password_hash": user.password_hash})

    def _welcome(self, user: User) -> None:
        self._mailer.send(user.email, "Welcome!", "Your account is ready.")
```

## SOLID — Open/Closed Principle

### Before — switch on type string

```python
class ShippingCalculator:
    def cost(self, order) -> int:
        if order.type == "standard":
            return 5
        elif order.type == "express":
            return 15
        elif order.type == "overnight":
            return 25
        return 0
```

### After — open for extension, closed for modification

```python
from abc import ABC, abstractmethod

class ShippingPolicy(ABC):
    @abstractmethod
    def cost(self, order) -> int:
        ...

class StandardShipping(ShippingPolicy):
    def cost(self, order) -> int:
        return 5

class ExpressShipping(ShippingPolicy):
    def cost(self, order) -> int:
        return 15

class OvernightShipping(ShippingPolicy):
    def cost(self, order) -> int:
        return 25

class ShippingCalculator:
    def __init__(self, policy: ShippingPolicy) -> None:
        self._policy = policy

    def cost(self, order) -> int:
        return self._policy.cost(order)
```

## SOLID — Liskov Substitution Principle

### Before — subclass breaks the contract

```python
class Collection:
    def __init__(self) -> None:
        self._items: list = []

    def add(self, item) -> None:
        self._items.append(item)

    def all(self) -> list:
        return list(self._items)

class ReadOnlyCollection(Collection):
    def add(self, item) -> None:
        raise NotImplementedError("This collection is read-only")  # LSP violation
```

### After — two independent classes with composition

```python
class MutableCollection:
    def __init__(self, items: list | None = None) -> None:
        self._items: list = list(items) if items else []

    def add(self, item) -> None:
        self._items.append(item)

    def all(self) -> list:
        return list(self._items)

class ReadOnlyCollection:
    def __init__(self, items: list) -> None:
        self._items = list(items)

    def all(self) -> list:
        return list(self._items)
```

## SOLID — Interface Segregation Principle

### Before — fat ABC forces irrelevant methods

```python
from abc import ABC, abstractmethod

class Worker(ABC):
    @abstractmethod
    def work(self) -> None:
        ...

    @abstractmethod
    def eat(self) -> None:
        ...

    @abstractmethod
    def sleep(self) -> None:
        ...

class RobotWorker(Worker):
    def work(self) -> None:
        print("Robot working")

    def eat(self) -> None:
        raise NotImplementedError("Robots do not eat")

    def sleep(self) -> None:
        raise NotImplementedError("Robots do not sleep")
```

### After — focused Protocol types per capability

```python
from typing import Protocol

class Workable(Protocol):
    def work(self) -> None:
        ...

class Eatable(Protocol):
    def eat(self) -> None:
        ...

class Sleepable(Protocol):
    def sleep(self) -> None:
        ...

class HumanWorker:
    def work(self) -> None:
        print("Human working")

    def eat(self) -> None:
        print("Human eating")

    def sleep(self) -> None:
        print("Human sleeping")

class RobotWorker:
    def work(self) -> None:
        print("Robot working")
```

## SOLID — Dependency Inversion Principle

### Before — high-level module depends on a concrete detail

```python
class PostgresDatabase:
    def save_order(self, order) -> None:
        ...  # writes directly to Postgres

class OrderProcessor:
    def __init__(self) -> None:
        self._db = PostgresDatabase()  # hardcoded volatile dependency

    def process(self, order) -> None:
        self._db.save_order(order)
```

### After — high-level module owns the abstraction

```python
from typing import Protocol

# Protocol owned by the high-level module.
class OrderStore(Protocol):
    def save_order(self, order) -> None:
        ...

class OrderProcessor:
    def __init__(self, store: OrderStore) -> None:
        self._store = store

    def process(self, order) -> None:
        self._store.save_order(order)
```

## Object Calisthenics — One Level of Indentation

### Before — nested loops and conditions in one function

```python
def generate_report(orders: list) -> list[str]:
    lines = []
    for order in orders:
        if order.is_complete():
            for item in order.items:
                if item.price > 100:
                    lines.append(f"{item.name}: {item.price}")
    return lines
```

### After — three extracted helpers, each with one level

```python
def complete_orders(orders: list) -> list:
    return [order for order in orders if order.is_complete()]

def expensive_items(order) -> list:
    return [item for item in order.items if item.price > 100]

def format_item(item) -> str:
    return f"{item.name}: {item.price}"

def generate_report(orders: list) -> list[str]:
    return [
        format_item(item)
        for order in complete_orders(orders)
        for item in expensive_items(order)
    ]
```

## Object Calisthenics — No Getters/Setters

### Before — callers extract data and compute behavior externally

```python
class Rectangle:
    def __init__(self, width: int, height: int) -> None:
        self._width = width
        self._height = height

    def get_width(self) -> int:
        return self._width

    def get_height(self) -> int:
        return self._height

rect = Rectangle(4, 6)
area = rect.get_width() * rect.get_height()
perimeter = 2 * (rect.get_width() + rect.get_height())
```

### After — behavior lives inside the object

```python
class Rectangle:
    def __init__(self, width: int, height: int) -> None:
        self._width = width
        self._height = height

    def area(self) -> int:
        return self._width * self._height

    def perimeter(self) -> int:
        return 2 * (self._width + self._height)

    def is_square(self) -> bool:
        return self._width == self._height

rect = Rectangle(4, 6)
area = rect.area()
perimeter = rect.perimeter()
```

## Object Calisthenics — Don't Abbreviate

### Before — cryptic names obscure intent

```python
class OrdMgr:
    def calc(self, o) -> int:
        t = 0
        for i in o.itms:
            t += i.p * i.q
        return t

    def proc(self, o) -> None:
        if self.calc(o) > 0:
            o.confirm()
```

### After — names reveal meaning at a glance

```python
class OrderManager:
    def calculate_total(self, order) -> int:
        return sum(item.price * item.quantity for item in order.items)

    def process_order(self, order) -> None:
        if self.calculate_total(order) > 0:
            order.confirm()
```

## Explaining Message

### Before — inline expression hides intent

```python
from datetime import datetime, timedelta

class Subscription:
    def __init__(self, start_date: datetime, duration_days: int) -> None:
        self._start_date = start_date
        self._duration_days = duration_days

    def is_expired(self) -> bool:
        return datetime.now() > self._start_date + timedelta(days=self._duration_days)
```

### After — delegate to a named private method

```python
from datetime import datetime, timedelta

class Subscription:
    def __init__(self, start_date: datetime, duration_days: int) -> None:
        self._start_date = start_date
        self._duration_days = duration_days

    def is_expired(self) -> bool:
        return datetime.now() > self._expiration_date()

    def _expiration_date(self) -> datetime:
        return self._start_date + timedelta(days=self._duration_days)
```

## What to Notice

- Rich models and clear object responsibilities help keep knowledge close to the concept.
- Python can express the same object boundaries with very little ceremony.
- Protocols and duck typing both support role-based collaboration.
- Composition and message passing stay readable without large frameworks.
- Wrapping primitives and splitting responsibilities keep each class focused on one reason to change.
- SOLID principles, Object Calisthenics rules, and extracted explaining messages each reduce a different kind of coupling or noise.
