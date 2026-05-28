# Object Calisthenics

Use this reference when reviewing or writing object-oriented code and you want to apply Jeff Bay's nine structural rules as a discipline for forcing better design habits.

## Rule 1: One Level of Indentation Per Method

- **Intent**: Deep nesting is a signal that a method is doing more than one thing. Each additional level forces the reader to hold more mental context simultaneously, increasing the chance of misreading the logic. Keeping one level per method forces each method to have a single, clear entry point and a single job.
- **Application**: When a method body requires a nested block — a loop inside a condition, a condition inside a loop — extract the inner block into a named private method. The name of the extracted method becomes documentation. Codigo Sostenible (Ble) frames this as maintaining a uniform level of abstraction within each block: all lines inside a method should live at the same conceptual altitude.
- **When to relax**: A single well-named guard clause that wraps the whole body is acceptable. Very short utility methods (two to three lines) with a trivially nested ternary do not need extraction if the nesting communicates the intent better than a helper name would.
- **Practical heuristic**: If you can see two levels of indentation inside a single method body, extract the inner block into a named method before doing anything else.

## Rule 2: Do Not Use the Else Keyword

- **Intent**: The `else` branch is often the sign that a method handles two distinct cases at the same conceptual level rather than resolving one and moving on. Removing `else` pushes you toward guard clauses for edge cases and polymorphism for true variation, both of which reduce coupling.
- **Application**: Replace early-exit conditions with guard clauses that return or throw immediately. Codigo Sostenible (Ble) distinguishes guard clauses — which handle terminal edge cases — from symmetric `if/else` branches that express mutually exclusive business paths. Not every `else` is wrong; when two paths are genuinely equal partners in the domain, a symmetric `if/else` or ternary is more honest than a forced early return. The goal is to eliminate `else` when it exists only to avoid returning early, not to remove it dogmatically when the symmetry of two branches is the actual intent.
- **When to relax**: When two branches represent co-equal alternatives that together define a concept, a symmetric structure with `else` can be clearer than sequential guards. Refactorcotidiano (Iglesias) shows that forcing a single return point in modern languages — the historical reason behind avoiding multiple exits — creates the very nesting that `else` elimination is supposed to prevent.
- **Practical heuristic**: If the first branch of an `if` ends in a return, throw, or continue, remove the `else` and let the remaining code fall through naturally.

## Rule 3: Wrap All Primitives and Strings

- **Intent**: Primitives carry no domain meaning on their own. A raw string can be a name, an email address, a postal code, or an error message — the type system cannot tell them apart. Wrapping a primitive in a domain type gives it meaning, allows it to enforce its own invariants, and keeps validation co-located with the concept. Refactorcotidiano (Iglesias) describes this as leaving primitives behind: built-in types are generic and sometimes you need something that adds meaning and constraints.
- **Application**: Introduce a value object for any primitive that has rules (a non-empty string, a positive number, a currency amount, an identifier). The value object validates in its constructor and exposes only behavior, not raw state. Codigo Sostenible (Ble) lists this as one of the four pillars of avoiding JaBOL-style programming: do not use built-in data types in the business layer — wrap them in your own types.
- **When to relax**: Primitives used purely as configuration values, array indices, or truly universal concepts (boolean flags for simple toggles) do not need wrapping unless they start accumulating validation logic or appear in multiple places with the same constraints.
- **Practical heuristic**: If the same primitive appears in two or more places with the same validation condition, it is a concept that deserves its own type.

## Rule 4: First-Class Collections

- **Intent**: A raw collection exposed to a caller forces that caller to know the collection's structure, its iteration logic, and its filtering rules. This spreads collection behavior across many classes — a form of shotgun coupling. A first-class collection is a class whose sole instance variable is the collection, and which owns all behavior over that collection. Refactorcotidiano (Iglesias) illustrates this with `TaskService`: when the service holds a raw array, it must know how to iterate it, filter it, and understand `Task` internals — three sources of coupling that a dedicated collection class would absorb.
- **Application**: When a collection has any rules — a minimum size, a filter predicate, a uniqueness constraint, a specific ordering — extract it into a named class. That class owns its add, remove, and query operations. Callers send messages to it; they do not reach inside.
- **When to relax**: Simple read-only lists passed through a method signature for the sole purpose of iteration need not become classes. Extract a collection class when the collection accumulates behavior, not when it is merely transported.
- **Practical heuristic**: If any class outside the collection's origin knows how to iterate, filter, or validate its contents, the collection needs to be a first-class object.

## Rule 5: One Dot Per Line (Law of Demeter)

- **Intent**: Chaining method calls across multiple objects — `a.getB().getC().doSomething()` — couples the calling class to every intermediate object and every step in the chain. POODR (Metz) calls this a train wreck: any change in `B` or `C` can force changes in the class that started the chain. The Law of Demeter says an object should only send messages to itself, its direct collaborators, objects it creates, and objects passed to it as arguments.
- **Application**: Each message chain that crosses object boundaries is a candidate for delegation. Instead of the caller navigating through B to reach C, B should expose a method that asks C on the caller's behalf. Refactorcotidiano (Iglesias) frames this under Tell, Don't Ask: send a command, do not navigate to retrieve state and act on it yourself. POODR adds that Demeter violations often reveal a missing abstraction — the journey through the graph is doing a job that belongs in a dedicated object.
- **When to relax**: Fluent builder APIs and method chaining on the same object (returning `self`) are not Demeter violations. Chaining through stable value objects with no behavioral variation is low risk. The rule applies most strongly to chains that cross behavioral objects.
- **Practical heuristic**: If you see more than one dot accessing collaborators (not fluent self-returns), add a delegating method to the first object in the chain.

## Rule 6: Do Not Abbreviate

- **Intent**: Abbreviations optimize for typing speed and penalize reading. Names are read many more times than they are written. An abbreviated name forces every reader to reconstruct what the author meant, and different readers may reconstruct it differently. Codigo Sostenible (Ble) links this to the historical context of scientific programming — single-letter variables and abbreviations came from a time when memory was scarce and keyboards were slow. That constraint no longer exists. Implementation Patterns (Beck) states explicitly that names should be optimized for readability, not ease of typing.
- **Application**: Use full words. Name methods by their intent, classes by their responsibility, and variables by their role in the computation. If a name requires three words to be unambiguous, use three words. Consistency across the model matters: use the same term everywhere for the same concept.
- **When to relax**: Widely understood domain abbreviations that all team members share (e.g., `http`, `id`, `url`, `dto`) are acceptable. Loop counters in a two-line body where the variable's role is visually obvious are a reasonable concession.
- **Practical heuristic**: If you have to explain what an abbreviation stands for to a new reader, spell it out in the code.

## Rule 7: Keep All Entities Small

- **Intent**: A class that grows beyond roughly fifty lines is usually doing more than one thing. A package with more than ten files is usually covering more than one concept. Size is a proxy for responsibility: when a class is small, it is easier to give it a single, precise name, and a single precise name resists the accumulation of unrelated methods. POODR (Metz) states that a class should do the smallest possible useful thing — it should have a single responsibility.
- **Application**: When a class approaches the size limit, ask: can you describe its responsibility in one sentence without using "and" or "or"? If not, it has more than one responsibility. Extract the secondary responsibility into a collaborator. Apply the same logic to packages: a namespace that holds too many files is a signal that it needs to be split into subdomains. POODR's heuristic is to rephrase each method as a statement about the class's responsibility — if the statement does not fit, the method belongs elsewhere.
- **When to relax**: Generated code, data-binding classes, and infrastructure adapters often grow beyond fifty lines for structural reasons unrelated to design decisions. The rule applies most strongly to domain and application-layer classes where responsibility concentration is a real design risk.
- **Practical heuristic**: If you cannot name a class without using a conjunction, split it until each part earns a single, unambiguous name.

## Rule 8: No Classes with More than Two Instance Variables

- **Intent**: This is the most severe rule and it is deliberately so. A class with many instance variables is managing multiple pieces of state that likely change for different reasons. Forcing a limit of two variables pushes you to extract collaborating objects and to model real domain concepts as types rather than as fields on a large class. In practice, the rule is a thinking tool: even if you never reach exactly two, the pressure it creates exposes hidden abstractions.
- **Application**: When a class has three or more instance variables, look for a cluster of two or more variables that belong together. That cluster is likely a concept the domain needs — extract it into its own class. Repeat until each class holds only the variables that define its identity. POODR's treatment of SRP supports this: different instance variables that change for different reasons signal that a class has multiple responsibilities.
- **When to relax**: Some domain entities genuinely require more than two attributes to define their identity — an order with a customer, a date, a list of items, and a status cannot be forced to two without artificial extraction. Treat this rule as a pressure to find hidden objects, not as a hard limit to obey in every case.
- **Practical heuristic**: If two instance variables always appear together in method signatures or are always read in the same methods, they belong in their own class.

## Rule 9: No Getters, Setters, or Properties

- **Intent**: Getters and setters expose internal state, inviting callers to retrieve data and act on it externally — the Ask side of Tell, Don't Ask. This converts objects into passive data containers and moves behavior to the callers, scattering logic that belongs together. Codigo Sostenible (Ble) calls this "JaBOL" — writing in an object-oriented language as if writing procedural code. Alan Kay, one of OOP's originators, emphasized message passing between self-contained objects, not data bags with accessors. Getters and setters add indirection but not real encapsulation.
- **Application**: Replace getters with methods that express what the caller needs done. Instead of asking for a value and acting on it, send a command to the object that holds the value and let it act on itself. Use constructors and factory methods for initialization; avoid setters entirely. Minimize the number of public methods overall. Refactorcotidiano (Iglesias) expresses this as Tell, Don't Ask: give the object a job to do rather than extracting its state to do the job for it.
- **When to relax**: Boundary objects that must serialize to an external format (DTOs, API response models, ORM entities) often require readable properties by convention. These are interface adapters, not domain objects; the rule applies to the core domain where encapsulation matters most. Read-only accessors that expose computed results — not raw state — are generally acceptable.
- **Practical heuristic**: If the caller retrieves a value with a getter and then makes a decision based on it, move that decision into the object that owns the value.
