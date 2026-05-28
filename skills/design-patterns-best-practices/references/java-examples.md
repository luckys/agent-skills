# Java Examples

Pattern examples in Java. Each section shows one design pattern using the same domain scenario as the other language files.

## Strategy

A small role interface isolates the variation. The host class depends on the role, not on concrete branching logic.

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

**What to notice:**
- The variation is isolated behind a small role.
- `Invoice` depends on the behavior it needs, not on concrete branching details.
- Adding another tax policy becomes an additive change.

---

## State

An object changes its behavior as it transitions through states. Each state is an object that knows what actions are legal and what the next state should be.

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

**What to notice:**
- Each state object enforces which transitions are legal, eliminating conditionals in `Order`.
- Adding a new state (e.g., `DeliveredState`) is an additive change — existing state classes are untouched.
- The host object delegates every action to the current state and holds no branching logic of its own.

---

## Factory Method

A base class defines the creation step; subclasses decide which concrete type to instantiate. Callers work with the returned object through a shared interface.

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

**What to notice:**
- The `notify` method in the base class never names a concrete type — construction is fully deferred to subclasses.
- Adding a push notification channel means adding one new subclass pair; the base class is untouched.
- Callers use `NotificationSender` and never know which channel they are talking to.

---

## Decorator

Behavior is layered onto an object without changing its interface or subclassing it. Each decorator wraps the previous one, adding one concern at a time.

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

**What to notice:**
- Every decorator implements the same interface as the object it wraps, so they are interchangeable from the caller's perspective.
- Layers compose at construction time — order matters and is explicit.
- Neither `FileExporter` nor any decorator changes when a new concern (e.g., logging) is added.

---

## Observer

An object (Subject) maintains a list of listeners and notifies them automatically when its state changes. Listeners and Subject are decoupled — neither knows the concrete type of the other.

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

**What to notice:**
- `UserService` depends only on the `EventListener` interface — it has no knowledge of `Logger` or `WelcomeEmailSender`.
- New reactions to user registration are added by writing a new listener and calling `subscribe`; `UserService` is not touched.
- The event object carries all the data listeners need, keeping the notification call-site clean.
