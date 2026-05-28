# SOLID Principles

Use this reference when reviewing class design, evaluating dependencies, or deciding how to extend behavior without breaking existing code.

## Single Responsibility Principle (SRP)

**Pressure it addresses:** Classes with multiple responsibilities become hard to reuse, because their responsibilities are entangled. A change needed for one reason can break code that depends on a different reason.

**The rule:** Every class, method, and module should have exactly one reason to change. That reason comes from the domain, not from technical convenience.

**How to identify the responsibility:** Try to describe the class in one sentence. If the description requires the word "and," the class likely has more than one responsibility. If it requires "or," the responsibilities are not even closely related. Ask each method as a question directed at the class — if a question sounds ridiculous, that behavior belongs elsewhere.

**Warning signs:**
- A class handles both formatting and calculation (for example, invoice formatting mixed with invoice totals).
- Methods in the same class change for different business reasons — layout decisions versus pricing rules.
- A blank line or comment separates logically distinct phases inside a single method; those phases are candidates for extraction.
- The class is hard to reuse in isolation because pulling in one behavior forces you to accept all the others.
- Changing one feature consistently breaks tests for an unrelated feature.

**Practical heuristics:**
- If you need only part of a class's behavior but cannot get at it without the rest, then the class has too many responsibilities.
- If a class is difficult to test in isolation, it is probably doing too much or depending on too many things.
- If multiple teams or stories touch the same class regularly for different reasons, split it.
- Delay the split until a second responsibility actually appears; premature separation creates complexity without benefit.

---

## Open-Closed Principle (OCP)

**Pressure it addresses:** Every modification to existing, working code is a risk. The goal is to add behavior by adding new code, not by editing code that already works and is already tested.

**The rule:** A class or module should be open to extension and closed to modification. New behavior should be introducible by supplying new collaborators, not by editing the original source.

**How it works in practice:** Composition and role-based injection are the primary tools. When a class depends on an abstraction (an interface or duck-typed role) rather than a concrete type, a new variant of behavior can be introduced by implementing that abstraction without touching the consuming class. The Strategy pattern is a direct application: swap the algorithm object, not the algorithm's host.

**Warning signs:**
- Adding a new case requires editing a switch statement or an if/else chain in an existing class.
- Every new business variant forces a change to the same central class.
- A class constructor hard-codes the name of a collaborator it creates internally.
- The class cannot be tested with a substitute collaborator because creation is embedded.

**Practical heuristics:**
- If you find yourself editing the same class every time a new variant of behavior arrives, that class is not closed.
- If a class instantiates its own collaborators directly, inject them instead; this opens the class to extension without touching it.
- Apply OCP selectively: over-engineering every class with extension hooks before any variant exists adds unnecessary complexity. Introduce the hook when a second variant actually appears, or when a plausible future variant is visible from domain knowledge.
- Frameworks and libraries are the strongest case for OCP — their users must be able to extend behavior without modifying the library source.

---

## Liskov Substitution Principle (LSP)

**Pressure it addresses:** Inheritance hierarchies break when a subclass cannot be used wherever the parent type is expected. Code that type-checks subtypes at runtime is a signal that the hierarchy is incoherent.

**The rule:** Any subtype must be substitutable for its supertype. Code that operates on a reference of the parent type must work correctly when handed any subtype — without knowing which subtype it received.

**Three rules that define substitutability:**
- **Signature rule:** Methods in the subtype must have the same signatures as the methods they override. A compiler enforces this in statically typed languages; in dynamic languages it must be maintained by discipline.
- **Method rule (behavioral):** A subtype must preserve the behavioral contract of the supertype. If a supertype's method increments a count every time it is called, the subtype's override must also increment the count. Postconditions cannot be weakened. This rule is semantic and cannot be enforced by a compiler.
- **Property rule:** Invariants of the supertype must remain invariants in the subtype. A set is not a valid subtype of a list if adding a duplicate element leaves the size unchanged, because the list invariant is that size always increases on addition.

**Warning signs:**
- A method checks the runtime type of an argument and branches on it to call type-specific methods. This is a substitution violation in disguise.
- A subclass overrides a method and does less than the superclass promised, or raises an error that the superclass never raised.
- A subclass must call `super` in very precise places, and forgetting it silently produces wrong results. This indicates the hierarchy forces subclasses to know the superclass algorithm, a form of coupling that leads to violations.
- A test written against the parent type fails when handed a subtype instance.

**Practical heuristics:**
- If substituting a subtype for the supertype requires callers to add special cases, the hierarchy is broken.
- If a subclass needs to override a method to make it a no-op or throw "not supported," then it is not a true subtype — use composition instead of inheritance.
- Prefer hook methods over requiring subclasses to call `super`. Hook methods let the superclass control the algorithm while the subclass contributes only its specialization.
- When designing types, find the hierarchy by refactoring: if two or three concrete types share behavior, explore whether a common supertype makes sense under LSP, not just whether it is convenient.

---

## Interface Segregation Principle (ISP)

**Pressure it addresses:** When a single interface groups methods needed by different clients, each client is forced to depend on methods it never calls. Changes driven by one client's needs ripple across all clients even when those changes are irrelevant to them.

**The rule:** Interfaces should be minimal — small enough that every method in the interface is used by every consumer. If different clients use different subsets of an interface, split the interface into those subsets.

**Warning signs:**
- A class implements an interface but leaves several methods as no-ops or stubs because it does not need them.
- A consumer imports or depends on an interface but only ever calls one or two of its methods.
- Updating an interface to satisfy one client forces recompilation or redeployment of modules that do not use the changed method.
- The same fat interface is shared across microservices or independently deployed units — a single change forces a cascade of unrelated redeployments.

**Practical heuristics:**
- If you can describe a client's use of an interface with a narrow role name (a "Printable," a "Persistable," a "Notifiable"), that role should likely be its own interface.
- If adding a method to an interface requires touching every implementor, ask whether the method truly belongs with the existing contract or if it represents a separate concern.
- ISP is a specific application of SRP applied to the interface boundary rather than the class body.
- In languages with duck typing or structural typing, ISP is enforced naturally: depend only on the messages you actually send, not on the full class.

---

## Dependency Inversion Principle (DIP)

**Pressure it addresses:** High-level business logic should not be hostage to low-level infrastructure details. If a service class hard-codes a database driver, the business rules cannot be tested, reused, or replaced without dragging in the infrastructure.

**The rule:** High-level modules should not depend on low-level modules. Both should depend on abstractions. Abstractions should not depend on details; details should depend on abstractions. "High level" means closer to the business domain; "low level" means closer to infrastructure, I/O, or hardware.

**How inversion works:** The consuming class declares what it needs (an abstraction — interface or duck-typed role). A third party — a factory, a container, or the composition root — decides which concrete implementation to supply. The direction of the dependency arrow reverses: the concrete implementation depends on the abstraction, not the other way around.

**Warning signs:**
- A business-layer class imports or instantiates a database class, a mailer class, or an HTTP client directly.
- Changing the database or messaging system requires editing classes that have nothing to do with infrastructure.
- A class cannot be unit-tested without spinning up a real database or network connection.
- The same class name appears in many places throughout the codebase as a direct reference rather than through a shared abstraction.

**Practical heuristics:**
- If a class calls `new` on a collaborator inside its own methods or constructor, inject the collaborator instead.
- Prefer depending on a narrow role (a "Repository," a "Notifier," a "Logger") over depending on a specific class.
- The fewer concrete class names a module knows, the more loosely coupled it is.
- Dependency injection is the mechanism; DIP is the design principle behind it. The injection point — constructor, method parameter, or setter — makes the abstraction explicit.
- Depend on things that change less often than you do. Abstractions defined in terms of your domain change less often than concrete infrastructure classes.

---

## Warning Signs Across All Five Principles

- A class cannot be described in one sentence without "and" or "or."
- Changing one thing breaks something unrelated.
- Adding a new variant requires editing code in multiple existing classes.
- instanceof / type checks appear in business logic.
- A class cannot be tested without setting up infrastructure.
- Interfaces with methods that some implementors leave unimplemented.
- Hard-coded class names in business logic that should be injection points.
- Subclass behavior surprises callers who thought they were talking to the parent type.

---

## How the Principles Work Together

SRP produces cohesive classes — each class handles one concern. This makes the boundary of each class clear, which makes it easier to define a stable interface around it (ISP). A stable, narrow interface is what OCP depends on: you can extend behavior by swapping implementations of that interface without touching the class that consumes it. LSP ensures that those swapped implementations are genuinely interchangeable — callers never need to know which concrete type they received. DIP ties the system together: high-level classes declare dependencies on the abstractions produced by ISP, and composition roots wire in the concrete implementations that satisfy LSP.

Violations compound each other. A class with multiple responsibilities (SRP violation) tends to accumulate a wide interface (ISP violation). That wide interface makes it hard to swap implementations (OCP limitation). When inheritance is used to share the bloated behavior, subtypes often cannot fully honor the contract (LSP violation). And because the class grew fat by pulling in concrete collaborators, it is now coupled to infrastructure (DIP violation).

Following any one principle consistently creates pressure to follow the others. The principles are heuristics for the same underlying goal: keep each piece of code responsible for one thing, depend on stable abstractions, and make new behavior additive rather than destructive.
