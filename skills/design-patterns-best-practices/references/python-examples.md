# Python Examples

Pattern examples in Python. Each section shows one design pattern using the same domain scenario as the other language files.

## Strategy

A small role interface isolates the variation. The host class depends on the role, not on concrete branching logic.

```python
class TaxPolicy:
    def calculate(self, subtotal_in_cents: int) -> int:
        raise NotImplementedError


class StandardTaxPolicy(TaxPolicy):
    def calculate(self, subtotal_in_cents: int) -> int:
        return round(subtotal_in_cents * 0.21)


class Invoice:
    def __init__(self, tax_policy: TaxPolicy) -> None:
        self._tax_policy = tax_policy

    def tax(self, subtotal_in_cents: int) -> int:
        return self._tax_policy.calculate(subtotal_in_cents)
```

**What to notice:**
- The variation is isolated behind a small role.
- `Invoice` depends on the behavior it needs, not on concrete branching details.
- Adding another tax policy becomes an additive change.

---

## State

An object changes its behavior as it transitions through states. Each state is an object that knows what actions are legal and what the next state should be.

```python
class OrderState:
    def confirm(self, order): raise NotImplementedError
    def ship(self, order):    raise NotImplementedError
    def cancel(self, order):  raise NotImplementedError


class PendingState(OrderState):
    def confirm(self, order): order.transition_to(ConfirmedState())
    def ship(self, order):    raise ValueError("Cannot ship a pending order")
    def cancel(self, order):  order.transition_to(CancelledState())


class ConfirmedState(OrderState):
    def confirm(self, order): raise ValueError("Already confirmed")
    def ship(self, order):    order.transition_to(ShippedState())
    def cancel(self, order):  order.transition_to(CancelledState())


class ShippedState(OrderState):
    def confirm(self, order): raise ValueError("Already shipped")
    def ship(self, order):    raise ValueError("Already shipped")
    def cancel(self, order):  raise ValueError("Cannot cancel a shipped order")


class CancelledState(OrderState):
    def confirm(self, order): raise ValueError("Order is cancelled")
    def ship(self, order):    raise ValueError("Order is cancelled")
    def cancel(self, order):  raise ValueError("Already cancelled")


class Order:
    def __init__(self):
        self._state: OrderState = PendingState()

    def transition_to(self, state: OrderState) -> None:
        self._state = state

    def confirm(self): self._state.confirm(self)
    def ship(self):    self._state.ship(self)
    def cancel(self):  self._state.cancel(self)
```

**What to notice:**
- Each state object enforces which transitions are legal, eliminating conditionals in `Order`.
- Adding a new state (e.g., `DeliveredState`) is an additive change — existing state classes are untouched.
- The host object delegates every action to the current state and holds no branching logic of its own.

---

## Factory Method

A base class defines the creation step; subclasses decide which concrete type to instantiate. Callers work with the returned object through a shared interface.

```python
from abc import ABC, abstractmethod


class Notification(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> None: ...


class EmailNotification(Notification):
    def send(self, recipient: str, message: str) -> None:
        print(f"Email to {recipient}: {message}")


class SmsNotification(Notification):
    def send(self, recipient: str, message: str) -> None:
        print(f"SMS to {recipient}: {message}")


class NotificationSender(ABC):
    @abstractmethod
    def _create_notification(self) -> Notification: ...

    def notify(self, recipient: str, message: str) -> None:
        self._create_notification().send(recipient, message)


class EmailSender(NotificationSender):
    def _create_notification(self) -> Notification:
        return EmailNotification()


class SmsSender(NotificationSender):
    def _create_notification(self) -> Notification:
        return SmsNotification()
```

**What to notice:**
- The `notify` method in the base class never names a concrete type — construction is fully deferred to subclasses.
- Adding a push notification channel means adding one new subclass pair; the base class is untouched.
- Callers use `NotificationSender` and never know which channel they are talking to.

---

## Decorator

Behavior is layered onto an object without changing its interface or subclassing it. Each decorator wraps the previous one, adding one concern at a time.

```python
class DataExporter:
    def export(self, data: str) -> str:
        raise NotImplementedError


class FileExporter(DataExporter):
    def export(self, data: str) -> str:
        return f"[FILE] {data}"


class CompressionDecorator(DataExporter):
    def __init__(self, inner: DataExporter) -> None:
        self._inner = inner

    def export(self, data: str) -> str:
        return f"[COMPRESSED] {self._inner.export(data)}"


class EncryptionDecorator(DataExporter):
    def __init__(self, inner: DataExporter) -> None:
        self._inner = inner

    def export(self, data: str) -> str:
        return f"[ENCRYPTED] {self._inner.export(data)}"


# Usage
exporter = EncryptionDecorator(CompressionDecorator(FileExporter()))
print(exporter.export("report"))
# [ENCRYPTED] [COMPRESSED] [FILE] report
```

**What to notice:**
- Every decorator shares the same interface as the object it wraps, so they are interchangeable from the caller's perspective.
- Layers compose at construction time — order matters and is explicit.
- Neither `FileExporter` nor any decorator changes when a new concern (e.g., logging) is added.

---

## Observer

An object (Subject) maintains a list of listeners and notifies them automatically when its state changes. Listeners and Subject are decoupled — neither knows the concrete type of the other.

```python
from dataclasses import dataclass
from typing import Protocol


@dataclass
class UserRegisteredEvent:
    user_id: str
    email: str


class EventListener(Protocol):
    def on_user_registered(self, event: UserRegisteredEvent) -> None: ...


class Logger:
    def on_user_registered(self, event: UserRegisteredEvent) -> None:
        print(f"[LOG] User registered: {event.user_id}")


class WelcomeEmailSender:
    def on_user_registered(self, event: UserRegisteredEvent) -> None:
        print(f"[EMAIL] Welcome email sent to {event.email}")


class UserService:
    def __init__(self) -> None:
        self._listeners: list[EventListener] = []

    def subscribe(self, listener: EventListener) -> None:
        self._listeners.append(listener)

    def register(self, user_id: str, email: str) -> None:
        # ... persist the user ...
        event = UserRegisteredEvent(user_id, email)
        for listener in self._listeners:
            listener.on_user_registered(event)
```

**What to notice:**
- `UserService` depends only on the `EventListener` protocol — it has no knowledge of `Logger` or `WelcomeEmailSender`.
- New reactions to user registration are added by writing a new listener and calling `subscribe`; `UserService` is not touched.
- The event object carries all the data listeners need, keeping the notification call-site clean.

---

## Command

Encapsulate a request as an object so that the sender and the executor are fully decoupled — enabling undo/redo, queuing, and logging of operations.

```python
from abc import ABC, abstractmethod


class Command(ABC):
    @abstractmethod
    def execute(self) -> None: ...

    @abstractmethod
    def undo(self) -> None: ...


class TextEditor:
    def __init__(self) -> None:
        self.content: str = ""

    def apply_bold(self, text: str) -> None:
        self.content += f"**{text}**"

    def remove_last(self, length: int) -> None:
        self.content = self.content[:-length]


class BoldCommand(Command):
    def __init__(self, editor: TextEditor, text: str) -> None:
        self._editor = editor
        self._text = text
        self._applied_length = len(f"**{text}**")

    def execute(self) -> None:
        self._editor.apply_bold(self._text)

    def undo(self) -> None:
        self._editor.remove_last(self._applied_length)


class CommandHistory:
    def __init__(self) -> None:
        self._history: list[Command] = []

    def execute(self, command: Command) -> None:
        command.execute()
        self._history.append(command)

    def undo(self) -> None:
        if self._history:
            self._history.pop().undo()
```

**What to notice:**
- Each command object captures both the action (`execute`) and its inverse (`undo`), keeping undo/redo logic out of the editor.
- `CommandHistory` is blind to what any command does — it only manages the stack, making it reusable for any command type.
- Adding a new operation (e.g., `ItalicCommand`) is an additive change; no existing class is modified.

---

## Template Method

Define a fixed algorithm skeleton in a base class and let subclasses override only the steps that vary, without changing the overall structure.

```python
from abc import ABC, abstractmethod


class ReportGenerator(ABC):
    def generate(self, raw_data: list[dict]) -> str:
        data = self._gather_data(raw_data)
        formatted = self._format_data(data)
        return self._output(formatted)

    def _gather_data(self, raw_data: list[dict]) -> list[dict]:
        return [row for row in raw_data if row]

    @abstractmethod
    def _format_data(self, data: list[dict]) -> str: ...

    def _output(self, formatted: str) -> str:
        return formatted


class CsvReportGenerator(ReportGenerator):
    def _format_data(self, data: list[dict]) -> str:
        if not data:
            return ""
        headers = ",".join(data[0].keys())
        rows = "\n".join(",".join(str(v) for v in row.values()) for row in data)
        return f"{headers}\n{rows}"


class PdfReportGenerator(ReportGenerator):
    def _format_data(self, data: list[dict]) -> str:
        lines = [" | ".join(str(v) for v in row.values()) for row in data]
        return "\n".join(lines)
```

**What to notice:**
- The invariant steps (`_gather_data`, `_output`) live once in the base class; subclasses touch only what actually differs.
- The `generate` method is the template — callers invoke it without knowing which subclass they are using.
- Adding a new output format (e.g., JSON) requires only a new subclass that overrides `_format_data`.

---

## Chain of Responsibility

Pass a request along a chain of handlers; each handler decides to process the request, pass it forward, or stop the chain.

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class HttpRequest:
    path: str
    token: str | None


class Middleware(ABC):
    def __init__(self) -> None:
        self._next: Middleware | None = None

    def set_next(self, handler: Middleware) -> Middleware:
        self._next = handler
        return handler

    def pass_to_next(self, request: HttpRequest) -> str:
        if self._next:
            return self._next.handle(request)
        return "200 OK"

    @abstractmethod
    def handle(self, request: HttpRequest) -> str: ...


class AuthMiddleware(Middleware):
    def handle(self, request: HttpRequest) -> str:
        if not request.token:
            return "401 Unauthorized"
        return self.pass_to_next(request)


class LoggingMiddleware(Middleware):
    def handle(self, request: HttpRequest) -> str:
        print(f"[LOG] {request.path}")
        return self.pass_to_next(request)


class RequestHandler(Middleware):
    def handle(self, request: HttpRequest) -> str:
        return f"Handled: {request.path}"


# Wiring
auth = AuthMiddleware()
auth.set_next(LoggingMiddleware()).set_next(RequestHandler())
```

**What to notice:**
- Each middleware is unaware of the others — it only knows how to call `pass_to_next`.
- The chain is assembled at the call site, not hardcoded inside any handler, so order and membership are easy to change.
- Short-circuiting (returning early from `AuthMiddleware`) stops the chain without any special coordination.

---

## Iterator

Provide sequential access to elements of a collection without exposing its internal representation.

```python
from __future__ import annotations


class NumberRangeIterator:
    def __init__(self, start: int, end: int, step: int) -> None:
        self._current = start
        self._end = end
        self._step = step

    def __iter__(self) -> NumberRangeIterator:
        return self

    def __next__(self) -> int:
        if self._current >= self._end:
            raise StopIteration
        value = self._current
        self._current += self._step
        return value


class NumberRange:
    def __init__(self, start: int, end: int, step: int = 1) -> None:
        self._start = start
        self._end = end
        self._step = step

    def __iter__(self) -> NumberRangeIterator:
        return NumberRangeIterator(self._start, self._end, self._step)


# Usage — works with all Python iteration protocols
for n in NumberRange(0, 10, 2):
    print(n)  # 0 2 4 6 8

total = sum(NumberRange(1, 6))  # 15
```

**What to notice:**
- `NumberRange` exposes no list, index, or internal cursor — callers iterate through the public protocol only.
- Separating the iterator object from the collection lets multiple independent iterations run over the same range simultaneously.
- Implementing `__iter__` and `__next__` integrates seamlessly with `for`, `sum`, `list()`, and every other Python construct that consumes iterables.

---

## Mediator

Centralize communication between objects so that they do not reference each other directly, reducing coupling across the system.

```python
from __future__ import annotations
from dataclasses import dataclass, field


class ChatRoom:
    def __init__(self) -> None:
        self._users: list[User] = []

    def join(self, user: User) -> None:
        self._users.append(user)

    def send(self, message: str, sender: User) -> None:
        for user in self._users:
            if user is not sender:
                user.receive(message, sender.name)


@dataclass
class User:
    name: str
    _room: ChatRoom = field(repr=False, default=None)  # type: ignore[assignment]

    def join(self, room: ChatRoom) -> None:
        self._room = room
        room.join(self)

    def send(self, message: str) -> None:
        self._room.send(message, self)

    def receive(self, message: str, from_name: str) -> None:
        print(f"[{self.name}] received from {from_name}: {message}")


# Usage
room = ChatRoom()
alice, bob = User("Alice"), User("Bob")
alice.join(room)
bob.join(room)
alice.send("Hello!")  # Bob receives; Alice does not
```

**What to notice:**
- `User` objects never hold references to each other — all routing goes through `ChatRoom`.
- Adding a new participant requires no changes to existing `User` instances or to `ChatRoom`'s routing logic.
- The mediator is the single place where delivery rules live (e.g., "don't echo back to sender"), so that logic is not scattered across users.

---

## Builder

Construct a complex object step by step through a fluent interface, separating the assembly process from the final representation.

```python
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Query:
    table: str
    columns: list[str]
    conditions: list[str]
    limit: int | None


class QueryBuilder:
    def __init__(self, table: str) -> None:
        self._table = table
        self._columns: list[str] = ["*"]
        self._conditions: list[str] = []
        self._limit: int | None = None

    def select(self, *columns: str) -> QueryBuilder:
        self._columns = list(columns)
        return self

    def where(self, condition: str) -> QueryBuilder:
        self._conditions.append(condition)
        return self

    def limit(self, n: int) -> QueryBuilder:
        self._limit = n
        return self

    def build(self) -> Query:
        return Query(
            table=self._table,
            columns=self._columns,
            conditions=self._conditions,
            limit=self._limit,
        )


# Usage
query = (
    QueryBuilder("users")
    .select("id", "email")
    .where("active = true")
    .where("age > 18")
    .limit(50)
    .build()
)
```

**What to notice:**
- Each method returns `self`, enabling a fluent chain that reads like a sentence describing the desired query.
- `build()` is the single point where the final object is assembled — partial state in the builder is never exposed.
- Construction order is flexible; callers can omit optional steps (`limit`, `where`) without receiving a broken object.

---

## Abstract Factory

Create families of related objects without coupling client code to any concrete class, ensuring that objects from one family are always used together.

```python
from abc import ABC, abstractmethod


class Button(ABC):
    @abstractmethod
    def render(self) -> str: ...


class Checkbox(ABC):
    @abstractmethod
    def render(self) -> str: ...


class UIFactory(ABC):
    @abstractmethod
    def create_button(self) -> Button: ...

    @abstractmethod
    def create_checkbox(self) -> Checkbox: ...


class WindowsButton(Button):
    def render(self) -> str:
        return "<WinButton>"


class WindowsCheckbox(Checkbox):
    def render(self) -> str:
        return "<WinCheckbox>"


class MacButton(Button):
    def render(self) -> str:
        return "<MacButton>"


class MacCheckbox(Checkbox):
    def render(self) -> str:
        return "<MacCheckbox>"


class WindowsFactory(UIFactory):
    def create_button(self) -> Button:
        return WindowsButton()

    def create_checkbox(self) -> Checkbox:
        return WindowsCheckbox()


class MacFactory(UIFactory):
    def create_button(self) -> Button:
        return MacButton()

    def create_checkbox(self) -> Checkbox:
        return MacCheckbox()


def render_ui(factory: UIFactory) -> None:
    print(factory.create_button().render())
    print(factory.create_checkbox().render())
```

**What to notice:**
- `render_ui` never mentions Windows or Mac — it works with any factory that satisfies `UIFactory`.
- The factory enforces consistency: a `WindowsFactory` can never accidentally hand out a `MacCheckbox`.
- Adding a new platform (e.g., `LinuxFactory`) is entirely additive; existing code is untouched.

---

## Singleton

Ensure that a class has exactly one instance and provide a global access point to it.

```python
class Logger:
    _instance: "Logger | None" = None

    def __new__(cls) -> "Logger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._log: list[str] = []
        return cls._instance

    def log(self, message: str) -> None:
        self._log.append(message)
        print(f"[LOG] {message}")

    def entries(self) -> list[str]:
        return list(self._log)


# Both references point to the same object
a = Logger()
b = Logger()
assert a is b
```

> **Trade-off note:** Singleton is widely considered an anti-pattern in application code. The shared instance is effectively global state, which creates hidden coupling between modules, makes execution order matter in surprising ways, and makes unit testing difficult — tests cannot easily replace the instance with a test double. Prefer passing a single instance through dependency injection (constructor or function argument) instead of fetching it via `__new__` or a class method.

**What to notice:**
- `__new__` guards construction, so `Logger()` always returns the same object regardless of how many times it is called.
- The pattern solves a real problem (one shared resource), but the solution introduces global state as a side effect.
- Dependency injection achieves the same "one instance" goal while keeping the object replaceable and the dependency explicit.

---

## Proxy

Provide a surrogate object that controls access to another object — deferring expensive work, adding access control, or logging transparently.

```python
from abc import ABC, abstractmethod


class Image(ABC):
    @abstractmethod
    def display(self) -> None: ...


class RealImage(Image):
    def __init__(self, path: str) -> None:
        self._path = path
        self._load()

    def _load(self) -> None:
        print(f"[LOAD] Loading image from disk: {self._path}")

    def display(self) -> None:
        print(f"[DISPLAY] {self._path}")


class VirtualImageProxy(Image):
    def __init__(self, path: str) -> None:
        self._path = path
        self._real: RealImage | None = None

    def display(self) -> None:
        if self._real is None:
            self._real = RealImage(self._path)  # loaded on first access
        self._real.display()


# Usage
image = VirtualImageProxy("photo.jpg")
# No disk I/O yet
image.display()  # [LOAD] + [DISPLAY] on first call
image.display()  # [DISPLAY] only — already loaded
```

**What to notice:**
- `VirtualImageProxy` shares the exact same interface as `RealImage`, so callers need no special handling.
- The expensive `_load` call is deferred until the resource is actually needed, not at construction time.
- The proxy is transparent: swapping `VirtualImageProxy` for `RealImage` requires no changes at the call site.

---

## Facade

Provide a single simplified interface to a complex subsystem, shielding clients from the coordination details between its parts.

```python
class Amplifier:
    def on(self) -> None:  print("[AMP] On")
    def off(self) -> None: print("[AMP] Off")
    def set_volume(self, level: int) -> None: print(f"[AMP] Volume {level}")


class DVDPlayer:
    def on(self) -> None:  print("[DVD] On")
    def off(self) -> None: print("[DVD] Off")
    def play(self, movie: str) -> None: print(f"[DVD] Playing '{movie}'")


class Projector:
    def on(self) -> None:  print("[PROJ] On")
    def off(self) -> None: print("[PROJ] Off")


class HomeTheaterFacade:
    def __init__(self, amp: Amplifier, dvd: DVDPlayer, proj: Projector) -> None:
        self._amp = amp
        self._dvd = dvd
        self._proj = proj

    def watch_movie(self, movie: str) -> None:
        self._proj.on()
        self._amp.on()
        self._amp.set_volume(5)
        self._dvd.on()
        self._dvd.play(movie)

    def end_movie(self) -> None:
        self._dvd.off()
        self._amp.off()
        self._proj.off()


# Usage
theater = HomeTheaterFacade(Amplifier(), DVDPlayer(), Projector())
theater.watch_movie("Inception")
theater.end_movie()
```

**What to notice:**
- `HomeTheaterFacade` does not add new behavior — it only coordinates the existing subsystem in a repeatable sequence.
- Clients call two methods; the six-step startup ritual is invisible to them.
- The subsystem components remain fully accessible for advanced use; the facade is an optional convenience layer, not a gatekeeper.

---

## Bridge

Decouple an abstraction from its implementation so that both can vary independently along separate axes.

```python
from abc import ABC, abstractmethod


class DrawingAPI(ABC):
    @abstractmethod
    def draw_circle(self, x: float, y: float, radius: float) -> str: ...

    @abstractmethod
    def draw_square(self, x: float, y: float, side: float) -> str: ...


class SVGDrawer(DrawingAPI):
    def draw_circle(self, x: float, y: float, radius: float) -> str:
        return f'<circle cx="{x}" cy="{y}" r="{radius}"/>'

    def draw_square(self, x: float, y: float, side: float) -> str:
        return f'<rect x="{x}" y="{y}" width="{side}" height="{side}"/>'


class CanvasDrawer(DrawingAPI):
    def draw_circle(self, x: float, y: float, radius: float) -> str:
        return f"ctx.arc({x},{y},{radius},0,2*Math.PI)"

    def draw_square(self, x: float, y: float, side: float) -> str:
        return f"ctx.fillRect({x},{y},{side},{side})"


class Shape(ABC):
    def __init__(self, api: DrawingAPI) -> None:
        self._api = api

    @abstractmethod
    def render(self) -> str: ...


class Circle(Shape):
    def __init__(self, x: float, y: float, radius: float, api: DrawingAPI) -> None:
        super().__init__(api)
        self._x, self._y, self._radius = x, y, radius

    def render(self) -> str:
        return self._api.draw_circle(self._x, self._y, self._radius)


class Square(Shape):
    def __init__(self, x: float, y: float, side: float, api: DrawingAPI) -> None:
        super().__init__(api)
        self._x, self._y, self._side = x, y, side

    def render(self) -> str:
        return self._api.draw_square(self._x, self._y, self._side)
```

**What to notice:**
- There are two independent variation axes: shape type (`Circle`, `Square`) and rendering target (`SVGDrawer`, `CanvasDrawer`). Each axis can grow without affecting the other.
- Without Bridge, supporting N shapes and M renderers would require N×M subclasses; here it requires N+M concrete classes.
- The shape abstraction holds a reference to the implementation rather than inheriting from it — this is the defining structural choice of Bridge.

---

## Flyweight

Share the intrinsic (context-independent) state of fine-grained objects so that a large number of instances can be maintained with low memory overhead.

```python
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Font:
    family: str
    size: int


class FontFactory:
    _cache: dict[tuple[str, int], Font] = {}

    @classmethod
    def get(cls, family: str, size: int) -> Font:
        key = (family, size)
        if key not in cls._cache:
            cls._cache[key] = Font(family, size)
        return cls._cache[key]


@dataclass
class Character:
    char: str
    position: int
    font: Font  # shared flyweight — not duplicated per character


# Simulating a 10 000-character document using only a handful of Font objects
document: list[Character] = [
    Character(char="a", position=i, font=FontFactory.get("Arial", 12))
    for i in range(10_000)
]

assert len(FontFactory._cache) == 1          # one Font object
assert document[0].font is document[9999].font  # same identity
```

**What to notice:**
- `Font` is immutable (`frozen=True`) because shared state must not be mutated by any holder.
- The factory is the single point of truth — callers never construct `Font` directly, so the cache is never bypassed.
- Extrinsic state (`char`, `position`) stays in `Character`; only intrinsic state (`family`, `size`) is shared, keeping the pattern safe.

---

## Composite

Treat individual objects and compositions of objects uniformly through a shared interface, enabling recursive tree structures.

```python
from __future__ import annotations
from abc import ABC, abstractmethod


class FileSystemComponent(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def get_size(self) -> int: ...

    @abstractmethod
    def display(self, indent: int = 0) -> None: ...


class File(FileSystemComponent):
    def __init__(self, name: str, size: int) -> None:
        super().__init__(name)
        self._size = size

    def get_size(self) -> int:
        return self._size

    def display(self, indent: int = 0) -> None:
        print(" " * indent + f"{self.name} ({self._size}B)")


class Directory(FileSystemComponent):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._children: list[FileSystemComponent] = []

    def add(self, component: FileSystemComponent) -> None:
        self._children.append(component)

    def get_size(self) -> int:
        return sum(child.get_size() for child in self._children)

    def display(self, indent: int = 0) -> None:
        print(" " * indent + f"{self.name}/")
        for child in self._children:
            child.display(indent + 2)


# Usage
root = Directory("root")
src = Directory("src")
src.add(File("main.py", 1200))
src.add(File("utils.py", 800))
root.add(src)
root.add(File("README.md", 400))
root.display()
print(root.get_size())  # 2400
```

**What to notice:**
- `Directory.get_size()` calls `get_size()` on its children without knowing whether each child is a `File` or another `Directory` — the tree recurses naturally.
- Client code operates on `FileSystemComponent` throughout; it never needs to branch on type.
- Adding a new node type (e.g., `SymLink`) requires only a new subclass; traversal logic in `Directory` is untouched.

---

## Result Pattern

Return a typed Success/Failure value instead of raising exceptions, making error paths explicit in the type signature and forcing callers to handle them.

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T
    ok: bool = True


@dataclass(frozen=True)
class Err(Generic[E]):
    error: E
    ok: bool = False


Result = Ok[T] | Err[E]


@dataclass(frozen=True)
class User:
    email: str
    username: str


@dataclass(frozen=True)
class ValidationError:
    field: str
    message: str


def register_user(email: str, username: str) -> Result[User, ValidationError]:
    if "@" not in email:
        return Err(ValidationError(field="email", message="Invalid email address"))
    if len(username) < 3:
        return Err(ValidationError(field="username", message="Username too short"))
    return Ok(User(email=email, username=username))


# Usage — caller is forced to inspect .ok before using the value
result = register_user("alice@example.com", "al")
match result:
    case Ok(value=user):
        print(f"Registered: {user.username}")
    case Err(error=err):
        print(f"Validation failed on '{err.field}': {err.message}")
```

**What to notice:**
- The return type `Result[User, ValidationError]` documents both outcomes in the function signature — no hidden exception contract.
- `Ok` and `Err` are plain frozen dataclasses; no framework is needed, and they compose naturally with `match`, `if result.ok`, or unpacking.
- Callers cannot accidentally treat a failure as a success — they must inspect the result before accessing `value`.

---

## Enterprise Application Patterns

Patterns from Fowler's *Patterns of Enterprise Application Architecture* (PEAA). They address the layering, data access, and coordination concerns that arise in business applications.

---

### Transaction Script

**Intent:** Organise business logic for a single use case as a plain procedure that talks directly to the database.

```python
import sqlite3
from dataclasses import dataclass


@dataclass
class TransferResult:
    success: bool
    message: str


def transfer_funds(
    db: sqlite3.Connection,
    from_account: int,
    to_account: int,
    amount_cents: int,
) -> TransferResult:
    cursor = db.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE id = ?", (from_account,))
    row = cursor.fetchone()
    if row is None:
        return TransferResult(False, "Source account not found")
    if row[0] < amount_cents:
        return TransferResult(False, "Insufficient funds")

    cursor.execute(
        "UPDATE accounts SET balance = balance - ? WHERE id = ?",
        (amount_cents, from_account),
    )
    cursor.execute(
        "UPDATE accounts SET balance = balance + ? WHERE id = ?",
        (amount_cents, to_account),
    )
    db.commit()
    return TransferResult(True, "Transfer complete")
```

**Key point:** All logic for one use case lives in one function — easy to follow, but domain rules and SQL are interleaved, which becomes hard to test and reuse as the application grows.

---

### Service Layer

**Intent:** A class that coordinates domain objects and repositories and exposes coarse-grained application operations to callers.

```python
from dataclasses import dataclass


@dataclass
class Order:
    id: int
    customer_id: int
    total_cents: int
    status: str = "pending"


class OrderRepository:
    def find(self, order_id: int) -> Order: ...
    def save(self, order: Order) -> None: ...


class PaymentGateway:
    def charge(self, amount_cents: int, customer_id: int) -> bool: ...


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        payment_gateway: PaymentGateway,
    ) -> None:
        self._orders = order_repo
        self._payments = payment_gateway

    def place_order(self, order_id: int) -> None:
        order = self._orders.find(order_id)
        charged = self._payments.charge(order.total_cents, order.customer_id)
        if not charged:
            raise RuntimeError("Payment failed")
        order.status = "confirmed"
        self._orders.save(order)
```

**Key point:** The service layer owns the application workflow (fetch → charge → persist) but delegates every domain concept and I/O operation to dedicated collaborators, keeping it thin and testable.

---

### Data Mapper

**Intent:** A class that moves data between domain objects and database rows without letting either one know about the other.

```python
import sqlite3
from dataclasses import dataclass


@dataclass
class Product:
    id: int | None
    name: str
    price_cents: int


class ProductMapper:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def find(self, product_id: int) -> Product | None:
        row = self._db.execute(
            "SELECT id, name, price_cents FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        if row is None:
            return None
        return Product(id=row[0], name=row[1], price_cents=row[2])

    def insert(self, product: Product) -> Product:
        cursor = self._db.execute(
            "INSERT INTO products (name, price_cents) VALUES (?, ?)",
            (product.name, product.price_cents),
        )
        return Product(id=cursor.lastrowid, name=product.name, price_cents=product.price_cents)
```

**Key point:** `Product` contains zero SQL — all mapping logic lives in `ProductMapper`, so domain objects stay pure and the persistence strategy can change without touching the domain.

---

### Unit of Work

**Intent:** Track new, modified, and removed domain objects within a business transaction and flush all changes in a single commit.

```python
from dataclasses import dataclass, field


@dataclass
class Entity:
    id: int
    name: str


class UnitOfWork:
    def __init__(self) -> None:
        self._new: list[Entity] = []
        self._dirty: list[Entity] = []
        self._removed: list[Entity] = []

    def register_new(self, entity: Entity) -> None:
        self._new.append(entity)

    def register_dirty(self, entity: Entity) -> None:
        if entity not in self._dirty:
            self._dirty.append(entity)

    def register_removed(self, entity: Entity) -> None:
        self._removed.append(entity)

    def commit(self, db_session) -> None:
        for e in self._new:
            db_session.insert(e)
        for e in self._dirty:
            db_session.update(e)
        for e in self._removed:
            db_session.delete(e)
        db_session.flush()
        self._new.clear()
        self._dirty.clear()
        self._removed.clear()
```

**Key point:** Instead of issuing one SQL statement per change, the Unit of Work batches them and writes everything in one transaction, preventing partial updates and reducing round-trips.

---

### Data Transfer Object (DTO)

**Intent:** A plain dataclass that carries data across layer boundaries with no behaviour.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class UserDTO:
    id: int
    email: str
    display_name: str


@dataclass(frozen=True)
class CreateUserDTO:
    email: str
    password: str
    display_name: str


# Assembler — converts between domain object and DTO
class UserAssembler:
    @staticmethod
    def to_dto(user) -> UserDTO:
        return UserDTO(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
        )
```

**Key point:** DTOs are frozen and behaviour-free by design — they exist solely to transport data, preventing presentation or persistence concerns from leaking into the domain model.

---

### Value Object (Money)

**Intent:** An immutable frozen dataclass representing a monetary amount with value semantics — two Money instances with the same currency and amount are equal.

```python
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    amount_cents: int
    currency: str

    def __post_init__(self) -> None:
        if self.amount_cents < 0:
            raise ValueError("Amount cannot be negative")
        if len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")

    def add(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount_cents + other.amount_cents, self.currency)

    def multiply(self, factor: float) -> Money:
        return Money(round(self.amount_cents * factor), self.currency)

    def __str__(self) -> str:
        return f"{self.amount_cents / 100:.2f} {self.currency}"


price = Money(1000, "USD")
tax   = price.multiply(0.21)
total = price.add(tax)  # Money(1210, "USD")
```

**Key point:** `frozen=True` enforces immutability at the interpreter level, and equality is structural (amount + currency), so Money behaves like a true value rather than a mutable entity.

---

### Special Case

**Intent:** A subclass that represents a null or missing domain concept, providing safe default behaviour instead of forcing callers to check for `None`.

```python
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Customer:
    id: int
    name: str
    email: str
    credit_limit_cents: int

    def is_eligible_for_discount(self) -> bool:
        return self.credit_limit_cents > 50_000

    def send_welcome_email(self) -> None:
        print(f"Sending welcome email to {self.email}")


class NullCustomer(Customer):
    def __init__(self) -> None:
        super().__init__(id=0, name="Guest", email="", credit_limit_cents=0)

    def is_eligible_for_discount(self) -> bool:
        return False

    def send_welcome_email(self) -> None:
        pass  # no-op — no customer to email


def find_customer(customer_id: int) -> Customer:
    # ... lookup logic ...
    return NullCustomer()  # returned when not found


customer = find_customer(99)
customer.send_welcome_email()          # safe — no None check needed
print(customer.is_eligible_for_discount())  # False
```

**Key point:** By returning a `NullCustomer` instead of `None`, callers interact with the same interface without any `if customer is not None` guards scattered throughout the codebase.

---

### Gateway

**Intent:** A class that wraps an external API or service behind a clean, domain-focused interface, hiding HTTP details from the rest of the application.

```python
from dataclasses import dataclass
from typing import Protocol
import json
import urllib.request


@dataclass(frozen=True)
class ExchangeRate:
    from_currency: str
    to_currency: str
    rate: float


class CurrencyGateway(Protocol):
    def get_rate(self, from_currency: str, to_currency: str) -> ExchangeRate: ...


class OpenExchangeRateGateway:
    BASE_URL = "https://api.example.com/rates"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def get_rate(self, from_currency: str, to_currency: str) -> ExchangeRate:
        url = f"{self.BASE_URL}?base={from_currency}&key={self._api_key}"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
        rate = data["rates"][to_currency]
        return ExchangeRate(from_currency, to_currency, rate)
```

**Key point:** The `CurrencyGateway` Protocol lets tests swap in a stub without touching any HTTP code — the gateway isolates the volatility of the external dependency behind a stable interface.

---

### Query Object

**Intent:** An object that encapsulates filter criteria for a collection query, decoupling callers from raw SQL or query-language strings.

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProductQuery:
    max_price_cents: int | None = None
    min_price_cents: int | None = None
    name_contains: str | None = None
    in_stock_only: bool = False

    def to_sql(self) -> tuple[str, list[Any]]:
        clauses: list[str] = ["SELECT * FROM products WHERE 1=1"]
        params: list[Any] = []

        if self.max_price_cents is not None:
            clauses.append("AND price_cents <= ?")
            params.append(self.max_price_cents)
        if self.min_price_cents is not None:
            clauses.append("AND price_cents >= ?")
            params.append(self.min_price_cents)
        if self.name_contains is not None:
            clauses.append("AND name LIKE ?")
            params.append(f"%{self.name_contains}%")
        if self.in_stock_only:
            clauses.append("AND stock > 0")

        return " ".join(clauses), params


# Usage
query = ProductQuery(max_price_cents=5000, in_stock_only=True)
sql, params = query.to_sql()
```

**Key point:** Criteria are first-class objects that can be built, passed around, logged, and tested without ever concatenating raw SQL strings in business logic.

---

### Layer Supertype

**Intent:** A base class for an entire layer that holds shared behaviour — auto-generated IDs, timestamps, equality — so every entity inherits it without repeating the boilerplate.

```python
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Entity:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class Product(Entity):
    name: str = ""
    price_cents: int = 0


@dataclass
class Customer(Entity):
    email: str = ""
```

**Key point:** Identity (`id`), audit fields (`created_at`, `updated_at`), and equality semantics are defined exactly once in `Entity` — domain classes inherit the contract rather than duplicating it.

---

## Remaining GoF Patterns

### Adapter

**Intent:** Wrap a third-party or legacy interface behind the interface your code expects.

```python
from typing import Protocol
from dataclasses import dataclass


@dataclass
class PaymentResult:
    success: bool
    transaction_id: str


class PaymentGateway(Protocol):
    def charge(self, amount_cents: int, currency: str) -> PaymentResult: ...


# Simulated external SDK with an incompatible interface
class StripeSDK:
    def create_charge(self, amount: int, currency_code: str) -> dict:
        return {"status": "ok", "id": "ch_123"}


class StripeAdapter:
    def __init__(self, sdk: StripeSDK) -> None:
        self._sdk = sdk

    def charge(self, amount_cents: int, currency: str) -> PaymentResult:
        raw = self._sdk.create_charge(amount=amount_cents, currency_code=currency)
        return PaymentResult(success=raw["status"] == "ok", transaction_id=raw["id"])


# Usage — application code depends only on PaymentGateway Protocol
def process_payment(gateway: PaymentGateway, amount_cents: int) -> None:
    result = gateway.charge(amount_cents, "USD")
    print(f"Charged: {result.transaction_id}" if result.success else "Failed")
```

**Key point:** The adapter translates the external SDK's vocabulary into the local `PaymentGateway` Protocol so application code never imports or knows about the third-party SDK.

---

### Visitor

**Intent:** Separate an algorithm from the object structure it operates on.

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol


class DocumentElement(ABC):
    @abstractmethod
    def accept(self, visitor: ElementVisitor) -> None: ...


class ElementVisitor(Protocol):
    def visit_heading(self, heading: Heading) -> None: ...
    def visit_paragraph(self, paragraph: Paragraph) -> None: ...


@dataclass
class Heading(DocumentElement):
    text: str
    level: int

    def accept(self, visitor: ElementVisitor) -> None:
        visitor.visit_heading(self)


@dataclass
class Paragraph(DocumentElement):
    text: str

    def accept(self, visitor: ElementVisitor) -> None:
        visitor.visit_paragraph(self)


class WordCountVisitor:
    def __init__(self) -> None:
        self.count = 0

    def visit_heading(self, heading: Heading) -> None:
        self.count += len(heading.text.split())

    def visit_paragraph(self, paragraph: Paragraph) -> None:
        self.count += len(paragraph.text.split())


class HtmlRenderVisitor:
    def __init__(self) -> None:
        self.output: list[str] = []

    def visit_heading(self, heading: Heading) -> None:
        self.output.append(f"<h{heading.level}>{heading.text}</h{heading.level}>")

    def visit_paragraph(self, paragraph: Paragraph) -> None:
        self.output.append(f"<p>{paragraph.text}</p>")
```

**Key point:** New operations (word count, HTML render, PDF export) are added as new visitor classes without touching `Heading` or `Paragraph`, keeping the element hierarchy stable.

---

### Memento

**Intent:** Capture and restore object state without exposing internals.

```python
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Memento:
    content: str


class TextEditor:
    def __init__(self) -> None:
        self._content: str = ""

    def type(self, text: str) -> None:
        self._content += text

    def save(self) -> Memento:
        return Memento(content=self._content)

    def restore(self, memento: Memento) -> None:
        self._content = memento.content

    @property
    def content(self) -> str:
        return self._content


class History:
    def __init__(self) -> None:
        self._stack: list[Memento] = []

    def push(self, memento: Memento) -> None:
        self._stack.append(memento)

    def pop(self) -> Memento | None:
        return self._stack.pop() if self._stack else None


# Usage
editor = TextEditor()
history = History()

editor.type("Hello")
history.push(editor.save())
editor.type(", World")
history.push(editor.save())
editor.type("!!!")

editor.restore(history.pop())   # back to "Hello, World"
editor.restore(history.pop())   # back to "Hello"
print(editor.content)           # Hello
```

**Key point:** `Memento` is a frozen dataclass that captures a snapshot of internal state; `History` (the caretaker) stores and returns snapshots without ever reading their contents.

---

### Prototype

**Intent:** Clone a configured object instead of constructing from scratch.

```python
from __future__ import annotations
import copy
from dataclasses import dataclass, field


@dataclass
class PageLayout:
    font: str
    font_size: int
    margins: dict[str, int]
    tags: list[str]

    def clone(self) -> PageLayout:
        return copy.deepcopy(self)


# Build one fully-configured template once
report_template = PageLayout(
    font="Arial",
    font_size=11,
    margins={"top": 20, "bottom": 20, "left": 25, "right": 25},
    tags=["confidential"],
)

# Stamp out customised copies without re-specifying every field
cover_page = report_template.clone()
cover_page.font_size = 16
cover_page.tags.append("cover")

body_page = report_template.clone()
body_page.margins["left"] = 30

# Original is untouched
assert report_template.font_size == 11
assert report_template.tags == ["confidential"]
```

## DDD Tactical Patterns

### Entity

**Intent:** An object with a unique identity that persists over time; equality is based on identity, not attributes.

```python
from dataclasses import dataclass, field
from uuid import UUID, uuid4

@dataclass
class Order:
    id: UUID = field(default_factory=uuid4)
    customer_id: UUID = None
    status: str = "pending"

    def confirm(self) -> None:
        if self.status != "pending":
            raise ValueError("Only pending orders can be confirmed")
        self.status = "confirmed"

    def cancel(self) -> None:
        if self.status == "shipped":
            raise ValueError("Cannot cancel a shipped order")
        self.status = "cancelled"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Order):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
```

**Key point:** Two `Order` instances with the same ID are the same entity regardless of their current attribute values.

---

### Aggregate Root

**Intent:** An entity that controls access to a cluster of objects, enforces invariants, and collects domain events internally.

```python
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import List

@dataclass
class OrderItemAdded:
    order_id: UUID
    product_id: UUID
    quantity: int

@dataclass
class OrderItem:
    product_id: UUID
    quantity: int
    unit_price: float

@dataclass
class Order:
    id: UUID = field(default_factory=uuid4)
    items: List[OrderItem] = field(default_factory=list)
    _events: List[object] = field(default_factory=list, repr=False)
    MAX_ITEMS = 50

    def add_item(self, product_id: UUID, quantity: int, unit_price: float) -> None:
        if len(self.items) >= self.MAX_ITEMS:
            raise ValueError("Order cannot exceed 50 items")
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        self.items.append(OrderItem(product_id, quantity, unit_price))
        self._events.append(OrderItemAdded(self.id, product_id, quantity))

    def collect_events(self) -> List[object]:
        events, self._events = self._events, []
        return events

    @property
    def total(self) -> float:
        return sum(i.quantity * i.unit_price for i in self.items)
```

**Key point:** External code never manipulates `items` directly — all mutations go through the aggregate root, which enforces invariants and records events.

---

### Domain Event

**Intent:** An immutable record of something significant that happened in the domain.

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

@dataclass(frozen=True)
class OrderPlaced:
    order_id: UUID
    customer_id: UUID
    total_amount: float
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

# Usage
event = OrderPlaced(
    order_id=uuid4(),
    customer_id=uuid4(),
    total_amount=149.99,
)
# event.total_amount = 0  # raises FrozenInstanceError — immutable by design
```

**Key point:** `frozen=True` makes the event truly immutable; the `event_id` and `occurred_at` are auto-assigned so callers cannot accidentally omit them.

---

### Specification

**Intent:** An encapsulated, combinable business rule that can be tested against a candidate object.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Customer:
    is_active: bool
    total_spent: float
    age: int

class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, candidate: Customer) -> bool: ...

    def __and__(self, other: "Specification") -> "AndSpec":
        return AndSpec(self, other)

    def __or__(self, other: "Specification") -> "OrSpec":
        return OrSpec(self, other)

    def __invert__(self) -> "NotSpec":
        return NotSpec(self)

@dataclass
class AndSpec(Specification):
    left: Specification
    right: Specification
    def is_satisfied_by(self, c: Customer) -> bool:
        return self.left.is_satisfied_by(c) and self.right.is_satisfied_by(c)

@dataclass
class OrSpec(Specification):
    left: Specification
    right: Specification
    def is_satisfied_by(self, c: Customer) -> bool:
        return self.left.is_satisfied_by(c) or self.right.is_satisfied_by(c)

@dataclass
class NotSpec(Specification):
    spec: Specification
    def is_satisfied_by(self, c: Customer) -> bool:
        return not self.spec.is_satisfied_by(c)

class ActiveCustomerSpec(Specification):
    def is_satisfied_by(self, c: Customer) -> bool:
        return c.is_active

class PremiumCustomerSpec(Specification):
    def is_satisfied_by(self, c: Customer) -> bool:
        return c.total_spent >= 1000.0

# Combine: active AND premium
eligible = ActiveCustomerSpec() & PremiumCustomerSpec()
customer = Customer(is_active=True, total_spent=1500.0, age=30)
assert eligible.is_satisfied_by(customer)  # True
```

**Key point:** Business rules are named, testable objects that compose via `&`, `|`, and `~` without modifying either rule.

## CQRS and Error Patterns

### Command + CommandHandler (CQRS write side)

**Intent:** Separate the write-side intent (Command) from its execution logic (CommandHandler) using a generic protocol.

```python
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

T = TypeVar("T")

@dataclass(frozen=True)
class Command:
    """Abstract marker for all commands."""

@dataclass(frozen=True)
class CreateUserCommand(Command):
    user_id: str
    email: str
    name: str

class CommandHandler(Protocol[T]):
    def handle(self, command: T) -> None: ...

class CreateUserCommandHandler:
    def __init__(self, user_repo, event_bus) -> None:
        self._repo = user_repo
        self._bus = event_bus

    def handle(self, command: CreateUserCommand) -> None:
        user_id = UserId(command.user_id)
        email = Email(command.email)
        user = User.create(user_id, email, command.name)
        self._repo.save(user)
        self._bus.publish(user.pull_events())
```

**Key point:** Commands are immutable value objects; handlers own all orchestration so the domain stays free of infrastructure concerns.

### Object Mother

**Intent:** Centralise valid test-fixture construction in one place so tests stay readable and resilient to domain changes.

```python
import uuid
from dataclasses import dataclass

@dataclass(frozen=True)
class UserId:
    value: str

@dataclass
class User:
    id: UserId
    email: str
    name: str

class UserIdMother:
    @staticmethod
    def random() -> UserId:
        return UserId(value=str(uuid.uuid4()))

class UserMother:
    @staticmethod
    def random() -> User:
        return User(
            id=UserIdMother.random(),
            email=f"user_{uuid.uuid4().hex[:6]}@example.com",
            name="Test User",
        )

    @staticmethod
    def create(**overrides) -> User:
        base = UserMother.random()
        return User(**{**base.__dict__, **overrides})
```

**Key point:** `random()` produces a complete valid aggregate; `create(**overrides)` lets tests pin only the fields that matter.

### DomainError hierarchy

**Intent:** Give every domain error a stable string type that survives minification, serialisation, and class renaming.

```python
from abc import ABC, abstractmethod

class DomainError(ABC, Exception):
    @property
    @abstractmethod
    def type(self) -> str:
        """Stable error type identifier — never use __class__.__name__ in production."""

    def __str__(self) -> str:
        return f"[{self.type}] {self.args[0] if self.args else ''}"

class UserNotFoundError(DomainError):
    def __init__(self, user_id: str) -> None:
        super().__init__(f"User '{user_id}' not found")
        self.user_id = user_id

    @property
    def type(self) -> str:
        return "USER_NOT_FOUND"

# Error handling
try:
    raise UserNotFoundError("abc-123")
except DomainError as err:
    if err.type == "USER_NOT_FOUND":
        print("handle missing user")
```

**Key point:** The `type` property is a hand-written constant so error identity is stable across refactors and deployments.

### Either / Result type

**Intent:** Make failure an explicit part of the return type so callers are forced to handle both branches without exceptions.

```python
from dataclasses import dataclass
from typing import Generic, TypeVar, Union

TValue = TypeVar("TValue")
TError = TypeVar("TError")

@dataclass(frozen=True)
class Result(Generic[TValue, TError]):
    _value: Union[TValue, None]
    _error: Union[TError, None]

    @staticmethod
    def ok(value: TValue) -> "Result[TValue, TError]":
        return Result(_value=value, _error=None)

    @staticmethod
    def fail(error: TError) -> "Result[TValue, TError]":
        return Result(_value=None, _error=error)

    def is_ok(self) -> bool:
        return self._error is None

    @property
    def value(self) -> TValue:
        assert self._value is not None
        return self._value

    @property
    def error(self) -> TError:
        assert self._error is not None
        return self._error

def find_user(user_id: str) -> "Result[User, UserNotFoundError]":
    user = db.get(user_id)
    if user is None:
        return Result.fail(UserNotFoundError(user_id))
    return Result.ok(user)

result = find_user("abc-123")
if result.is_ok():
    print(result.value)
else:
    print(result.error.type)
```

**Key point:** `Result` forces the caller to branch on `is_ok()` before accessing `value` or `error`, eliminating silent exception swallowing.

**Key point:** `copy.deepcopy` inside `clone()` ensures nested structures (dicts, lists) are fully independent copies, so mutating a clone never corrupts the template or another clone.
