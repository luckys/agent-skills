# PHP Examples

Pattern examples in PHP. Each section shows one design pattern using the same domain scenario as the other language files.

## Strategy

A small role interface isolates the variation. The host class depends on the role, not on concrete branching logic.

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

**What to notice:**
- The variation is isolated behind a small role.
- `Invoice` depends on the behavior it needs, not on concrete branching details.
- Adding another tax policy becomes an additive change.

---

## State

An object changes its behavior as it transitions through states. Each state is an object that knows what actions are legal and what the next state should be.

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

**What to notice:**
- Each state object enforces which transitions are legal, eliminating conditionals in `Order`.
- Adding a new state (e.g., `DeliveredState`) is an additive change — existing state classes are untouched.
- The host object delegates every action to the current state and holds no branching logic of its own.

---

## Factory Method

A base class defines the creation step; subclasses decide which concrete type to instantiate. Callers work with the returned object through a shared interface.

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

**What to notice:**
- The `notify` method in the base class never names a concrete type — construction is fully deferred to subclasses.
- Adding a push notification channel means adding one new subclass pair; the base class is untouched.
- Callers use `NotificationSender` and never know which channel they are talking to.

---

## Decorator

Behavior is layered onto an object without changing its interface or subclassing it. Each decorator wraps the previous one, adding one concern at a time.

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

**What to notice:**
- Every decorator implements the same interface as the object it wraps, so they are interchangeable from the caller's perspective.
- Layers compose at construction time — order matters and is explicit.
- Neither `FileExporter` nor any decorator changes when a new concern (e.g., logging) is added.

---

## Observer

An object (Subject) maintains a list of listeners and notifies them automatically when its state changes. Listeners and Subject are decoupled — neither knows the concrete type of the other.

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

**What to notice:**
- `UserService` depends only on the `EventListener` interface — it has no knowledge of `Logger` or `WelcomeEmailSender`.
- New reactions to user registration are added by writing a new listener and calling `subscribe`; `UserService` is not touched.
- The event object carries all the data listeners need, keeping the notification call-site clean.
