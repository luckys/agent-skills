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

---

## Command

Encapsulate a request as an object so that operations can be queued, logged, or undone without the sender knowing the implementation details.

```ruby
class BoldCommand
  def initialize(editor)
    @editor = editor
    @previous = nil
  end

  def execute
    @previous = @editor.selection
    @editor.wrap(@previous, "<b>", "</b>")
  end

  def undo
    @editor.restore(@previous)
  end
end

class ItalicCommand
  def initialize(editor)
    @editor = editor
    @previous = nil
  end

  def execute
    @previous = @editor.selection
    @editor.wrap(@previous, "<i>", "</i>")
  end

  def undo
    @editor.restore(@previous)
  end
end

class TextEditor
  attr_reader :selection

  def initialize(text)
    @text = text
    @selection = text
    @history = []
  end

  def wrap(text, open, close) = @text = @text.sub(text, "#{open}#{text}#{close}")
  def restore(text)           = @text = text
  def run(command)
    command.execute
    @history << command
  end
  def undo = @history.pop&.undo
  def to_s = @text
end
```

**What to notice:**
- Each command object captures everything needed to execute and reverse the action — sender and executor are fully decoupled.
- The `history` stack in `TextEditor` knows nothing about what the commands do; undo is free.
- New operations (e.g., `UnderlineCommand`) are additive — the editor and history mechanism are untouched.

---

## Template Method

Define the skeleton of an algorithm in a base class and let subclasses fill in the variable steps without changing the overall structure.

```ruby
class ReportGenerator
  def generate
    data = gather_data
    formatted = format_data(data)
    output(formatted)
  end

  private

  def gather_data
    { title: "Q1 Sales", rows: [[1, "Widget", 100], [2, "Gadget", 200]] }
  end

  def format_data(_data)
    raise NotImplementedError, "#{self.class} must implement format_data"
  end

  def output(content)
    puts content
  end
end

class CsvReportGenerator < ReportGenerator
  private

  def format_data(data)
    lines = [data[:title]]
    data[:rows].each { |row| lines << row.join(",") }
    lines.join("\n")
  end
end

class PdfReportGenerator < ReportGenerator
  private

  def format_data(data)
    "[PDF] #{data[:title]}: #{data[:rows].map { |r| r.join(" | ") }.join("; ")}"
  end
end
```

**What to notice:**
- The `generate` method is the invariant skeleton — subclasses never override it, only the steps that vary.
- The base class documents the algorithm's shape; reading it tells you exactly what every report generator does.
- Adding a new output format (e.g., `HtmlReportGenerator`) is a single-class additive change.

---

## Chain of Responsibility

Pass a request along a chain of handlers; each handler decides to process it or forward it to the next one.

```ruby
class AuthMiddleware
  def initialize(next_handler = nil)
    @next = next_handler
  end

  def call(request)
    return { status: 401, body: "Unauthorized" } unless request[:token] == "valid-token"

    @next&.call(request) || { status: 200, body: "OK" }
  end
end

class LoggingMiddleware
  def initialize(next_handler = nil)
    @next = next_handler
  end

  def call(request)
    puts "[LOG] #{request[:method]} #{request[:path]}"
    @next&.call(request) || { status: 200, body: "OK" }
  end
end

class Handler
  def call(_request)
    { status: 200, body: "Hello, world!" }
  end
end

# Build the chain: Auth → Logging → Handler
chain = AuthMiddleware.new(LoggingMiddleware.new(Handler.new))
puts chain.call({ method: "GET", path: "/home", token: "valid-token" }).inspect
```

**What to notice:**
- Each middleware knows only about its own concern and the next handler — the chain is assembled at construction time.
- Adding or reordering middleware is a one-line change at the composition site; no handler is modified.
- The safe-navigation operator (`&.call`) means a handler at the end of the chain can terminate without a special null object.

---

## Iterator

Provide a sequential interface to a collection's elements without exposing its internal structure.

```ruby
class NumberRange
  include Enumerable

  def initialize(start, stop, step: 1)
    @start = start
    @stop  = stop
    @step  = step
  end

  def each
    current = @start
    while current <= @stop
      yield current
      current += @step
    end
  end
end

range = NumberRange.new(1, 10, step: 2)
puts range.to_a.inspect          # [1, 3, 5, 7, 9]
puts range.select(&:odd?).inspect
puts range.sum
```

**What to notice:**
- Implementing `each` and including `Enumerable` gives the class the full Ruby collection API for free (`map`, `select`, `sum`, `min`, `sort`, …).
- Callers never know whether the sequence is array-backed, lazily computed, or read from a database.
- The `step` parameter shows how a custom iterator can expose iteration policies the standard `Range` class does not.

---

## Mediator

Centralize inter-object communication so that objects talk to a mediator instead of referencing each other directly.

```ruby
class ChatRoom
  def initialize
    @users = {}
  end

  def join(user)
    @users[user.name] = user
    broadcast("[#{user.name} joined]", except: user)
  end

  def send_message(from:, to: nil, text:)
    if to
      @users[to]&.receive("[DM from #{from.name}] #{text}")
    else
      broadcast("[#{from.name}] #{text}", except: from)
    end
  end

  private

  def broadcast(message, except:)
    @users.each_value { |u| u.receive(message) unless u == except }
  end
end

class User
  attr_reader :name

  def initialize(name, room)
    @name = name
    @room = room
    @room.join(self)
  end

  def say(text, to: nil) = @room.send_message(from: self, to: to, text: text)
  def receive(message)   = puts "#{@name} received: #{message}"
end

room  = ChatRoom.new
alice = User.new("Alice", room)
bob   = User.new("Bob",   room)
alice.say("Hello, everyone!")
alice.say("Hey Bob", to: "Bob")
```

**What to notice:**
- `User` objects never hold references to each other — all routing logic lives in `ChatRoom`.
- Adding a new user or a new message type only touches the mediator, not any participant.
- The mediator trades many peer-to-peer edges for a single hub, which simplifies the object graph but centralizes complexity.

---

## Builder

Construct a complex object step by step using a fluent interface; keep construction logic out of the consumer.

```ruby
class QueryBuilder
  def initialize(table)
    @table      = table
    @selections = ["*"]
    @conditions = []
    @limit_val  = nil
  end

  def select(*columns)
    @selections = columns
    self
  end

  def where(condition)
    @conditions << condition
    self
  end

  def limit(n)
    @limit_val = n
    self
  end

  def build
    sql = "SELECT #{@selections.join(", ")} FROM #{@table}"
    sql += " WHERE #{@conditions.join(" AND ")}" unless @conditions.empty?
    sql += " LIMIT #{@limit_val}" if @limit_val
    sql
  end
end

query = QueryBuilder.new("users")
  .select("id", "email")
  .where("active = true")
  .where("age > 18")
  .limit(10)
  .build

puts query
# SELECT id, email FROM users WHERE active = true AND age > 18 LIMIT 10
```

**What to notice:**
- Each chainable method returns `self`, making the construction sequence read like a sentence.
- `build` is the only method that produces output — intermediate state accumulates silently inside the builder.
- The consumer never constructs a partially-valid query string; the builder enforces a complete representation at `build` time.

---

## Abstract Factory

Create families of related objects without naming their concrete classes; swap the entire family by swapping the factory.

```ruby
class WindowsButton
  def render = puts "[Windows] Rendering button"
end

class WindowsCheckbox
  def render = puts "[Windows] Rendering checkbox"
end

class MacButton
  def render = puts "[Mac] Rendering button"
end

class MacCheckbox
  def render = puts "[Mac] Rendering checkbox"
end

class WindowsFactory
  def create_button   = WindowsButton.new
  def create_checkbox = WindowsCheckbox.new
end

class MacFactory
  def create_button   = MacButton.new
  def create_checkbox = MacCheckbox.new
end

class Application
  def initialize(factory)
    @button   = factory.create_button
    @checkbox = factory.create_checkbox
  end

  def render
    @button.render
    @checkbox.render
  end
end

factory = ENV["OS"] == "mac" ? MacFactory.new : WindowsFactory.new
Application.new(factory).render
```

**What to notice:**
- `Application` names no concrete widget class — the factory is the only seam between platform-agnostic and platform-specific code.
- Switching platforms is a single-line change at the composition root.
- Adding a new widget (e.g., `create_text_field`) requires updating each factory, which keeps families consistent by construction.

---

## Singleton

Ensure a class has exactly one instance and provide a global access point to it.

```ruby
require "singleton"

class AppLogger
  include Singleton

  def initialize
    @log = []
  end

  def info(message)
    @log << "[INFO] #{message}"
    puts @log.last
  end

  def entries = @log.dup
end

AppLogger.instance.info("Application started")
AppLogger.instance.info("User logged in")
puts AppLogger.instance.entries.inspect
```

> **Anti-pattern warning:** Singleton is widely considered an anti-pattern. It introduces global mutable state, creates hidden coupling between callers, and makes unit testing hard (tests share the same instance and cannot isolate state). Prefer dependency injection — pass the logger as a constructor argument — so each consumer's dependency is explicit and replaceable in tests.

**What to notice:**
- Ruby's `Singleton` module privatizes `new` and `allocate` and memoizes `instance` in a thread-safe way.
- The convenience of a global access point (`AppLogger.instance`) is also its danger — any code anywhere can mutate shared state.
- When you feel the pull toward Singleton, ask whether dependency injection with a shared instance at the composition root solves the same problem without the global coupling.

---

## Proxy

Provide a surrogate that controls access to another object — deferring its creation until it is actually needed.

```ruby
class RealImage
  def initialize(path)
    @path = path
    puts "[RealImage] Loading #{@path} from disk…"
    @data = "…binary data…"
  end

  def display = puts "[RealImage] Displaying #{@path}"
end

class ImageProxy
  def initialize(path)
    @path  = path
    @image = nil
  end

  def display
    @image ||= RealImage.new(@path)
    @image.display
  end
end

# The real image is not loaded until display is first called.
proxy = ImageProxy.new("photo.jpg")
puts "Proxy created — no disk I/O yet"
proxy.display   # loads on first call
proxy.display   # uses cached instance
```

**What to notice:**
- `ImageProxy` and `RealImage` share the same public interface (`display`), so callers cannot tell which they hold.
- `@image ||=` is idiomatic Ruby for lazy memoization — one line replaces an explicit null-object guard.
- The proxy pattern is also used for access control, logging, and remote object stubs; the lazy-loading shape here is just one common application.

---

## Facade

Provide a single, simplified interface to a complex subsystem so callers are shielded from its inner workings.

```ruby
class Amplifier
  def on  = puts "Amplifier on"
  def off = puts "Amplifier off"
  def set_volume(level) = puts "Volume → #{level}"
end

class DVDPlayer
  def on  = puts "DVD player on"
  def off = puts "DVD player off"
  def play(movie) = puts "Playing '#{movie}'"
end

class Projector
  def on  = puts "Projector on"
  def off = puts "Projector off"
  def wide_screen_mode = puts "Projector: wide-screen mode"
end

class HomeTheaterFacade
  def initialize
    @amp       = Amplifier.new
    @dvd       = DVDPlayer.new
    @projector = Projector.new
  end

  def watch_movie(movie)
    puts "--- Get ready to watch a movie ---"
    @projector.on
    @projector.wide_screen_mode
    @amp.on
    @amp.set_volume(10)
    @dvd.on
    @dvd.play(movie)
  end

  def end_movie
    puts "--- Shutting down ---"
    @dvd.off
    @amp.off
    @projector.off
  end
end

theater = HomeTheaterFacade.new
theater.watch_movie("Inception")
theater.end_movie
```

**What to notice:**
- The facade owns the orchestration sequence — callers are not coupled to the order or presence of subsystem components.
- Each subsystem class remains independently testable and reusable; the facade adds no business logic of its own.
- When the subsystem grows (e.g., adding `StreamingDevice`), only the facade changes — no caller is affected.

---

## Bridge

Decouple an abstraction from its implementation so that both can vary independently along separate axes.

```ruby
class SvgDrawer
  def draw_circle(x, y, radius)
    puts "<circle cx='#{x}' cy='#{y}' r='#{radius}'/>"
  end

  def draw_square(x, y, side)
    puts "<rect x='#{x}' y='#{y}' width='#{side}' height='#{side}'/>"
  end
end

class CanvasDrawer
  def draw_circle(x, y, radius)
    puts "ctx.arc(#{x}, #{y}, #{radius}, 0, 2*Math.PI)"
  end

  def draw_square(x, y, side)
    puts "ctx.fillRect(#{x}, #{y}, #{side}, #{side})"
  end
end

class Circle
  def initialize(x, y, radius, drawer)
    @x = x; @y = y; @radius = radius; @drawer = drawer
  end

  def draw = @drawer.draw_circle(@x, @y, @radius)
end

class Square
  def initialize(x, y, side, drawer)
    @x = x; @y = y; @side = side; @drawer = drawer
  end

  def draw = @drawer.draw_square(@x, @y, @side)
end

svg    = SvgDrawer.new
canvas = CanvasDrawer.new

Circle.new(50, 50, 30, svg).draw
Square.new(10, 10, 40, canvas).draw
```

**What to notice:**
- Shape (what to draw) and DrawingAPI (how to draw) vary independently — adding a new shape does not touch any drawer, and vice versa.
- The Bridge pattern avoids the M×N subclass explosion that inheritance would create (2 shapes × 2 renderers = 4 classes instead of 6).
- In Ruby the drawer is a plain duck-typed collaborator; no abstract base class is required.

---

## Flyweight

Share common state between many fine-grained objects to reduce memory when large numbers of similar objects are needed.

```ruby
Font = Data.define(:family, :size)

class CharacterFactory
  def initialize
    @cache = {}
  end

  def font_for(family, size)
    @cache[[family, size]] ||= Font.new(family: family, size: size)
  end
end

class Character
  attr_reader :glyph

  def initialize(glyph, font)
    @glyph = glyph
    @font  = font
  end

  def render(x, y)
    puts "'#{@glyph}' at (#{x},#{y}) — #{@font.family} #{@font.size}pt [font_id: #{@font.object_id}]"
  end
end

factory = CharacterFactory.new

chars = [
  Character.new("H", factory.font_for("Arial", 12)),
  Character.new("e", factory.font_for("Arial", 12)),
  Character.new("l", factory.font_for("Arial", 12)),
  Character.new("!", factory.font_for("Arial", 14)),
]

chars.each_with_index { |c, i| c.render(i * 10, 0) }

puts "Unique Font objects: #{factory.instance_variable_get(:@cache).size}"
```

**What to notice:**
- All characters sharing the same font family and size point to the same `Font` object — the `object_id` lines confirm this.
- The factory's `Hash` cache (`||=`) is all the machinery needed; no complex pooling infrastructure is required.
- `Data.define` creates an immutable value object, which is safe to share because shared objects must not be mutated.

---

## Composite

Treat individual objects and compositions of objects uniformly through a shared interface — no explicit abstract class required in Ruby.

```ruby
class File
  def initialize(name, size_bytes)
    @name = name
    @size = size_bytes
  end

  def size = @size

  def display(indent = 0)
    puts "#{"  " * indent}📄 #{@name} (#{@size} B)"
  end
end

class Directory
  def initialize(name)
    @name     = name
    @children = []
  end

  def add(child)
    @children << child
    self
  end

  def size = @children.sum(&:size)

  def display(indent = 0)
    puts "#{"  " * indent}📁 #{@name}/ (#{size} B)"
    @children.each { |c| c.display(indent + 1) }
  end
end

root = Directory.new("project")
  .add(File.new("README.md", 1200))
  .add(
    Directory.new("src")
      .add(File.new("main.rb", 3400))
      .add(File.new("helper.rb", 800))
  )

root.display
puts "Total: #{root.size} B"
```

**What to notice:**
- `File` and `Directory` both respond to `size` and `display` — callers never check which they have.
- `Directory#size` delegates recursively to its children; the leaf and composite cases collapse into a single `sum` call.
- Ruby's duck typing means no `Component` base class is needed — the shared interface is purely behavioral.

---

## Result Pattern

Return a typed Success or Failure value instead of raising exceptions, making error handling explicit in the call chain.

```ruby
Result = Data.define(:success, :value, :error) do
  def self.ok(value)      = new(success: true,  value: value, error: nil)
  def self.fail(message)  = new(success: false, value: nil,   error: message)
  def success?            = success
end

class UserRegistration
  MIN_PASSWORD_LENGTH = 8

  def call(email:, password:)
    return Result.fail("Email is blank")    if email.to_s.strip.empty?
    return Result.fail("Email is invalid")  unless email.include?("@")
    return Result.fail("Password too short") if password.length < MIN_PASSWORD_LENGTH

    user = { id: rand(1000), email: email }
    Result.ok(user)
  end
end

service = UserRegistration.new

[
  { email: "alice@example.com", password: "s3cur3pass" },
  { email: "bad-email",         password: "s3cur3pass" },
  { email: "alice@example.com", password: "short"      },
].each do |params|
  result = service.call(**params)
  if result.success?
    puts "Registered: #{result.value}"
  else
    puts "Failed: #{result.error}"
  end
end
```

**What to notice:**
- The caller is forced to inspect `success?` before accessing `value` — there is no way to silently ignore a failure.
- `Data.define` with class-level factory methods (`ok`, `fail`) gives a clean, immutable value object with minimal boilerplate.
- This pattern composes well with pipelines: each step returns a `Result` and downstream steps short-circuit on `failure?` — no exception unwinding needed.

---

## Enterprise Application Patterns

Patterns from Fowler's *Patterns of Enterprise Application Architecture* (PEAA). Each addresses a recurring structural problem in layered, data-intensive systems.

---

### Transaction Script

**Intent:** Encapsulate one use case as a plain procedure that reads input, performs DB calls, and returns a result.

```ruby
class TransferFunds
  def initialize(db)
    @db = db
  end

  def call(from_id:, to_id:, amount_cents:)
    from = @db.find_account(from_id)
    to   = @db.find_account(to_id)

    raise "Insufficient funds" if from[:balance] < amount_cents

    @db.transaction do
      @db.update_balance(from_id, from[:balance] - amount_cents)
      @db.update_balance(to_id,   to[:balance]  + amount_cents)
    end

    { status: :ok }
  end
end
```

**Key point:** All logic for a single use case lives in one method — simple to follow, but grows unwieldy when multiple scripts share duplicated data-access or validation code.

---

### Service Layer

**Intent:** Coordinate domain objects and repositories to expose a clean set of application operations to callers.

```ruby
class OrderService
  def initialize(order_repo:, inventory_repo:, mailer:)
    @orders    = order_repo
    @inventory = inventory_repo
    @mailer    = mailer
  end

  def place_order(customer_id:, items:)
    items.each do |item|
      raise "#{item[:sku]} out of stock" unless @inventory.available?(item[:sku], item[:qty])
    end

    order = Order.new(customer_id: customer_id, items: items)
    @orders.save(order)
    @inventory.reserve(items)
    @mailer.send_confirmation(order)

    order
  end
end
```

**Key point:** The service layer owns orchestration and transaction boundaries — domain objects stay focused on business rules, and callers (controllers, jobs) stay thin.

---

### Data Mapper

**Intent:** Move data between domain objects and the database without the domain object knowing about persistence.

```ruby
class User
  attr_accessor :id, :name, :email

  def initialize(id: nil, name:, email:)
    @id    = id
    @name  = name
    @email = email
  end
end

class UserMapper
  def initialize(db)
    @db = db
  end

  def find(id)
    row = @db.execute("SELECT id, name, email FROM users WHERE id = ?", id).first
    User.new(id: row["id"], name: row["name"], email: row["email"])
  end

  def save(user)
    if user.id
      @db.execute("UPDATE users SET name=?, email=? WHERE id=?", user.name, user.email, user.id)
    else
      @db.execute("INSERT INTO users (name, email) VALUES (?, ?)", user.name, user.email)
      user.id = @db.last_insert_row_id
    end
  end
end
```

**Key point:** `User` contains zero SQL — the mapper is the only class that knows how rows translate to objects, so domain logic and schema concerns evolve independently.

---

### Unit of Work

**Intent:** Track new, dirty, and removed objects during a business transaction and flush all changes in a single DB round-trip.

```ruby
class UnitOfWork
  def initialize(db)
    @db      = db
    @new     = []
    @dirty   = []
    @removed = []
  end

  def register_new(entity)     = @new     << entity
  def register_dirty(entity)   = @dirty   << entity
  def register_removed(entity) = @removed << entity

  def commit
    @db.transaction do
      @new.each     { |e| @db.insert(e) }
      @dirty.each   { |e| @db.update(e) }
      @removed.each { |e| @db.delete(e) }
    end
    @new.clear; @dirty.clear; @removed.clear
  end
end
```

**Key point:** Callers mutate objects and register intent; a single `commit` call issues one transaction — eliminating scattered, interleaved DB calls throughout a business operation.

---

### Data Transfer Object (DTO)

**Intent:** Carry data across layer or process boundaries using a plain, behavior-free value container.

```ruby
UserDTO = Struct.new(:id, :name, :email, keyword_init: true) do
  def self.from_domain(user)
    new(id: user.id, name: user.name, email: user.email)
  end
end

# Controller / API layer — never exposes the domain User directly
class UsersController
  def initialize(user_service)
    @service = user_service
  end

  def show(id)
    user = @service.find(id)
    UserDTO.from_domain(user)   # only serializable data crosses the boundary
  end
end
```

**Key point:** A DTO has no methods beyond construction and attribute access — it prevents callers from accidentally invoking domain logic through a reference they were only meant to read.

---

### Value Object (Money)

**Intent:** Represent a monetary amount as a frozen, equality-by-value object with no identity beyond its attributes.

```ruby
Money = Data.define(:amount_cents, :currency) do
  def +(other)
    raise "Currency mismatch" unless currency == other.currency
    Money.new(amount_cents: amount_cents + other.amount_cents, currency: currency)
  end

  def *(factor)
    Money.new(amount_cents: (amount_cents * factor).round, currency: currency)
  end

  def to_s
    "#{currency} #{"%.2f" % (amount_cents / 100.0)}"
  end
end

price    = Money.new(amount_cents: 1000, currency: "USD")
tax      = price * 0.21
total    = price + tax
puts total   # USD 12.10
```

**Key point:** `Data.define` makes the struct frozen and equality-by-value by default — two `Money` objects with the same cents and currency are `==` without any custom `eql?` or `hash` implementation.

---

### Special Case

**Intent:** Replace nil checks with a subclass that represents a missing or null entity and provides safe default behavior.

```ruby
class Customer
  attr_reader :name, :email

  def initialize(name:, email:)
    @name  = name
    @email = email
  end

  def guest? = false
end

class GuestCustomer < Customer
  def initialize
    super(name: "Guest", email: "")
  end

  def guest? = true
end

class CustomerRepository
  def find(id)
    row = @db.find(id)
    row ? Customer.new(name: row[:name], email: row[:email]) : GuestCustomer.new
  end
end

# Caller — no nil checks anywhere
customer = repo.find(params[:id])
puts "Hello, #{customer.name}"
puts "Logged in" unless customer.guest?
```

**Key point:** Moving nil-handling into a dedicated subclass eliminates scattered `if customer` guards — callers call the same interface on every return value.

---

### Gateway

**Intent:** Wrap an external API or service behind a clean interface so the rest of the codebase is insulated from third-party specifics.

```ruby
class PaymentGateway
  def initialize(http_client, api_key)
    @http    = http_client
    @api_key = api_key
  end

  def charge(amount_cents:, currency:, token:)
    response = @http.post(
      "https://pay.example.com/charges",
      headers: { "Authorization" => "Bearer #{@api_key}" },
      body:    { amount: amount_cents, currency: currency, source: token }
    )

    raise "Payment failed: #{response[:error]}" unless response[:status] == "succeeded"

    { charge_id: response[:id], amount_cents: amount_cents }
  end
end
```

**Key point:** Switching payment providers means rewriting one class — all callers use `gateway.charge(...)` and never see HTTP, authentication, or provider-specific error shapes.

---

### Query Object

**Intent:** Encapsulate filter criteria and query logic for a collection in a dedicated object, keeping repositories thin.

```ruby
class InvoiceQuery
  def initialize(status: nil, customer_id: nil, overdue_only: false)
    @status      = status
    @customer_id = customer_id
    @overdue_only = overdue_only
  end

  def call(dataset)
    result = dataset
    result = result.select { |i| i[:status]      == @status      } if @status
    result = result.select { |i| i[:customer_id] == @customer_id } if @customer_id
    result = result.select { |i| i[:due_date]    < Date.today    } if @overdue_only
    result
  end
end

# Usage
overdue = InvoiceQuery.new(status: "open", overdue_only: true).call(all_invoices)
```

**Key point:** Query criteria are composable, testable objects — the repository stays free of conditional branching, and complex filter combinations do not proliferate into repository methods.

---

### Layer Supertype

**Intent:** Provide a base class for an entire layer that supplies shared infrastructure (IDs, timestamps, equality) so concrete classes stay focused on domain logic.

```ruby
require "securerandom"

class Entity
  attr_reader :id, :created_at, :updated_at

  def initialize
    @id         = SecureRandom.uuid
    @created_at = Time.now
    @updated_at = Time.now
  end

  def touch
    @updated_at = Time.now
  end

  def ==(other)
    other.is_a?(self.class) && id == other.id
  end

  alias eql? ==

  def hash = id.hash
end

class Product < Entity
  attr_reader :name, :price_cents

  def initialize(name:, price_cents:)
    super()
    @name        = name
    @price_cents = price_cents
  end
end
```

**Key point:** Shared cross-cutting concerns (identity, timestamps, equality semantics) live in one place — concrete entities inherit them without repeating boilerplate, and changes to the policy propagate automatically across the entire layer.

---

## Remaining GoF Patterns

### Adapter

**Intent:** Wrap a third-party or legacy interface behind the duck-type interface your code expects.

```ruby
# The interface our code depends on
module PaymentGateway
  def charge(amount_cents:, currency:, token:)
    raise NotImplementedError
  end
end

# A hypothetical external gem with its own API shape
class StripeGem
  def create_charge(opts)
    puts "Stripe: charging #{opts[:amount]} #{opts[:currency]} with token #{opts[:source]}"
    { id: "ch_123", status: "succeeded" }
  end
end

class StripeAdapter
  include PaymentGateway

  def initialize(stripe_client = StripeGem.new)
    @client = stripe_client
  end

  def charge(amount_cents:, currency:, token:)
    result = @client.create_charge(amount: amount_cents, currency: currency, source: token)
    raise "Charge failed" unless result[:status] == "succeeded"
    { charge_id: result[:id], amount_cents: amount_cents }
  end
end

gateway = StripeAdapter.new
gateway.charge(amount_cents: 2000, currency: "USD", token: "tok_visa")
```

**Key point:** The adapter is the only class that knows the gem's API — swapping providers means writing a new adapter, not touching any caller.

---

### Visitor

**Intent:** Separate an algorithm from the object structure it operates on, letting new operations be added without modifying the elements.

```ruby
Heading   = Struct.new(:level, :text)
Paragraph = Struct.new(:text)

class WordCountVisitor
  attr_reader :count

  def initialize
    @count = 0
  end

  def visit_heading(node)
    @count += node.text.split.size
  end

  def visit_paragraph(node)
    @count += node.text.split.size
  end
end

class HtmlRenderVisitor
  def visit_heading(node)
    "<h#{node.level}>#{node.text}</h#{node.level}>"
  end

  def visit_paragraph(node)
    "<p>#{node.text}</p>"
  end
end

module Visitable
  def accept(visitor)
    visitor.public_send(:"visit_#{self.class.name.downcase}", self)
  end
end

Heading.include(Visitable)
Paragraph.include(Visitable)

doc = [Heading.new(1, "Hello World"), Paragraph.new("Ruby is expressive and fun.")]

counter = WordCountVisitor.new
doc.each { |node| node.accept(counter) }
puts "Words: #{counter.count}"

renderer = HtmlRenderVisitor.new
doc.each { |node| puts node.accept(renderer) }
```

**Key point:** Adding a new operation (e.g., `PlainTextVisitor`) is an additive change — the `Heading` and `Paragraph` structs are never modified.

---

### Memento

**Intent:** Capture and restore an object's internal state without exposing its implementation details.

```ruby
Memento = Struct.new(:content)

class TextEditor
  def initialize
    @content = ""
  end

  def type(text)
    @content += text
  end

  def save
    Memento.new(@content.dup)
  end

  def restore(memento)
    @content = memento.content
  end

  def to_s = @content
end

class History
  def initialize
    @stack = []
  end

  def push(memento) = @stack.push(memento)
  def pop           = @stack.pop
end

editor  = TextEditor.new
history = History.new

editor.type("Hello")
history.push(editor.save)

editor.type(", World")
history.push(editor.save)

editor.type("!!!")
puts editor          # Hello, World!!!

editor.restore(history.pop)
puts editor          # Hello, World

editor.restore(history.pop)
puts editor          # Hello
```

**Key point:** The `History` caretaker never inspects the `Memento` contents — only `TextEditor` knows how to interpret its own saved state.

---

### Prototype

**Intent:** Clone a fully configured object instead of constructing it from scratch, preserving all setup in the copy.

```ruby
class DocumentTemplate
  attr_accessor :title, :font, :margins, :sections

  def initialize(title:, font: "Arial", margins: 20)
    @title    = title
    @font     = font
    @margins  = margins
    @sections = []
  end

  def add_section(name)
    @sections << name
    self
  end

  # Shallow clone via dup; sections array is independently duplicated
  def deep_clone
    copy          = dup
    copy.sections = @sections.dup
    copy
  end

  def to_s
    "#{@title} [#{@font}, #{@margins}mm] — #{@sections.join(", ")}"
  end
end

base = DocumentTemplate.new(title: "Report", font: "Georgia", margins: 25)
base.add_section("Introduction").add_section("Summary")

invoice   = base.deep_clone.tap { |d| d.title = "Invoice";   d.sections << "Billing" }
proposal  = base.deep_clone.tap { |d| d.title = "Proposal";  d.sections << "Pricing" }

puts base      # Report [Georgia, 25mm] — Introduction, Summary
puts invoice   # Invoice [Georgia, 25mm] — Introduction, Summary, Billing
puts proposal  # Proposal [Georgia, 25mm] — Introduction, Summary, Pricing
```

**Key point:** `deep_clone` duplicates only the mutable nested structures — shared immutable values (font, margins) are safely reused, keeping copies independent without a full deep copy.

---

## DDD Tactical Patterns

### Entity

**Intent:** An object with a unique identity that persists and is compared by ID, not by attribute values.

```ruby
require "securerandom"

class Order
  attr_reader :id, :customer_id, :status

  def initialize(customer_id:)
    @id          = SecureRandom.uuid
    @customer_id = customer_id
    @status      = :pending
  end

  def confirm
    raise "Order already confirmed" if @status == :confirmed
    @status = :confirmed
  end

  def ==(other) = other.is_a?(Order) && id == other.id
  alias eql? ==
  def hash = id.hash
end
```

**Key point:** Two `Order` objects with the same `customer_id` but different `id` values are never equal — identity, not data, defines sameness.

---

### Aggregate Root

**Intent:** An entity that controls access to a cluster of objects, enforces invariants, and collects domain events internally.

```ruby
OrderItemAdded = Data.define(:order_id, :sku, :quantity, :occurred_at)

class Order
  MAX_ITEMS = 10

  attr_reader :id, :events

  def initialize(id)
    @id    = id
    @items = []
    @events = []
  end

  def add_item(sku:, quantity:)
    raise "Order is full" if @items.size >= MAX_ITEMS
    raise "Quantity must be positive" unless quantity.positive?

    @items << { sku: sku, quantity: quantity }
    @events << OrderItemAdded.new(
      order_id:    @id,
      sku:         sku,
      quantity:    quantity,
      occurred_at: Time.now
    )
  end

  def item_count = @items.size
end
```

**Key point:** External code never touches `@items` directly — all mutations go through `add_item`, which enforces invariants and records what happened as domain events.

---

### Domain Event

**Intent:** An immutable record of something that happened in the domain, carrying all relevant data at the moment it occurred.

```ruby
OrderPlaced = Data.define(:order_id, :customer_id, :total_cents, :occurred_at) do
  def self.for(order, total_cents:)
    new(
      order_id:    order.id,
      customer_id: order.customer_id,
      total_cents: total_cents,
      occurred_at: Time.now.utc
    )
  end
end

event = OrderPlaced.for(order, total_cents: 4999)
puts event.order_id
puts event.occurred_at
# event.order_id = "x"  # => FrozenError — immutable by construction
```

**Key point:** `Data.define` produces a frozen, equality-by-value struct — domain events cannot be mutated after creation, making them safe to store, publish, and replay.

---

### Specification

**Intent:** Encapsulate a business rule as a combinable predicate object that can be composed with AND, OR, and NOT.

```ruby
module Specification
  def satisfied_by?(candidate) = raise NotImplementedError
  def &(other) = AndSpecification.new(self, other)
  def |(other) = OrSpecification.new(self, other)
  def ~@       = NotSpecification.new(self)
end

AndSpecification = Struct.new(:left, :right) do
  include Specification
  def satisfied_by?(candidate) = left.satisfied_by?(candidate) && right.satisfied_by?(candidate)
end

OrSpecification = Struct.new(:left, :right) do
  include Specification
  def satisfied_by?(candidate) = left.satisfied_by?(candidate) || right.satisfied_by?(candidate)
end

NotSpecification = Struct.new(:inner) do
  include Specification
  def satisfied_by?(candidate) = !inner.satisfied_by?(candidate)
end

class ActiveCustomerSpecification
  include Specification
  def satisfied_by?(customer) = customer[:active]
end

class PremiumCustomerSpecification
  include Specification
  def satisfied_by?(customer) = customer[:tier] == :premium
end

active_premium = ActiveCustomerSpecification.new & PremiumCustomerSpecification.new
customers.select { |c| active_premium.satisfied_by?(c) }
```

---

## CQRS and Error Patterns

### Command + CommandHandler (CQRS write side)

**Intent:** Separate the write-side intent (command) from the logic that executes it (handler), keeping each independently testable.

```ruby
module Command; end
module CommandHandler
  def handle(command)
    raise NotImplementedError
  end
end

CreateUserCommand = Struct.new(:user_id, :email, :name, keyword_init: true) do
  include Command
  def initialize(**)
    super
    freeze
  end
end

class CreateUserCommandHandler
  include CommandHandler

  def initialize(user_repository, event_bus)
    @user_repository = user_repository
    @event_bus       = event_bus
  end

  def handle(command)
    user_id = UserId.new(command.user_id)
    email   = Email.new(command.email)
    user    = User.create(id: user_id, email: email, name: command.name)
    @user_repository.save(user)
    @event_bus.publish(user.pull_events)
  end
end
```

**Key point:** Commands are plain immutable structs of primitives; handlers own all orchestration so commands stay dependency-free.

---

### Object Mother

**Intent:** Centralise valid test-fixture construction behind a factory so tests read intent, not setup noise.

```ruby
module UserIdMother
  def self.random = UserId.new(SecureRandom.uuid)
end

class UserMother
  def self.random
    new(
      id:    UserIdMother.random,
      email: Email.new("user_#{SecureRandom.hex(4)}@example.com"),
      name:  "User #{rand(1000)}"
    )
  end

  def self.create(overrides = {})
    defaults = { id: UserIdMother.random,
                 email: Email.new("default@example.com"),
                 name: "Default User" }
    new(**defaults.merge(overrides))
  end

  private_class_method :new

  def initialize(id:, email:, name:)
    @id    = id
    @email = email
    @name  = name
  end
end
```

**Key point:** `random` builds a fully valid object with safe defaults; `create` accepts overrides so each test names only the attribute it cares about.

---

### DomainError hierarchy

**Intent:** Give domain errors a stable machine-readable `type` that decouples error identity from class names.

```ruby
class DomainError < StandardError
  def type
    raise NotImplementedError, "#{self.class} must implement #type"
  end
end

class UserNotFoundError < DomainError
  def initialize(user_id)
    super("User not found: #{user_id}")
    @user_id = user_id
  end

  def type = "user.not_found"
end

# Rescue by base class, then branch on type if needed
begin
  user_repository.find(id)
rescue UserNotFoundError => e
  { error: e.type, message: e.message }
rescue DomainError => e
  { error: e.type, message: e.message }
end
```

**Key point:** `type` is an explicit string constant, not `self.class.name`, so renaming a class never breaks API consumers.

---

### Either / Result type

**Intent:** Make success and failure explicit return values instead of exceptions for expected domain outcomes.

```ruby
class Result
  attr_reader :value, :error

  def self.ok(value)      = new(value: value)
  def self.failure(error) = new(error: error)

  def ok?      = @error.nil?
  def failure? = !ok?

  private

  def initialize(value: nil, error: nil)
    @value = value
    @error = error
    freeze
  end
end

# Returning a Result
def find_user(id)
  user = repository.find(id)
  user ? Result.ok(user) : Result.failure(UserNotFoundError.new(id))
end

# Caller pattern-matches on the result
result = find_user(params[:id])
if result.ok?
  render json: result.value
else
  render json: { error: result.error.type }, status: :not_found
end
```

**Key point:** Callers are forced to handle both branches at compile-read time; no hidden control-flow jumps via exceptions.

**Key point:** Business rules are named, testable objects that compose naturally — `active & premium` reads like the domain language and adds no branching to the host class.
