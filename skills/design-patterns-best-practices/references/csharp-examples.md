# C# Examples

Pattern examples in C#. Each section shows one design pattern using the same domain scenario as the other language files.

## Strategy

A small role interface isolates the variation. The host class depends on the role, not on concrete branching logic.

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

**What to notice:**
- The variation is isolated behind a small role.
- `Invoice` depends on the behavior it needs, not on concrete branching details.
- Adding another tax policy becomes an additive change.

---

## State

An object changes its behavior as it transitions through states. Each state is an object that knows what actions are legal and what the next state should be.

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

**What to notice:**
- Each state object enforces which transitions are legal, eliminating conditionals in `Order`.
- Adding a new state (e.g., `DeliveredState`) is an additive change — existing state classes are untouched.
- The host object delegates every action to the current state and holds no branching logic of its own.

---

## Factory Method

A base class defines the creation step; subclasses decide which concrete type to instantiate. Callers work with the returned object through a shared interface.

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

**What to notice:**
- The `Notify` method in the base class never names a concrete type — construction is fully deferred to subclasses.
- Adding a push notification channel means adding one new subclass pair; the base class is untouched.
- Callers use `NotificationSender` and never know which channel they are talking to.

---

## Decorator

Behavior is layered onto an object without changing its interface or subclassing it. Each decorator wraps the previous one, adding one concern at a time.

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

**What to notice:**
- Every decorator implements the same interface as the object it wraps, so they are interchangeable from the caller's perspective.
- Layers compose at construction time — order matters and is explicit.
- Neither `FileExporter` nor any decorator changes when a new concern (e.g., logging) is added.

---

## Observer

An object (Subject) maintains a list of listeners and notifies them automatically when its state changes. Listeners and Subject are decoupled — neither knows the concrete type of the other.

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

**What to notice:**
- `UserService` depends only on the `IEventListener` interface — it has no knowledge of `Logger` or `WelcomeEmailSender`.
- New reactions to user registration are added by writing a new listener and calling `Subscribe`; `UserService` is not touched.
- The event object carries all the data listeners need, keeping the notification call-site clean.
