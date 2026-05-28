# Structural Patterns

Structural patterns define how classes and objects are composed to form larger structures. Choose them when the coupling between subsystems, external APIs, or object creation is the source of the problem — not when the logic itself is the problem.

## Proxy

**Intent:** Provide a surrogate object that controls access to another object without changing the interface the client already uses.

**Variants:**

- **Virtual Proxy (lazy loading):** The real object is expensive to create or initialize. The proxy creates it only on first use and caches it. Example: loading a high-resolution image only when it is actually displayed, or caching a slow external API response (as in the `ProxyWeatherService` example that wraps `RealWeatherServiceSDK` and stores the forecast for 24 hours).
- **Protection Proxy (access control):** The proxy checks permissions before forwarding each call. It sits between the caller and the real subject and can refuse or alter the request. Example: a `checkAccess()` guard that returns false blocks the real method from ever running.
- **Remote Proxy (local interface to remote resource):** The real object lives in a different process or machine. The proxy presents a local interface and handles all serialization and network transport transparently. The client calls a method locally; the proxy ships the call over the wire and returns the result. Head First Design Patterns calls this a "local representative to a remote object" — the client thinks it is talking to the real machine, but it is talking to a stub.

All three variants share the same structural shape: a proxy class implements the same interface as the real subject and holds a reference to it. What differs is the reason the intercepting layer exists.

**Pressure that calls for it:**

You need to intercept calls to an object without the caller noticing — to defer initialization, enforce authorization, add caching, or hide network transport behind a local call.

**Warning signs you need it:**

- Every caller instantiates an expensive object up front even when it might never use it.
- Access rules are duplicated across multiple call sites instead of being enforced in one place.
- Client code has network or I/O details mixed into business logic because the remote service has no local interface.

**Warning signs you are overusing it:**

- The proxy adds no behavior — it just forwards calls. Use direct composition or delegation instead.
- You are proxying a proxy because the first one had too much responsibility. Flatten the chain and split concerns differently.
- The indirection makes stack traces and debugging harder without any tangible benefit in the current codebase.

**Practical heuristic:** Name the proxy after what it *does*, not what it wraps — `CachingWeatherService`, `AuthorizingRepository`, `RemoteGumballMachine`. If you cannot name the added responsibility, the proxy is probably unnecessary.

---

## Facade

**Intent:** Provide a single simplified interface to a complex subsystem so callers do not need to know its internal parts.

**Facade vs Adapter — the direction test:**

These two patterns look identical in code (a class that wraps other classes and exposes a different interface) but serve opposite directions:

- **Facade** works *inward*: you own the subsystem and you simplify it for your own callers. The subsystem stays untouched; the facade is a convenience layer on top of it. Example: an `ETLProcessor` that composes `FileExtractor`, `FileTransformer`, and `FileLoader` behind a single `process()` call. Callers do not need to know the pipeline exists.
- **Adapter** works *outward*: you do not own the external interface and you convert it to match your internal model. You adapt *their* interface so your code can consume it without changing either side.

If the complexity lives inside your own codebase, use Facade. If the mismatch comes from an external dependency or legacy API, use Adapter.

**Pressure that calls for it:**

Multiple classes must be orchestrated in a specific sequence and callers keep repeating the same multi-step setup. The subsystem is correct; the friction is in using it.

**Warning signs you need it:**

- Callers must instantiate three or more subsystem objects and call them in the right order to accomplish one logical task.
- A change to the internal subsystem breaks many call sites that had no business knowing about that detail.
- Onboarding friction is high because the subsystem exposes too many knobs for common cases.

**Warning signs you are overusing it:**

- The facade grows into a "god object" that owns all behavior and the subsystem classes become anemic. Keep the real logic in the subsystem; the facade only routes.
- You are adding a facade on top of a subsystem that has only one class. The simplification is not worth the extra layer.
- Callers bypass the facade and call subsystem classes directly anyway, meaning the boundary is not respected and the facade adds no real encapsulation.

**Practical heuristic:** A facade should be deletable — if you removed it, callers could still do the same work by calling subsystem classes directly. If removing it would break logic, the logic does not belong in the facade.

---

## Bridge

**Intent:** Decouple an abstraction from its implementation so that the two can vary independently.

**Bridge vs inheritance for two dimensions of variation:**

Use Bridge when a class has two independent axes of variation and inheritance would produce a combinatorial explosion of subclasses. The classic diagram in the TypeScript examples shows this:

```
Without Bridge:           With Bridge:
       A                    A (abstraction)      N (implementation)
     /   \                /   \                 / \
   Aa    Ab             Aa(N) Ab(N)            1   2
  / \   /  \
Aa1 Aa2 Ab1 Ab2
```

If you have *m* abstraction variants and *n* implementation variants, inheritance requires *m × n* classes. Bridge requires *m + n* classes.

The real-world Bridge example makes this concrete: a list can be rendered in different **views** (Visual, Descriptive) and can show different **content types** (Post, Video, Tweet). Combining these with inheritance would mean `VisualPost`, `VisualVideo`, `VisualTweet`, `DescriptivePost`, etc. With Bridge, adding a new view or a new content type requires one new class, not a row of combinations.

The abstraction (`ListItemViewAbstraction`) holds a reference to the implementation (`ContentTypeImplementation`) and delegates the content-specific rendering to it. The abstraction defines the *how to display*; the implementation defines the *what to display*.

**Pressure that calls for it:**

You need to vary two things — what an object is and how it behaves — and those two dimensions change for different reasons or at different rates.

**Warning signs you need it:**

- You find yourself writing class names like `RedCircle`, `BlueCircle`, `RedSquare`, `BlueSquare` — shape and color are two independent dimensions combined by inheritance.
- A change in one dimension (e.g., adding a rendering target) forces you to modify or duplicate classes in another dimension (e.g., all content types).
- You want to switch implementations at runtime but inheritance locks the behavior in at compile time.

**Warning signs you are overusing it:**

- There is only one implementation now and no credible second one in sight. Introduce Bridge when the second dimension actually appears.
- The abstraction and implementation never vary independently in practice; you are always deploying the same combination. Plain composition is simpler.
- The indirection adds complexity without enabling any real substitution.

**Practical heuristic:** If you can draw the two dimensions as separate rows in a table where any row value can combine with any column value, Bridge is the right shape. If one dimension fully determines the other, use strategy or plain subclassing.

---

## Flyweight

**Intent:** Reduce memory consumption by sharing the common, immutable portions of state across many fine-grained objects.

**Intrinsic vs extrinsic state:**

The key split is:

- **Intrinsic state** — data that is the same for many objects and never changes per-instance. This goes into the flyweight and is shared. Example: the 3D model data for a car type (`shared3DModel` in `VehicleFlyweight`), or the brand/model/color of a vehicle class in a police database.
- **Extrinsic state** — data that is unique per instance and changes with context. This is passed in at call time, never stored in the flyweight. Example: the position (`x`, `y`) and `direction` of each specific car on the map, or the license plate and owner name of a specific vehicle.

The `VehicleFactory` in the real-world example maintains a pool of exactly three flyweights (one per `VehicleType`). Creating 6,500 vehicles only creates three large 3D model arrays instead of 6,500. The position and direction of each vehicle are extrinsic and passed to `render()` at draw time.

A `FlyweightFactory` (or pool/registry) is almost always needed alongside the flyweight itself. Clients should not create flyweights directly; they request them from the factory, which returns an existing instance when the intrinsic state matches.

**Pressure that calls for it:**

You are creating a very large number of objects that share significant chunks of data, and memory usage is a measured problem — not a speculative one.

**Warning signs you need it:**

- Profiling shows that most of the heap is consumed by duplicate data stored redundantly in thousands of objects.
- The objects are numerous (tens of thousands or more) and most of their fields have the same value across many instances.
- You are hitting memory limits or GC pressure caused by object count, not object size of unique data.

**Warning signs you are overusing it:**

- The object count is low (hundreds, not thousands). The added complexity of separating state is not justified.
- The "shared" state is not truly immutable — if the flyweight changes, all objects sharing it change unexpectedly, introducing bugs that are hard to trace.
- The extrinsic state is so large or complex that passing it on every method call is more expensive than just storing it per-object.

**Practical heuristic:** Split state on paper first. List every field and classify it as intrinsic (same for a category of objects, never mutated) or extrinsic (varies per instance, passed at runtime). If the intrinsic fields are small or there are few unique combinations, Flyweight will not help. Only proceed if the intrinsic portion is large and the number of unique combinations is much smaller than the total object count.

---

## Adapter

**Intent:** Convert the interface of a class into the interface the client expects — let classes work together that otherwise couldn't due to incompatible interfaces.

**How it works:** The Adapter wraps an existing object (the Adaptee) and exposes a target interface. The client calls the target interface; the Adapter translates each call to the Adaptee's corresponding method. Can be implemented as an object adapter (composition) or class adapter (inheritance).

**When to use:**
- You want to use an existing class but its interface doesn't match what the code expects.
- You need to integrate a third-party library without spreading knowledge of its interface throughout your codebase.
- You're building a layer between your domain and an external system (file system, HTTP client, payment gateway).

**When NOT to use:**
- The interfaces are only slightly different — a thin wrapper or method rename is enough.
- You control both sides; change the source interface directly instead.

**Key trade-off:** Adds a translation layer that can hide type mismatches and make debugging harder when the Adaptee changes.

**Related patterns:** Facade (simplifies, doesn't translate), Proxy (same interface, different behavior), Decorator (same interface, adds behavior).

**Practical heuristic:** If you find yourself writing `thirdPartyClient.doSomething(mapper.from(ourThing))` in multiple places, extract an Adapter that hides both the third-party interface and the mapping.
