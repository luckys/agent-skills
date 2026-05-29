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

---

## Command

Encapsulates a request as an object, decoupling the sender from the executor and enabling undo/redo.

```php
interface Command
{
    public function execute(): void;
    public function undo(): void;
}

final class TextEditor
{
    private string $content = '';

    public function bold(string $text): void  { $this->content .= "<b>{$text}</b>"; }
    public function italic(string $text): void { $this->content .= "<i>{$text}</i>"; }
    public function removeLast(int $chars): void { $this->content = substr($this->content, 0, -$chars); }
    public function getContent(): string { return $this->content; }
}

final class BoldCommand implements Command
{
    private readonly int $insertedLength;

    public function __construct(private TextEditor $editor, private string $text)
    {
        $this->insertedLength = strlen("<b>{$text}</b>");
    }

    public function execute(): void { $this->editor->bold($this->text); }
    public function undo(): void    { $this->editor->removeLast($this->insertedLength); }
}

final class CommandHistory
{
    /** @var Command[] */
    private array $history = [];

    public function execute(Command $command): void
    {
        $command->execute();
        $this->history[] = $command;
    }

    public function undo(): void
    {
        if ($command = array_pop($this->history)) {
            $command->undo();
        }
    }
}
```

**What to notice:**
- Each command captures both the action and enough context to reverse it, making undo a first-class concern.
- `CommandHistory` orchestrates execution without knowing anything about the concrete commands it holds.
- New operations (e.g., `ItalicCommand`) are additive — no existing class changes.

---

## Template Method

Defines an algorithm skeleton in a base class; subclasses override specific steps without changing the overall structure.

```php
abstract class ReportGenerator
{
    // Template method — the invariant algorithm
    final public function generate(): string
    {
        $data = $this->gatherData();
        $formatted = $this->formatData($data);
        return $this->output($formatted);
    }

    private function gatherData(): array
    {
        return ['sales' => 42_000, 'refunds' => 1_200];
    }

    abstract protected function formatData(array $data): string;

    private function output(string $formatted): string
    {
        return $formatted;
    }
}

final class CsvReportGenerator extends ReportGenerator
{
    protected function formatData(array $data): string
    {
        return implode(',', array_keys($data)) . "\n" . implode(',', $data);
    }
}

final class PdfReportGenerator extends ReportGenerator
{
    protected function formatData(array $data): string
    {
        $lines = array_map(fn($k, $v) => "{$k}: {$v}", array_keys($data), $data);
        return "[PDF]\n" . implode("\n", $lines);
    }
}
```

**What to notice:**
- `final` on the template method prevents subclasses from breaking the algorithm's invariant structure.
- Only the varying step (`formatData`) is abstract; shared steps remain in the base class, avoiding duplication.
- Adding a new output format means writing one new subclass — nothing else changes.

---

## Chain of Responsibility

Passes a request along a chain of handlers; each handler decides to handle it or forward it.

```php
interface Middleware
{
    public function handle(array $request, callable $next): mixed;
}

final class AuthMiddleware implements Middleware
{
    public function handle(array $request, callable $next): mixed
    {
        if (empty($request['token'])) {
            return ['status' => 401, 'body' => 'Unauthorized'];
        }
        return $next($request);
    }
}

final class LoggingMiddleware implements Middleware
{
    public function handle(array $request, callable $next): mixed
    {
        echo "[LOG] Handling request to {$request['path']}\n";
        $response = $next($request);
        echo "[LOG] Response status: {$response['status']}\n";
        return $response;
    }
}

final class Pipeline
{
    /** @param Middleware[] $middlewares */
    public function __construct(private array $middlewares, private callable $handler) {}

    public function run(array $request): mixed
    {
        $chain = array_reduce(
            array_reverse($this->middlewares),
            fn(callable $next, Middleware $mw) => fn($req) => $mw->handle($req, $next),
            $this->handler,
        );
        return $chain($request);
    }
}
```

**What to notice:**
- Each middleware is unaware of what comes before or after it — coupling runs only through the `$next` callable.
- The pipeline composes handlers at construction time; reordering or inserting a middleware is a one-line change.
- The terminal handler (the real controller) is just another callable, keeping it free of middleware concerns.

---

## Iterator

Provides sequential access to a collection's elements without exposing its internal structure.

```php
final class NumberRange implements \Iterator
{
    private int $current;

    public function __construct(
        private readonly int $start,
        private readonly int $end,
        private readonly int $step = 1,
    ) {
        $this->current = $start;
    }

    public function current(): int  { return $this->current; }
    public function key(): int      { return ($this->current - $this->start) / $this->step; }
    public function next(): void    { $this->current += $this->step; }
    public function rewind(): void  { $this->current = $this->start; }
    public function valid(): bool   { return $this->current <= $this->end; }
}

// Usage
foreach (new NumberRange(start: 0, end: 10, step: 2) as $n) {
    echo $n . ' '; // 0 2 4 6 8 10
}
```

**What to notice:**
- Implementing PHP's built-in `Iterator` interface makes the custom collection a first-class citizen in `foreach` loops.
- The step logic lives entirely inside the iterator — callers never manipulate the underlying state.
- The same range can be iterated multiple times because `rewind()` resets internal state.

---

## Mediator

Centralizes communication between objects so they do not reference each other directly.

```php
interface ChatMediator
{
    public function sendMessage(string $message, User $sender): void;
}

final class ChatRoom implements ChatMediator
{
    /** @var User[] */
    private array $users = [];

    public function join(User $user): void
    {
        $this->users[] = $user;
    }

    public function sendMessage(string $message, User $sender): void
    {
        foreach ($this->users as $user) {
            if ($user !== $sender) {
                $user->receive($message, $sender->name);
            }
        }
    }
}

final class User
{
    public function __construct(
        public readonly string $name,
        private readonly ChatMediator $mediator,
    ) {}

    public function send(string $message): void
    {
        $this->mediator->sendMessage($message, $this);
    }

    public function receive(string $message, string $from): void
    {
        echo "[{$this->name}] received from {$from}: {$message}\n";
    }
}
```

**What to notice:**
- Users hold a reference to the mediator only — they have zero knowledge of other users.
- All routing logic lives in `ChatRoom`; adding features like filtering or logging touches one class.
- Replacing `ChatRoom` with a different mediator (e.g., a moderated room) requires no changes to `User`.

---

## Builder

Constructs a complex object step by step, separating its assembly from its representation.

```php
final class Query
{
    public function __construct(
        public readonly string $table,
        public readonly array $columns,
        public readonly array $conditions,
        public readonly ?int $limit,
    ) {}
}

final class QueryBuilder
{
    private array $columns = ['*'];
    private array $conditions = [];
    private ?int $limit = null;

    public function __construct(private readonly string $table) {}

    public function select(string ...$columns): static
    {
        $this->columns = $columns;
        return $this;
    }

    public function where(string $condition): static
    {
        $this->conditions[] = $condition;
        return $this;
    }

    public function limit(int $limit): static
    {
        $this->limit = $limit;
        return $this;
    }

    public function build(): Query
    {
        return new Query(
            table: $this->table,
            columns: $this->columns,
            conditions: $this->conditions,
            limit: $this->limit,
        );
    }
}

// Usage
$query = (new QueryBuilder('users'))
    ->select('id', 'email')
    ->where('active = 1')
    ->limit(25)
    ->build();
```

**What to notice:**
- Each chainable method returns `static`, preserving the builder's concrete type when subclassed.
- `build()` is the only place where the immutable `Query` value object is constructed — all validation can live there.
- The builder accumulates optional configuration without requiring long constructor argument lists.

---

## Abstract Factory

Creates families of related objects without specifying their concrete classes.

```php
interface Button
{
    public function render(): string;
}

interface Checkbox
{
    public function render(): string;
}

interface UIFactory
{
    public function createButton(): Button;
    public function createCheckbox(): Checkbox;
}

final class WindowsButton implements Button
{
    public function render(): string { return '<button class="win">OK</button>'; }
}

final class WindowsCheckbox implements Checkbox
{
    public function render(): string { return '<input type="checkbox" class="win">'; }
}

final class MacButton implements Button
{
    public function render(): string { return '<button class="mac">OK</button>'; }
}

final class MacCheckbox implements Checkbox
{
    public function render(): string { return '<input type="checkbox" class="mac">'; }
}

final class WindowsFactory implements UIFactory
{
    public function createButton(): Button     { return new WindowsButton(); }
    public function createCheckbox(): Checkbox { return new WindowsCheckbox(); }
}

final class MacFactory implements UIFactory
{
    public function createButton(): Button     { return new MacButton(); }
    public function createCheckbox(): Checkbox { return new MacCheckbox(); }
}

// Usage
function renderUI(UIFactory $factory): void
{
    echo $factory->createButton()->render() . "\n";
    echo $factory->createCheckbox()->render() . "\n";
}
```

**What to notice:**
- The factory interface guarantees that all produced objects belong to the same family — mixing Windows buttons with Mac checkboxes is impossible by construction.
- `renderUI` depends only on interfaces; swapping the entire platform requires changing one argument at the call site.
- Adding a Linux family means adding three classes and one factory — no existing code changes.

---

## Singleton

Ensures only one instance of a class exists and provides a global access point.

```php
final class Logger
{
    private static ?Logger $instance = null;
    private array $logs = [];

    private function __construct() {}

    public static function getInstance(): static
    {
        if (static::$instance === null) {
            static::$instance = new static();
        }
        return static::$instance;
    }

    public function log(string $message): void
    {
        $this->logs[] = date('H:i:s') . ' ' . $message;
        echo end($this->logs) . "\n";
    }
}

// Usage
Logger::getInstance()->log('Application started');
Logger::getInstance()->log('Request received');
```

> **Trade-off note:** Singleton is widely considered an anti-pattern. It introduces hidden global state, making behaviour hard to predict across subsystems. The static access point hides dependencies (callers do not declare them), and the single instance is shared across tests, making isolation nearly impossible without resetting global state. Prefer dependency injection: construct one instance and pass it wherever it is needed.

**What to notice:**
- The private constructor and `static::$instance` guard enforce the single-instance contract at the language level.
- Every call to `getInstance()` returns the same object, so state accumulated by one caller is visible to all others.
- In most modern applications this pattern should be replaced by a DI container that manages object lifetimes explicitly.

---

## Proxy

Provides a surrogate that controls access to another object, enabling lazy loading, access control, or logging.

```php
interface Image
{
    public function render(): string;
}

final class RealImage implements Image
{
    private readonly string $data;

    public function __construct(private readonly string $path)
    {
        // Expensive: simulates loading from disk / network
        $this->data = "pixel-data-from({$path})";
        echo "[RealImage] Loaded {$path}\n";
    }

    public function render(): string { return $this->data; }
}

final class LazyImageProxy implements Image
{
    private ?RealImage $real = null;

    public function __construct(private readonly string $path) {}

    public function render(): string
    {
        if ($this->real === null) {
            $this->real = new RealImage($this->path);
        }
        return $this->real->render();
    }
}

// Usage
$image = new LazyImageProxy('photo.jpg'); // no loading yet
echo $image->render();                    // loads on first access
echo $image->render();                    // served from cache
```

**What to notice:**
- The proxy implements the same `Image` interface, so callers are unaware they are talking to a surrogate.
- The expensive `RealImage` constructor is deferred until the resource is actually needed.
- Subsequent calls skip construction because the proxy caches the real instance after the first load.

---

## Facade

Provides a simplified interface to a complex subsystem, hiding its internal wiring from callers.

```php
final class Amplifier
{
    public function on(): void  { echo "[Amplifier] On\n"; }
    public function off(): void { echo "[Amplifier] Off\n"; }
    public function setVolume(int $level): void { echo "[Amplifier] Volume {$level}\n"; }
}

final class DVDPlayer
{
    public function on(): void           { echo "[DVD] On\n"; }
    public function off(): void          { echo "[DVD] Off\n"; }
    public function play(string $movie): void { echo "[DVD] Playing {$movie}\n"; }
}

final class Projector
{
    public function on(): void  { echo "[Projector] On\n"; }
    public function off(): void { echo "[Projector] Off\n"; }
}

final class HomeTheaterFacade
{
    public function __construct(
        private readonly Amplifier $amp,
        private readonly DVDPlayer $dvd,
        private readonly Projector $projector,
    ) {}

    public function watchMovie(string $movie): void
    {
        $this->projector->on();
        $this->amp->on();
        $this->amp->setVolume(20);
        $this->dvd->on();
        $this->dvd->play($movie);
    }

    public function endMovie(): void
    {
        $this->dvd->off();
        $this->amp->off();
        $this->projector->off();
    }
}
```

**What to notice:**
- The facade collapses a multi-step orchestration into two intent-named methods; callers never see the subsystem.
- Each subsystem class remains unchanged and can still be used directly when fine-grained control is needed.
- The facade does not add new behaviour — it only re-sequences existing calls.

---

## Bridge

Decouples an abstraction from its implementation so both hierarchies can vary independently.

```php
interface DrawingApi
{
    public function drawCircle(float $x, float $y, float $radius): string;
    public function drawSquare(float $x, float $y, float $side): string;
}

final class SvgDrawer implements DrawingApi
{
    public function drawCircle(float $x, float $y, float $radius): string
    {
        return "<circle cx=\"{$x}\" cy=\"{$y}\" r=\"{$radius}\"/>";
    }

    public function drawSquare(float $x, float $y, float $side): string
    {
        return "<rect x=\"{$x}\" y=\"{$y}\" width=\"{$side}\" height=\"{$side}\"/>";
    }
}

final class CanvasDrawer implements DrawingApi
{
    public function drawCircle(float $x, float $y, float $radius): string
    {
        return "ctx.arc({$x},{$y},{$radius},0,2*Math.PI)";
    }

    public function drawSquare(float $x, float $y, float $side): string
    {
        return "ctx.fillRect({$x},{$y},{$side},{$side})";
    }
}

abstract class Shape
{
    public function __construct(protected readonly DrawingApi $api) {}
    abstract public function draw(): string;
}

final class Circle extends Shape
{
    public function __construct(DrawingApi $api, private float $x, private float $y, private float $radius)
    {
        parent::__construct($api);
    }

    public function draw(): string { return $this->api->drawCircle($this->x, $this->y, $this->radius); }
}

final class Square extends Shape
{
    public function __construct(DrawingApi $api, private float $x, private float $y, private float $side)
    {
        parent::__construct($api);
    }

    public function draw(): string { return $this->api->drawSquare($this->x, $this->y, $this->side); }
}
```

**What to notice:**
- There are two independent variation axes — shape type and rendering technology — that can grow without a combinatorial explosion of subclasses.
- `Shape` subclasses delegate all rendering to the injected `DrawingApi`, holding zero renderer-specific logic.
- Swapping from SVG to Canvas requires changing only the injected implementation at the call site.

---

## Flyweight

Shares common intrinsic state between many fine-grained objects to reduce memory overhead.

```php
final class Font
{
    public function __construct(
        public readonly string $family,
        public readonly int $size,
    ) {}
}

final class CharacterFactory
{
    /** @var array<string, Font> */
    private array $cache = [];

    public function getFont(string $family, int $size): Font
    {
        $key = "{$family}_{$size}";
        if (!isset($this->cache[$key])) {
            $this->cache[$key] = new Font(family: $family, size: $size);
            echo "[Factory] Created font {$key}\n";
        }
        return $this->cache[$key];
    }

    public function cacheSize(): int { return count($this->cache); }
}

final class Character
{
    public function __construct(
        public readonly string $char,
        public readonly Font $font,  // shared flyweight
        public readonly int $x,      // extrinsic (unique per character)
        public readonly int $y,
    ) {}
}

// Usage: 1 000 characters share just 2 Font objects
$factory = new CharacterFactory();
$characters = [];
for ($i = 0; $i < 1_000; $i++) {
    $characters[] = new Character(
        char: chr(65 + ($i % 26)),
        font: $factory->getFont('Arial', 12),
        x: $i * 8,
        y: 0,
    );
}
echo $factory->cacheSize(); // 1
```

**What to notice:**
- Intrinsic state (font family + size) lives in a shared `Font` object; extrinsic state (x, y coordinates) stays in `Character`.
- The factory is the only place that decides whether to reuse or create — callers never manage the cache.
- 1 000 characters share one `Font` instance; without Flyweight each would hold its own copy.

---

## Composite

Treats individual objects and compositions uniformly through a shared interface.

```php
interface FilesystemNode
{
    public function getName(): string;
    public function getSize(): int;
}

final class File implements FilesystemNode
{
    public function __construct(
        private readonly string $name,
        private readonly int $size,
    ) {}

    public function getName(): string { return $this->name; }
    public function getSize(): int    { return $this->size; }
}

final class Directory implements FilesystemNode
{
    /** @var FilesystemNode[] */
    private array $children = [];

    public function __construct(private readonly string $name) {}

    public function add(FilesystemNode $node): void { $this->children[] = $node; }

    public function getName(): string { return $this->name; }

    public function getSize(): int
    {
        return array_sum(array_map(fn($n) => $n->getSize(), $this->children));
    }
}

// Usage
$root = new Directory('root');
$src  = new Directory('src');
$src->add(new File('main.php', 1_200));
$src->add(new File('helper.php', 800));
$root->add($src);
$root->add(new File('README.md', 300));

echo $root->getSize(); // 2300
```

**What to notice:**
- Client code calls `getSize()` on `FilesystemNode` without knowing whether it is a leaf or a subtree.
- `Directory::getSize()` recurses naturally — the tree structure is encoded in the object graph, not in conditional logic.
- Adding a new node type (e.g., `Symlink`) only requires implementing `FilesystemNode`.

---

## Result Pattern

Returns a typed Success/Failure value object instead of throwing exceptions, making error paths explicit in the type system.

```php
final class Result
{
    private function __construct(
        private readonly bool $success,
        private readonly mixed $value,
        private readonly ?string $error,
    ) {}

    public static function success(mixed $value): static
    {
        return new static(true, $value, null);
    }

    public static function failure(string $error): static
    {
        return new static(false, null, $error);
    }

    public function isSuccess(): bool   { return $this->success; }
    public function getValue(): mixed   { return $this->value; }
    public function getError(): ?string { return $this->error; }
}

final class UserRegistration
{
    public function register(string $email, string $password): Result
    {
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            return Result::failure('Invalid email address');
        }
        if (strlen($password) < 8) {
            return Result::failure('Password must be at least 8 characters');
        }
        // ... persist user ...
        return Result::success(['id' => 42, 'email' => $email]);
    }
}

// Usage
$result = (new UserRegistration())->register('user@example.com', 'secret123');

if ($result->isSuccess()) {
    echo 'Registered: ' . $result->getValue()['email'];
} else {
    echo 'Error: ' . $result->getError();
}
```

**What to notice:**
- Callers are forced to check `isSuccess()` before accessing the value — the error path cannot be silently ignored.
- No exception crosses a method boundary; failures are first-class return values, making them easy to test and compose.
- Named constructors (`success` / `failure`) keep the distinction clear at the call site without exposing the constructor's boolean flag.

---

## Enterprise Application Patterns

### Transaction Script

**Intent:** Organizes business logic for a single use case as a procedure that calls the database directly.

```php
final class TransferFunds
{
    public function __construct(private readonly \PDO $db) {}

    public function execute(int $fromId, int $toId, int $amountCents): void
    {
        $this->db->beginTransaction();
        try {
            $stmt = $this->db->prepare('SELECT balance FROM accounts WHERE id = ? FOR UPDATE');
            $stmt->execute([$fromId]);
            $from = $stmt->fetch();

            if ($from['balance'] < $amountCents) {
                throw new \DomainException('Insufficient funds');
            }

            $this->db->prepare('UPDATE accounts SET balance = balance - ? WHERE id = ?')
                ->execute([$amountCents, $fromId]);
            $this->db->prepare('UPDATE accounts SET balance = balance + ? WHERE id = ?')
                ->execute([$amountCents, $toId]);

            $this->db->commit();
        } catch (\Throwable $e) {
            $this->db->rollBack();
            throw $e;
        }
    }
}
```

**Key point:** All logic for one use case lives in one method — appropriate for simple workflows where domain objects would add indirection without value.

---

### Service Layer

**Intent:** Defines application operations that coordinate domain objects, repositories, and infrastructure without leaking domain logic into controllers.

```php
final class OrderService
{
    public function __construct(
        private readonly OrderRepository $orders,
        private readonly InventoryRepository $inventory,
        private readonly EventDispatcher $events,
    ) {}

    public function placeOrder(int $customerId, array $lineItems): Order
    {
        foreach ($lineItems as $item) {
            $this->inventory->reserve($item['sku'], $item['qty']);
        }

        $order = Order::create(customerId: $customerId, lines: $lineItems);
        $this->orders->save($order);
        $this->events->dispatch(new OrderPlaced($order->id()));

        return $order;
    }
}
```

**Key point:** The service layer is the only entry point for application operations — controllers stay thin and domain objects stay free of infrastructure concerns.

---

### Data Mapper

**Intent:** Transfers data between in-memory domain objects and the database while keeping domain objects unaware of persistence.

```php
final class User
{
    public function __construct(
        public readonly int $id,
        public readonly string $name,
        public readonly string $email,
    ) {}
}

final class UserMapper
{
    public function __construct(private readonly \PDO $db) {}

    public function findById(int $id): ?User
    {
        $stmt = $this->db->prepare('SELECT id, name, email FROM users WHERE id = ?');
        $stmt->execute([$id]);
        $row = $stmt->fetch(\PDO::FETCH_ASSOC);

        return $row ? new User(id: $row['id'], name: $row['name'], email: $row['email']) : null;
    }

    public function insert(User $user): void
    {
        $this->db->prepare('INSERT INTO users (name, email) VALUES (?, ?)')
            ->execute([$user->name, $user->email]);
    }
}
```

**Key point:** `User` contains zero SQL — all mapping logic is isolated in `UserMapper`, so the domain object can be tested without a database.

---

### Unit of Work

**Intent:** Tracks which domain objects have been created, changed, or removed during a request and writes all changes in a single transaction at the end.

```php
final class UnitOfWork
{
    private array $new     = [];
    private array $dirty   = [];
    private array $removed = [];

    public function __construct(private readonly \PDO $db) {}

    public function registerNew(object $entity): void    { $this->new[]     = $entity; }
    public function registerDirty(object $entity): void  { $this->dirty[]   = $entity; }
    public function registerRemoved(object $entity): void { $this->removed[] = $entity; }

    public function commit(UserMapper $mapper): void
    {
        $this->db->beginTransaction();
        try {
            foreach ($this->new     as $e) { $mapper->insert($e); }
            foreach ($this->dirty   as $e) { $mapper->update($e); }
            foreach ($this->removed as $e) { $mapper->delete($e); }
            $this->db->commit();
        } catch (\Throwable $e) {
            $this->db->rollBack();
            throw $e;
        }
        $this->new = $this->dirty = $this->removed = [];
    }
}
```

**Key point:** Business code mutates objects freely during a request and calls `commit()` once — the Unit of Work batches all writes into one atomic transaction.

---

### Data Transfer Object (DTO)

**Intent:** Carries data across layer boundaries as a plain, behavior-free structure.

```php
final readonly class CreateUserRequest
{
    public function __construct(
        public string $name,
        public string $email,
        public string $role,
    ) {}
}

final readonly class UserResponse
{
    public function __construct(
        public int    $id,
        public string $name,
        public string $email,
    ) {}
}

// Controller → Service
$request = new CreateUserRequest(name: 'Alice', email: 'alice@example.com', role: 'editor');
$service->createUser($request);

// Service → Controller
return new UserResponse(id: 42, name: 'Alice', email: 'alice@example.com');
```

**Key point:** A `readonly` DTO is an immutable data envelope — it carries no validation, no business rules, and no dependencies, making it safe to serialize and pass across any boundary.

---

### Value Object (Money)

**Intent:** Represents a monetary amount as an immutable object with value semantics and domain-aware arithmetic.

```php
final readonly class Money
{
    public function __construct(
        public int    $amount,   // minor units (cents)
        public string $currency, // ISO 4217
    ) {}

    public function add(Money $other): self
    {
        $this->assertSameCurrency($other);
        return new self($this->amount + $other->amount, $this->currency);
    }

    public function multiply(float $factor): self
    {
        return new self((int) round($this->amount * $factor), $this->currency);
    }

    public function equals(Money $other): bool
    {
        return $this->amount === $other->amount && $this->currency === $other->currency;
    }

    private function assertSameCurrency(Money $other): void
    {
        if ($this->currency !== $other->currency) {
            throw new \DomainException("Cannot mix {$this->currency} and {$other->currency}");
        }
    }
}

$price = new Money(1000, 'USD');
$tax   = $price->multiply(0.08);
$total = $price->add($tax);   // Money(1080, 'USD')
```

**Key point:** Immutability and same-currency guards make `Money` safe to pass anywhere — arithmetic always returns a new instance, so the original is never mutated by accident.

---

### Special Case

**Intent:** Replaces null checks by providing a subclass that represents a missing or default entity with safe, do-nothing behavior.

```php
abstract class Customer
{
    abstract public function getName(): string;
    abstract public function getDiscount(): float;
    abstract public function isGuest(): bool;
}

final class RegisteredCustomer extends Customer
{
    public function __construct(private readonly string $name, private readonly float $discount) {}

    public function getName(): string    { return $this->name; }
    public function getDiscount(): float { return $this->discount; }
    public function isGuest(): bool      { return false; }
}

final class GuestCustomer extends Customer   // Special Case
{
    public function getName(): string    { return 'Guest'; }
    public function getDiscount(): float { return 0.0; }
    public function isGuest(): bool      { return true; }
}

// Usage — no null checks anywhere
function greet(Customer $customer): string
{
    return "Hello, {$customer->getName()}! Your discount: {$customer->getDiscount()}%";
}
```

**Key point:** `GuestCustomer` eliminates `if ($customer === null)` guards throughout the codebase by giving the "missing" case real, predictable behavior.

---

### Gateway

**Intent:** Wraps an external API or service behind a clean, domain-vocabulary interface so the rest of the application never depends on third-party details.

```php
interface CurrencyGateway
{
    /** Returns the exchange rate from $from to $to. */
    public function getRate(string $from, string $to): float;
}

final class HttpCurrencyGateway implements CurrencyGateway
{
    public function __construct(
        private readonly string $baseUrl,
        private readonly string $apiKey,
    ) {}

    public function getRate(string $from, string $to): float
    {
        $url      = "{$this->baseUrl}/rates?base={$from}&symbols={$to}&apikey={$this->apiKey}";
        $response = json_decode(file_get_contents($url), true);

        return (float) $response['rates'][$to];
    }
}

final class StubCurrencyGateway implements CurrencyGateway
{
    public function getRate(string $from, string $to): float { return 1.08; }
}
```

**Key point:** Domain code depends only on `CurrencyGateway` — swapping the HTTP provider for a stub in tests, or migrating to a different API, requires changing one class.

---

### Query Object

**Intent:** Encapsulates filter criteria for a collection query as a first-class object, keeping query-building logic out of repositories and controllers.

```php
final class ProductQuery
{
    private ?string $category = null;
    private ?int    $maxPrice = null;
    private bool    $inStock  = false;

    public function inCategory(string $category): static
    {
        $clone           = clone $this;
        $clone->category = $category;
        return $clone;
    }

    public function cheaperThan(int $cents): static
    {
        $clone           = clone $this;
        $clone->maxPrice = $cents;
        return $clone;
    }

    public function onlyInStock(): static
    {
        $clone          = clone $this;
        $clone->inStock = true;
        return $clone;
    }

    public function toSql(): array   // returns [sql, bindings]
    {
        $where    = ['1=1'];
        $bindings = [];

        if ($this->category !== null) { $where[] = 'category = ?'; $bindings[] = $this->category; }
        if ($this->maxPrice  !== null) { $where[] = 'price <= ?';   $bindings[] = $this->maxPrice; }
        if ($this->inStock)            { $where[] = 'stock > 0'; }

        return ['SELECT * FROM products WHERE ' . implode(' AND ', $where), $bindings];
    }
}

// Usage
$query = (new ProductQuery())->inCategory('books')->cheaperThan(2000)->onlyInStock();
[$sql, $bindings] = $query->toSql();
```

**Key point:** Each filter is an immutable clone operation, making Query Objects composable, testable, and safe to reuse without risking cross-request state leakage.

---

### Layer Supertype

**Intent:** Provides a base class for an entire layer that centralizes shared infrastructure — IDs, timestamps, equality — so concrete classes inherit it without repeating it.

```php
abstract class Entity
{
    private readonly string $id;
    private readonly \DateTimeImmutable $createdAt;
    private \DateTimeImmutable $updatedAt;

    public function __construct()
    {
        $this->id        = bin2hex(random_bytes(16));
        $this->createdAt = new \DateTimeImmutable();
        $this->updatedAt = $this->createdAt;
    }

    public function id(): string                        { return $this->id; }
    public function createdAt(): \DateTimeImmutable      { return $this->createdAt; }
    public function updatedAt(): \DateTimeImmutable      { return $this->updatedAt; }

    protected function touch(): void
    {
        $this->updatedAt = new \DateTimeImmutable();
    }

    public function equals(self $other): bool
    {
        return $this->id === $other->id;
    }
}

final class Product extends Entity
{
    public function __construct(private string $name, private int $priceCents)
    {
        parent::__construct();
    }

    public function rename(string $name): void
    {
        $this->name = $name;
        $this->touch();
    }
}
```

**Key point:** Identity generation, timestamp management, and equality by ID are written once in `Entity` — every domain class that extends it gets this infrastructure for free without any duplication.

---

## Remaining GoF Patterns

### Adapter

**Intent:** Wrap a third-party or legacy interface behind the interface your code expects.

```php
interface PaymentGatewayInterface
{
    public function charge(int $amountCents, string $currency): string;
}

// Third-party SDK we cannot modify
final class StripeClient
{
    public function createCharge(array $params): array
    {
        // Stripe-specific call
        return ['id' => 'ch_abc123', 'status' => 'succeeded'];
    }
}

final class StripeGatewayAdapter implements PaymentGatewayInterface
{
    public function __construct(private readonly StripeClient $stripe) {}

    public function charge(int $amountCents, string $currency): string
    {
        $result = $this->stripe->createCharge([
            'amount'   => $amountCents,
            'currency' => strtolower($currency),
        ]);
        return $result['id'];
    }
}

// Usage — domain code depends only on PaymentGatewayInterface
function processPayment(PaymentGatewayInterface $gateway): void
{
    $transactionId = $gateway->charge(4999, 'USD');
    echo "Charged: {$transactionId}\n";
}
```

**Key point:** The adapter translates the external SDK's vocabulary into your domain interface so application code never imports Stripe types directly.

---

### Visitor

**Intent:** Separate an algorithm from the object structure it operates on.

```php
interface DocumentElement
{
    public function accept(DocumentVisitor $visitor): mixed;
}

interface DocumentVisitor
{
    public function visitHeading(Heading $heading): mixed;
    public function visitParagraph(Paragraph $paragraph): mixed;
}

final class Heading implements DocumentElement
{
    public function __construct(public readonly string $text, public readonly int $level) {}
    public function accept(DocumentVisitor $visitor): mixed { return $visitor->visitHeading($this); }
}

final class Paragraph implements DocumentElement
{
    public function __construct(public readonly string $text) {}
    public function accept(DocumentVisitor $visitor): mixed { return $visitor->visitParagraph($this); }
}

final class WordCountVisitor implements DocumentVisitor
{
    public function visitHeading(Heading $h): int   { return str_word_count($h->text); }
    public function visitParagraph(Paragraph $p): int { return str_word_count($p->text); }
}

final class HtmlRenderVisitor implements DocumentVisitor
{
    public function visitHeading(Heading $h): string
    {
        return "<h{$h->level}>{$h->text}</h{$h->level}>";
    }
    public function visitParagraph(Paragraph $p): string
    {
        return "<p>{$p->text}</p>";
    }
}
```

**Key point:** New operations (word count, HTML render, PDF export) are added as new visitor classes without touching the element hierarchy.

---

### Memento

**Intent:** Capture and restore object state without exposing internals.

```php
final class Memento
{
    public function __construct(private readonly string $content) {}
    public function getContent(): string { return $this->content; }
}

final class TextEditor
{
    private string $content = '';

    public function type(string $text): void { $this->content .= $text; }
    public function getContent(): string     { return $this->content; }

    public function save(): Memento          { return new Memento($this->content); }
    public function restore(Memento $m): void { $this->content = $m->getContent(); }
}

final class History
{
    /** @var Memento[] */
    private array $snapshots = [];

    public function push(Memento $memento): void { $this->snapshots[] = $memento; }

    public function pop(): ?Memento { return array_pop($this->snapshots); }
}

// Usage
$editor  = new TextEditor();
$history = new History();

$editor->type('Hello');
$history->push($editor->save());

$editor->type(', world!');
$history->push($editor->save());

$editor->type(' — oops');
$editor->restore($history->pop()); // undo "— oops"

echo $editor->getContent(); // Hello, world!
```

**Key point:** `Memento` is opaque to the caretaker (`History`) — state is captured and restored without leaking the editor's internals.

---

### Prototype

**Intent:** Clone a configured object instead of constructing it from scratch.

```php
final class DocumentTemplate
{
    public function __construct(
        public string $title,
        public string $footer,
        public array  $sections,
    ) {}

    public function __clone(): void
    {
        // Deep-copy mutable nested state so clones are independent
        $this->sections = array_map(fn(array $s) => $s, $this->sections);
    }

    public function withTitle(string $title): static
    {
        $clone        = clone $this;
        $clone->title = $title;
        return $clone;
    }

    public function addSection(string $heading, string $body): static
    {
        $clone = clone $this;
        $clone->sections[] = ['heading' => $heading, 'body' => $body];
        return $clone;
    }
}

// One configured prototype; stamp out variants cheaply
$base = new DocumentTemplate(
    title:    'Monthly Report',
    footer:   'Confidential — Acme Corp',
    sections: [],
);

$q1Report = $base->withTitle('Q1 Report')->addSection('Summary', 'Q1 exceeded targets.');
$q2Report = $base->withTitle('Q2 Report')->addSection('Summary', 'Q2 on track.');

echo $q1Report->title;             // Q1 Report
echo count($q2Report->sections);   // 1
```

**Key point:** `clone` combined with `__clone()` for deep-copying nested arrays keeps each stamped document fully independent from the prototype and from each other.

---

## DDD Tactical Patterns

### Entity

**Intent:** An object with a unique identity that persists and is compared by ID, not by attribute values.

```php
final class Order
{
    private readonly string $id;
    private string $status;

    public function __construct(
        public readonly string $customerId,
    ) {
        $this->id     = bin2hex(random_bytes(16));
        $this->status = 'pending';
    }

    public function id(): string     { return $this->id; }
    public function status(): string { return $this->status; }

    public function confirm(): void
    {
        if ($this->status === 'confirmed') {
            throw new \DomainException('Order already confirmed');
        }
        $this->status = 'confirmed';
    }

    public function equals(self $other): bool
    {
        return $this->id === $other->id;
    }
}
```

**Key point:** Two `Order` objects with the same `customerId` but different `id` values are never equal — identity, not data, defines sameness.

---

### Aggregate Root

**Intent:** An entity that controls access to a cluster of objects, enforces invariants, and collects domain events internally.

```php
final class OrderItemAdded
{
    public function __construct(
        public readonly string $orderId,
        public readonly string $sku,
        public readonly int    $quantity,
        public readonly \DateTimeImmutable $occurredAt,
    ) {}
}

final class Order
{
    private const MAX_ITEMS = 10;

    private array $items  = [];
    private array $events = [];

    public function __construct(private readonly string $id) {}

    public function addItem(string $sku, int $quantity): void
    {
        if (count($this->items) >= self::MAX_ITEMS) {
            throw new \DomainException('Order is full');
        }
        if ($quantity < 1) {
            throw new \DomainException('Quantity must be positive');
        }

        $this->items[] = ['sku' => $sku, 'quantity' => $quantity];
        $this->events[] = new OrderItemAdded($this->id, $sku, $quantity, new \DateTimeImmutable());
    }

    public function releaseEvents(): array { $e = $this->events; $this->events = []; return $e; }
    public function itemCount(): int       { return count($this->items); }
}
```

**Key point:** External code never touches `$items` directly — all mutations go through `addItem`, which enforces invariants and records what happened as domain events.

---

### Domain Event

**Intent:** An immutable record of something that happened in the domain, carrying all relevant data at the moment it occurred.

```php
final readonly class OrderPlaced
{
    public \DateTimeImmutable $occurredAt;

    public function __construct(
        public string $orderId,
        public string $customerId,
        public int    $totalCents,
    ) {
        $this->occurredAt = new \DateTimeImmutable();
    }
}

// Usage
$event = new OrderPlaced(
    orderId:     $order->id(),
    customerId:  $order->customerId,
    totalCents:  4999,
);

echo $event->orderId;
echo $event->occurredAt->format(\DATE_ATOM);
// $event->orderId = 'x';  // Fatal — readonly properties cannot be mutated
```

**Key point:** `readonly` on the class makes every property immutable after construction — domain events cannot be altered after they are created, making them safe to store, publish, and replay.

---

### Specification

**Intent:** Encapsulate a business rule as a combinable predicate object that can be composed with AND, OR, and NOT.

```php
interface Specification
{
    public function isSatisfiedBy(object $candidate): bool;
    public function and(Specification $other): Specification;
    public function or(Specification $other): Specification;
    public function not(): Specification;
}

abstract class AbstractSpecification implements Specification
{
    public function and(Specification $other): Specification
    {
        return new class($this, $other) extends AbstractSpecification {
            public function __construct(private Specification $a, private Specification $b) {}
            public function isSatisfiedBy(object $c): bool { return $this->a->isSatisfiedBy($c) && $this->b->isSatisfiedBy($c); }
        };
    }

    public function or(Specification $other): Specification
    {
        return new class($this, $other) extends AbstractSpecification {
            public function __construct(private Specification $a, private Specification $b) {}
            public function isSatisfiedBy(object $c): bool { return $this->a->isSatisfiedBy($c) || $this->b->isSatisfiedBy($c); }
        };
    }

    public function not(): Specification
    {
        return new class($this) extends AbstractSpecification {
            public function __construct(private Specification $inner) {}
            public function isSatisfiedBy(object $c): bool { return !$this->inner->isSatisfiedBy($c); }
        };
    }
}

final class ActiveCustomerSpecification extends AbstractSpecification
{
    public function isSatisfiedBy(object $customer): bool { return $customer->active; }
}

final class PremiumCustomerSpecification extends AbstractSpecification
{
    public function isSatisfiedBy(object $customer): bool { return $customer->tier === 'premium'; }
}

// Usage
$spec = (new ActiveCustomerSpecification())->and(new PremiumCustomerSpecification());
$eligible = array_filter($customers, fn($c) => $spec->isSatisfiedBy($c));
```

---

## CQRS and Error Patterns

### Command + CommandHandler (CQRS write side)

**Intent:** Separate the write-side intent (command) from the logic that executes it (handler), keeping each independently testable.

```php
interface Command {}

interface CommandHandler
{
    public function handle(Command $command): void;
}

final readonly class CreateUserCommand implements Command
{
    public function __construct(
        public string $userId,
        public string $email,
        public string $name,
    ) {}
}

final class CreateUserCommandHandler implements CommandHandler
{
    public function __construct(
        private UserRepository $userRepository,
        private EventBus $eventBus,
    ) {}

    public function handle(Command $command): void
    {
        $userId = new UserId($command->userId);
        $email  = new Email($command->email);
        $user   = User::create($userId, $email, $command->name);
        $this->userRepository->save($user);
        $this->eventBus->publish($user->pullEvents());
    }
}
```

**Key point:** Commands are readonly value objects of primitives; handlers own all orchestration so commands stay dependency-free.

---

### Object Mother

**Intent:** Centralise valid test-fixture construction behind a factory so tests read intent, not setup noise.

```php
final class UserIdMother
{
    public static function random(): UserId
    {
        return new UserId(uuid_create());
    }
}

final class UserMother
{
    public static function random(): User
    {
        $hex = bin2hex(random_bytes(4));
        return new User(
            id:    UserIdMother::random(),
            email: new Email("user_{$hex}@example.com"),
            name:  'User ' . rand(1, 1000),
        );
    }

    public static function create(array $overrides = []): User
    {
        $defaults = [
            'id'    => UserIdMother::random(),
            'email' => new Email('default@example.com'),
            'name'  => 'Default User',
        ];
        $data = array_merge($defaults, $overrides);
        return new User($data['id'], $data['email'], $data['name']);
    }
}
```

**Key point:** `random()` builds a fully valid object with safe defaults; `create()` accepts overrides so each test names only the attribute it cares about.

---

### DomainError hierarchy

**Intent:** Give domain errors a stable machine-readable `type` that decouples error identity from class names.

```php
abstract class DomainError extends \RuntimeException
{
    abstract public function type(): string;
}

final class UserNotFoundError extends DomainError
{
    public function __construct(private readonly string $userId)
    {
        parent::__construct("User not found: {$userId}");
    }

    public function type(): string
    {
        return 'user.not_found';
    }
}

// Catch by base class, branch on type() if needed
try {
    $userRepository->find($id);
} catch (UserNotFoundError $e) {
    return ['error' => $e->type(), 'message' => $e->getMessage()];
} catch (DomainError $e) {
    return ['error' => $e->type(), 'message' => $e->getMessage()];
}
```

**Key point:** `type()` is an explicit string constant, not `static::class`, so renaming a class never breaks API consumers.

---

### Either / Result type

**Intent:** Make success and failure explicit return values instead of exceptions for expected domain outcomes.

```php
final class Result
{
    private function __construct(
        private readonly mixed $value,
        private readonly mixed $error,
    ) {}

    public static function ok(mixed $value): self    { return new self($value, null); }
    public static function failure(mixed $error): self { return new self(null, $error); }

    public function isOk(): bool      { return $this->error === null; }
    public function isFailure(): bool { return !$this->isOk(); }
    public function value(): mixed    { return $this->value; }
    public function error(): mixed    { return $this->error; }
}

// Returning a Result
function findUser(string $id, UserRepository $repo): Result
{
    $user = $repo->find($id);
    return $user !== null ? Result::ok($user) : Result::failure(new UserNotFoundError($id));
}

// Caller pattern-matches on the result
$result = findUser($request->id, $userRepository);
if ($result->isOk()) {
    return new JsonResponse($result->value());
}
return new JsonResponse(['error' => $result->error()->type()], 404);
```

**Key point:** Callers are forced to handle both branches explicitly; no hidden control-flow jumps via exceptions.

**Key point:** Business rules are named, testable objects that compose naturally — `and`/`or`/`not` read like domain language and add no branching to the host class.
