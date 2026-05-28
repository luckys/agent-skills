# Language Examples

These examples cover five common patterns — Strategy, State, Factory Method, Decorator, and Observer — each shown in TypeScript, Java, Python, C#, Ruby, and PHP using the same domain scenario across all six languages.

## Strategy

A small role interface isolates the variation. The host class depends on the role, not on concrete branching logic.

### TypeScript

```typescript
interface TaxPolicy {
  calculate(subtotalInCents: number): number
}

class StandardTaxPolicy implements TaxPolicy {
  calculate(subtotalInCents: number): number {
    return Math.round(subtotalInCents * 0.21)
  }
}

class ReducedTaxPolicy implements TaxPolicy {
  calculate(subtotalInCents: number): number {
    return Math.round(subtotalInCents * 0.1)
  }
}

class Invoice {
  constructor(private readonly taxPolicy: TaxPolicy) {}

  tax(subtotalInCents: number): number {
    return this.taxPolicy.calculate(subtotalInCents)
  }
}
```

### Java

```java
public interface TaxPolicy {
    int calculate(int subtotalInCents);
}

public final class StandardTaxPolicy implements TaxPolicy {
    public int calculate(int subtotalInCents) {
        return Math.round(subtotalInCents * 0.21f);
    }
}

public final class Invoice {
    private final TaxPolicy taxPolicy;

    public Invoice(TaxPolicy taxPolicy) {
        this.taxPolicy = taxPolicy;
    }

    public int tax(int subtotalInCents) {
        return taxPolicy.calculate(subtotalInCents);
    }
}
```

### Python

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

### C#

```csharp
public interface ITaxPolicy
{
    int Calculate(int subtotalInCents);
}

public sealed class StandardTaxPolicy : ITaxPolicy
{
    public int Calculate(int subtotalInCents)
    {
        return (int)Math.Round(subtotalInCents * 0.21);
    }
}

public sealed class Invoice
{
    private readonly ITaxPolicy taxPolicy;

    public Invoice(ITaxPolicy taxPolicy)
    {
        this.taxPolicy = taxPolicy;
    }

    public int Tax(int subtotalInCents)
    {
        return taxPolicy.Calculate(subtotalInCents);
    }
}
```

### Ruby

```ruby
class StandardTaxPolicy
  def calculate(subtotal_in_cents)
    (subtotal_in_cents * 0.21).round
  end
end

class Invoice
  def initialize(tax_policy)
    @tax_policy = tax_policy
  end

  def tax(subtotal_in_cents)
    @tax_policy.calculate(subtotal_in_cents)
  end
end
```

### PHP

```php
interface TaxPolicy
{
    public function calculate(int $subtotalInCents): int;
}

final class StandardTaxPolicy implements TaxPolicy
{
    public function calculate(int $subtotalInCents): int
    {
        return (int) round($subtotalInCents * 0.21);
    }
}

final class Invoice
{
    public function __construct(private TaxPolicy $taxPolicy)
    {
    }

    public function tax(int $subtotalInCents): int
    {
        return $this->taxPolicy->calculate($subtotalInCents);
    }
}
```

### What to Notice

- The variation is isolated behind a small role.
- `Invoice` depends on the behavior it needs, not on concrete branching details.
- Adding another tax policy becomes an additive change.

---

## State

An object changes its behavior as it transitions through states. Each state is an object that knows what actions are legal and what the next state should be.

### TypeScript

```typescript
interface OrderState {
  confirm(order: Order): void
  ship(order: Order): void
  cancel(order: Order): void
}

class PendingState implements OrderState {
  confirm(order: Order) { order.transitionTo(new ConfirmedState()) }
  ship(_order: Order) { throw new Error('Cannot ship a pending order') }
  cancel(order: Order) { order.transitionTo(new CancelledState()) }
}

class ConfirmedState implements OrderState {
  confirm(_order: Order) { throw new Error('Already confirmed') }
  ship(order: Order) { order.transitionTo(new ShippedState()) }
  cancel(order: Order) { order.transitionTo(new CancelledState()) }
}

class ShippedState implements OrderState {
  confirm(_order: Order) { throw new Error('Already shipped') }
  ship(_order: Order) { throw new Error('Already shipped') }
  cancel(_order: Order) { throw new Error('Cannot cancel a shipped order') }
}

class CancelledState implements OrderState {
  confirm(_order: Order) { throw new Error('Order is cancelled') }
  ship(_order: Order) { throw new Error('Order is cancelled') }
  cancel(_order: Order) { throw new Error('Already cancelled') }
}

class Order {
  private state: OrderState = new PendingState()

  transitionTo(state: OrderState) { this.state = state }
  confirm() { this.state.confirm(this) }
  ship()    { this.state.ship(this) }
  cancel()  { this.state.cancel(this) }
}
```

### Java

```java
public interface OrderState {
    void confirm(Order order);
    void ship(Order order);
    void cancel(Order order);
}

public final class PendingState implements OrderState {
    public void confirm(Order order) { order.transitionTo(new ConfirmedState()); }
    public void ship(Order order)    { throw new IllegalStateException("Cannot ship a pending order"); }
    public void cancel(Order order)  { order.transitionTo(new CancelledState()); }
}

public final class ConfirmedState implements OrderState {
    public void confirm(Order order) { throw new IllegalStateException("Already confirmed"); }
    public void ship(Order order)    { order.transitionTo(new ShippedState()); }
    public void cancel(Order order)  { order.transitionTo(new CancelledState()); }
}

public final class ShippedState implements OrderState {
    public void confirm(Order order) { throw new IllegalStateException("Already shipped"); }
    public void ship(Order order)    { throw new IllegalStateException("Already shipped"); }
    public void cancel(Order order)  { throw new IllegalStateException("Cannot cancel a shipped order"); }
}

public final class Order {
    private OrderState state = new PendingState();

    public void transitionTo(OrderState state) { this.state = state; }
    public void confirm() { state.confirm(this); }
    public void ship()    { state.ship(this); }
    public void cancel()  { state.cancel(this); }
}
```

### Python

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

### C#

```csharp
public interface IOrderState
{
    void Confirm(Order order);
    void Ship(Order order);
    void Cancel(Order order);
}

public sealed class PendingState : IOrderState
{
    public void Confirm(Order order) => order.TransitionTo(new ConfirmedState());
    public void Ship(Order order)    => throw new InvalidOperationException("Cannot ship a pending order");
    public void Cancel(Order order)  => order.TransitionTo(new CancelledState());
}

public sealed class ConfirmedState : IOrderState
{
    public void Confirm(Order order) => throw new InvalidOperationException("Already confirmed");
    public void Ship(Order order)    => order.TransitionTo(new ShippedState());
    public void Cancel(Order order)  => order.TransitionTo(new CancelledState());
}

public sealed class ShippedState : IOrderState
{
    public void Confirm(Order order) => throw new InvalidOperationException("Already shipped");
    public void Ship(Order order)    => throw new InvalidOperationException("Already shipped");
    public void Cancel(Order order)  => throw new InvalidOperationException("Cannot cancel a shipped order");
}

public sealed class Order
{
    private IOrderState state = new PendingState();

    public void TransitionTo(IOrderState state) => this.state = state;
    public void Confirm() => state.Confirm(this);
    public void Ship()    => state.Ship(this);
    public void Cancel()  => state.Cancel(this);
}
```

### Ruby

```ruby
class PendingState
  def confirm(order) = order.transition_to(ConfirmedState.new)
  def ship(order)    = raise("Cannot ship a pending order")
  def cancel(order)  = order.transition_to(CancelledState.new)
end

class ConfirmedState
  def confirm(order) = raise("Already confirmed")
  def ship(order)    = order.transition_to(ShippedState.new)
  def cancel(order)  = order.transition_to(CancelledState.new)
end

class ShippedState
  def confirm(order) = raise("Already shipped")
  def ship(order)    = raise("Already shipped")
  def cancel(order)  = raise("Cannot cancel a shipped order")
end

class CancelledState
  def confirm(order) = raise("Order is cancelled")
  def ship(order)    = raise("Order is cancelled")
  def cancel(order)  = raise("Already cancelled")
end

class Order
  def initialize
    @state = PendingState.new
  end

  def transition_to(state) = @state = state
  def confirm = @state.confirm(self)
  def ship    = @state.ship(self)
  def cancel  = @state.cancel(self)
end
```

### PHP

```php
interface OrderState
{
    public function confirm(Order $order): void;
    public function ship(Order $order): void;
    public function cancel(Order $order): void;
}

final class PendingState implements OrderState
{
    public function confirm(Order $order): void { $order->transitionTo(new ConfirmedState()); }
    public function ship(Order $order): void    { throw new \LogicException('Cannot ship a pending order'); }
    public function cancel(Order $order): void  { $order->transitionTo(new CancelledState()); }
}

final class ConfirmedState implements OrderState
{
    public function confirm(Order $order): void { throw new \LogicException('Already confirmed'); }
    public function ship(Order $order): void    { $order->transitionTo(new ShippedState()); }
    public function cancel(Order $order): void  { $order->transitionTo(new CancelledState()); }
}

final class ShippedState implements OrderState
{
    public function confirm(Order $order): void { throw new \LogicException('Already shipped'); }
    public function ship(Order $order): void    { throw new \LogicException('Already shipped'); }
    public function cancel(Order $order): void  { throw new \LogicException('Cannot cancel a shipped order'); }
}

final class Order
{
    private OrderState $state;

    public function __construct() { $this->state = new PendingState(); }

    public function transitionTo(OrderState $state): void { $this->state = $state; }
    public function confirm(): void { $this->state->confirm($this); }
    public function ship(): void    { $this->state->ship($this); }
    public function cancel(): void  { $this->state->cancel($this); }
}
```

### What to Notice

- Each state object enforces which transitions are legal, eliminating conditionals in `Order`.
- Adding a new state (e.g., `DeliveredState`) is an additive change — existing state classes are untouched.
- The host object (`Order`) delegates every action to the current state and holds no branching logic of its own.

---

## Factory Method

A base class defines the creation step; subclasses decide which concrete type to instantiate. Callers work with the returned object through a shared interface.

### TypeScript

```typescript
interface Notification {
  send(recipient: string, message: string): void
}

class EmailNotification implements Notification {
  send(recipient: string, message: string) {
    console.log(`Email to ${recipient}: ${message}`)
  }
}

class SmsNotification implements Notification {
  send(recipient: string, message: string) {
    console.log(`SMS to ${recipient}: ${message}`)
  }
}

abstract class NotificationSender {
  protected abstract createNotification(): Notification

  notify(recipient: string, message: string): void {
    const notification = this.createNotification()
    notification.send(recipient, message)
  }
}

class EmailSender extends NotificationSender {
  protected createNotification(): Notification {
    return new EmailNotification()
  }
}

class SmsSender extends NotificationSender {
  protected createNotification(): Notification {
    return new SmsNotification()
  }
}
```

### Java

```java
public interface Notification {
    void send(String recipient, String message);
}

public final class EmailNotification implements Notification {
    public void send(String recipient, String message) {
        System.out.printf("Email to %s: %s%n", recipient, message);
    }
}

public final class SmsNotification implements Notification {
    public void send(String recipient, String message) {
        System.out.printf("SMS to %s: %s%n", recipient, message);
    }
}

public abstract class NotificationSender {
    protected abstract Notification createNotification();

    public void notify(String recipient, String message) {
        createNotification().send(recipient, message);
    }
}

public final class EmailSender extends NotificationSender {
    protected Notification createNotification() { return new EmailNotification(); }
}

public final class SmsSender extends NotificationSender {
    protected Notification createNotification() { return new SmsNotification(); }
}
```

### Python

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

### C#

```csharp
public interface INotification
{
    void Send(string recipient, string message);
}

public sealed class EmailNotification : INotification
{
    public void Send(string recipient, string message) =>
        Console.WriteLine($"Email to {recipient}: {message}");
}

public sealed class SmsNotification : INotification
{
    public void Send(string recipient, string message) =>
        Console.WriteLine($"SMS to {recipient}: {message}");
}

public abstract class NotificationSender
{
    protected abstract INotification CreateNotification();

    public void Notify(string recipient, string message) =>
        CreateNotification().Send(recipient, message);
}

public sealed class EmailSender : NotificationSender
{
    protected override INotification CreateNotification() => new EmailNotification();
}

public sealed class SmsSender : NotificationSender
{
    protected override INotification CreateNotification() => new SmsNotification();
}
```

### Ruby

```ruby
class EmailNotification
  def send(recipient, message)
    puts "Email to #{recipient}: #{message}"
  end
end

class SmsNotification
  def send(recipient, message)
    puts "SMS to #{recipient}: #{message}"
  end
end

class NotificationSender
  def notify(recipient, message)
    create_notification.send(recipient, message)
  end

  private

  def create_notification
    raise NotImplementedError
  end
end

class EmailSender < NotificationSender
  private
  def create_notification = EmailNotification.new
end

class SmsSender < NotificationSender
  private
  def create_notification = SmsNotification.new
end
```

### PHP

```php
interface Notification
{
    public function send(string $recipient, string $message): void;
}

final class EmailNotification implements Notification
{
    public function send(string $recipient, string $message): void
    {
        echo "Email to {$recipient}: {$message}\n";
    }
}

final class SmsNotification implements Notification
{
    public function send(string $recipient, string $message): void
    {
        echo "SMS to {$recipient}: {$message}\n";
    }
}

abstract class NotificationSender
{
    abstract protected function createNotification(): Notification;

    public function notify(string $recipient, string $message): void
    {
        $this->createNotification()->send($recipient, $message);
    }
}

final class EmailSender extends NotificationSender
{
    protected function createNotification(): Notification
    {
        return new EmailNotification();
    }
}

final class SmsSender extends NotificationSender
{
    protected function createNotification(): Notification
    {
        return new SmsNotification();
    }
}
```

### What to Notice

- The `notify` method in the base class never names a concrete type — construction is fully deferred to subclasses.
- Adding a push notification channel means adding one new subclass pair; the base class is untouched.
- Callers use `NotificationSender` and never know which channel they are talking to.

---

## Decorator

Behavior is layered onto an object without changing its interface or subclassing it. Each decorator wraps the previous one, adding one concern at a time.

### TypeScript

```typescript
interface DataExporter {
  export(data: string): string
}

class FileExporter implements DataExporter {
  export(data: string): string {
    return `[FILE] ${data}`
  }
}

class CompressionDecorator implements DataExporter {
  constructor(private readonly inner: DataExporter) {}

  export(data: string): string {
    const exported = this.inner.export(data)
    return `[COMPRESSED] ${exported}`
  }
}

class EncryptionDecorator implements DataExporter {
  constructor(private readonly inner: DataExporter) {}

  export(data: string): string {
    const exported = this.inner.export(data)
    return `[ENCRYPTED] ${exported}`
  }
}

// Usage: encrypt(compress(file))
const exporter: DataExporter =
  new EncryptionDecorator(new CompressionDecorator(new FileExporter()))

console.log(exporter.export('report'))
// [ENCRYPTED] [COMPRESSED] [FILE] report
```

### Java

```java
public interface DataExporter {
    String export(String data);
}

public final class FileExporter implements DataExporter {
    public String export(String data) { return "[FILE] " + data; }
}

public final class CompressionDecorator implements DataExporter {
    private final DataExporter inner;
    public CompressionDecorator(DataExporter inner) { this.inner = inner; }

    public String export(String data) {
        return "[COMPRESSED] " + inner.export(data);
    }
}

public final class EncryptionDecorator implements DataExporter {
    private final DataExporter inner;
    public EncryptionDecorator(DataExporter inner) { this.inner = inner; }

    public String export(String data) {
        return "[ENCRYPTED] " + inner.export(data);
    }
}

// Usage
DataExporter exporter = new EncryptionDecorator(new CompressionDecorator(new FileExporter()));
System.out.println(exporter.export("report"));
// [ENCRYPTED] [COMPRESSED] [FILE] report
```

### Python

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

### C#

```csharp
public interface IDataExporter
{
    string Export(string data);
}

public sealed class FileExporter : IDataExporter
{
    public string Export(string data) => $"[FILE] {data}";
}

public sealed class CompressionDecorator : IDataExporter
{
    private readonly IDataExporter inner;
    public CompressionDecorator(IDataExporter inner) => this.inner = inner;

    public string Export(string data) => $"[COMPRESSED] {inner.Export(data)}";
}

public sealed class EncryptionDecorator : IDataExporter
{
    private readonly IDataExporter inner;
    public EncryptionDecorator(IDataExporter inner) => this.inner = inner;

    public string Export(string data) => $"[ENCRYPTED] {inner.Export(data)}";
}

// Usage
IDataExporter exporter = new EncryptionDecorator(new CompressionDecorator(new FileExporter()));
Console.WriteLine(exporter.Export("report"));
// [ENCRYPTED] [COMPRESSED] [FILE] report
```

### Ruby

```ruby
class FileExporter
  def export(data)
    "[FILE] #{data}"
  end
end

class CompressionDecorator
  def initialize(inner)
    @inner = inner
  end

  def export(data)
    "[COMPRESSED] #{@inner.export(data)}"
  end
end

class EncryptionDecorator
  def initialize(inner)
    @inner = inner
  end

  def export(data)
    "[ENCRYPTED] #{@inner.export(data)}"
  end
end

# Usage
exporter = EncryptionDecorator.new(CompressionDecorator.new(FileExporter.new))
puts exporter.export("report")
# [ENCRYPTED] [COMPRESSED] [FILE] report
```

### PHP

```php
interface DataExporter
{
    public function export(string $data): string;
}

final class FileExporter implements DataExporter
{
    public function export(string $data): string { return "[FILE] {$data}"; }
}

final class CompressionDecorator implements DataExporter
{
    public function __construct(private DataExporter $inner) {}

    public function export(string $data): string
    {
        return "[COMPRESSED] " . $this->inner->export($data);
    }
}

final class EncryptionDecorator implements DataExporter
{
    public function __construct(private DataExporter $inner) {}

    public function export(string $data): string
    {
        return "[ENCRYPTED] " . $this->inner->export($data);
    }
}

// Usage
$exporter = new EncryptionDecorator(new CompressionDecorator(new FileExporter()));
echo $exporter->export("report");
// [ENCRYPTED] [COMPRESSED] [FILE] report
```

### What to Notice

- Every decorator implements the same interface as the object it wraps, so they are interchangeable from the caller's perspective.
- Layers compose at construction time — order matters and is explicit.
- Neither `FileExporter` nor any decorator changes when a new concern (e.g., logging) is added.

---

## Observer

An object (Subject) maintains a list of listeners and notifies them automatically when its state changes. Listeners and Subject are decoupled — neither knows the concrete type of the other.

### TypeScript

```typescript
interface UserRegisteredEvent {
  userId: string
  email: string
}

interface EventListener {
  onUserRegistered(event: UserRegisteredEvent): void
}

class Logger implements EventListener {
  onUserRegistered(event: UserRegisteredEvent) {
    console.log(`[LOG] User registered: ${event.userId}`)
  }
}

class WelcomeEmailSender implements EventListener {
  onUserRegistered(event: UserRegisteredEvent) {
    console.log(`[EMAIL] Welcome email sent to ${event.email}`)
  }
}

class UserService {
  private listeners: EventListener[] = []

  subscribe(listener: EventListener): void {
    this.listeners.push(listener)
  }

  register(userId: string, email: string): void {
    // ... persist the user ...
    const event: UserRegisteredEvent = { userId, email }
    this.listeners.forEach(l => l.onUserRegistered(event))
  }
}
```

### Java

```java
public record UserRegisteredEvent(String userId, String email) {}

public interface EventListener {
    void onUserRegistered(UserRegisteredEvent event);
}

public final class Logger implements EventListener {
    public void onUserRegistered(UserRegisteredEvent event) {
        System.out.println("[LOG] User registered: " + event.userId());
    }
}

public final class WelcomeEmailSender implements EventListener {
    public void onUserRegistered(UserRegisteredEvent event) {
        System.out.println("[EMAIL] Welcome email sent to " + event.email());
    }
}

public final class UserService {
    private final List<EventListener> listeners = new ArrayList<>();

    public void subscribe(EventListener listener) { listeners.add(listener); }

    public void register(String userId, String email) {
        // ... persist the user ...
        UserRegisteredEvent event = new UserRegisteredEvent(userId, email);
        listeners.forEach(l -> l.onUserRegistered(event));
    }
}
```

### Python

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

### C#

```csharp
public sealed record UserRegisteredEvent(string UserId, string Email);

public interface IEventListener
{
    void OnUserRegistered(UserRegisteredEvent @event);
}

public sealed class Logger : IEventListener
{
    public void OnUserRegistered(UserRegisteredEvent @event) =>
        Console.WriteLine($"[LOG] User registered: {@event.UserId}");
}

public sealed class WelcomeEmailSender : IEventListener
{
    public void OnUserRegistered(UserRegisteredEvent @event) =>
        Console.WriteLine($"[EMAIL] Welcome email sent to {@event.Email}");
}

public sealed class UserService
{
    private readonly List<IEventListener> listeners = new();

    public void Subscribe(IEventListener listener) => listeners.Add(listener);

    public void Register(string userId, string email)
    {
        // ... persist the user ...
        var @event = new UserRegisteredEvent(userId, email);
        foreach (var listener in listeners) listener.OnUserRegistered(@event);
    }
}
```

### Ruby

```ruby
UserRegisteredEvent = Data.define(:user_id, :email)

class Logger
  def on_user_registered(event)
    puts "[LOG] User registered: #{event.user_id}"
  end
end

class WelcomeEmailSender
  def on_user_registered(event)
    puts "[EMAIL] Welcome email sent to #{event.email}"
  end
end

class UserService
  def initialize
    @listeners = []
  end

  def subscribe(listener)
    @listeners << listener
  end

  def register(user_id, email)
    # ... persist the user ...
    event = UserRegisteredEvent.new(user_id: user_id, email: email)
    @listeners.each { |l| l.on_user_registered(event) }
  end
end
```

### PHP

```php
final class UserRegisteredEvent
{
    public function __construct(
        public readonly string $userId,
        public readonly string $email,
    ) {}
}

interface EventListener
{
    public function onUserRegistered(UserRegisteredEvent $event): void;
}

final class Logger implements EventListener
{
    public function onUserRegistered(UserRegisteredEvent $event): void
    {
        echo "[LOG] User registered: {$event->userId}\n";
    }
}

final class WelcomeEmailSender implements EventListener
{
    public function onUserRegistered(UserRegisteredEvent $event): void
    {
        echo "[EMAIL] Welcome email sent to {$event->email}\n";
    }
}

final class UserService
{
    /** @var EventListener[] */
    private array $listeners = [];

    public function subscribe(EventListener $listener): void
    {
        $this->listeners[] = $listener;
    }

    public function register(string $userId, string $email): void
    {
        // ... persist the user ...
        $event = new UserRegisteredEvent($userId, $email);
        foreach ($this->listeners as $listener) {
            $listener->onUserRegistered($event);
        }
    }
}
```

### What to Notice

- `UserService` depends only on the `EventListener` interface — it has no knowledge of `Logger` or `WelcomeEmailSender`.
- New reactions to user registration are added by writing a new listener and calling `subscribe`; the `UserService` is not touched.
- The event object carries all the data listeners need, keeping the notification call-site clean.
