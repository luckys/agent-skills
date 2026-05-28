# Implementation Patterns

Patterns from Kent Beck's *Implementation Patterns* — micro-level decisions about how to express code clearly. These complement the GoF and PoEAA patterns, which operate at design level. Beck's patterns answer: given that I need to write a class/method/variable, how should I structure it?

## Philosophy

Three values drive these patterns:
- **Communication** — code is read more than written; optimize for the reader
- **Simplicity** — only express what the system needs today
- **Flexibility** — keep options open where cost is low

---

## Simple Superclass Name

**Category:** Class

**Intent:** Name the roots of class hierarchies with short, evocative words drawn from a single metaphor.

**How it works:** A strong metaphor gives every single-word class name a rich web of associations. When Ward Cunningham replaced `DrawingObject` with `Figure` (from a typography metaphor), the name became simultaneously shorter, richer, and more precise. Good names are found through conversation, thesaurus searches, and time.

**When to use:**
- When naming the root of a new class hierarchy
- When an existing name requires multiple words or feels unclear in conversation
- When the current name encodes implementation rather than concept

**Practical heuristic:** If you cannot say the class name naturally in a sentence describing the problem, keep searching. One strong word beats three descriptive ones.

---

## Qualified Subclass Name

**Category:** Class

**Intent:** Name subclasses by prepending one or more modifiers to the superclass name to communicate both similarity and difference.

**How it works:** Subclass names have two jobs: show what the class *is like* and how it is *different*. Prepend modifiers to the superclass name — `StretchyHandle`, `TransparencyHandle`. An exception: if the subclass is the root of its own significant hierarchy, give it a simple superclass name instead.

**When to use:**
- When creating a subclass that is a true specialization of the superclass
- When the reader needs to know both what the class shares with its parent and how it differs

**Practical heuristic:** Read the name from the reader's perspective — what class does the reader need to know *this* class is like? Use that as the base name, not necessarily the direct superclass.

---

## Abstract Interface

**Category:** Class

**Intent:** Separate the interface from the implementation to hide decisions that should not propagate to callers.

**How it works:** Introduce an abstract interface (Java interface or abstract class) only when flexibility is definitely needed. Every layer of interface has costs: something more to learn, debug, and maintain. Pay for interfaces only where you will actually need the flexibility they create. Introduce them speculatively only where the cost of adding them later is high.

**When to use:**
- When multiple implementations of the same concept are needed or likely
- When hiding the concrete type from callers reduces coupling in a meaningful way
- When changing the implementation without affecting callers is a real requirement

**Practical heuristic:** Ask: will I actually need to substitute implementations here? If the answer is "maybe someday," defer. Add the interface when you have a second concrete implementation in hand.

---

## Versioned Interface

**Category:** Class

**Intent:** Extend an existing published interface safely by introducing a new sub-interface that adds the required operations.

**How it works:** When you cannot change an interface (because all implementors would break), declare a new interface that extends the original and adds the new operation. Callers who need the new operation check with `instanceof` and downcast. Existing implementations continue working untouched.

**When to use:**
- When an interface has been widely published and cannot be changed without breaking all implementors
- When only a subset of clients needs the new functionality

**Practical heuristic:** Versioned interfaces are an ugly answer to an ugly problem. Multiple alternative interfaces are a sign it is time to rethink the design. Prefer abstract classes when you anticipate interface evolution, since you can add default implementations without breaking existing subclasses.

---

## Value Object

**Category:** Class

**Intent:** Write an object that acts like a mathematical value — immutable, equality by content, no identity.

**How it works:** Set all state in the constructor. Provide no setters. Operations that would change state return new objects instead. Two value objects with the same data are equal and interchangeable. Value objects eliminate a class of concurrency problems and make reasoning about code easier, since you never have to wonder whether the object was modified elsewhere.

**When to use:**
- When modeling concepts that are defined by their attributes rather than their identity (money, coordinates, dates, measurements)
- When the computation is essentially mathematical: you want to make absolute, timeless statements
- At the edges of a system of stateful objects — use values to represent the immutable leaves

**Practical heuristic:** If two instances with identical data should be treated identically in all circumstances, make it a value object. The performance cost of creating intermediate objects is rarely a bottleneck in practice.

---

## Inner Class

**Category:** Class

**Intent:** Bundle locally useful code in a private class without incurring the cost of a separate top-level class.

**How it works:** Inner classes give you many of the benefits of a class (encapsulation, a type, a name) without the cost of a separate file. Non-static inner classes receive a hidden reference to the enclosing instance, useful for accessing enclosing data without explicit parameters. Declare inner classes static to detach them from the enclosing instance.

**When to use:**
- When a class is only meaningful within the context of one other class
- When you want to express a refinement or variant that is too minor to promote to a top-level class

**Practical heuristic:** Anonymous inner classes should stay short (one or two methods) and contain no complicated logic. If you cannot name the anonymous class, you cannot communicate your intention — consider promoting it to a named inner class.

---

## Common State

**Category:** State

**Intent:** Store the state shared by all instances of a class as fields declared directly on the class.

**How it works:** When all calculations with a class require the same data elements, declare them as fields. The reader of the code — or the complete constructor — can immediately see what data is necessary to have a well-formed object. Common state communicates data requirements precisely and clearly.

**When to use:**
- When all instances of a class need the same set of data elements
- When you want readers to be able to determine the object's data requirements at a glance

**Practical heuristic:** If you are tempted to introduce a field that is only used by a subset of methods, or that is only valid during one method's execution, find a better home: a parameter, a local variable, or a helper object.

---

## Variable State

**Category:** State

**Intent:** Store state whose presence differs from instance to instance in a map, not as direct fields.

**How it works:** When different instances of the same class need different data elements, store those elements in a `Map<String, Object>` keyed by element name. This gives maximum flexibility at the cost of communicability — a reader cannot tell from the class definition what keys will be present at runtime.

**When to use:**
- When the presence of one field logically implies other fields (e.g., a `bordered` flag implies `borderWidth` and `borderColor`)
- When objects of the same class may legitimately have completely different data elements depending on usage

**Practical heuristic:** Prefer common state wherever possible. Use variable state only for fields that may or may not be present depending on usage. A shared common prefix on several variable names is a signal that a helper object would express the relationship more clearly.

---

## Extrinsic State

**Category:** State

**Intent:** Store special-purpose state associated with an object in a map held by the subsystem that needs it, not in the object itself.

**How it works:** When only one subsystem (e.g., a persistence layer) needs to associate extra data with an object, putting that data in a field on the object pollutes the object's API and breaks symmetry with other fields. Instead, that subsystem maintains an `IdentityMap` keyed by the object, storing the extrinsic data as values.

**When to use:**
- When only one narrow part of the system needs extra data about an object
- When adding a field to the object would violate the principle that all fields are useful to the system as a whole

**Practical heuristic:** Extrinsic state is rare but useful when necessary. It complicates copying (extrinsic state must be copied separately) and debugging (a standard inspector will not show it). Reserve it for cross-cutting subsystem concerns.

---

## Eager Initialization

**Category:** State

**Intent:** Initialize fields at declaration time or in the constructor so the object is ready to compute as soon as it is created.

**How it works:** Initialize a field either at its declaration (`List<Person> members = new ArrayList<>()`) or in the constructor. This makes a clear, single place for initialization logic. Readers can be certain that variables are initialized before use. There is symmetry: all fields come into existence together.

**When to use:**
- When the cost of initialization is low and the field is always needed
- As the default strategy; switch to lazy initialization only when profiling reveals a bottleneck

**Practical heuristic:** Initialize fields at declaration when possible. Use the constructor when initialization requires parameters. Mixing both is fine as long as the class stays small and readable.

---

## Lazy Initialization

**Category:** State

**Intent:** Initialize a field the first time it is accessed rather than at construction time, deferring cost until the value is definitely needed.

**How it works:** Leave the field null. In the getter, check for null and initialize before returning. This defers potentially expensive initialization until the value is actually needed, and avoids the cost entirely if the value is never used.

**When to use:**
- When computation is expensive and the field may never be accessed at all
- When startup time is critical (e.g., plugin loading in Eclipse)

**Practical heuristic:** A lazily initialized field is harder to read — the reader must look in two places. Use lazy initialization sparingly and only when the performance benefit is real. It says, "Performance is important here."

---

## Composed Method

**Category:** Methods

**Intent:** Compose methods out of calls to other methods, each at roughly the same level of abstraction.

**How it works:** A well-composed method reads like a summary. All the lines in the method body are at a similar conceptual altitude — high-level calls to named helpers, not a mix of high-level intent and low-level bit manipulation. When a method mixes abstraction levels (three method calls and then a raw flag assignment), extract the low-level detail into a named helper.

**When to use:**
- When a method is mixing high-level steps with implementation details
- When a method is hard to summarize in a single sentence

**Practical heuristic:** Get the code working first, then decompose it based on what you learned. If you cannot name a helper method clearly, that is a sign the decomposition is wrong — consider inlining everything and repartitioning.

---

## Intention-Revealing Name

**Category:** Methods

**Intent:** Name methods after what they are intended to accomplish for the caller, not how they accomplish it.

**How it works:** `Customer.find(id)` communicates intent; `Customer.linearCustomerSearch(id)` communicates implementation strategy. The implementation strategy is an irrelevant detail to callers — they can read the body if curious. Think about how the method name reads in *calling code*, not in its own definition. The calling method should tell a story; method names help tell it.

**When to use:**
- Always, when naming any method
- Especially when tempted to include words like "linear", "hash", "cached", or other implementation details in the name

**Practical heuristic:** Read the method call in context. Does it read naturally in the sentence formed by the calling method? If the name describes the implementation rather than the purpose, rename it.

---

## Method Object

**Category:** Methods

**Intent:** Turn a complex method that cannot be cleanly decomposed into a dedicated class whose fields are the method's local variables and parameters.

**How it works:** When a long method has many parameters and local variables that make extraction difficult (every sub-method would need a long parameter list), create a class named after the method. Each parameter and local variable becomes a field. Copy the method body into a `compute()` or `calculate()` method on the new class. The original method now delegates to `new MethodObject(args).compute()`. From there, extract helper methods freely — no parameters needed since all state is in fields.

**When to use:**
- When a long method cannot be cleanly split because variables are used across multiple sub-sections
- When trying to extract methods results in helper methods with five or more parameters

**Practical heuristic:** If you suspect a method object is needed but the method has already been split into many helpers, inline all helpers first, giving yourself one big method again, then apply the method object transformation.

---

## Guard Clause

**Category:** Behavior

**Intent:** Express local exceptional flows with an early return rather than nesting the main logic inside a conditional.

**How it works:** Instead of wrapping the main computation in an `if (condition)` block, check for the exceptional case first and return immediately. This flattens the nesting and lets the reader focus on the main flow. Guard clauses are appropriate when one path is clearly the normal case and another is a deviation.

**When to use:**
- When multiple preconditions must be checked before the main logic can run
- When an if-then-else would make both branches look equally important, obscuring which is the main flow

**Practical heuristic:** If reading the method requires keeping more than one condition in mental working memory simultaneously, replace nested conditionals with sequential guard clauses.

---

## Explaining Message

**Category:** Behavior

**Intent:** Send a method named after the problem being solved that in turn sends a method named after how it is solved, to separate intention from implementation.

**How it works:** `highlight(area)` calls `reverse(area)`. The `highlight` method communicates intent; `reverse` communicates mechanism. Even though `highlight` does nothing but delegate, it earns its existence by communicating. When you are tempted to write a one-line comment on a statement, extract that statement into a method named after the comment.

**When to use:**
- When a single line of code would otherwise need a comment to explain its purpose
- When an operation is logically named differently from its implementation

**Practical heuristic:** "When tempted to comment a single line of code, extract it into a method instead." — Beck

---

## Collecting Parameter

**Category:** Behavior / State

**Intent:** Pass a parameter to collect results across multiple method invocations when returning values from each call would be cumbersome.

**How it works:** When a computation distributes result-gathering across many calls (e.g., traversing a tree), pass a collector object to each call. Each invocation adds to the collector instead of returning an independent value. Examples: `GraphicsContext` passed around a widget tree; `TestResult` passed through a JUnit test suite.

**When to use:**
- When a tree traversal or recursive algorithm must gather results across many nodes
- When merging independently returned values is more complicated than simple addition

**Practical heuristic:** If all the methods in a class need the same parameter to collect results, consider making the collector a field instead.

---

## Complete Constructor

**Category:** Methods

**Intent:** Write constructors that return fully formed objects — objects that are ready to compute without additional setup calls.

**How it works:** A complete constructor communicates what data is required to create a valid object. If there are multiple valid initial states, provide multiple constructors. Avoid the pattern of a zero-argument constructor followed by a series of setter calls — that pattern hides the required data and leaves objects in an invalid intermediate state.

**When to use:**
- For any class whose instances have invariants that must hold before the object is useful
- When you want to communicate prerequisites to users of the class clearly

**Practical heuristic:** Funnel all constructors to a single master constructor that does all the initialization. This ensures every path creates an object that satisfies all invariants.

---

## Factory Method

**Category:** Methods

**Intent:** Express complex or abstract object creation as a static method on the class rather than through a constructor.

**How it works:** Factory methods differ from constructors in two important ways: they can return a more abstract type (an interface or a superclass), and they can be named after their intent. Use `Rectangle.create(0, 0, 50, 200)` when creation involves more than just allocating and initializing — caching, subclass selection, or returning an existing instance. If all that is happening is vanilla object creation, a constructor communicates better.

**When to use:**
- When creation may return a subclass decided at runtime
- When creation involves caching or other logic beyond simple allocation
- When the returned type should be abstract

**Practical heuristic:** If a reader sees a factory method and wonders "what else is going on beyond object creation?", the factory method is earning its existence. If nothing else is going on, use a constructor.

---

## Internal Factory

**Category:** Methods

**Intent:** Encapsulate the creation of a helper object in a dedicated method when that creation is complex or needs to be overridden by subclasses.

**How it works:** When a getter does lazy initialization, extract the initialization logic into a separate `computeX()` helper rather than embedding it inline. This keeps the getter focused on one thing (checking and returning) and makes the creation logic overridable by subclasses independently.

**When to use:**
- When lazy initialization logic is non-trivial
- When subclasses might need to provide different implementations of the helper object

**Practical heuristic:** If the null-check and initialization in a getter are longer than two lines, extract the initialization into an internal factory method named `computeX()` or `createX()`.

---

## Collection Accessor Method

**Category:** Methods

**Intent:** Provide limited, meaningful access to a collection field through purpose-specific methods rather than returning the raw collection.

**How it works:** Instead of `List<Book> getBooks()`, provide `void addBook(Book)`, `int bookCount()`, and `Iterator<Book> getBooks()`. Each method communicates a specific intention. Returning the raw collection allows callers to invalidate internal invariants behind your back and passes up the opportunity to build a rich, meaningful interface. If clients iterate, return an iterator (or an unmodifiable view) rather than the live collection.

**When to use:**
- Any time an object owns a collection that is accessed by clients
- When the collection is part of the object's internal state that must remain consistent

**Practical heuristic:** If you find yourself duplicating the full collection protocol across clients, it is a design smell — your object should be doing more work for its clients, not just exposing its innards.

---

## Declared Type

**Category:** State

**Intent:** Declare variables with the most general type that communicates how the variable will be used, not how it is implemented.

**How it works:** Declaring `List<Person> members = new ArrayList<>()` tells readers members will be used like a `List` (indexed access). Declaring it as `Collection<Person>` hides the implementation decision and maintains flexibility to swap in a `LinkedList` or `HashSet`. The further a decision propagates, the less flexibility you have for future change. Allow information to spread as narrowly as possible.

**When to use:**
- Always: prefer the most abstract declared type that accurately describes intended usage
- Especially on method return types and field declarations

**Practical heuristic:** Declare variables and methods with general types where possible. Losing a little precision to gain consistency is a reasonable trade-off. Communicating well provides the best flexibility.

---

## Role-Suggesting Name

**Category:** State

**Intent:** Name variables after the role they play in the computation, communicating the *why*, not the *what*.

**How it works:** Scope, lifetime, and type are communicated through context (declaration site, type annotation). The name's job is to communicate the role. Common roles: `result` (what will be returned), `each` or the singular form of the collection name (the element being iterated), `count` (a tally). If you need multiple variables with similar roles, qualify the name: `eachX`, `eachY`, `rowCount`, `columnCount`.

**When to use:**
- Always, when naming any variable
- Especially when tempted to encode type or scope into the name (Hungarian notation, `m_` prefixes)

**Practical heuristic:** If you need several words to distinguish a variable's role from other variables in scope, that is a signal to simplify the design, not lengthen the name.

---

## Parameter Object

**Category:** State

**Intent:** Consolidate a group of parameters that recur together across multiple method calls into a single object.

**How it works:** When `x, y, width, height` appear together in five method signatures, introduce a `Rectangle` object. The object shortens parameter lists, documents that the four values are strongly related, and provides a natural home for logic that used to be duplicated at every call site. Parameter objects often evolve into genuinely useful domain objects.

**When to use:**
- When the same set of parameters appears in three or more method signatures
- When a group of parameters is always passed together and the values have a common domain meaning

**Practical heuristic:** "Many powerful objects begin life as parameter objects." Once introduced, look for bits of code that use only fields of the parameter object — those bits probably belong as methods on the object itself.

---

## Constant

**Category:** State

**Intent:** Store values that are used in multiple places but never change as named constants rather than literals.

**How it works:** Declare values as `static final` with ALL_CAPS names. Constants serve three purposes: they eliminate repetition (change `5` to `6` in one place), they communicate meaning (`Color.WHITE` is more readable than `0xFFFFFF`), and they enable extension without modification when used as arguments to polymorphic methods. When every call to a method passes one of a fixed set of constants, consider replacing the constant with dedicated methods (`justifyCenter()` instead of `setJustification(Justification.CENTERED)`).

**When to use:**
- When a literal value appears in more than one place
- When a value has a domain meaning that is obscured by the raw literal

**Practical heuristic:** If an interface's variants are all expressed as constants passed to one method, prefer a separate named method for each constant value — it reads better and is more discoverable.
