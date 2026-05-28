# Creational Patterns

Creational patterns manage object construction. Choose them when creation logic is complex, repeated, or reveals too much about concrete types to callers. The four patterns below address distinct pressures — pick the one whose problem statement matches your situation, not just the one whose name sounds familiar.

## Builder

**Intent:** Construct a complex object step by step, allowing the same construction process to produce different representations.

**Pressure that calls for it:**
A class has many optional fields, and callers are forced to pass `null`, `undefined`, or meaningless defaults for the ones they do not need. The real-world example from the TypeScript sources shows a `User` class with `name`, `surname`, `email`, `gender`, `phoneNumber`, `isAdmin`, and more — each combination valid for a different caller. Without Builder, every caller either receives a constructor with eight parameters (most of them ignored) or the code grows a separate subclass per combination.

**Warning signs you need it:**
- Constructors with four or more parameters, several of which are optional or share the same type (making argument order error-prone).
- Callers duplicate multi-step initialization sequences — `user.setName(...)`, `user.setEmail(...)`, `user.validate()` — scattered across the codebase instead of living in one place.
- You need to produce structurally similar objects that differ only in which parts are assembled (e.g., a minimal product vs. a full-featured product), as the Director/Builder pair demonstrates with `buildMinimalViableProduct()` and `buildFullFeaturedProduct()`.

**Warning signs you're overusing it:**
- The object has two or three fields and all are required — a plain constructor is clearer and less ceremony.
- You introduce a Builder only to chain setters for cosmetic reasons; if the object is simple and immutable, a factory function or named-parameter object literal (in TypeScript) is sufficient.
- The Director ends up with a single method that always calls every builder step — the pattern adds indirection with no configurability benefit.

**Practical heuristic:** Introduce Builder when the object's valid states form a large combinatorial space and callers should only see the states they explicitly opted into. Keep `reset()` inside `getProduct()` so the builder is reusable without manual cleanup.

---

## Abstract Factory

**Intent:** Produce families of related objects without specifying their concrete classes, guaranteeing that the objects within one family are compatible with each other.

**Pressure that calls for it:**
The system must switch between entire sets of collaborating objects — not just one type — depending on context (environment, platform, tenant, theme). The real-world TypeScript example captures this precisely: a `DevEnvironmentFactory` returns an `InMemoryMockDB`, `MockFS`, and `ConsoleLogProvider`; a `ProdEnvironmentFactory` returns `MySQLDB`, `S3FS`, and `SentryLogProvider`. The client function (`client(environmentFactory)`) never imports a concrete class — it receives a factory and calls `getDB()`, `getFS()`, `getLogProvider()` without knowing which environment it is in.

**Warning signs you need it:**
- You have two or more product types (e.g., DB, FS, Logger) that must always be used together from the same variant — mixing a production database with a mock logger would break correctness.
- New environments or platforms are added regularly, and each addition requires touching the same scattered `if/switch` blocks that decide which concrete classes to instantiate.
- Client code knows more about environment configuration than it should, because it must import and instantiate concrete classes directly.

**Warning signs you're overusing it:**
- There is only one product type to create — Factory Method is sufficient and far simpler.
- The "family" contains a single variant that never changes; the abstraction adds hierarchy with no substitutability payoff.
- You reach for Abstract Factory because you want to group factory methods, not because the products must be compatible across a variant boundary.

**Practical heuristic:** If you can answer "which products must always come from the same variant?" with a concrete list, Abstract Factory is correct. If you cannot, you likely only need Factory Method or a simple factory.

---

## Factory Method (and how it differs from Abstract Factory and simple Factory)

**Intent:** Define an interface for creating an object in a superclass, but let subclasses decide which concrete class to instantiate.

### The three-way distinction — a common confusion point

| | Who decides the concrete type | Structure | When to use |
|---|---|---|---|
| **Simple Factory** | A static or standalone helper method with a switch/if | One class, one method | Centralizing `new` calls when there is no need for subclass extensibility |
| **Factory Method** | A subclass, by overriding an abstract method in a Creator | Inheritance hierarchy | When the Creator class must defer instantiation to subclasses, each of which produces one product type |
| **Abstract Factory** | A family-level factory object, with one method per product type | Composition — client receives a factory | When multiple related products must be created together from the same variant |

A simple factory is not a GoF pattern — it is a useful helper that eliminates scattered `new ConcreteClass()` calls, but it does not enable extension without modification. Factory Method is the actual pattern: `Creator` declares `abstract factoryMethod(): Product`, and `ConcreteCreator1` / `ConcreteCreator2` each return a different concrete product. The client works only with the abstract `Creator` interface. The real-world TypeScript example extends this cleanly: `DBConnectionFactory` is the abstract creator; `MongoConnectionFactory` and `RedisConnectionFactory` are concrete creators; the choice is made at startup from an environment variable, and the `main()` function never names a concrete connection class.

**Pressure that calls for it:**
A class contains core business logic that depends on an object whose concrete type should vary by deployment, configuration, or subclass. The Creator's `someOperation()` method calls `this.factoryMethod()` and uses the returned product without knowing its concrete type — that is the structural tell.

**Warning signs you need it:**
- You have a `switch` or `if-else` inside a method that instantiates different classes based on a type parameter, and that switch is duplicated across callers.
- A base class must be reused across contexts, but the exact objects it works with differ per context — subclasses should supply those objects without the base class importing them.
- Adding a new product type today requires modifying an existing class rather than adding a new subclass.

**Warning signs you're overusing it:**
- There is only one concrete creator and it will never be extended — a constructor or simple factory is enough.
- You use Factory Method to avoid writing `new` in one place, with no polymorphic dispatch involved; that is a simple factory, not Factory Method.
- The inheritance hierarchy grows one subclass per tiny variant; if the variation is data-driven, a configuration object or strategy passed at construction is simpler.

**Practical heuristic:** Use Factory Method when you need to open a class for extension (new product types) without modification (changing the creator). If you also need multiple products per variant, graduate to Abstract Factory.

---

## Singleton

**Intent:** Ensure a class has only one instance and provide a global access point to it.

**Pressure that calls for it:**
A resource that is inherently singular — a logger, a connection pool, a hardware interface, an in-process event bus — must be shared across the application without passing it through every call site. The TypeScript examples show this as a `Logger` with a private constructor and a static `getInstance()` method (or a static getter `instance`): two callers that both call `Singleton.instance` receive the same object reference.

**Warning signs you need it (legitimate cases):**
- The resource is stateful and shared mutation must be serialized through a single object (e.g., a write-ahead log).
- Construction is expensive and must happen exactly once (e.g., loading a large configuration file at startup).
- The runtime environment physically enforces a single instance (e.g., a hardware device handle).

**Why Singleton is often an anti-pattern — be direct about the trade-offs:**

1. **Global mutable state.** A Singleton is globally accessible state. Any part of the codebase can read or write it without that dependency appearing in function signatures or constructor parameters. This is the same problem as global variables, wrapped in a class.

2. **Hidden coupling.** Callers import the Singleton directly (`Logger.getInstance()`) rather than receiving a `Logger` interface through dependency injection. The coupling is invisible until you try to change implementations or run multiple instances in the same process.

3. **Testing difficulty.** Unit tests cannot substitute a test double for a Singleton without monkey-patching the class or resetting static state between tests. Shared static state leaks between test cases, causing order-dependent failures that are hard to diagnose.

4. **Concurrency hazards.** In multi-threaded environments, the lazy initialization check (`if (!instance) { instance = new ... }`) is a race condition unless explicitly synchronized — an easy detail to miss.

**Warning signs you're overusing it:**
- You reach for Singleton because "there should only be one of these" by convention, not by physical necessity — use dependency injection and instantiate once at the composition root instead.
- Tests require resetting or replacing the Singleton between runs — this is a clear signal that the pattern is the wrong tool.
- The class holds no state and is used only for its methods — a module-level function or a stateless service passed by injection is simpler.

**Practical heuristic:** Prefer instantiating once at the application's composition root and injecting the single instance wherever it is needed. Reserve the Singleton pattern for cases where the runtime environment itself enforces uniqueness, or where there is no dependency-injection infrastructure at all.
