# TypeScript Examples

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

```typescript
class Money {
  constructor(private readonly cents: number) {
    if (cents < 0) {
      throw new Error('Money cannot be negative')
    }
  }

  add(other: Money): Money {
    return new Money(this.cents + other.cents)
  }

  multiplyBy(percent: number): Money {
    return new Money(Math.round(this.cents * percent / 100))
  }

  value(): number {
    return this.cents
  }
}
```

## First-Class Collections

```typescript
class OrderLine {
  constructor(private readonly subtotalAmount: Money) {}

  subtotal(): Money {
    return this.subtotalAmount
  }
}

class OrderLines {
  constructor(private readonly items: OrderLine[]) {}

  total(): Money {
    return this.items.reduce(
      (current, item) => current.add(item.subtotal()),
      new Money(0),
    )
  }

  isEmpty(): boolean {
    return this.items.length === 0
  }
}
```

## Tell, Don't Ask

```typescript
class Address {
  constructor(private readonly countryCodeValue: string) {}

  isDomestic(): boolean {
    return this.countryCodeValue === 'ES'
  }
}

class Shipment {
  constructor(private readonly address: Address) {}

  dispatchWindowInDays(): number {
    return this.address.isDomestic() ? 2 : 5
  }
}
```

## Role-Based Collaboration

```typescript
interface CurrencyFormatter {
  format(amount: Money): string
}

class OrderSummary {
  constructor(private readonly formatter: CurrencyFormatter) {}

  totalLabel(lines: OrderLines): string {
    return this.formatter.format(lines.total())
  }
}
```

## Dependency Injection

```typescript
interface Mailer {
  send(to: string, body: string): void
}

class Invoice {
  constructor(
    private readonly recipient: string,
    private readonly bodyText: string,
  ) {}

  recipientEmail(): string {
    return this.recipient
  }

  body(): string {
    return this.bodyText
  }
}

class InvoiceSender {
  constructor(private readonly mailer: Mailer) {}

  send(invoice: Invoice): void {
    this.mailer.send(invoice.recipientEmail(), invoice.body())
  }
}
```

## Explicit Interfaces

```typescript
interface PaymentGateway {
  charge(customerId: string, amount: Money): void
}

class SubscriptionActivator {
  constructor(private readonly paymentGateway: PaymentGateway) {}

  activate(customerId: string, fee: Money): void {
    this.paymentGateway.charge(customerId, fee)
  }
}
```

## Duck Typing / Protocol-Style Roles

```typescript
type StockSource = {
  availableUnits(): number
}

class InventoryReport {
  constructor(private readonly source: StockSource) {}

  isAvailable(): boolean {
    return this.source.availableUnits() > 0
  }
}

class WarehouseBin {
  constructor(private readonly units: number) {}

  availableUnits(): number {
    return this.units
  }
}
```

## Composition over Inheritance

```typescript
interface DiscountPolicy {
  apply(total: Money): Money
}

interface TaxPolicy {
  apply(total: Money): Money
}

class CartPricing {
  constructor(
    private readonly discountPolicy: DiscountPolicy,
    private readonly taxPolicy: TaxPolicy,
  ) {}

  total(subtotal: Money): Money {
    return this.taxPolicy.apply(this.discountPolicy.apply(subtotal))
  }
}
```

## Message-Based Design

```typescript
interface SeatInventory {
  reserve(seatCount: number): void
}

interface PaymentService {
  charge(amount: Money): void
}

class Booking {
  constructor(
    private readonly seats: number,
    private readonly amount: Money,
    private readonly inventory: SeatInventory,
    private readonly payments: PaymentService,
  ) {}

  confirm(): void {
    this.inventory.reserve(this.seats)
    this.payments.charge(this.amount)
  }
}
```

## Law of Demeter Violation and Fix

### Before

```typescript
class CustomerRecord {
  constructor(private readonly address: Address) {}

  shippingAddress(): Address {
    return this.address
  }
}

class Order {
  constructor(private readonly customer: CustomerRecord) {}

  customerRecord(): CustomerRecord {
    return this.customer
  }
}

const domestic = order.customerRecord().shippingAddress().isDomestic()
```

### After

```typescript
class Customer {
  constructor(private readonly address: Address) {}

  shipsDomestically(): boolean {
    return this.address.isDomestic()
  }
}

class PurchaseOrder {
  constructor(private readonly customer: Customer) {}

  shipsDomestically(): boolean {
    return this.customer.shipsDomestically()
  }
}

const domestic = order.shipsDomestically()
```

## Immutable Objects

```typescript
class Rooms {
  constructor(private readonly items: readonly string[]) {}

  add(room: string): Rooms {
    return new Rooms([...this.items, room])
  }

  count(): number {
    return this.items.length
  }
}
```

## Null Object

```typescript
interface Logger {
  info(message: string): void
}

class NullLogger implements Logger {
  info(_message: string): void {}
}
```

## Anemic versus Rich Model

### Anemic

```typescript
class ScoreData {
  constructor(public value: number) {}
}

function increaseScore(score: ScoreData, points: number): void {
  score.value = score.value + points
}
```

### Rich

```typescript
class Score {
  constructor(private readonly points: number) {}

  increase(extraPoints: number): Score {
    return new Score(this.points + extraPoints)
  }

  value(): number {
    return this.points
  }
}
```

## SOLID — Single Responsibility Violation and Fix

### Before

```typescript
class Report {
  constructor(
    private readonly reportTitle: string,
    private readonly content: string,
  ) {}

  title(): string {
    return this.reportTitle
  }

  save(): void {
    // writing to database — second unrelated responsibility
    database.insert('reports', { title: this.reportTitle, content: this.content })
  }
}
```

### After

```typescript
class Report {
  constructor(
    private readonly reportTitle: string,
    private readonly content: string,
  ) {}

  title(): string {
    return this.reportTitle
  }

  body(): string {
    return this.content
  }
}

class ReportRepository {
  save(report: Report): void {
    database.insert('reports', { title: report.title(), content: report.body() })
  }
}
```

## Object Calisthenics — Wrap Primitive

### Before

```typescript
function applyDiscount(priceInCents: number, discountPercent: number): number {
  if (discountPercent < 0 || discountPercent > 100) {
    throw new Error('Invalid discount')
  }
  return Math.round(priceInCents * (1 - discountPercent / 100))
}
```

### After

```typescript
class Percentage {
  constructor(private readonly value: number) {
    if (value < 0 || value > 100) {
      throw new Error('Percentage must be between 0 and 100')
    }
  }

  of(amount: number): number {
    return Math.round(amount * (this.value / 100))
  }
}

class Price {
  constructor(private readonly cents: number) {}

  applyDiscount(discount: Percentage): Price {
    return new Price(this.cents - discount.of(this.cents))
  }

  value(): number {
    return this.cents
  }
}
```

## Object Calisthenics — No Else Rule

### Before

```typescript
function shippingCost(order: Order): number {
  if (order.isExpress()) {
    return 15
  } else {
    if (order.totalWeight() > 10) {
      return 8
    } else {
      return 3
    }
  }
}
```

### After

```typescript
function shippingCost(order: Order): number {
  if (order.isExpress()) return 15
  if (order.totalWeight() > 10) return 8
  return 3
}
```

## Dependency Direction

### Before

```typescript
class InvoiceExporter {
  export(invoice: Invoice): void {
    const fs = new FileSystem()
    fs.write(`invoices/${invoice.id()}.txt`, invoice.body())
  }
}
```

### After

```typescript
interface DocumentStorage {
  write(path: string, content: string): void
}

class InvoiceExporter {
  constructor(private readonly storage: DocumentStorage) {}

  export(invoice: Invoice): void {
    this.storage.write(`invoices/${invoice.id()}.txt`, invoice.body())
  }
}
```

## Composed Method

### Before

```typescript
class RegistrationService {
  register(email: string, password: string): void {
    if (!email.includes('@')) throw new Error('Invalid email')
    if (password.length < 8) throw new Error('Password too short')
    const hashed = hashPassword(password)
    this.userRepository.save(new User(email, hashed))
    this.mailer.send(email, 'Welcome!')
  }
}
```

### After

```typescript
class RegistrationService {
  register(email: string, password: string): void {
    this.validate(email, password)
    const user = this.buildUser(email, password)
    this.persist(user)
    this.welcome(user)
  }

  private validate(email: string, password: string): void {
    if (!email.includes('@')) throw new Error('Invalid email')
    if (password.length < 8) throw new Error('Password too short')
  }

  private buildUser(email: string, password: string): User {
    return new User(email, hashPassword(password))
  }

  private persist(user: User): void {
    this.userRepository.save(user)
  }

  private welcome(user: User): void {
    this.mailer.send(user.email(), 'Welcome!')
  }
}
```

## What to Notice

- Rich models and clear object responsibilities help keep knowledge close to the concept.
- The same concepts stay recognizable even when the syntax changes.
- Small interfaces and injected collaborators keep dependencies explicit.
- Structural typing lets TypeScript model protocol-style roles without forcing inheritance.
- Composition and message passing keep change local.
- Wrapping primitives and splitting responsibilities keep each class focused on one reason to change.
