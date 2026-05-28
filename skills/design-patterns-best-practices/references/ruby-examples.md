# Ruby Examples

Pattern examples in Ruby. Each section shows one design pattern using the same domain scenario as the other language files.

## Strategy

A small role interface isolates the variation. The host class depends on the role, not on concrete branching logic.

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

**What to notice:**
- The variation is isolated behind a duck-typed role — no explicit interface declaration needed.
- `Invoice` depends on the behavior it needs, not on concrete branching details.
- Adding another tax policy becomes an additive change.

---

## State

An object changes its behavior as it transitions through states. Each state is an object that knows what actions are legal and what the next state should be.

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

**What to notice:**
- Each state object enforces which transitions are legal, eliminating conditionals in `Order`.
- Adding a new state (e.g., `DeliveredState`) is an additive change — existing state classes are untouched.
- The host object delegates every action to the current state and holds no branching logic of its own.

---

## Factory Method

A base class defines the creation step; subclasses decide which concrete type to instantiate. Callers work with the returned object through a shared duck-typed interface.

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

**What to notice:**
- The `notify` method in the base class never names a concrete type — construction is fully deferred to subclasses.
- Adding a push notification channel means adding one new subclass pair; the base class is untouched.
- Callers use `NotificationSender` and never know which channel they are talking to.

---

## Decorator

Behavior is layered onto an object without changing its interface or subclassing it. Each decorator wraps the previous one, adding one concern at a time.

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

**What to notice:**
- Every decorator responds to the same `export` message as the object it wraps — duck typing makes this natural in Ruby.
- Layers compose at construction time — order matters and is explicit.
- Neither `FileExporter` nor any decorator changes when a new concern (e.g., logging) is added.

---

## Observer

An object (Subject) maintains a list of listeners and notifies them automatically when its state changes. Listeners and Subject are decoupled — neither knows the concrete type of the other.

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

**What to notice:**
- `UserService` depends on duck-typed listeners — it has no knowledge of `Logger` or `WelcomeEmailSender`.
- New reactions to user registration are added by writing a new listener and calling `subscribe`; `UserService` is not touched.
- The event object carries all the data listeners need, keeping the notification call-site clean.
