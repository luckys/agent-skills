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

---

## Command

Encapsulates a request as an object, letting you parameterize clients with operations and support undoable actions.

```typescript
interface Command {
  execute(): void
  undo(): void
}

class TextEditor {
  private content = ''
  private history: Command[] = []

  applyCommand(cmd: Command): void {
    cmd.execute()
    this.history.push(cmd)
  }

  undoLast(): void {
    this.history.pop()?.undo()
  }

  getContent(): string { return this.content }
  setContent(value: string): void { this.content = value }
}

class BoldCommand implements Command {
  private previous = ''
  constructor(private readonly editor: TextEditor) {}

  execute(): void {
    this.previous = this.editor.getContent()
    this.editor.setContent(`**${this.previous}**`)
  }
  undo(): void { this.editor.setContent(this.previous) }
}

class ItalicCommand implements Command {
  private previous = ''
  constructor(private readonly editor: TextEditor) {}

  execute(): void {
    this.previous = this.editor.getContent()
    this.editor.setContent(`_${this.previous}_`)
  }
  undo(): void { this.editor.setContent(this.previous) }
}
```

**What to notice:**
- Each command stores enough state to reverse itself — the editor holds no undo logic.
- The editor's `applyCommand` method is closed to modification: new operations are new classes, not new branches.
- Sender and executor are fully decoupled — the editor never knows which concrete command it runs.

---

## Template Method

Defines an algorithm's skeleton in a base class while letting subclasses override specific steps without changing the overall structure.

```typescript
abstract class ReportGenerator {
  // Template method — the skeleton
  generate(): void {
    const data = this.gatherData()
    const formatted = this.formatData(data)
    this.output(formatted)
  }

  private gatherData(): string[] {
    return ['row1', 'row2', 'row3']
  }

  protected abstract formatData(data: string[]): string

  private output(content: string): void {
    console.log(content)
  }
}

class CsvReportGenerator extends ReportGenerator {
  protected formatData(data: string[]): string {
    return data.join(',')
  }
}

class PdfReportGenerator extends ReportGenerator {
  protected formatData(data: string[]): string {
    return data.map(row => `<p>${row}</p>`).join('\n')
  }
}
```

**What to notice:**
- The invariant steps (`gatherData`, `output`) live once in the base class and are never duplicated.
- Subclasses provide only the variant step (`formatData`), keeping each class small and focused.
- Adding a new format (e.g., JSON) means adding one subclass without touching the base or siblings.

---

## Chain of Responsibility

Passes a request along a chain of handlers; each handler decides to process it or forward it to the next.

```typescript
interface HttpRequest { path: string; token?: string }
interface HttpResponse { status: number; body: string }

abstract class Middleware {
  private next?: Middleware

  setNext(middleware: Middleware): Middleware {
    this.next = middleware
    return middleware
  }

  protected forward(req: HttpRequest): HttpResponse {
    return this.next
      ? this.next.handle(req)
      : { status: 200, body: 'OK' }
  }

  abstract handle(req: HttpRequest): HttpResponse
}

class AuthMiddleware extends Middleware {
  handle(req: HttpRequest): HttpResponse {
    if (!req.token) return { status: 401, body: 'Unauthorized' }
    return this.forward(req)
  }
}

class LoggingMiddleware extends Middleware {
  handle(req: HttpRequest): HttpResponse {
    console.log(`[LOG] ${req.path}`)
    return this.forward(req)
  }
}

// Wiring: auth → logging → handler
const auth = new AuthMiddleware()
auth.setNext(new LoggingMiddleware())
```

**What to notice:**
- Each middleware is unaware of what comes before or after it in the chain.
- The chain is assembled at configuration time, making it trivial to reorder or remove steps.
- `forward` provides the default pass-through, so handlers only implement what they care about.

---

## Iterator

Provides sequential access to the elements of a collection without exposing its internal representation.

```typescript
class NumberRange implements Iterable<number> {
  constructor(
    private readonly start: number,
    private readonly end: number,
    private readonly step: number = 1,
  ) {}

  [Symbol.iterator](): Iterator<number> {
    let current = this.start
    const { end, step } = this

    return {
      next(): IteratorResult<number> {
        if (current <= end) {
          const value = current
          current += step
          return { value, done: false }
        }
        return { value: undefined as unknown as number, done: true }
      },
    }
  }
}

// Usage
for (const n of new NumberRange(1, 10, 2)) {
  console.log(n) // 1, 3, 5, 7, 9
}

const evens = [...new NumberRange(2, 8, 2)] // [2, 4, 6, 8]
```

**What to notice:**
- Implementing `Symbol.iterator` makes `NumberRange` a first-class iterable — it works with `for...of`, spread, and destructuring natively.
- The internal cursor (`current`) is captured in closure, so multiple independent iterators over the same range do not interfere.
- Callers consume values without knowing the range is computed on the fly rather than stored in an array.

---

## Mediator

Centralizes communication between objects so they do not reference each other directly, reducing coupling.

```typescript
interface ChatMediator {
  send(message: string, sender: User): void
  join(user: User): void
}

class ChatRoom implements ChatMediator {
  private readonly users: User[] = []

  join(user: User): void {
    this.users.push(user)
  }

  send(message: string, sender: User): void {
    for (const user of this.users) {
      if (user !== sender) {
        user.receive(message, sender.name)
      }
    }
  }
}

class User {
  constructor(
    readonly name: string,
    private readonly mediator: ChatMediator,
  ) {}

  send(message: string): void {
    this.mediator.send(message, this)
  }

  receive(message: string, from: string): void {
    console.log(`[${this.name}] ${from}: ${message}`)
  }
}

const room = new ChatRoom()
const alice = new User('Alice', room)
const bob   = new User('Bob',   room)
room.join(alice)
room.join(bob)
alice.send('Hello!')
```

**What to notice:**
- `User` objects hold a reference to the mediator only — they never reference each other directly.
- Adding a new user or changing routing logic (e.g., private channels) changes `ChatRoom` alone.
- The mediator pattern trades peer-to-peer coupling for a single central dependency, which is easier to reason about and test.

---

## Builder

Constructs a complex object step by step with a fluent API, separating construction logic from the final representation.

```typescript
interface Query {
  readonly table: string
  readonly fields: readonly string[]
  readonly condition?: string
  readonly maxRows?: number
}

class QueryBuilder {
  private fields: string[] = ['*']
  private condition?: string
  private maxRows?: number

  constructor(private readonly table: string) {}

  select(...fields: string[]): this {
    this.fields = fields
    return this
  }

  where(condition: string): this {
    this.condition = condition
    return this
  }

  limit(n: number): this {
    this.maxRows = n
    return this
  }

  build(): Query {
    return {
      table: this.table,
      fields: this.fields,
      condition: this.condition,
      maxRows: this.maxRows,
    }
  }
}

const query = new QueryBuilder('users')
  .select('id', 'email')
  .where('active = true')
  .limit(20)
  .build()
```

**What to notice:**
- Each step returns `this`, enabling a fluent, readable chain without requiring every option to be specified.
- `build()` is the single point where the final immutable object is created — callers cannot receive a partially constructed one.
- Adding a new clause (e.g., `orderBy`) is an additive change; the rest of the builder is untouched.

---

## Abstract Factory

Creates families of related objects without coupling the caller to any concrete class, ensuring that produced objects are always compatible with each other.

```typescript
interface Button   { render(): string }
interface Checkbox { render(): string }

interface UIFactory {
  createButton(): Button
  createCheckbox(): Checkbox
}

class WindowsButton   implements Button   { render() { return 'Windows Button'   } }
class WindowsCheckbox implements Checkbox { render() { return 'Windows Checkbox' } }

class MacButton   implements Button   { render() { return 'Mac Button'   } }
class MacCheckbox implements Checkbox { render() { return 'Mac Checkbox' } }

class WindowsFactory implements UIFactory {
  createButton():   Button   { return new WindowsButton()   }
  createCheckbox(): Checkbox { return new WindowsCheckbox() }
}

class MacFactory implements UIFactory {
  createButton():   Button   { return new MacButton()   }
  createCheckbox(): Checkbox { return new MacCheckbox() }
}

function renderUI(factory: UIFactory): void {
  console.log(factory.createButton().render())
  console.log(factory.createCheckbox().render())
}

renderUI(new WindowsFactory())
renderUI(new MacFactory())
```

**What to notice:**
- `renderUI` depends only on `UIFactory` — it is impossible for it to mix a `MacButton` with a `WindowsCheckbox`.
- Adding a Linux theme means one new factory class and two new widget classes; no existing code changes.
- Abstract Factory is Factory Method scaled to a family: each factory method produces one compatible member of the set.

---

## Singleton

Ensures a class has exactly one instance and provides a global access point to it.

```typescript
class Logger {
  private static instance: Logger | undefined

  private constructor(private readonly prefix: string) {}

  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger('[APP]')
    }
    return Logger.instance
  }

  log(message: string): void {
    console.log(`${this.prefix} ${message}`)
  }
}

Logger.getInstance().log('Server started')
Logger.getInstance().log('Request received')
```

**What to notice:**
- The private constructor prevents direct instantiation; all access goes through `getInstance`.
- The instance is created lazily — only when first requested.

> **Trade-off note:** Singleton is widely considered an anti-pattern. The instance is effectively global state, which introduces hidden coupling between unrelated modules. It makes unit testing difficult because tests share the same instance and side-effects bleed between them. Prefer dependency injection: create one instance at the composition root and pass it explicitly to consumers.

---

## Proxy

Provides a surrogate for another object to control access to it — here used for lazy initialization of an expensive resource.

```typescript
interface ImageLoader {
  display(): void
}

class RealImageLoader implements ImageLoader {
  private readonly data: string

  constructor(private readonly filename: string) {
    // Expensive: simulates disk/network load
    this.data = `<pixels of ${filename}>`
    console.log(`Loaded: ${filename}`)
  }

  display(): void {
    console.log(`Displaying: ${this.data}`)
  }
}

class VirtualImageProxy implements ImageLoader {
  private real?: RealImageLoader

  constructor(private readonly filename: string) {}

  display(): void {
    if (!this.real) {
      this.real = new RealImageLoader(this.filename)
    }
    this.real.display()
  }
}

const image: ImageLoader = new VirtualImageProxy('photo.jpg')
// RealImageLoader not yet created
image.display() // loads and displays on first access
image.display() // uses cached instance
```

**What to notice:**
- The proxy and the real object share the same interface — callers cannot tell the difference.
- The expensive load happens exactly once and only if `display` is ever called.
- Other proxy variants (access control, remote, logging) follow the same structural shape.

---

## Facade

Provides a single, simplified interface to a complex subsystem, hiding its internal coordination from callers.

```typescript
class Amplifier {
  on()  { console.log('Amplifier on')  }
  off() { console.log('Amplifier off') }
  setVolume(level: number) { console.log(`Volume: ${level}`) }
}

class DVDPlayer {
  on()  { console.log('DVD Player on')  }
  off() { console.log('DVD Player off') }
  play(movie: string) { console.log(`Playing: ${movie}`) }
}

class Projector {
  on()  { console.log('Projector on')  }
  off() { console.log('Projector off') }
}

class HomeTheaterFacade {
  constructor(
    private readonly amp: Amplifier,
    private readonly dvd: DVDPlayer,
    private readonly projector: Projector,
  ) {}

  watchMovie(movie: string): void {
    this.projector.on()
    this.amp.on()
    this.amp.setVolume(8)
    this.dvd.on()
    this.dvd.play(movie)
  }

  endMovie(): void {
    this.dvd.off()
    this.amp.off()
    this.projector.off()
  }
}
```

**What to notice:**
- Callers invoke two methods instead of orchestrating five objects and ten calls.
- The subsystem classes are unchanged — the facade only coordinates them, it does not modify them.
- The facade does not prevent advanced callers from accessing subsystem components directly when needed.

---

## Bridge

Decouples an abstraction from its implementation so both can vary independently, avoiding a combinatorial explosion of subclasses.

```typescript
interface DrawingAPI {
  drawCircle(x: number, y: number, radius: number): void
  drawSquare(x: number, y: number, side: number): void
}

class SVGDrawer implements DrawingAPI {
  drawCircle(x: number, y: number, r: number) {
    console.log(`<circle cx="${x}" cy="${y}" r="${r}"/>`)
  }
  drawSquare(x: number, y: number, s: number) {
    console.log(`<rect x="${x}" y="${y}" width="${s}" height="${s}"/>`)
  }
}

class CanvasDrawer implements DrawingAPI {
  drawCircle(x: number, y: number, r: number) {
    console.log(`ctx.arc(${x},${y},${r},0,2*Math.PI)`)
  }
  drawSquare(x: number, y: number, s: number) {
    console.log(`ctx.fillRect(${x},${y},${s},${s})`)
  }
}

abstract class Shape {
  constructor(protected readonly api: DrawingAPI) {}
  abstract draw(): void
}

class Circle extends Shape {
  constructor(api: DrawingAPI, private readonly x: number, private readonly y: number, private readonly r: number) {
    super(api)
  }
  draw() { this.api.drawCircle(this.x, this.y, this.r) }
}

class Square extends Shape {
  constructor(api: DrawingAPI, private readonly x: number, private readonly y: number, private readonly s: number) {
    super(api)
  }
  draw() { this.api.drawSquare(this.x, this.y, this.s) }
}
```

**What to notice:**
- Two independent axes of variation (shape type vs. rendering technology) are kept in separate hierarchies.
- Without the bridge, supporting 2 shapes × 2 renderers would require 4 subclasses; bridge keeps it at 2 + 2.
- Swapping the renderer (e.g., from SVG to Canvas) is a constructor argument change — no subclassing required.

---

## Flyweight

Shares the intrinsic (immutable) state of many fine-grained objects to reduce memory usage when large numbers of similar objects are needed.

```typescript
interface Font {
  readonly family: string
  readonly size: number
}

class FontFactory {
  private readonly cache = new Map<string, Font>()

  getFont(family: string, size: number): Font {
    const key = `${family}:${size}`
    if (!this.cache.has(key)) {
      this.cache.set(key, { family, size })
      console.log(`Created font: ${key}`)
    }
    return this.cache.get(key)!
  }

  get cachedCount(): number { return this.cache.size }
}

interface Character {
  readonly glyph: string
  readonly font: Font   // shared flyweight
  readonly x: number    // extrinsic — unique per character
  readonly y: number
}

const fonts = new FontFactory()

const characters: Character[] = [
  { glyph: 'H', font: fonts.getFont('Arial', 12), x: 0,  y: 0 },
  { glyph: 'e', font: fonts.getFont('Arial', 12), x: 8,  y: 0 },
  { glyph: 'l', font: fonts.getFont('Arial', 12), x: 16, y: 0 },
  { glyph: 'o', font: fonts.getFont('Arial', 14), x: 24, y: 0 },
]

console.log(fonts.cachedCount) // 2, not 4
```

**What to notice:**
- Intrinsic state (font family + size) is shared; extrinsic state (position, glyph) is stored per instance.
- Ten thousand characters using the same font share one `Font` object, not ten thousand copies.
- The factory's cache is the mechanism that enforces sharing — callers never instantiate `Font` directly.

---

## Composite

Lets clients treat individual objects and compositions of objects uniformly through a common interface.

```typescript
interface FileSystemComponent {
  name: string
  getSize(): number
}

class File implements FileSystemComponent {
  constructor(readonly name: string, private readonly size: number) {}
  getSize(): number { return this.size }
}

class Directory implements FileSystemComponent {
  private readonly children: FileSystemComponent[] = []

  constructor(readonly name: string) {}

  add(component: FileSystemComponent): void {
    this.children.push(component)
  }

  getSize(): number {
    return this.children.reduce((sum, c) => sum + c.getSize(), 0)
  }
}

const root = new Directory('root')
const src  = new Directory('src')
src.add(new File('index.ts', 120))
src.add(new File('app.ts',   340))
root.add(src)
root.add(new File('README.md', 80))

console.log(root.getSize()) // 540 — callers don't know or care about the tree structure
```

**What to notice:**
- `Directory.getSize()` recurses through children without knowing whether each child is a `File` or another `Directory`.
- The uniform interface (`FileSystemComponent`) means callers can pass either a leaf or a subtree wherever a component is expected.
- Adding a new leaf type (e.g., `Symlink`) requires only implementing `FileSystemComponent` — no changes to `Directory` or callers.

---

## Result Pattern

Returns a typed `Success | Failure` value instead of throwing exceptions, making error paths explicit and composable.

```typescript
type Result<T, E> = { ok: true; value: T } | { ok: false; error: E }

function success<T>(value: T): Result<T, never> {
  return { ok: true, value }
}
function failure<E>(error: E): Result<never, E> {
  return { ok: false, error }
}

interface User { id: string; email: string }
interface ValidationError { field: string; message: string }

function registerUser(email: string): Result<User, ValidationError> {
  if (!email.includes('@')) {
    return failure({ field: 'email', message: 'Invalid email address' })
  }
  if (email.length < 5) {
    return failure({ field: 'email', message: 'Email too short' })
  }
  const user: User = { id: crypto.randomUUID(), email }
  return success(user)
}

const result = registerUser('alice@example.com')

if (result.ok) {
  console.log(`Registered: ${result.value.id}`)
} else {
  console.error(`${result.error.field}: ${result.error.message}`)
}
```

**What to notice:**
- TypeScript narrows the union after the `ok` check — `result.value` is only accessible in the `true` branch, eliminating accidental access to an error value.
- Callers are forced by the type system to handle both paths; there is no way to ignore a failure silently.
- The pattern composes: a function can accept a `Result` and return a `Result`, building pipelines without try/catch nesting.

---

## Enterprise Application Patterns

### Transaction Script

**Intent:** Organizes business logic as a single procedural function that handles one use case end-to-end, including direct DB calls.

```typescript
interface DbConnection {
  query<T>(sql: string, params: unknown[]): Promise<T[]>
  execute(sql: string, params: unknown[]): Promise<void>
}

async function transferFunds(
  db: DbConnection,
  fromAccountId: string,
  toAccountId: string,
  amountInCents: number,
): Promise<void> {
  const [from] = await db.query<{ balance: number }>(
    'SELECT balance FROM accounts WHERE id = ?', [fromAccountId]
  )
  if (!from || from.balance < amountInCents) {
    throw new Error('Insufficient funds')
  }
  await db.execute(
    'UPDATE accounts SET balance = balance - ? WHERE id = ?',
    [amountInCents, fromAccountId]
  )
  await db.execute(
    'UPDATE accounts SET balance = balance + ? WHERE id = ?',
    [amountInCents, toAccountId]
  )
}
```

**Key point:** All logic for one use case lives in one place — simple to read and trace, but grows unwieldy when use cases share business rules across multiple scripts.

---

### Service Layer

**Intent:** A class that coordinates domain objects and repositories to expose coarse-grained application operations to callers.

```typescript
interface AccountRepository {
  findById(id: string): Promise<Account | null>
  save(account: Account): Promise<void>
}

class Account {
  constructor(public id: string, private balance: number) {}
  debit(amount: number): void {
    if (amount > this.balance) throw new Error('Insufficient funds')
    this.balance -= amount
  }
  credit(amount: number): void { this.balance += amount }
}

class TransferService {
  constructor(private readonly accounts: AccountRepository) {}

  async transfer(fromId: string, toId: string, amount: number): Promise<void> {
    const [from, to] = await Promise.all([
      this.accounts.findById(fromId),
      this.accounts.findById(toId),
    ])
    if (!from || !to) throw new Error('Account not found')
    from.debit(amount)
    to.credit(amount)
    await Promise.all([this.accounts.save(from), this.accounts.save(to)])
  }
}
```

**Key point:** The service holds no business rules itself — it delegates to domain objects and repositories, acting as the transaction boundary and orchestrator.

---

### Data Mapper

**Intent:** A class that moves data between domain objects and database rows, keeping SQL entirely out of the domain model.

```typescript
interface UserRow { id: string; full_name: string; email_address: string }

class User {
  constructor(
    readonly id: string,
    readonly fullName: string,
    readonly email: string,
  ) {}
}

class UserMapper {
  toDomain(row: UserRow): User {
    return new User(row.id, row.full_name, row.email_address)
  }

  toPersistence(user: User): UserRow {
    return { id: user.id, full_name: user.fullName, email_address: user.email }
  }
}

// Usage (repository layer)
// const row = await db.query('SELECT * FROM users WHERE id = ?', [id])
// return mapper.toDomain(row)
```

**Key point:** The domain object `User` knows nothing about column names or persistence — all schema-to-model translation is isolated in one mapper class.

---

### Unit of Work

**Intent:** Tracks objects registered as new, dirty, or removed during a business transaction and flushes all changes in a single atomic write.

```typescript
class UnitOfWork {
  private readonly newEntities: object[] = []
  private readonly dirtyEntities: object[] = []
  private readonly removedEntities: object[] = []

  registerNew(entity: object): void    { this.newEntities.push(entity) }
  registerDirty(entity: object): void  { this.dirtyEntities.push(entity) }
  registerRemoved(entity: object): void { this.removedEntities.push(entity) }

  async commit(db: { insert: Function; update: Function; delete: Function }): Promise<void> {
    for (const e of this.newEntities)     await db.insert(e)
    for (const e of this.dirtyEntities)   await db.update(e)
    for (const e of this.removedEntities) await db.delete(e)
    this.newEntities.length = 0
    this.dirtyEntities.length = 0
    this.removedEntities.length = 0
  }
}
```

**Key point:** Callers accumulate changes throughout a use case and call `commit` once — preventing partial writes and avoiding redundant round-trips to the database.

---

### Data Transfer Object (DTO)

**Intent:** A plain, immutable object that carries data across layer boundaries with no behavior.

```typescript
interface CreateOrderDto {
  readonly customerId: string
  readonly lineItems: ReadonlyArray<{ readonly productId: string; readonly quantity: number }>
  readonly shippingAddressId: string
}

interface OrderSummaryDto {
  readonly orderId: string
  readonly status: string
  readonly totalInCents: number
  readonly createdAt: string
}

// Usage: HTTP layer creates the DTO from request JSON,
// passes it to the service layer, receives a summary DTO back.
// No domain objects or database entities cross the boundary.
```

**Key point:** DTOs are deliberately behavior-free — they prevent domain logic from leaking into serialization code and make layer contracts explicit and type-safe.

---

### Value Object (Money)

**Intent:** An immutable object with value semantics that represents a monetary amount — equality is based on amount and currency, not identity.

```typescript
class Money {
  private constructor(
    readonly amountInCents: number,
    readonly currency: string,
  ) {}

  static of(amountInCents: number, currency: string): Money {
    if (amountInCents < 0) throw new Error('Amount must be non-negative')
    return new Money(amountInCents, currency)
  }

  add(other: Money): Money {
    this.assertSameCurrency(other)
    return new Money(this.amountInCents + other.amountInCents, this.currency)
  }

  equals(other: Money): boolean {
    return this.amountInCents === other.amountInCents && this.currency === other.currency
  }

  private assertSameCurrency(other: Money): void {
    if (this.currency !== other.currency) throw new Error('Currency mismatch')
  }
}

const price = Money.of(1000, 'USD')
const tax   = Money.of(210,  'USD')
const total = price.add(tax) // Money.of(1210, 'USD') — original unchanged
```

**Key point:** Immutability guarantees that operations return new values rather than mutating shared state, eliminating entire classes of currency-mixing and aliasing bugs.

---

### Special Case

**Intent:** A subclass that represents a null or missing entity with safe default behavior, eliminating null checks throughout calling code.

```typescript
class Customer {
  constructor(readonly name: string, readonly discountRate: number) {}

  applyDiscount(priceInCents: number): number {
    return Math.round(priceInCents * (1 - this.discountRate))
  }
}

class GuestCustomer extends Customer {
  constructor() { super('Guest', 0) }

  applyDiscount(priceInCents: number): number {
    return priceInCents // no discount for guests
  }
}

// Repository returns GuestCustomer when no account is found
function findCustomer(id: string | null): Customer {
  if (!id) return new GuestCustomer()
  // ... db lookup ...
  return new Customer('Alice', 0.1)
}

// Caller never checks for null
const customer = findCustomer(null)
console.log(customer.applyDiscount(1000)) // 1000
```

**Key point:** By returning a well-behaved object instead of `null`, callers are freed from defensive null checks — the missing-case behavior is defined once, in one place.

---

### Gateway

**Intent:** A class that wraps an external API or service behind a clean, domain-facing interface, hiding HTTP, auth, and serialization details.

```typescript
interface ExchangeRate { from: string; to: string; rate: number }

interface CurrencyGateway {
  getRate(from: string, to: string): Promise<ExchangeRate>
}

class OpenExchangeGateway implements CurrencyGateway {
  constructor(
    private readonly apiKey: string,
    private readonly http: { get: (url: string) => Promise<{ data: unknown }> },
  ) {}

  async getRate(from: string, to: string): Promise<ExchangeRate> {
    const { data } = await this.http.get(
      `https://openexchangerates.org/api/latest.json?app_id=${this.apiKey}&base=${from}&symbols=${to}`
    )
    const rates = (data as { rates: Record<string, number> }).rates
    return { from, to, rate: rates[to] }
  }
}

// Domain code depends only on CurrencyGateway — easily replaced with a stub in tests.
```

**Key point:** The rest of the application depends on the `CurrencyGateway` interface — switching providers or stubbing in tests requires no changes to domain code.

---

### Query Object

**Intent:** An object that encapsulates filter criteria for a collection query, separating query construction from query execution.

```typescript
class OrderQuery {
  private _customerId?: string
  private _status?: string
  private _limit?: number

  forCustomer(customerId: string): this { this._customerId = customerId; return this }
  withStatus(status: string): this      { this._status = status;     return this }
  limitTo(n: number): this              { this._limit = n;           return this }

  toSql(): { sql: string; params: unknown[] } {
    const conditions: string[] = []
    const params: unknown[] = []
    if (this._customerId) { conditions.push('customer_id = ?'); params.push(this._customerId) }
    if (this._status)     { conditions.push('status = ?');      params.push(this._status)     }
    const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : ''
    const limit = this._limit ? `LIMIT ${this._limit}` : ''
    return { sql: `SELECT * FROM orders ${where} ${limit}`.trim(), params }
  }
}

// Usage
const query = new OrderQuery().forCustomer('c-1').withStatus('pending').limitTo(10)
const { sql, params } = query.toSql()
// SELECT * FROM orders WHERE customer_id = ? AND status = ? LIMIT 10
```

**Key point:** Query criteria are built up as a first-class object rather than assembled as raw SQL strings scattered across callers, making queries composable and testable without a database.

---

### Layer Supertype

**Intent:** A base class for an entire layer that holds shared behavior — auto-generated IDs, timestamps, equality — so every entity in the layer inherits it without repetition.

```typescript
abstract class BaseEntity {
  readonly id: string
  readonly createdAt: Date
  protected updatedAt: Date

  constructor() {
    this.id        = crypto.randomUUID()
    this.createdAt = new Date()
    this.updatedAt = new Date()
  }

  protected touch(): void {
    this.updatedAt = new Date()
  }

  equals(other: BaseEntity): boolean {
    return this.id === other.id
  }
}

class Product extends BaseEntity {
  constructor(public name: string, public priceInCents: number) {
    super()
  }

  updatePrice(newPrice: number): void {
    this.priceInCents = newPrice
    this.touch()
  }
}
```

**Key point:** ID generation, timestamp management, and identity comparison are defined once in the supertype — concrete entity classes stay focused on their own domain behavior.

---

## Remaining GoF Patterns

### Adapter

**Intent:** Wrap a third-party or legacy interface behind the interface your code expects.

```typescript
interface PaymentGateway {
  charge(amountInCents: number, token: string): Promise<{ transactionId: string }>
}

// External SDK — interface we cannot change
class StripeSDK {
  createCharge(opts: { amount: number; currency: string; source: string }) {
    return Promise.resolve({ id: `ch_${Math.random().toString(36).slice(2)}` })
  }
}

class StripeAdapter implements PaymentGateway {
  constructor(private readonly stripe: StripeSDK) {}

  async charge(amountInCents: number, token: string) {
    const result = await this.stripe.createCharge({
      amount: amountInCents,
      currency: 'usd',
      source: token,
    })
    return { transactionId: result.id }
  }
}

// Domain code depends only on PaymentGateway — never on StripeSDK directly.
const gateway: PaymentGateway = new StripeAdapter(new StripeSDK())
```

**Key point:** The adapter translates the external SDK's vocabulary into the local interface, so the rest of the codebase never imports or knows about the third-party SDK.

---

### Visitor

**Intent:** Separate an algorithm from the object structure it operates on, allowing new operations without changing the element classes.

```typescript
interface DocumentElement {
  accept(visitor: DocumentVisitor): void
}

interface DocumentVisitor {
  visitHeading(el: Heading): void
  visitParagraph(el: Paragraph): void
}

class Heading implements DocumentElement {
  constructor(readonly text: string, readonly level: number) {}
  accept(visitor: DocumentVisitor) { visitor.visitHeading(this) }
}

class Paragraph implements DocumentElement {
  constructor(readonly text: string) {}
  accept(visitor: DocumentVisitor) { visitor.visitParagraph(this) }
}

class WordCountVisitor implements DocumentVisitor {
  count = 0
  visitHeading(el: Heading)   { this.count += el.text.split(/\s+/).length }
  visitParagraph(el: Paragraph) { this.count += el.text.split(/\s+/).length }
}

class HtmlRenderVisitor implements DocumentVisitor {
  output = ''
  visitHeading(el: Heading)     { this.output += `<h${el.level}>${el.text}</h${el.level}>\n` }
  visitParagraph(el: Paragraph) { this.output += `<p>${el.text}</p>\n` }
}

const doc: DocumentElement[] = [new Heading('Hello', 1), new Paragraph('World tour')]
const wc = new WordCountVisitor()
doc.forEach(el => el.accept(wc))
console.log(wc.count) // 3
```

**Key point:** Adding a new operation (e.g., a markdown renderer) means adding a new visitor class — `Heading` and `Paragraph` are never touched.

---

### Memento

**Intent:** Capture and restore an object's internal state without exposing its internals.

```typescript
class Memento {
  constructor(readonly state: string) {}
}

class TextEditor {
  private content = ''

  type(text: string): void { this.content += text }
  getContent(): string     { return this.content }

  save(): Memento          { return new Memento(this.content) }
  restore(m: Memento): void { this.content = m.state }
}

class History {
  private readonly stack: Memento[] = []

  push(m: Memento): void   { this.stack.push(m) }
  pop(): Memento | undefined { return this.stack.pop() }
}

const editor  = new TextEditor()
const history = new History()

editor.type('Hello')
history.push(editor.save())

editor.type(', World')
history.push(editor.save())

editor.type('!!!')
console.log(editor.getContent()) // Hello, World!!!

const previous = history.pop()
if (previous) editor.restore(previous)
console.log(editor.getContent()) // Hello, World
```

**Key point:** `Memento` is opaque to the `History` caretaker — it stores state without understanding it, preserving encapsulation of `TextEditor`.

---

### Prototype

**Intent:** Clone a fully configured object instead of constructing one from scratch, when setup is expensive or complex.

```typescript
interface Cloneable<T> {
  clone(): T
}

class DocumentTemplate implements Cloneable<DocumentTemplate> {
  constructor(
    public title: string,
    public sections: string[],
    public styles: Record<string, string>,
  ) {}

  clone(): DocumentTemplate {
    return new DocumentTemplate(
      this.title,
      [...this.sections],              // deep-copy array
      { ...this.styles },              // deep-copy styles map
    )
  }
}

const reportTemplate = new DocumentTemplate(
  'Quarterly Report',
  ['Executive Summary', 'Financials', 'Outlook'],
  { font: 'Arial', fontSize: '12pt', margin: '1in' },
)

const q1Report = reportTemplate.clone()
q1Report.title = 'Q1 2026 Report'
q1Report.sections.push('Appendix')

// reportTemplate.sections is unchanged — clone owns its own copy
console.log(reportTemplate.sections.length) // 3
console.log(q1Report.sections.length)        // 4
```

## DDD Tactical Patterns

### Entity

**Intent:** An object with a unique identity that persists and changes over time.

```typescript
class Order {
  constructor(
    readonly id: string,
    private _status: 'draft' | 'placed' | 'shipped',
    private _customerId: string,
  ) {}

  place(): void {
    if (this._status !== 'draft') throw new Error('Order already placed')
    this._status = 'placed'
  }

  get status() { return this._status }

  equals(other: Order): boolean {
    return this.id === other.id  // identity-based equality
  }
}
```

**Key point:** Two entities are equal when their IDs match, regardless of attribute differences.

---

### Aggregate Root

**Intent:** An entity that guards a cluster of objects, enforces invariants, and records domain events.

```typescript
class OrderAggregate {
  private items: { productId: string; qty: number }[] = []
  private events: object[] = []

  constructor(readonly id: string, private readonly maxItems = 10) {}

  addItem(productId: string, qty: number): void {
    if (this.items.length >= this.maxItems)
      throw new Error('Order exceeds maximum item limit')
    if (qty <= 0) throw new Error('Quantity must be positive')

    this.items.push({ productId, qty })
    this.events.push(new OrderItemAdded(this.id, productId, qty))
  }

  pullEvents(): object[] {
    const pending = [...this.events]
    this.events = []
    return pending
  }
}
```

**Key point:** All mutations go through the aggregate root so invariants are always enforced before state changes.

---

### Domain Event

**Intent:** An immutable record of something that happened in the domain, carrying all relevant data.

```typescript
class OrderItemAdded {
  readonly occurredAt: Date

  constructor(
    readonly orderId: string,
    readonly productId: string,
    readonly quantity: number,
  ) {
    this.occurredAt = new Date()
    Object.freeze(this)
  }
}

class OrderPlaced {
  readonly occurredAt: Date

  constructor(readonly orderId: string, readonly customerId: string) {
    this.occurredAt = new Date()
    Object.freeze(this)
  }
}
```

**Key point:** `Object.freeze` guarantees immutability so the event record cannot be altered after creation.

---

### Specification

**Intent:** An encapsulated, combinable business rule that answers whether an object satisfies a condition.

```typescript
interface Specification<T> {
  isSatisfiedBy(candidate: T): boolean
  and(other: Specification<T>): Specification<T>
  or(other: Specification<T>): Specification<T>
  not(): Specification<T>
}

abstract class BaseSpec<T> implements Specification<T> {
  abstract isSatisfiedBy(candidate: T): boolean
  and(other: Specification<T>) { return new AndSpec(this, other) }
  or(other: Specification<T>)  { return new OrSpec(this, other) }
  not()                        { return new NotSpec(this) }
}

class AndSpec<T> extends BaseSpec<T> {
  constructor(private a: Specification<T>, private b: Specification<T>) { super() }
  isSatisfiedBy(c: T) { return this.a.isSatisfiedBy(c) && this.b.isSatisfiedBy(c) }
}
class OrSpec<T>  extends BaseSpec<T> {
  constructor(private a: Specification<T>, private b: Specification<T>) { super() }
  isSatisfiedBy(c: T) { return this.a.isSatisfiedBy(c) || this.b.isSatisfiedBy(c) }
}
class NotSpec<T> extends BaseSpec<T> {
  constructor(private inner: Specification<T>) { super() }
  isSatisfiedBy(c: T) { return !this.inner.isSatisfiedBy(c) }
}

type Customer = { active: boolean; totalSpend: number }

class ActiveCustomerSpec   extends BaseSpec<Customer> {
  isSatisfiedBy(c: Customer) { return c.active }
}
class PremiumCustomerSpec  extends BaseSpec<Customer> {
  isSatisfiedBy(c: Customer) { return c.totalSpend >= 10_000 }
}

// Compose: active AND premium
const eligibleForPromo = new ActiveCustomerSpec().and(new PremiumCustomerSpec())
console.log(eligibleForPromo.isSatisfiedBy({ active: true, totalSpend: 15_000 })) // true
```

**Key point:** Composing specifications with `and`/`or`/`not` expresses complex business rules without scattering conditionals.

---

## CQRS and Error Patterns

### Command + CommandHandler (CQRS write side)

**Intent:** Separate the write operation into an immutable value object (Command) and a handler that orchestrates domain logic.

```typescript
abstract class Command {}

interface CommandHandler<T extends Command> {
  handle(command: T): Promise<void>
}

class CreateUserCommand extends Command {
  constructor(
    readonly id: string,
    readonly email: string,
    readonly name: string,
  ) { super() }
}

class CreateUserCommandHandler implements CommandHandler<CreateUserCommand> {
  constructor(
    private readonly userRepository: UserRepository,
    private readonly eventBus: EventBus,
  ) {}

  async handle(command: CreateUserCommand): Promise<void> {
    const id    = new UserId(command.id)
    const email = new UserEmail(command.email)
    const user  = User.create(id, email, command.name)
    await this.userRepository.save(user)
    await this.eventBus.publish(user.pullDomainEvents())
  }
}
```

**Key point:** The Command is a plain immutable value object; the handler owns orchestration — value object construction, aggregate creation, persistence, and event dispatch.

---

### Object Mother

**Intent:** Provide a centralized factory for valid test objects so tests stay readable and free of setup boilerplate.

```typescript
class UserIdMother {
  static random(): UserId {
    return new UserId(crypto.randomUUID())
  }
}

type UserOverrides = Partial<{ id: UserId; email: string; name: string }>

class UserMother {
  static random(): User {
    return User.create(
      UserIdMother.random(),
      new UserEmail(`user-${Math.random().toString(36).slice(2)}@example.com`),
      'Random User',
    )
  }

  static create(overrides: UserOverrides = {}): User {
    return User.create(
      overrides.id    ?? UserIdMother.random(),
      new UserEmail(overrides.email ?? 'alice@example.com'),
      overrides.name  ?? 'Alice',
    )
  }
}

// In a test:
const user = UserMother.create({ name: 'Bob' })
```

**Key point:** Object Mothers generate complete, valid domain objects with sensible defaults, keeping test intent visible and setup noise invisible.

---

### DomainError hierarchy

**Intent:** Give every domain error a stable, explicit string type so errors survive minification and production builds.

```typescript
abstract class DomainError extends Error {
  abstract readonly type: string

  constructor(message: string) {
    super(message)
    this.name = this.constructor.name
  }
}

class UserNotFoundError extends DomainError {
  readonly type = 'UserNotFoundError'

  constructor(id: string) {
    super(`User with id <${id}> not found`)
  }
}

// Usage in a catch block:
try {
  await handler.handle(command)
} catch (err) {
  if (err instanceof DomainError && err.type === 'UserNotFoundError') {
    // handle 404 path
  }
  throw err
}
```

**Key point:** Use an explicit `readonly type` string instead of `constructor.name` — minifiers rename classes, making `constructor.name` unreliable in production builds.

---

### Either / Result type

**Intent:** Make failure an explicit return value so callers are forced to handle both the success and error paths at compile time.

```typescript
class Result<TValue, TError extends DomainError> {
  private constructor(
    private readonly _value: TValue | undefined,
    private readonly _error: TError | undefined,
  ) {}

  static ok<TValue, TError extends DomainError>(value: TValue): Result<TValue, TError> {
    return new Result(value, undefined)
  }

  static err<TValue, TError extends DomainError>(error: TError): Result<TValue, TError> {
    return new Result(undefined, error)
  }

  isOk():  boolean { return this._error === undefined }
  isErr(): boolean { return this._error !== undefined }
  getValue(): TValue { if (!this.isOk())  throw new Error('No value'); return this._value! }
  getError(): TError { if (!this.isErr()) throw new Error('No error'); return this._error! }
}

// Domain method:
function findUser(id: string): Result<User, UserNotFoundError> {
  const user = store.get(id)
  return user ? Result.ok(user) : Result.err(new UserNotFoundError(id))
}

// Caller:
const result = findUser('abc')
if (result.isOk()) {
  console.log(result.getValue().name)
} else {
  console.error(result.getError().message)
}
```

**Key point:** Returning `Result<TValue, TError>` instead of throwing makes the failure contract explicit in the type signature and forces the caller to handle both paths.

**Key point:** Each clone is an independent deep copy — mutating one report does not affect the template or sibling reports cloned from it.
