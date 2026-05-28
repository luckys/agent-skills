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
