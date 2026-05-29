# Python — Functional Programming Examples

Concepts covered: pure functions, composition/pipe, currying, Optional/None, Result pattern, immutable data, higher-order functions, comprehensions, generators, pattern matching.

Libraries: `functools`, `itertools`, [`returns`](https://returns.readthedocs.io), [`toolz`](https://toolz.readthedocs.io).

---

## Pure Functions and Referential Transparency

```python
# Impure — mutates argument, depends on external state
discount_rate = 0.1

def apply_discount(price):
    return price * (1 - discount_rate)  # hidden dependency

# Pure — all inputs explicit, no side effects
def apply_discount(rate: float, price: float) -> float:
    return price * (1 - rate)

# Pure — returns new dict, original unchanged
def add_item(cart: dict, item: dict) -> dict:
    return {**cart, "items": [*cart["items"], item]}
```

---

## Function Composition and Pipe

```python
from functools import reduce

# Manual pipe (left-to-right)
def pipe(*fns):
    return lambda x: reduce(lambda v, f: f(v), fns, x)

normalize = lambda s: s.strip().lower()
validate  = lambda s: s if "@" in s else None
wrap      = lambda s: f"<{s}>" if s else None

process_email = pipe(normalize, validate, wrap)
process_email("  Alice@Example.com  ")  # "<alice@example.com>"

# With toolz
from toolz import pipe, compose, curry

result = pipe(
    orders,
    lambda os: filter(lambda o: o["active"], os),
    lambda os: map(lambda o: o["total"], os),
    sum,
)

# compose — right-to-left
normalize_email = compose(str.lower, str.strip)
normalize_email("  Alice@EXAMPLE.COM  ")  # "alice@example.com"
```

---

## Currying and Partial Application

```python
from functools import partial

# Manual currying
def multiply(a):
    return lambda b: a * b

double = multiply(2)
triple = multiply(3)

list(map(double, [1, 2, 3]))  # [2, 4, 6]

# functools.partial — fix leftmost arguments
def apply_discount(rate, price):
    return price * (1 - rate)

apply_ten_percent  = partial(apply_discount, 0.1)
apply_twenty       = partial(apply_discount, 0.2)

apply_ten_percent(200)   # 180.0
list(map(apply_ten_percent, [100, 200, 300]))  # [90.0, 180.0, 270.0]

# With toolz.curry — auto-curry any function
from toolz import curry

@curry
def apply_discount(rate, price):
    return price * (1 - rate)

apply_ten_percent = apply_discount(0.1)
apply_ten_percent(200)  # 180.0
```

---

## Optional / None Handling

```python
from typing import Optional

# None as Optional — always declare Optional[T] in type hints
def find_user(user_id: str) -> Optional[dict]:
    return db.users.get(user_id)  # returns None if not found

# Safe chaining — check at each step
def get_city(user: Optional[dict]) -> Optional[str]:
    if user is None:
        return None
    address = user.get("address")
    if address is None:
        return None
    return address.get("city")

# Python 3.10+ — match on Optional
def display_city(user_id: str) -> str:
    match get_city(find_user(user_id)):
        case None:
            return "Unknown city"
        case city:
            return city

# With returns library — Option monad
from returns.maybe import Maybe, Nothing, Some

def find_user(user_id: str) -> Maybe[dict]:
    user = db.users.get(user_id)
    return Some(user) if user else Nothing

def get_city(user_id: str) -> Maybe[str]:
    return (
        find_user(user_id)
        .bind(lambda u: Maybe.from_optional(u.get("address")))
        .bind(lambda a: Maybe.from_optional(a.get("city")))
    )

get_city("123").value_or("Unknown city")
```

---

## Result Pattern — Explicit Failure

```python
from dataclasses import dataclass
from typing import Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")

@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T

@dataclass(frozen=True)
class Err(Generic[E]):
    error: E

Result = Union[Ok[T], Err[E]]

# Validation functions
def validate_email(email: str) -> Result:
    if "@" not in email:
        return Err("Invalid email")
    return Ok(email.strip().lower())

def validate_age(age: int) -> Result:
    if not (0 <= age <= 150):
        return Err("Age must be between 0 and 150")
    return Ok(age)

def parse_user(email: str, age: int) -> Result:
    email_result = validate_email(email)
    if isinstance(email_result, Err):
        return email_result
    age_result = validate_age(age)
    if isinstance(age_result, Err):
        return age_result
    return Ok({"email": email_result.value, "age": age_result.value})

# With returns library — Result monad + Railway-Oriented Programming
from returns.result import Result, Success, Failure

def validate_email(email: str) -> Result[str, str]:
    if "@" not in email:
        return Failure("Invalid email")
    return Success(email.strip().lower())

def validate_age(age: int) -> Result[int, str]:
    if not (0 <= age <= 150):
        return Failure("Age out of range")
    return Success(age)
```

---

## Immutable Data

```python
from dataclasses import dataclass, replace
from typing import FrozenSet, Tuple

# frozen=True makes the dataclass immutable
@dataclass(frozen=True)
class User:
    id: str
    name: str
    email: str

# replace() — creates a new instance with updated fields
user = User(id="1", name="Alice", email="alice@example.com")
updated = replace(user, email="new@example.com")
# user is unchanged

# Named tuple — immutable, lightweight
from typing import NamedTuple

class Point(NamedTuple):
    x: float
    y: float

p = Point(1.0, 2.0)
moved = Point(p.x + 1, p.y)  # new Point

# Immutable collections
items: Tuple[int, ...] = (1, 2, 3)
tags: FrozenSet[str] = frozenset({"python", "fp"})

# "Update" by creating new tuples
more_items = items + (4,)   # (1, 2, 3, 4) — items unchanged
```

---

## Higher-Order Functions

```python
from functools import reduce
from itertools import chain, groupby
from operator import attrgetter

orders = [
    {"id": 1, "status": "active",    "total": 150.0},
    {"id": 2, "status": "cancelled", "total":  80.0},
    {"id": 3, "status": "active",    "total": 200.0},
]

# map — transform
totals = list(map(lambda o: o["total"], orders))

# filter — select
active = list(filter(lambda o: o["status"] == "active", orders))

# reduce — fold
grand_total = reduce(lambda acc, o: acc + o["total"], orders, 0.0)

# Comprehensions — idiomatic Python alternative to map/filter
totals = [o["total"] for o in orders]
active = [o for o in orders if o["status"] == "active"]

# Generator expressions — lazy (no intermediate list)
grand_total = sum(o["total"] for o in orders if o["status"] == "active")

# itertools.chain — flatMap equivalent
all_items = list(chain.from_iterable(o["items"] for o in orders))

# groupby (requires pre-sorting)
sorted_orders = sorted(orders, key=lambda o: o["status"])
by_status = {k: list(v) for k, v in groupby(sorted_orders, key=lambda o: o["status"])}

# sorted with key — functional sort
top_orders = sorted(orders, key=lambda o: o["total"], reverse=True)[:3]
```

---

## Pattern Matching (Python 3.10+)

```python
# Structural pattern matching — like algebraic data type dispatch

def describe_status(status: dict) -> str:
    match status:
        case {"kind": "pending"}:
            return "Awaiting shipment"
        case {"kind": "shipped", "tracking_code": code}:
            return f"Shipped — {code}"
        case {"kind": "delivered", "delivered_at": date}:
            return f"Delivered on {date}"
        case {"kind": "cancelled", "reason": reason}:
            return f"Cancelled: {reason}"
        case _:
            return "Unknown status"

# Pattern matching on types (sum type simulation)
from dataclasses import dataclass

@dataclass
class Pending: created_at: str
@dataclass
class Shipped: tracking_code: str
@dataclass
class Cancelled: reason: str

def describe(status) -> str:
    match status:
        case Pending():        return "Awaiting shipment"
        case Shipped(code):    return f"Shipped — {code}"
        case Cancelled(reason): return f"Cancelled: {reason}"
```

---

## Side Effect Boundary

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class RegistrationInput:
    email: str
    name: str

# Pure core — all logic, no I/O
def process_registration(
    existing_emails: frozenset[str],
    input: RegistrationInput,
    user_id: str,
) -> Result:
    email = input.email.strip().lower()
    if "@" not in email:
        return Err("Invalid email")
    if email in existing_emails:
        return Err("Email already registered")
    return Ok({"id": user_id, "email": email, "name": input.name})

# Impure shell — thin I/O coordination
def register_user(input: RegistrationInput) -> Result:
    existing = frozenset(db.users.all_emails())   # I/O
    user_id = generate_uuid()                      # I/O (randomness)
    result = process_registration(existing, input, user_id)  # pure
    if isinstance(result, Ok):
        db.users.save(result.value)               # I/O
    return result

# Dependency injection via function parameters
def register_user(
    input: RegistrationInput,
    fetch_emails=lambda: db.users.all_emails(),
    save_user=db.users.save,
    gen_id=generate_uuid,
) -> Result:
    existing = frozenset(fetch_emails())
    result = process_registration(existing, input, gen_id())
    if isinstance(result, Ok):
        save_user(result.value)
    return result
```

---

## Generators and Lazy Evaluation

```python
from itertools import islice, takewhile, count

# Generator function — lazy sequence
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Consume lazily — no infinite list in memory
first_10_fibs = list(islice(fibonacci(), 10))
fibs_under_100 = list(takewhile(lambda n: n < 100, fibonacci()))

# Generator expression — lazy pipeline
def process_large_file(path: str):
    with open(path) as f:
        lines = (line.strip() for line in f)
        valid = (line for line in lines if line and not line.startswith("#"))
        parsed = (parse_record(line) for line in valid)
        return sum(r["amount"] for r in parsed if r["active"])
    # Only one line in memory at a time
```
