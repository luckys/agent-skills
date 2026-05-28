# Python Examples

Pattern examples in Python. Each section shows one design pattern using the same domain scenario as the other language files.

## Strategy

A small role interface isolates the variation. The host class depends on the role, not on concrete branching logic.

```python
class TaxPolicy:
    def calculate(self, subtotal_in_cents: int) -> int:
        raise NotImplementedError


class StandardTaxPolicy(TaxPolicy):
    def calculate(self, subtotal_in_cents: int) -> int:
        return round(subtotal_in_cents * 0.21)


class Invoice:
    def __init__(self, tax_policy: TaxPolicy) -> None:
        self._tax_policy = tax_policy

    def tax(self, subtotal_in_cents: int) -> int:
        return self._tax_policy.calculate(subtotal_in_cents)
```

**What to notice:**
- The variation is isolated behind a small role.
- `Invoice` depends on the behavior it needs, not on concrete branching details.
- Adding another tax policy becomes an additive change.

---

## State

An object changes its behavior as it transitions through states. Each state is an object that knows what actions are legal and what the next state should be.

```python
class OrderState:
    def confirm(self, order): raise NotImplementedError
    def ship(self, order):    raise NotImplementedError
    def cancel(self, order):  raise NotImplementedError


class PendingState(OrderState):
    def confirm(self, order): order.transition_to(ConfirmedState())
    def ship(self, order):    raise ValueError("Cannot ship a pending order")
    def cancel(self, order):  order.transition_to(CancelledState())


class ConfirmedState(OrderState):
    def confirm(self, order): raise ValueError("Already confirmed")
    def ship(self, order):    order.transition_to(ShippedState())
    def cancel(self, order):  order.transition_to(CancelledState())


class ShippedState(OrderState):
    def confirm(self, order): raise ValueError("Already shipped")
    def ship(self, order):    raise ValueError("Already shipped")
    def cancel(self, order):  raise ValueError("Cannot cancel a shipped order")


class CancelledState(OrderState):
    def confirm(self, order): raise ValueError("Order is cancelled")
    def ship(self, order):    raise ValueError("Order is cancelled")
    def cancel(self, order):  raise ValueError("Already cancelled")


class Order:
    def __init__(self):
        self._state: OrderState = PendingState()

    def transition_to(self, state: OrderState) -> None:
        self._state = state

    def confirm(self): self._state.confirm(self)
    def ship(self):    self._state.ship(self)
    def cancel(self):  self._state.cancel(self)
```

**What to notice:**
- Each state object enforces which transitions are legal, eliminating conditionals in `Order`.
- Adding a new state (e.g., `DeliveredState`) is an additive change — existing state classes are untouched.
- The host object delegates every action to the current state and holds no branching logic of its own.

---

## Factory Method

A base class defines the creation step; subclasses decide which concrete type to instantiate. Callers work with the returned object through a shared interface.

```python
from abc import ABC, abstractmethod


class Notification(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> None: ...


class EmailNotification(Notification):
    def send(self, recipient: str, message: str) -> None:
        print(f"Email to {recipient}: {message}")


class SmsNotification(Notification):
    def send(self, recipient: str, message: str) -> None:
        print(f"SMS to {recipient}: {message}")


class NotificationSender(ABC):
    @abstractmethod
    def _create_notification(self) -> Notification: ...

    def notify(self, recipient: str, message: str) -> None:
        self._create_notification().send(recipient, message)


class EmailSender(NotificationSender):
    def _create_notification(self) -> Notification:
        return EmailNotification()


class SmsSender(NotificationSender):
    def _create_notification(self) -> Notification:
        return SmsNotification()
```

**What to notice:**
- The `notify` method in the base class never names a concrete type — construction is fully deferred to subclasses.
- Adding a push notification channel means adding one new subclass pair; the base class is untouched.
- Callers use `NotificationSender` and never know which channel they are talking to.

---

## Decorator

Behavior is layered onto an object without changing its interface or subclassing it. Each decorator wraps the previous one, adding one concern at a time.

```python
class DataExporter:
    def export(self, data: str) -> str:
        raise NotImplementedError


class FileExporter(DataExporter):
    def export(self, data: str) -> str:
        return f"[FILE] {data}"


class CompressionDecorator(DataExporter):
    def __init__(self, inner: DataExporter) -> None:
        self._inner = inner

    def export(self, data: str) -> str:
        return f"[COMPRESSED] {self._inner.export(data)}"


class EncryptionDecorator(DataExporter):
    def __init__(self, inner: DataExporter) -> None:
        self._inner = inner

    def export(self, data: str) -> str:
        return f"[ENCRYPTED] {self._inner.export(data)}"


# Usage
exporter = EncryptionDecorator(CompressionDecorator(FileExporter()))
print(exporter.export("report"))
# [ENCRYPTED] [COMPRESSED] [FILE] report
```

**What to notice:**
- Every decorator shares the same interface as the object it wraps, so they are interchangeable from the caller's perspective.
- Layers compose at construction time — order matters and is explicit.
- Neither `FileExporter` nor any decorator changes when a new concern (e.g., logging) is added.

---

## Observer

An object (Subject) maintains a list of listeners and notifies them automatically when its state changes. Listeners and Subject are decoupled — neither knows the concrete type of the other.

```python
from dataclasses import dataclass
from typing import Protocol


@dataclass
class UserRegisteredEvent:
    user_id: str
    email: str


class EventListener(Protocol):
    def on_user_registered(self, event: UserRegisteredEvent) -> None: ...


class Logger:
    def on_user_registered(self, event: UserRegisteredEvent) -> None:
        print(f"[LOG] User registered: {event.user_id}")


class WelcomeEmailSender:
    def on_user_registered(self, event: UserRegisteredEvent) -> None:
        print(f"[EMAIL] Welcome email sent to {event.email}")


class UserService:
    def __init__(self) -> None:
        self._listeners: list[EventListener] = []

    def subscribe(self, listener: EventListener) -> None:
        self._listeners.append(listener)

    def register(self, user_id: str, email: str) -> None:
        # ... persist the user ...
        event = UserRegisteredEvent(user_id, email)
        for listener in self._listeners:
            listener.on_user_registered(event)
```

**What to notice:**
- `UserService` depends only on the `EventListener` protocol — it has no knowledge of `Logger` or `WelcomeEmailSender`.
- New reactions to user registration are added by writing a new listener and calling `subscribe`; `UserService` is not touched.
- The event object carries all the data listeners need, keeping the notification call-site clean.
