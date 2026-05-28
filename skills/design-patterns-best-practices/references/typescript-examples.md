# TypeScript Examples

Pattern examples in TypeScript. Each section shows one design pattern using the same domain scenario as the other language files.

## Strategy

A small role interface isolates the variation. The host class depends on the role, not on concrete branching logic.

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

**What to notice:**
- The variation is isolated behind a small role.
- `Invoice` depends on the behavior it needs, not on concrete branching details.
- Adding another tax policy becomes an additive change.

---

## State

An object changes its behavior as it transitions through states. Each state is an object that knows what actions are legal and what the next state should be.

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

**What to notice:**
- Each state object enforces which transitions are legal, eliminating conditionals in `Order`.
- Adding a new state (e.g., `DeliveredState`) is an additive change — existing state classes are untouched.
- The host object delegates every action to the current state and holds no branching logic of its own.

---

## Factory Method

A base class defines the creation step; subclasses decide which concrete type to instantiate. Callers work with the returned object through a shared interface.

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

**What to notice:**
- The `notify` method in the base class never names a concrete type — construction is fully deferred to subclasses.
- Adding a push notification channel means adding one new subclass pair; the base class is untouched.
- Callers use `NotificationSender` and never know which channel they are talking to.

---

## Decorator

Behavior is layered onto an object without changing its interface or subclassing it. Each decorator wraps the previous one, adding one concern at a time.

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

**What to notice:**
- Every decorator implements the same interface as the object it wraps, so they are interchangeable from the caller's perspective.
- Layers compose at construction time — order matters and is explicit.
- Neither `FileExporter` nor any decorator changes when a new concern (e.g., logging) is added.

---

## Observer

An object (Subject) maintains a list of listeners and notifies them automatically when its state changes. Listeners and Subject are decoupled — neither knows the concrete type of the other.

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

**What to notice:**
- `UserService` depends only on the `EventListener` interface — it has no knowledge of `Logger` or `WelcomeEmailSender`.
- New reactions to user registration are added by writing a new listener and calling `subscribe`; `UserService` is not touched.
- The event object carries all the data listeners need, keeping the notification call-site clean.
