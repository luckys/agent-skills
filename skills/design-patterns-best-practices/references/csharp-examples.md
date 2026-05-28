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

---

## Command

Encapsulates a request as an object, decoupling the sender from the executor and enabling undo/redo support.

```csharp
public interface ICommand
{
    void Execute();
    void Undo();
}

public sealed class BoldCommand : ICommand
{
    private readonly TextEditor editor;
    private string previousText = string.Empty;

    public BoldCommand(TextEditor editor) => this.editor = editor;

    public void Execute()
    {
        previousText = editor.Text;
        editor.Text = $"<b>{editor.Text}</b>";
    }

    public void Undo() => editor.Text = previousText;
}

public sealed class ItalicCommand : ICommand
{
    private readonly TextEditor editor;
    private string previousText = string.Empty;

    public ItalicCommand(TextEditor editor) => this.editor = editor;

    public void Execute()
    {
        previousText = editor.Text;
        editor.Text = $"<i>{editor.Text}</i>";
    }

    public void Undo() => editor.Text = previousText;
}

public sealed class TextEditor
{
    public string Text { get; set; } = string.Empty;
    private readonly Stack<ICommand> history = new();

    public void ExecuteCommand(ICommand command)
    {
        command.Execute();
        history.Push(command);
    }

    public void UndoLast()
    {
        if (history.TryPop(out var command))
            command.Undo();
    }
}
```

**What to notice:**
- Each command captures enough state (`previousText`) to reverse itself, enabling clean undo without the editor tracking history details.
- `TextEditor` depends only on `ICommand` — adding a new formatting command is an additive change.
- The history stack composes arbitrarily many commands, making multi-level undo trivial.

---

## Template Method

Defines an algorithm skeleton in a base class; subclasses override specific steps without changing the overall structure.

```csharp
public abstract class ReportGenerator
{
    public void Generate()
    {
        var data = GatherData();
        var formatted = FormatData(data);
        Output(formatted);
    }

    private string[] GatherData() =>
        new[] { "Q1: 120k", "Q2: 145k", "Q3: 98k" };

    protected abstract string FormatData(string[] data);

    private void Output(string content) =>
        Console.WriteLine(content);
}

public sealed class CsvReportGenerator : ReportGenerator
{
    protected override string FormatData(string[] data) =>
        string.Join(",", data);
}

public sealed class PdfReportGenerator : ReportGenerator
{
    protected override string FormatData(string[] data) =>
        $"[PDF]\n{string.Join("\n", data)}";
}
```

**What to notice:**
- `Generate()` in the base class controls sequencing; subclasses only supply the variable step.
- `GatherData` and `Output` are private — they cannot be accidentally overridden, protecting the algorithm's invariants.
- Adding a new output format (e.g., HTML) requires only a new subclass with `FormatData` overridden.

---

## Chain of Responsibility

Passes a request along a chain of handlers; each handler decides to process it or forward it to the next.

```csharp
public sealed class HttpContext
{
    public string? User { get; set; }
    public string Path { get; init; } = "/";
    public List<string> Log { get; } = new();
}

public abstract class Middleware
{
    protected Middleware? Next { get; private set; }

    public Middleware SetNext(Middleware next)
    {
        Next = next;
        return next;
    }

    public abstract void Handle(HttpContext context);
}

public sealed class AuthMiddleware : Middleware
{
    public override void Handle(HttpContext context)
    {
        if (context.User is null)
            context.Log.Add("Auth: rejected — no user");
        else
            Next?.Handle(context);
    }
}

public sealed class LoggingMiddleware : Middleware
{
    public override void Handle(HttpContext context)
    {
        context.Log.Add($"Log: {context.User} → {context.Path}");
        Next?.Handle(context);
    }
}

public sealed class RequestHandler : Middleware
{
    public override void Handle(HttpContext context) =>
        context.Log.Add($"Handler: processed {context.Path}");
}

// Usage
var auth = new AuthMiddleware();
auth.SetNext(new LoggingMiddleware()).SetNext(new RequestHandler());
auth.Handle(new HttpContext { User = "alice", Path = "/api/data" });
```

**What to notice:**
- Each middleware is unaware of what comes before or after it — only `Next` is known.
- The fluent `SetNext` call makes pipeline assembly readable at the composition root.
- Short-circuiting (returning without calling `Next`) is how a handler absorbs the request.

---

## Iterator

Provides sequential access to a collection's elements without exposing its internal structure.

```csharp
public sealed class NumberRange : IEnumerable<int>
{
    private readonly int start;
    private readonly int end;
    private readonly int step;

    public NumberRange(int start, int end, int step = 1)
    {
        this.start = start;
        this.end = end;
        this.step = step;
    }

    public IEnumerator<int> GetEnumerator()
    {
        for (var i = start; i <= end; i += step)
            yield return i;
    }

    System.Collections.IEnumerator System.Collections.IEnumerable.GetEnumerator() =>
        GetEnumerator();
}

// Usage
foreach (var n in new NumberRange(0, 10, 2))
    Console.Write($"{n} "); // 0 2 4 6 8 10
```

**What to notice:**
- `yield return` lets the compiler generate the state machine; no explicit enumerator class is needed.
- Implementing `IEnumerable<int>` makes `NumberRange` compatible with `foreach`, LINQ, and any method that accepts a sequence.
- The step logic lives entirely in one place — callers see only a sequence.

---

## Mediator

Centralizes communication between objects so they do not reference each other directly, reducing coupling.

```csharp
public sealed class ChatRoom
{
    private readonly List<User> users = new();

    public void Join(User user) => users.Add(user);

    public void Send(string fromName, string message)
    {
        foreach (var user in users.Where(u => u.Name != fromName))
            user.Receive(fromName, message);
    }
}

public sealed class User
{
    public string Name { get; }
    private readonly ChatRoom room;

    public User(string name, ChatRoom room)
    {
        Name = name;
        this.room = room;
        room.Join(this);
    }

    public void Send(string message) => room.Send(Name, message);

    public void Receive(string from, string message) =>
        Console.WriteLine($"[{Name}] {from}: {message}");
}

// Usage
var room = new ChatRoom();
var alice = new User("Alice", room);
var bob   = new User("Bob",   room);
alice.Send("Hello!");  // Bob receives; Alice does not
```

**What to notice:**
- `User` objects have no references to each other — all routing goes through `ChatRoom`.
- Adding a new participant requires no changes to existing users or the mediator's interface.
- The mediator owns the routing policy (e.g., skip sender), keeping that logic in one place.

---

## Builder

Constructs a complex object step by step, separating construction logic from the final representation.

```csharp
public sealed class Query
{
    public string Table { get; init; } = string.Empty;
    public string[] Columns { get; init; } = Array.Empty<string>();
    public string? WhereClause { get; init; }
    public int? LimitValue { get; init; }

    public override string ToString()
    {
        var cols = Columns.Length > 0 ? string.Join(", ", Columns) : "*";
        var sql = $"SELECT {cols} FROM {Table}";
        if (WhereClause is not null) sql += $" WHERE {WhereClause}";
        if (LimitValue is not null)  sql += $" LIMIT {LimitValue}";
        return sql;
    }
}

public sealed class QueryBuilder
{
    private string table = string.Empty;
    private string[] columns = Array.Empty<string>();
    private string? where;
    private int? limit;

    public QueryBuilder From(string table)          { this.table = table; return this; }
    public QueryBuilder Select(params string[] cols) { columns = cols;     return this; }
    public QueryBuilder Where(string clause)         { where = clause;     return this; }
    public QueryBuilder Limit(int n)                 { limit = n;          return this; }

    public Query Build() => new() { Table = table, Columns = columns, WhereClause = where, LimitValue = limit };
}

// Usage
var query = new QueryBuilder()
    .From("orders")
    .Select("id", "total")
    .Where("total > 100")
    .Limit(50)
    .Build();
Console.WriteLine(query); // SELECT id, total FROM orders WHERE total > 100 LIMIT 50
```

**What to notice:**
- Each chainable method returns `this`, enabling a fluent API that reads like a sentence.
- `Build()` is the single place where the final object is assembled and validated.
- `Query` is immutable (`init`-only properties); the builder owns all mutable state during construction.

---

## Abstract Factory

Creates families of related objects without specifying their concrete classes, ensuring components from the same family are always used together.

```csharp
public interface IButton   { void Render(); }
public interface ICheckbox { void Render(); }

public sealed class WindowsButton   : IButton   { public void Render() => Console.WriteLine("Windows Button"); }
public sealed class WindowsCheckbox : ICheckbox { public void Render() => Console.WriteLine("Windows Checkbox"); }

public sealed class MacButton   : IButton   { public void Render() => Console.WriteLine("Mac Button"); }
public sealed class MacCheckbox : ICheckbox { public void Render() => Console.WriteLine("Mac Checkbox"); }

public interface IUIFactory
{
    IButton   CreateButton();
    ICheckbox CreateCheckbox();
}

public sealed class WindowsFactory : IUIFactory
{
    public IButton   CreateButton()   => new WindowsButton();
    public ICheckbox CreateCheckbox() => new WindowsCheckbox();
}

public sealed class MacFactory : IUIFactory
{
    public IButton   CreateButton()   => new MacButton();
    public ICheckbox CreateCheckbox() => new MacCheckbox();
}

public sealed class Application
{
    private readonly IButton button;
    private readonly ICheckbox checkbox;

    public Application(IUIFactory factory)
    {
        button   = factory.CreateButton();
        checkbox = factory.CreateCheckbox();
    }

    public void RenderUI() { button.Render(); checkbox.Render(); }
}
```

**What to notice:**
- `Application` is compiled entirely against interfaces — it cannot accidentally mix a `WindowsButton` with a `MacCheckbox`.
- Adding a Linux theme means one new factory class; `Application` and existing factories are untouched.
- The factory is the single decision point for which family is active, typically chosen at the composition root.

---

## Singleton

Ensures only one instance of a class exists; `Lazy<T>` makes initialization thread-safe without explicit locking.

```csharp
public sealed class Logger
{
    private static readonly Lazy<Logger> instance =
        new(() => new Logger(), isThreadSafe: true);

    public static Logger Instance => instance.Value;

    private Logger() { }

    public void Log(string message) =>
        Console.WriteLine($"[{DateTime.UtcNow:O}] {message}");
}

// Usage
Logger.Instance.Log("Application started");
Logger.Instance.Log("Request received");
```

**What to notice:**
- `Lazy<T>` defers construction until first use and guarantees thread safety without a manual double-checked lock.
- The private constructor prevents external instantiation; `sealed` prevents subclassing that could escape the guarantee.

> **Trade-off note:** Singleton is widely considered an anti-pattern. It introduces global mutable state, hides dependencies (callers cannot see `Logger` in the constructor signature), and makes unit testing hard (you cannot substitute a test double without static seams or reflection). Prefer constructor injection of a shared instance managed by a DI container.

---

## Proxy

Provides a surrogate for another object, controlling access to it — here for lazy initialization of an expensive resource.

```csharp
public interface IImage
{
    void Display();
}

public sealed class RealImage : IImage
{
    private readonly string filename;

    public RealImage(string filename)
    {
        this.filename = filename;
        Console.WriteLine($"Loading image from disk: {filename}");
    }

    public void Display() => Console.WriteLine($"Displaying: {filename}");
}

public sealed class ImageProxy : IImage
{
    private readonly string filename;
    private RealImage? realImage;

    public ImageProxy(string filename) => this.filename = filename;

    public void Display()
    {
        realImage ??= new RealImage(filename); // loaded only on first access
        realImage.Display();
    }
}

// Usage
IImage image = new ImageProxy("photo.jpg");
// No disk I/O yet
image.Display(); // loads and displays
image.Display(); // displays only — already loaded
```

**What to notice:**
- The proxy implements the same interface as the real object, so callers need no changes when a proxy is introduced.
- The `??=` null-coalescing assignment is idiomatic C# for lazy initialization without an explicit `Lazy<T>`.
- The proxy pattern also covers remote proxies (network calls), protection proxies (access control), and logging proxies.

---

## Facade

Provides a simplified, unified interface to a complex subsystem, hiding its internal coordination from callers.

```csharp
public sealed class Amplifier
{
    public void On()  => Console.WriteLine("Amplifier on");
    public void Off() => Console.WriteLine("Amplifier off");
    public void SetVolume(int level) => Console.WriteLine($"Volume: {level}");
}

public sealed class DVDPlayer
{
    public void On()   => Console.WriteLine("DVD player on");
    public void Play() => Console.WriteLine("DVD playing");
    public void Off()  => Console.WriteLine("DVD player off");
}

public sealed class Projector
{
    public void On()  => Console.WriteLine("Projector on");
    public void Off() => Console.WriteLine("Projector off");
}

public sealed class HomeTheaterFacade
{
    private readonly Amplifier amp;
    private readonly DVDPlayer dvd;
    private readonly Projector projector;

    public HomeTheaterFacade(Amplifier amp, DVDPlayer dvd, Projector projector)
    {
        this.amp       = amp;
        this.dvd       = dvd;
        this.projector = projector;
    }

    public void WatchMovie()
    {
        amp.On(); amp.SetVolume(10);
        dvd.On(); dvd.Play();
        projector.On();
    }

    public void EndMovie()
    {
        projector.Off();
        dvd.Off();
        amp.Off();
    }
}
```

**What to notice:**
- The facade does not add behavior; it orchestrates existing subsystem calls behind a single, intention-revealing method.
- Subsystem classes remain fully usable directly — the facade is an optional convenience layer.
- Callers depend only on `HomeTheaterFacade`, insulating them from future changes in subsystem APIs.

---

## Bridge

Decouples an abstraction from its implementation so both can vary independently along separate axes.

```csharp
public interface IDrawingApi
{
    void DrawCircle(double x, double y, double radius);
    void DrawSquare(double x, double y, double side);
}

public sealed class SvgDrawer : IDrawingApi
{
    public void DrawCircle(double x, double y, double radius) =>
        Console.WriteLine($"<circle cx='{x}' cy='{y}' r='{radius}'/>");

    public void DrawSquare(double x, double y, double side) =>
        Console.WriteLine($"<rect x='{x}' y='{y}' width='{side}' height='{side}'/>");
}

public sealed class CanvasDrawer : IDrawingApi
{
    public void DrawCircle(double x, double y, double radius) =>
        Console.WriteLine($"ctx.arc({x},{y},{radius},0,2*Math.PI)");

    public void DrawSquare(double x, double y, double side) =>
        Console.WriteLine($"ctx.fillRect({x},{y},{side},{side})");
}

public abstract class Shape
{
    protected readonly IDrawingApi Api;
    protected Shape(IDrawingApi api) => Api = api;
    public abstract void Draw();
}

public sealed class Circle : Shape
{
    private readonly double x, y, radius;
    public Circle(double x, double y, double radius, IDrawingApi api) : base(api)
        => (this.x, this.y, this.radius) = (x, y, radius);

    public override void Draw() => Api.DrawCircle(x, y, radius);
}

public sealed class Square : Shape
{
    private readonly double x, y, side;
    public Square(double x, double y, double side, IDrawingApi api) : base(api)
        => (this.x, this.y, this.side) = (x, y, side);

    public override void Draw() => Api.DrawSquare(x, y, side);
}
```

**What to notice:**
- Shape hierarchy (Circle, Square) and rendering hierarchy (Svg, Canvas) grow independently — N shapes × M renderers without N×M subclasses.
- The bridge is the `IDrawingApi` reference held in the abstraction; it is injected, not inherited.
- Contrast with Decorator: Bridge separates two variation axes; Decorator layers behavior on one.

---

## Flyweight

Shares common intrinsic state between many fine-grained objects to reduce memory when large numbers of similar objects exist.

```csharp
public sealed record Font(string Family, int Size);

public sealed class Character
{
    public char Glyph { get; init; }
    public Font Font  { get; init; } = null!; // shared flyweight
    public int  X     { get; init; }
    public int  Y     { get; init; }
}

public static class FontFactory
{
    private static readonly Dictionary<(string, int), Font> cache = new();

    public static Font Get(string family, int size)
    {
        var key = (family, size);
        if (!cache.TryGetValue(key, out var font))
        {
            font = new Font(family, size);
            cache[key] = font;
        }
        return font;
    }
}

// Usage — thousands of characters share a handful of Font instances
var chars = new[]
{
    new Character { Glyph = 'H', Font = FontFactory.Get("Arial", 12), X = 0,  Y = 0  },
    new Character { Glyph = 'i', Font = FontFactory.Get("Arial", 12), X = 10, Y = 0  },
    new Character { Glyph = '!', Font = FontFactory.Get("Arial", 14), X = 20, Y = 0  },
};
```

**What to notice:**
- `Font` is a `record` — value equality means two calls with the same arguments return the same cached instance.
- Intrinsic state (`Font`) is shared; extrinsic state (`X`, `Y`, `Glyph`) stays per-object.
- The factory is the only place that decides whether to create or reuse, keeping caching transparent to callers.

---

## Composite

Treats individual objects and compositions of objects uniformly through a shared interface.

```csharp
public interface IComponent
{
    string Name { get; }
    long GetSize();
}

public sealed class File : IComponent
{
    public string Name { get; }
    private readonly long size;

    public File(string name, long size) => (Name, this.size) = (name, size);

    public long GetSize() => size;
}

public sealed class Directory : IComponent
{
    public string Name { get; }
    private readonly List<IComponent> children = new();

    public Directory(string name) => Name = name;

    public void Add(IComponent component) => children.Add(component);

    public long GetSize() => children.Sum(c => c.GetSize());
}

// Usage
var root = new Directory("root");
var src  = new Directory("src");
src.Add(new File("Program.cs", 4_096));
src.Add(new File("Utils.cs",   2_048));
root.Add(src);
root.Add(new File("README.md", 512));

Console.WriteLine(root.GetSize()); // 6656
```

**What to notice:**
- `Directory.GetSize()` calls `GetSize()` on each child without knowing whether the child is a `File` or another `Directory`.
- Adding a new node type (e.g., `SymLink`) only requires implementing `IComponent` — no existing code changes.
- The recursive nature of `GetSize()` emerges naturally from the composite structure, not from explicit tree-walking logic in the caller.

---

## Result Pattern

Returns a typed Success/Failure value instead of throwing exceptions, making error paths explicit and composable.

```csharp
public sealed class Result<T>
{
    public bool IsSuccess { get; }
    public T?   Value     { get; }
    public string Error   { get; }

    private Result(bool isSuccess, T? value, string error)
    {
        IsSuccess = isSuccess;
        Value     = value;
        Error     = error;
    }

    public static Result<T> Success(T value) => new(true,  value,  string.Empty);
    public static Result<T> Failure(string error) => new(false, default, error);
}

public sealed record User(string Id, string Email);

public static class UserRegistration
{
    public static Result<User> Register(string email, string password)
    {
        if (string.IsNullOrWhiteSpace(email))
            return Result<User>.Failure("Email is required.");

        if (password.Length < 8)
            return Result<User>.Failure("Password must be at least 8 characters.");

        var user = new User(Guid.NewGuid().ToString(), email);
        return Result<User>.Success(user);
    }
}

// Usage
var result = UserRegistration.Register("alice@example.com", "s3cr3t!!");
if (result.IsSuccess)
    Console.WriteLine($"Registered: {result.Value!.Email}");
else
    Console.WriteLine($"Error: {result.Error}");
```

**What to notice:**
- Error paths are visible in the return type — callers cannot ignore them without a deliberate `!` or unchecked access.
- The private constructor enforces that `Value` is only populated on success and `Error` only on failure.
- This pattern composes well with LINQ (`Select`, `Where`) or monadic chains (`Map`, `Bind`) once the `Result<T>` type is extended.
