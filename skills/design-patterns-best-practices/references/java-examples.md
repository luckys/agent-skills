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

---

## Command

Encapsulates a request as an object, decoupling the sender from the executor and enabling undo/redo support.

```java
public interface Command {
    void execute();
    void undo();
}

public final class BoldCommand implements Command {
    private final TextEditor editor;
    private String previousText;

    public BoldCommand(TextEditor editor) { this.editor = editor; }

    public void execute() {
        previousText = editor.getText();
        editor.setText("**" + previousText + "**");
    }

    public void undo() { editor.setText(previousText); }
}

public final class ItalicCommand implements Command {
    private final TextEditor editor;
    private String previousText;

    public ItalicCommand(TextEditor editor) { this.editor = editor; }

    public void execute() {
        previousText = editor.getText();
        editor.setText("_" + previousText + "_");
    }

    public void undo() { editor.setText(previousText); }
}

public final class TextEditor {
    private String text;
    private final Deque<Command> history = new ArrayDeque<>();

    public TextEditor(String text) { this.text = text; }

    public String getText() { return text; }
    public void setText(String text) { this.text = text; }

    public void executeCommand(Command command) {
        command.execute();
        history.push(command);
    }

    public void undoLast() {
        if (!history.isEmpty()) history.pop().undo();
    }
}
```

**What to notice:**
- Each command captures enough state (`previousText`) to reverse itself — undo is a first-class concern, not an afterthought.
- `TextEditor` never knows which command it is running; it only sees the `Command` interface.
- Commands can be queued, logged, or replayed without changing the editor or the command implementations.

---

## Template Method

Defines an algorithm skeleton in a base class; subclasses override specific steps without changing the overall structure.

```java
public abstract class ReportGenerator {
    // Template method — the fixed algorithm skeleton
    public final void generate() {
        Object data = gatherData();
        String formatted = formatData(data);
        output(formatted);
    }

    protected abstract Object gatherData();
    protected abstract String formatData(Object data);

    protected void output(String content) {
        System.out.println(content);
    }
}

public final class CsvReportGenerator extends ReportGenerator {
    protected Object gatherData() { return List.of("Alice,30", "Bob,25"); }

    protected String formatData(Object data) {
        @SuppressWarnings("unchecked")
        List<String> rows = (List<String>) data;
        return "name,age\n" + String.join("\n", rows);
    }
}

public final class PdfReportGenerator extends ReportGenerator {
    protected Object gatherData() { return List.of("Alice, age 30", "Bob, age 25"); }

    protected String formatData(Object data) {
        @SuppressWarnings("unchecked")
        List<String> rows = (List<String>) data;
        return "[PDF] " + String.join(" | ", rows);
    }
}
```

**What to notice:**
- `generate()` is `final` — subclasses cannot reorder or skip steps.
- Only the varying steps (`gatherData`, `formatData`) are abstract; shared behavior (`output`) lives in the base class.
- Adding a new format (e.g., JSON) requires only a new subclass, not touching the algorithm skeleton.

---

## Chain of Responsibility

Passes a request along a chain of handlers; each handler decides to process it, enrich it, or pass it forward.

```java
public record HttpRequest(String path, String authToken) {}
public record HttpResponse(int status, String body) {}

@FunctionalInterface
public interface Middleware {
    HttpResponse handle(HttpRequest request, Middleware next);
}

public final class AuthMiddleware implements Middleware {
    public HttpResponse handle(HttpRequest request, Middleware next) {
        if (request.authToken() == null || request.authToken().isBlank()) {
            return new HttpResponse(401, "Unauthorized");
        }
        return next.handle(request, next);
    }
}

public final class LoggingMiddleware implements Middleware {
    private final Middleware inner;

    public LoggingMiddleware(Middleware inner) { this.inner = inner; }

    public HttpResponse handle(HttpRequest request, Middleware next) {
        System.out.println("[LOG] " + request.path());
        return inner.handle(request, next);
    }
}

public final class FinalHandler implements Middleware {
    public HttpResponse handle(HttpRequest request, Middleware next) {
        return new HttpResponse(200, "OK: " + request.path());
    }
}
```

**What to notice:**
- Each middleware is unaware of what comes before or after it in the chain — it only calls `next`.
- The chain is assembled at the call site, making the order explicit and easy to change.
- Short-circuiting (e.g., returning 401) stops propagation without any conditional in the surrounding code.

---

## Iterator

Provides sequential access to elements of a collection without exposing its internal representation.

```java
public final class NumberRange implements Iterable<Integer> {
    private final int start;
    private final int end;
    private final int step;

    public NumberRange(int start, int end, int step) {
        this.start = start;
        this.end = end;
        this.step = step;
    }

    @Override
    public Iterator<Integer> iterator() {
        return new Iterator<>() {
            private int current = start;

            public boolean hasNext() { return current <= end; }

            public Integer next() {
                if (!hasNext()) throw new NoSuchElementException();
                int value = current;
                current += step;
                return value;
            }
        };
    }
}

// Usage
for (int n : new NumberRange(1, 10, 2)) {
    System.out.println(n); // 1, 3, 5, 7, 9
}
```

**What to notice:**
- Implementing `Iterable<Integer>` integrates with Java's for-each loop and the entire `java.util` ecosystem.
- The iteration state (`current`) lives inside the anonymous `Iterator` — multiple iterators over the same range are independent.
- Callers never know whether the source is an array, a DB cursor, or a computed sequence.

---

## Mediator

Centralizes communication between objects so they don't reference each other directly, reducing a many-to-many coupling to a one-to-many hub.

```java
public interface ChatMediator {
    void sendMessage(String message, User sender);
}

public final class ChatRoom implements ChatMediator {
    private final List<User> participants = new ArrayList<>();

    public void join(User user) { participants.add(user); }

    public void sendMessage(String message, User sender) {
        participants.stream()
            .filter(u -> u != sender)
            .forEach(u -> u.receive(sender.getName() + ": " + message));
    }
}

public final class User {
    private final String name;
    private final ChatMediator mediator;

    public User(String name, ChatMediator mediator) {
        this.name = name;
        this.mediator = mediator;
    }

    public String getName() { return name; }

    public void send(String message) { mediator.sendMessage(message, this); }

    public void receive(String message) {
        System.out.println("[" + name + "] received: " + message);
    }
}
```

**What to notice:**
- `User` objects hold a reference to the mediator only — they never reference other users directly.
- Adding a new participant or a new routing rule (e.g., private messages) changes only `ChatRoom`.
- The mediator pattern trades direct object coupling for centralized coordination logic.

---

## Builder

Constructs a complex object step by step using a fluent API, separating configuration from the final object.

```java
public final class Query {
    private final String table;
    private final List<String> columns;
    private final String whereClause;
    private final int limit;

    private Query(Builder builder) {
        this.table = builder.table;
        this.columns = List.copyOf(builder.columns);
        this.whereClause = builder.whereClause;
        this.limit = builder.limit;
    }

    @Override
    public String toString() {
        String cols = columns.isEmpty() ? "*" : String.join(", ", columns);
        String sql = "SELECT " + cols + " FROM " + table;
        if (whereClause != null) sql += " WHERE " + whereClause;
        if (limit > 0) sql += " LIMIT " + limit;
        return sql;
    }

    public static final class Builder {
        private final String table;
        private final List<String> columns = new ArrayList<>();
        private String whereClause;
        private int limit;

        public Builder(String table) { this.table = table; }

        public Builder select(String... cols) { columns.addAll(List.of(cols)); return this; }
        public Builder where(String clause)   { this.whereClause = clause; return this; }
        public Builder limit(int n)           { this.limit = n; return this; }
        public Query build()                  { return new Query(this); }
    }
}

// Usage
Query q = new Query.Builder("users")
    .select("id", "email")
    .where("active = true")
    .limit(20)
    .build();
```

**What to notice:**
- `Query` is immutable — all mutation happens in the `Builder` before `build()` is called.
- Each builder method returns `this`, enabling a fluent call chain without boilerplate.
- Optional fields (`whereClause`, `limit`) are simply omitted from the chain; the builder supplies sensible defaults.

---

## Abstract Factory

Creates families of related objects without specifying their concrete classes, ensuring that products from one factory are compatible with each other.

```java
public interface Button   { void render(); }
public interface Checkbox { void render(); }

public interface UIFactory {
    Button createButton();
    Checkbox createCheckbox();
}

public final class WindowsButton   implements Button   { public void render() { System.out.println("[Win] Button");   } }
public final class WindowsCheckbox implements Checkbox { public void render() { System.out.println("[Win] Checkbox"); } }

public final class MacButton   implements Button   { public void render() { System.out.println("[Mac] Button");   } }
public final class MacCheckbox implements Checkbox { public void render() { System.out.println("[Mac] Checkbox"); } }

public final class WindowsFactory implements UIFactory {
    public Button createButton()     { return new WindowsButton(); }
    public Checkbox createCheckbox() { return new WindowsCheckbox(); }
}

public final class MacFactory implements UIFactory {
    public Button createButton()     { return new MacButton(); }
    public Checkbox createCheckbox() { return new MacCheckbox(); }
}

public final class Application {
    private final Button button;
    private final Checkbox checkbox;

    public Application(UIFactory factory) {
        this.button   = factory.createButton();
        this.checkbox = factory.createCheckbox();
    }

    public void renderUI() { button.render(); checkbox.render(); }
}
```

**What to notice:**
- `Application` is written entirely against interfaces — it never names `WindowsButton` or `MacButton`.
- Switching the entire UI toolkit requires changing one factory instance at the composition root.
- Consistency is enforced by the factory: a `WindowsFactory` can never accidentally produce a `MacCheckbox`.

---

## Singleton

Ensures a class has only one instance and provides a global access point to it.

```java
public final class Logger {
    private static volatile Logger instance;

    private Logger() {}

    public static Logger getInstance() {
        if (instance == null) {
            synchronized (Logger.class) {
                if (instance == null) {
                    instance = new Logger();
                }
            }
        }
        return instance;
    }

    public void log(String message) {
        System.out.println("[LOG] " + message);
    }
}

// Usage
Logger.getInstance().log("Application started");
```

> **Anti-pattern note:** Singleton is widely considered problematic in modern codebases.
> - **Global state** — any code anywhere can mutate shared state, making side-effects hard to trace.
> - **Hidden coupling** — callers depend on a concrete class rather than an interface, violating the Dependency Inversion Principle.
> - **Testing difficulty** — the singleton cannot be replaced with a test double without reflection hacks or resetting global state between tests.
>
> Prefer passing a single shared instance via dependency injection. The DI container manages the lifecycle; your code stays testable and interface-driven.

**What to notice:**
- Double-checked locking with `volatile` is required for thread safety in lazy initialization.
- The private constructor prevents external instantiation, but it also blocks subclassing and mocking.
- In almost every real-world case, injecting a `Logger` instance achieves the same sharing without the coupling.

---

## Proxy

Provides a surrogate that controls access to another object — useful for lazy initialization, access control, or caching.

```java
public interface ImageLoader {
    void display();
}

public final class RealImageLoader implements ImageLoader {
    private final String filename;
    private byte[] imageData;

    public RealImageLoader(String filename) {
        this.filename = filename;
    }

    private void loadFromDisk() {
        System.out.println("[IO] Loading " + filename + " from disk...");
        imageData = new byte[]{/* ... */};
    }

    public void display() {
        if (imageData == null) loadFromDisk();
        System.out.println("[DISPLAY] Showing " + filename);
    }
}

public final class VirtualImageProxy implements ImageLoader {
    private final String filename;
    private RealImageLoader real;

    public VirtualImageProxy(String filename) { this.filename = filename; }

    public void display() {
        if (real == null) {
            real = new RealImageLoader(filename);
        }
        real.display();
    }
}

// Usage — the expensive load happens only on first display()
ImageLoader image = new VirtualImageProxy("photo.jpg");
image.display(); // triggers load
image.display(); // cached — no reload
```

**What to notice:**
- The proxy implements the same interface as the real object — callers are completely unaware of the indirection.
- The expensive operation (`loadFromDisk`) is deferred until it is actually needed.
- Additional cross-cutting concerns (access control, metrics) can be added to the proxy without touching `RealImageLoader`.

---

## Facade

Provides a simplified interface to a complex subsystem, hiding its components and their wiring from callers.

```java
public final class Amplifier  { public void on() { System.out.println("Amp on");       } public void off() { System.out.println("Amp off"); } }
public final class DVDPlayer  { public void on() { System.out.println("DVD on");       } public void off() { System.out.println("DVD off"); } public void play(String movie) { System.out.println("Playing: " + movie); } }
public final class Projector  { public void on() { System.out.println("Projector on"); } public void off() { System.out.println("Projector off"); } }

public final class HomeTheaterFacade {
    private final Amplifier amp;
    private final DVDPlayer dvd;
    private final Projector projector;

    public HomeTheaterFacade(Amplifier amp, DVDPlayer dvd, Projector projector) {
        this.amp = amp; this.dvd = dvd; this.projector = projector;
    }

    public void watchMovie(String movie) {
        amp.on();
        projector.on();
        dvd.on();
        dvd.play(movie);
    }

    public void endMovie() {
        dvd.off();
        projector.off();
        amp.off();
    }
}

// Usage
HomeTheaterFacade theater = new HomeTheaterFacade(new Amplifier(), new DVDPlayer(), new Projector());
theater.watchMovie("Inception");
theater.endMovie();
```

**What to notice:**
- Callers interact with two methods instead of orchestrating six subsystem calls in the correct order.
- The subsystem classes are not hidden — advanced callers can still use them directly when needed.
- Facade does not add new behavior; it repackages existing behavior behind a convenient entry point.

---

## Bridge

Decouples an abstraction from its implementation so that both can vary independently along separate axes.

```java
public interface DrawingAPI {
    void drawCircle(double x, double y, double radius);
    void drawSquare(double x, double y, double side);
}

public final class SVGDrawer implements DrawingAPI {
    public void drawCircle(double x, double y, double r) { System.out.printf("<circle cx='%.0f' cy='%.0f' r='%.0f'/>%n", x, y, r); }
    public void drawSquare(double x, double y, double s) { System.out.printf("<rect x='%.0f' y='%.0f' width='%.0f' height='%.0f'/>%n", x, y, s, s); }
}

public final class CanvasDrawer implements DrawingAPI {
    public void drawCircle(double x, double y, double r) { System.out.printf("ctx.arc(%.0f,%.0f,%.0f)%n", x, y, r); }
    public void drawSquare(double x, double y, double s) { System.out.printf("ctx.fillRect(%.0f,%.0f,%.0f,%.0f)%n", x, y, s, s); }
}

public abstract class Shape {
    protected final DrawingAPI api;
    protected Shape(DrawingAPI api) { this.api = api; }
    public abstract void draw();
}

public final class Circle extends Shape {
    private final double x, y, radius;
    public Circle(double x, double y, double radius, DrawingAPI api) { super(api); this.x = x; this.y = y; this.radius = radius; }
    public void draw() { api.drawCircle(x, y, radius); }
}

public final class Square extends Shape {
    private final double x, y, side;
    public Square(double x, double y, double side, DrawingAPI api) { super(api); this.x = x; this.y = y; this.side = side; }
    public void draw() { api.drawSquare(x, y, side); }
}
```

**What to notice:**
- There are two independent variation axes: shape type (Circle, Square) and rendering target (SVG, Canvas). Bridge prevents a 2×2 class explosion.
- `Shape` subclasses are never aware of which renderer they are using — they only call the `DrawingAPI` interface.
- Adding a new renderer (e.g., `WebGLDrawer`) requires no changes to any `Shape` subclass.

---

## Flyweight

Shares intrinsic (immutable) state across many fine-grained objects to reduce memory usage when the number of instances is large.

```java
public record Font(String family, int size) {} // intrinsic state — shared

public final class FontFactory {
    private static final Map<String, Font> cache = new HashMap<>();

    public static Font getFont(String family, int size) {
        String key = family + ":" + size;
        return cache.computeIfAbsent(key, k -> new Font(family, size));
    }
}

public final class Character {
    private final char glyph;        // extrinsic — unique per character
    private final int x;             // extrinsic — unique per character
    private final int y;             // extrinsic — unique per character
    private final Font font;         // intrinsic — shared via factory

    public Character(char glyph, int x, int y, String fontFamily, int fontSize) {
        this.glyph = glyph;
        this.x = x;
        this.y = y;
        this.font = FontFactory.getFont(fontFamily, fontSize);
    }

    public void render() {
        System.out.printf("'%c' at (%d,%d) in %s%n", glyph, x, y, font);
    }
}
```

**What to notice:**
- The key distinction is intrinsic state (shared, immutable — `Font`) vs. extrinsic state (unique per instance — position, glyph).
- `FontFactory` ensures that thousands of characters sharing the same font hold a reference to the same object, not thousands of copies.
- Java `record` is ideal for flyweight objects because its value-based equality makes cache keying straightforward.

---

## Composite

Treats individual objects and compositions of objects uniformly through a shared interface, enabling recursive tree structures.

```java
public interface FileSystemComponent {
    String name();
    long getSize();
    void print(String indent);
}

public record File(String name, long size) implements FileSystemComponent {
    public long getSize() { return size; }
    public void print(String indent) {
        System.out.printf("%s- %s (%d bytes)%n", indent, name, size);
    }
}

public final class Directory implements FileSystemComponent {
    private final String name;
    private final List<FileSystemComponent> children = new ArrayList<>();

    public Directory(String name) { this.name = name; }

    public String name() { return name; }

    public void add(FileSystemComponent component) { children.add(component); }

    public long getSize() {
        return children.stream().mapToLong(FileSystemComponent::getSize).sum();
    }

    public void print(String indent) {
        System.out.printf("%s+ %s/%n", indent, name);
        children.forEach(c -> c.print(indent + "  "));
    }
}

// Usage
Directory root = new Directory("root");
root.add(new File("readme.txt", 120));
Directory src = new Directory("src");
src.add(new File("Main.java", 540));
root.add(src);
root.print("");
System.out.println("Total: " + root.getSize() + " bytes");
```

**What to notice:**
- `getSize()` is called identically on a `File` (leaf) and a `Directory` (composite) — callers never check which they have.
- The recursive `getSize()` and `print()` on `Directory` delegate to children, which may themselves be directories — the tree is arbitrarily deep.
- Adding a new node type (e.g., `Symlink`) requires only implementing `FileSystemComponent`; traversal code is untouched.

---

## Result Pattern

Returns a typed Success/Failure value instead of throwing exceptions, making error paths explicit in the type signature.

```java
public sealed interface Result<T, E> permits Result.Success, Result.Failure {
    record Success<T, E>(T value)  implements Result<T, E> {}
    record Failure<T, E>(E error)  implements Result<T, E> {}

    static <T, E> Result<T, E> ok(T value)    { return new Success<>(value); }
    static <T, E> Result<T, E> fail(E error)  { return new Failure<>(error); }

    default boolean isSuccess() { return this instanceof Success; }
}

public record User(String id, String email) {}
public record ValidationError(String field, String message) {}

public final class UserRegistration {
    public Result<User, ValidationError> register(String email, String password) {
        if (email == null || !email.contains("@")) {
            return Result.fail(new ValidationError("email", "Invalid email address"));
        }
        if (password == null || password.length() < 8) {
            return Result.fail(new ValidationError("password", "Must be at least 8 characters"));
        }
        User user = new User(UUID.randomUUID().toString(), email);
        return Result.ok(user);
    }
}

// Usage
switch (new UserRegistration().register("alice@example.com", "secret123")) {
    case Result.Success<User, ValidationError> s -> System.out.println("Created: " + s.value().id());
    case Result.Failure<User, ValidationError> f -> System.out.println("Error: " + f.error().message());
}
```

**What to notice:**
- `sealed interface` + `record` permits gives exhaustive `switch` expressions — the compiler enforces that both paths are handled.
- The error is part of the return type, not an invisible side-channel; callers cannot accidentally ignore it.
- No exception is thrown for expected failure cases (invalid input), reserving exceptions for truly unexpected conditions.

---

## Enterprise Application Patterns

### Transaction Script

**Intent:** Organize business logic as a single procedure that handles one request end-to-end with direct data access.

```java
public final class TransferScript {
    private final Connection db;

    public TransferScript(Connection db) { this.db = db; }

    public void transfer(long fromId, long toId, int amountCents) throws SQLException {
        db.setAutoCommit(false);
        try {
            int fromBalance = queryBalance(fromId);
            if (fromBalance < amountCents) throw new IllegalStateException("Insufficient funds");
            updateBalance(fromId, -amountCents);
            updateBalance(toId,   +amountCents);
            db.commit();
        } catch (Exception e) {
            db.rollback();
            throw e;
        } finally {
            db.setAutoCommit(true);
        }
    }

    private int queryBalance(long id) throws SQLException {
        try (PreparedStatement ps = db.prepareStatement("SELECT balance FROM accounts WHERE id=?")) {
            ps.setLong(1, id);
            ResultSet rs = ps.executeQuery();
            rs.next();
            return rs.getInt("balance");
        }
    }

    private void updateBalance(long id, int delta) throws SQLException {
        try (PreparedStatement ps = db.prepareStatement("UPDATE accounts SET balance=balance+? WHERE id=?")) {
            ps.setInt(1, delta);
            ps.setLong(2, id);
            ps.executeUpdate();
        }
    }
}
```

**Key point:** All logic for one use case lives in one method — fast to write, but grows brittle as rules multiply across scripts.

---

### Service Layer

**Intent:** Define application operations as a thin coordination layer that delegates to domain objects and repositories.

```java
public final class TransferService {
    private final AccountRepository accounts;
    private final TransactionLog log;

    public TransferService(AccountRepository accounts, TransactionLog log) {
        this.accounts = accounts;
        this.log = log;
    }

    public void transfer(long fromId, long toId, int amountCents) {
        Account from = accounts.findById(fromId).orElseThrow();
        Account to   = accounts.findById(toId).orElseThrow();

        from.debit(amountCents);   // domain logic lives here
        to.credit(amountCents);    // domain logic lives here

        accounts.save(from);
        accounts.save(to);
        log.record(fromId, toId, amountCents);
    }
}

public interface AccountRepository {
    Optional<Account> findById(long id);
    void save(Account account);
}
```

**Key point:** The service layer owns transaction boundaries and use-case flow but contains no business rules — those belong to domain objects.

---

### Data Mapper

**Intent:** Transfer data between domain objects and the database without letting either know about the other.

```java
public final class Account {
    private long id;
    private int balanceCents;

    public Account(long id, int balanceCents) { this.id = id; this.balanceCents = balanceCents; }
    public long getId()          { return id; }
    public int getBalance()      { return balanceCents; }
    public void debit(int cents) { if (cents > balanceCents) throw new IllegalStateException(); balanceCents -= cents; }
    public void credit(int cents){ balanceCents += cents; }
}

public final class AccountMapper {
    private final Connection db;

    public AccountMapper(Connection db) { this.db = db; }

    public Optional<Account> findById(long id) throws SQLException {
        try (PreparedStatement ps = db.prepareStatement("SELECT id, balance FROM accounts WHERE id=?")) {
            ps.setLong(1, id);
            ResultSet rs = ps.executeQuery();
            if (!rs.next()) return Optional.empty();
            return Optional.of(new Account(rs.getLong("id"), rs.getInt("balance")));
        }
    }

    public void update(Account account) throws SQLException {
        try (PreparedStatement ps = db.prepareStatement("UPDATE accounts SET balance=? WHERE id=?")) {
            ps.setInt(1, account.getBalance());
            ps.setLong(2, account.getId());
            ps.executeUpdate();
        }
    }
}
```

**Key point:** `Account` has zero SQL — the mapper alone knows the table structure, so schema changes touch only one class.

---

### Unit of Work

**Intent:** Track objects registered as new, dirty, or deleted within a business transaction and flush all changes in one commit.

```java
public final class UnitOfWork {
    private final List<Account> newObjects     = new ArrayList<>();
    private final List<Account> dirtyObjects   = new ArrayList<>();
    private final List<Account> removedObjects = new ArrayList<>();
    private final AccountMapper mapper;

    public UnitOfWork(AccountMapper mapper) { this.mapper = mapper; }

    public void registerNew(Account a)     { newObjects.add(a); }
    public void registerDirty(Account a)   { if (!dirtyObjects.contains(a)) dirtyObjects.add(a); }
    public void registerRemoved(Account a) { removedObjects.add(a); }

    public void commit() throws SQLException {
        for (Account a : newObjects)     mapper.insert(a);
        for (Account a : dirtyObjects)   mapper.update(a);
        for (Account a : removedObjects) mapper.delete(a);
        newObjects.clear(); dirtyObjects.clear(); removedObjects.clear();
    }
}
```

**Key point:** Callers mutate domain objects freely during a business operation; the Unit of Work batches all resulting DB writes into one atomic flush.

---

### Data Transfer Object (DTO)

**Intent:** Carry data across layer or process boundaries as a plain, immutable structure with no behavior.

```java
public record AccountSummaryDto(
    long   accountId,
    String ownerName,
    int    balanceCents,
    String currency
) {}

// Assembled at the service/mapper boundary — never passed down into domain logic
public final class AccountQueryService {
    private final AccountMapper mapper;

    public AccountQueryService(AccountMapper mapper) { this.mapper = mapper; }

    public AccountSummaryDto getSummary(long id) throws SQLException {
        Account account = mapper.findById(id).orElseThrow();
        return new AccountSummaryDto(
            account.getId(),
            account.getOwnerName(),
            account.getBalance(),
            "USD"
        );
    }
}
```

**Key point:** A `record` DTO is immutable by default and serialization-friendly — it carries data, never decides anything.

---

### Value Object (Money)

**Intent:** Represent a monetary amount as an immutable object with value semantics, arithmetic, and currency safety.

```java
public final class Money {
    private final int cents;
    private final String currency;

    public Money(int cents, String currency) {
        this.cents    = cents;
        this.currency = currency;
    }

    public Money add(Money other) {
        assertSameCurrency(other);
        return new Money(this.cents + other.cents, currency);
    }

    public Money subtract(Money other) {
        assertSameCurrency(other);
        return new Money(this.cents - other.cents, currency);
    }

    public boolean isGreaterThan(Money other) {
        assertSameCurrency(other);
        return this.cents > other.cents;
    }

    private void assertSameCurrency(Money other) {
        if (!this.currency.equals(other.currency))
            throw new IllegalArgumentException("Currency mismatch: " + currency + " vs " + other.currency);
    }

    @Override public boolean equals(Object o) {
        return o instanceof Money m && cents == m.cents && currency.equals(m.currency);
    }
    @Override public int hashCode() { return 31 * cents + currency.hashCode(); }
    @Override public String toString() { return currency + " " + (cents / 100.0); }
}
```

**Key point:** Every arithmetic operation returns a new `Money` instance — no mutation, no primitive leakage, and currency mismatches fail loudly.

---

### Special Case

**Intent:** Replace null checks with a subclass that represents an absent or unknown entity and returns safe default behavior.

```java
public abstract class Customer {
    public abstract String getName();
    public abstract int getCreditLimitCents();
    public abstract boolean isAllowedToPurchase(int amountCents);
}

public final class RegisteredCustomer extends Customer {
    private final String name;
    private final int creditLimitCents;

    public RegisteredCustomer(String name, int creditLimitCents) {
        this.name = name; this.creditLimitCents = creditLimitCents;
    }
    public String getName()                           { return name; }
    public int getCreditLimitCents()                  { return creditLimitCents; }
    public boolean isAllowedToPurchase(int amount)    { return amount <= creditLimitCents; }
}

public final class GuestCustomer extends Customer {
    public String getName()                           { return "Guest"; }
    public int getCreditLimitCents()                  { return 0; }
    public boolean isAllowedToPurchase(int amount)    { return amount <= 5000; } // small limit for guests
}

// Usage — callers never check for null
Customer customer = repository.findById(id).orElse(new GuestCustomer());
System.out.println(customer.getName());
System.out.println(customer.isAllowedToPurchase(3000));
```

**Key point:** `GuestCustomer` eliminates `if (customer == null)` branches by providing meaningful defaults — the callsite reads like the happy path.

---

### Gateway

**Intent:** Wrap an external API or service behind a clean interface so the rest of the system never sees its details.

```java
public interface ExchangeRateGateway {
    double getRate(String fromCurrency, String toCurrency);
}

public final class HttpExchangeRateGateway implements ExchangeRateGateway {
    private final String baseUrl;
    private final HttpClient http;

    public HttpExchangeRateGateway(String baseUrl) {
        this.baseUrl = baseUrl;
        this.http    = HttpClient.newHttpClient();
    }

    public double getRate(String from, String to) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + "/rate?from=" + from + "&to=" + to))
                .build();
            HttpResponse<String> response = http.send(request, HttpResponse.BodyHandlers.ofString());
            return Double.parseDouble(response.body().trim());
        } catch (Exception e) {
            throw new RuntimeException("Exchange rate lookup failed", e);
        }
    }
}

public final class StubExchangeRateGateway implements ExchangeRateGateway {
    public double getRate(String from, String to) { return 1.0; } // always 1:1 in tests
}
```

**Key point:** Domain code imports only `ExchangeRateGateway` — swapping the real HTTP call for a test stub requires zero changes to business logic.

---

### Query Object

**Intent:** Represent filter criteria as an object so queries can be composed, passed, and reused without embedding SQL strings.

```java
public final class AccountQuery {
    private String currency;
    private Integer minBalanceCents;
    private Integer maxBalanceCents;

    public AccountQuery currency(String currency)          { this.currency = currency; return this; }
    public AccountQuery minBalance(int cents)              { this.minBalanceCents = cents; return this; }
    public AccountQuery maxBalance(int cents)              { this.maxBalanceCents = cents; return this; }

    public List<Account> execute(List<Account> source) {
        return source.stream()
            .filter(a -> currency        == null || a.getCurrency().equals(currency))
            .filter(a -> minBalanceCents == null || a.getBalance() >= minBalanceCents)
            .filter(a -> maxBalanceCents == null || a.getBalance() <= maxBalanceCents)
            .toList();
    }
}

// Usage
List<Account> richUsdAccounts = new AccountQuery()
    .currency("USD")
    .minBalance(100_000)
    .execute(allAccounts);
```

**Key point:** Filter criteria become a first-class object that can be passed between layers, logged, or translated to SQL — no string interpolation scattered across callers.

---

### Layer Supertype

**Intent:** Provide a base class for an entire layer that centralizes shared infrastructure concerns like identity, timestamps, and equality.

```java
public abstract class PersistentEntity {
    private final long id;
    private final Instant createdAt;
    private Instant updatedAt;

    protected PersistentEntity(long id) {
        this.id        = id;
        this.createdAt = Instant.now();
        this.updatedAt = this.createdAt;
    }

    public long    getId()        { return id; }
    public Instant getCreatedAt() { return createdAt; }
    public Instant getUpdatedAt() { return updatedAt; }

    protected void touch() { this.updatedAt = Instant.now(); }

    @Override public boolean equals(Object o) {
        return o instanceof PersistentEntity e && id == e.id && getClass() == o.getClass();
    }
    @Override public int hashCode() { return Long.hashCode(id); }
}

public final class Account extends PersistentEntity {
    private int balanceCents;

    public Account(long id, int balanceCents) { super(id); this.balanceCents = balanceCents; }

    public void credit(int cents) { balanceCents += cents; touch(); }
    public int getBalance()       { return balanceCents; }
}
```

**Key point:** Identity-based equality, audit timestamps, and the `touch()` lifecycle hook are defined once in the supertype — every entity in the layer inherits them without repetition.

---

## Remaining GoF Patterns

### Adapter

**Intent:** Wrap a third-party or legacy interface behind the interface your code expects.

```java
public interface PaymentGateway {
    void charge(String customerId, int amountCents);
}

// External SDK we cannot modify
public final class StripeClient {
    public void createCharge(String stripeCustomer, double amountDollars, String currency) {
        System.out.printf("[Stripe] Charging %s $%.2f%n", stripeCustomer, amountDollars);
    }
}

public final class StripePaymentAdapter implements PaymentGateway {
    private final StripeClient stripe;

    public StripePaymentAdapter(StripeClient stripe) { this.stripe = stripe; }

    public void charge(String customerId, int amountCents) {
        double dollars = amountCents / 100.0;
        stripe.createCharge(customerId, dollars, "USD");
    }
}

// Usage — domain code never imports StripeClient
PaymentGateway gateway = new StripePaymentAdapter(new StripeClient());
gateway.charge("cus_abc123", 4999);
```

**Key point:** The adapter translates the local `PaymentGateway` contract into Stripe SDK calls, so domain code is never coupled to the third-party type.

---

### Visitor

**Intent:** Separate an algorithm from the object structure it operates on.

```java
public interface DocumentElement {
    void accept(DocumentVisitor visitor);
}

public record Heading(String text) implements DocumentElement {
    public void accept(DocumentVisitor visitor) { visitor.visitHeading(this); }
}

public record Paragraph(String text) implements DocumentElement {
    public void accept(DocumentVisitor visitor) { visitor.visitParagraph(this); }
}

public interface DocumentVisitor {
    void visitHeading(Heading heading);
    void visitParagraph(Paragraph paragraph);
}

public final class WordCountVisitor implements DocumentVisitor {
    private int count = 0;
    public void visitHeading(Heading h)     { count += h.text().split("\\s+").length; }
    public void visitParagraph(Paragraph p) { count += p.text().split("\\s+").length; }
    public int getCount() { return count; }
}

public final class HtmlRenderVisitor implements DocumentVisitor {
    private final StringBuilder html = new StringBuilder();
    public void visitHeading(Heading h)     { html.append("<h1>").append(h.text()).append("</h1>\n"); }
    public void visitParagraph(Paragraph p) { html.append("<p>").append(p.text()).append("</p>\n"); }
    public String getHtml() { return html.toString(); }
}
```

**Key point:** New operations (word count, HTML render) are added as new visitor classes without touching `Heading` or `Paragraph`.

---

### Memento

**Intent:** Capture and restore object state without exposing internals.

```java
public final class TextEditor {
    private String text;

    public TextEditor(String text) { this.text = text; }

    public void type(String addition) { this.text += addition; }
    public String getText() { return text; }

    public record Memento(String savedText) {}

    public Memento save()             { return new Memento(text); }
    public void restore(Memento m)    { this.text = m.savedText(); }
}

public final class History {
    private final Deque<TextEditor.Memento> stack = new ArrayDeque<>();

    public void push(TextEditor.Memento m) { stack.push(m); }

    public TextEditor.Memento pop() {
        if (stack.isEmpty()) throw new IllegalStateException("Nothing to undo");
        return stack.pop();
    }
}

// Usage
TextEditor editor = new TextEditor("Hello");
History history = new History();
history.push(editor.save());
editor.type(", world");
history.push(editor.save());
editor.type("!!!");
editor.restore(history.pop()); // back to "Hello, world"
editor.restore(history.pop()); // back to "Hello"
```

**Key point:** `Memento` is a `record` nested inside `TextEditor`, so only the editor can construct one — internal state never leaks to the `History` caretaker.

---

### Prototype

**Intent:** Clone a configured object instead of constructing it from scratch.

```java
public final class DocumentTemplate implements Cloneable {
    private String title;
    private String header;
    private String footer;
    private List<String> sections;

    public DocumentTemplate(String title, String header, String footer, List<String> sections) {
        this.title    = title;
        this.header   = header;
        this.footer   = footer;
        this.sections = new ArrayList<>(sections);
    }

    public void setTitle(String title)       { this.title = title; }
    public void addSection(String section)   { this.sections.add(section); }
    public String getTitle()                 { return title; }

    @Override
    public DocumentTemplate clone() {
        return new DocumentTemplate(title, header, footer, sections);
    }

    @Override public String toString() {
        return header + "\n" + title + "\n" + String.join("\n", sections) + "\n" + footer;
    }
}

// Usage
DocumentTemplate base = new DocumentTemplate("Untitled", "ACME Corp", "Confidential", List.of("Introduction"));
DocumentTemplate report = base.clone();
report.setTitle("Q1 Sales Report");
report.addSection("Summary");
```

## DDD Tactical Patterns

### Entity

**Intent:** An object with a unique identity that persists and changes over time.

```java
public class Order {
    private final String id;
    private String status; // "draft" | "placed" | "shipped"
    private final String customerId;

    public Order(String id, String customerId) {
        this.id = id;
        this.status = "draft";
        this.customerId = customerId;
    }

    public void place() {
        if (!"draft".equals(status)) throw new IllegalStateException("Order already placed");
        this.status = "placed";
    }

    public String getStatus() { return status; }

    @Override
    public boolean equals(Object o) {  // identity-based equality
        if (this == o) return true;
        if (!(o instanceof Order other)) return false;
        return id.equals(other.id);
    }

    @Override public int hashCode() { return id.hashCode(); }
}
```

**Key point:** Two entities are equal when their IDs match, regardless of attribute differences.

---

### Aggregate Root

**Intent:** An entity that guards a cluster of objects, enforces invariants, and records domain events.

```java
public class OrderAggregate {
    private final String id;
    private final int maxItems;
    private final List<OrderItem> items = new ArrayList<>();
    private final List<Object> events = new ArrayList<>();

    public OrderAggregate(String id, int maxItems) {
        this.id = id;
        this.maxItems = maxItems;
    }

    public void addItem(String productId, int qty) {
        if (items.size() >= maxItems)
            throw new IllegalStateException("Order exceeds maximum item limit");
        if (qty <= 0)
            throw new IllegalArgumentException("Quantity must be positive");

        items.add(new OrderItem(productId, qty));
        events.add(new OrderItemAdded(id, productId, qty));
    }

    public List<Object> pullEvents() {
        var pending = List.copyOf(events);
        events.clear();
        return pending;
    }

    record OrderItem(String productId, int qty) {}
}
```

**Key point:** All mutations go through the aggregate root so invariants are always enforced before state changes.

---

### Domain Event

**Intent:** An immutable record of something that happened in the domain, carrying all relevant data.

```java
public record OrderItemAdded(
    String orderId,
    String productId,
    int quantity,
    Instant occurredAt
) {
    public OrderItemAdded(String orderId, String productId, int quantity) {
        this(orderId, productId, quantity, Instant.now());
    }
}

public record OrderPlaced(
    String orderId,
    String customerId,
    Instant occurredAt
) {
    public OrderPlaced(String orderId, String customerId) {
        this(orderId, customerId, Instant.now());
    }
}
```

**Key point:** Java `record` types are shallowly immutable by default, making them a natural fit for domain events.

---

### Specification

**Intent:** An encapsulated, combinable business rule that answers whether an object satisfies a condition.

```java
public interface Specification<T> {
    boolean isSatisfiedBy(T candidate);

    default Specification<T> and(Specification<T> other) {
        return candidate -> isSatisfiedBy(candidate) && other.isSatisfiedBy(candidate);
    }
    default Specification<T> or(Specification<T> other) {
        return candidate -> isSatisfiedBy(candidate) || other.isSatisfiedBy(candidate);
    }
    default Specification<T> not() {
        return candidate -> !isSatisfiedBy(candidate);
    }
}

record Customer(boolean active, double totalSpend) {}

class ActiveCustomerSpec implements Specification<Customer> {
    public boolean isSatisfiedBy(Customer c) { return c.active(); }
}

class PremiumCustomerSpec implements Specification<Customer> {
    public boolean isSatisfiedBy(Customer c) { return c.totalSpend() >= 10_000; }
}

// Compose: active AND premium
Specification<Customer> eligibleForPromo =
    new ActiveCustomerSpec().and(new PremiumCustomerSpec());

boolean result = eligibleForPromo.isSatisfiedBy(new Customer(true, 15_000)); // true
```

**Key point:** Composing specifications with `and`/`or`/`not` expresses complex business rules without scattering conditionals.

---

## CQRS and Error Patterns

### Command + CommandHandler (CQRS write side)

**Intent:** Separate the write operation into an immutable value object (Command) and a handler that orchestrates domain logic.

```java
public abstract class Command {}

public interface CommandHandler<T extends Command> {
    void handle(T command);
}

public final class CreateUserCommand extends Command {
    public final String id;
    public final String email;
    public final String name;

    public CreateUserCommand(String id, String email, String name) {
        this.id = id; this.email = email; this.name = name;
    }
}

public final class CreateUserCommandHandler implements CommandHandler<CreateUserCommand> {
    private final UserRepository userRepository;
    private final EventBus eventBus;

    public CreateUserCommandHandler(UserRepository userRepository, EventBus eventBus) {
        this.userRepository = userRepository;
        this.eventBus = eventBus;
    }

    @Override
    public void handle(CreateUserCommand command) {
        UserId id    = new UserId(command.id);
        UserEmail email = new UserEmail(command.email);
        User user   = User.create(id, email, command.name);
        userRepository.save(user);
        eventBus.publish(user.pullDomainEvents());
    }
}
```

**Key point:** The Command is a plain immutable value object; the handler owns orchestration — value object construction, aggregate creation, persistence, and event dispatch.

---

### Object Mother

**Intent:** Provide a centralized factory for valid test objects so tests stay readable and free of setup boilerplate.

```java
public final class UserIdMother {
    public static UserId random() {
        return new UserId(UUID.randomUUID().toString());
    }
}

public final class UserMother {
    public static User random() {
        return User.create(
            UserIdMother.random(),
            new UserEmail("user-" + UUID.randomUUID() + "@example.com"),
            "Random User"
        );
    }

    public static User withName(String name) {
        return User.create(UserIdMother.random(), new UserEmail("alice@example.com"), name);
    }
}

// In a test:
User user = UserMother.withName("Bob");
```

**Key point:** Object Mothers generate complete, valid domain objects with sensible defaults, keeping test intent visible and setup noise invisible.

---

### DomainError hierarchy

**Intent:** Give every domain error a stable, explicit string type so errors are identifiable without relying on class names.

```java
public abstract class DomainError extends RuntimeException {
    private final String type;

    protected DomainError(String type, String message) {
        super(message);
        this.type = type;
    }

    public String getType() { return type; }
}

public final class UserNotFoundError extends DomainError {
    public UserNotFoundError(String id) {
        super("UserNotFoundError", "User with id <" + id + "> not found");
    }
}

// Usage in a catch block:
try {
    handler.handle(command);
} catch (DomainError err) {
    if ("UserNotFoundError".equals(err.getType())) {
        // handle 404 path
    }
    throw err;
}
```

**Key point:** Passing the type string explicitly to the base constructor keeps error identity stable across refactors and obfuscation — never rely solely on `getClass().getSimpleName()`.

---

### Either / Result type

**Intent:** Make failure an explicit return value so callers are forced to handle both the success and error paths without hidden exception paths.

```java
public final class Result<TValue, TError extends DomainError> {
    private final TValue value;
    private final TError error;

    private Result(TValue value, TError error) {
        this.value = value; this.error = error;
    }

    public static <V, E extends DomainError> Result<V, E> ok(V value) {
        return new Result<>(value, null);
    }

    public static <V, E extends DomainError> Result<V, E> err(E error) {
        return new Result<>(null, error);
    }

    public boolean isOk()  { return error == null; }
    public boolean isErr() { return error != null; }
    public TValue getValue() { if (!isOk())  throw new IllegalStateException("No value"); return value; }
    public TError getError() { if (!isErr()) throw new IllegalStateException("No error"); return error; }
}

// Domain method:
Result<User, UserNotFoundError> findUser(String id) {
    User user = store.get(id);
    return user != null ? Result.ok(user) : Result.err(new UserNotFoundError(id));
}

// Caller:
Result<User, UserNotFoundError> result = findUser("abc");
if (result.isOk()) {
    System.out.println(result.getValue().getName());
} else {
    System.err.println(result.getError().getMessage());
}
```

**Key point:** Returning `Result<TValue, TError>` instead of throwing makes the failure contract explicit in the method signature and forces the caller to handle both paths.

**Key point:** `clone()` produces a fully configured copy with independent state — callers avoid repeating header/footer setup for every new document.
