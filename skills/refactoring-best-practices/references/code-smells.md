# Code Smells

Use this reference when you need to name what is wrong with a piece of code and decide which refactoring move to apply first.

## Long Method

Recognition signals:
- The method body does not fit on a single screen
- You need to read the whole body before understanding what it does
- The method mixes several levels of abstraction in the same block
- Blank lines separate internally distinct responsibilities within the same method
- The method is a "monster": it has complex conditional logic, nested loops, and no extracted helpers (Working Effectively with Legacy Code, Ch. 22)

What it means:
- The method is doing more than one thing
- Understanding and testing it in isolation becomes increasingly difficult

Move to apply: Extract Method; Split Phase when the method has two sequential concerns

---

## Large Class

Recognition signals:
- The class has many instance variables that are not all used by the same methods
- Methods cluster into groups that are largely independent of each other
- You struggle to give the class a single, precise name
- Private methods accumulate that would make more sense as public methods on a smaller collaborator
- Testing a part of the class requires instantiating the whole thing (Working Effectively with Legacy Code, Ch. 20)

What it means:
- The class carries more than one responsibility
- It will have multiple unrelated reasons to change

Move to apply: Extract Class; Extract Interface / Protocol when callers only use a subset of the class

---

## Feature Envy

Recognition signals:
- A method calls several methods on another object, or accesses several of its fields, more than its own
- A method needs to pull data out of a collaborator before it can do its work
- A Service class contains all the logic while model classes hold only raw data (Codigo Sostenible, Ch. 6 — "Service se dedica a saquearles, porque no posee ningún dato propio — les envidia")

What it means:
- The behavior belongs to the object whose data it uses, not to the class where it lives
- The current placement creates unnecessary coupling and weakens the collaborating object

Move to apply: Move Method to the class whose data the method most uses

---

## Data Clumps

Recognition signals:
- The same group of two or more fields appears together in multiple class definitions
- The same set of parameters is repeated across several method signatures
- Removing one item from the group makes the remaining items meaningless on their own (refactorcotidiano, Ch. "Deja atrás lo primitivo")

What it means:
- The group of data represents a concept that does not yet have a name in the code
- Validation and formatting rules for that concept are scattered

Move to apply: Introduce Value Object; Introduce Parameter Object when the clump appears in method signatures

---

## Primitive Obsession

Recognition signals:
- Domain concepts are represented as raw strings, integers, or booleans
- Validation of a value is repeated wherever the value is used
- A parameter named `email`, `currency`, or `status` is typed as `string` or `int`
- Many methods take the same primitive argument and share the same conditional logic on it (99 Bottles of OOP, Ch. 5 — "Primitive Obsession is when you use one of these data types to represent a concept in your domain")
- The refactorcotidiano book calls this out explicitly: encapsulating a primitive is "Replace Data with Object" and yields consistency across the domain (refactorcotidiano, Ch. "Deja atrás lo primitivo")

What it means:
- Domain rules live outside the domain concept they belong to
- The type system cannot enforce invariants that belong to the value

Move to apply: Introduce Value Object

---

## Shotgun Surgery

Recognition signals:
- A single conceptual change requires edits in many unrelated classes
- Accessing a shared data structure directly from multiple call sites means every structural change ripples outward (refactorcotidiano, "si cambiamos la estructura de datos, tendremos que cambiar el código que la usa — un caso de Shotgun Surgery")
- Every new requirement means touching five files instead of one

What it means:
- A single responsibility is spread across the codebase instead of being owned by one place
- The inverse of Divergent Change: one change, many classes affected

Move to apply: Move Method and Move Field to consolidate scattered logic; Extract Class to create the missing owner

---

## Divergent Change

Recognition signals:
- The same class is modified for different, unrelated reasons across releases
- You can point to two distinct groups of methods in the class, each driven by a different external force
- Adding a new payment type requires changes in the same class as adding a new report format

What it means:
- The class has more than one axis of variation, which means more than one responsibility
- The symmetric opposite of Shotgun Surgery: one class, many change reasons

Move to apply: Extract Class so that each resulting class has a single reason to change

---

## Middle Man

Recognition signals:
- Most of the class's methods delegate directly to another object without adding logic
- Removing the class and calling the delegate directly would change nothing observable
- The class exists because it used to do more but was progressively emptied out

What it means:
- The abstraction no longer earns its place
- Callers pay indirection cost without receiving encapsulation benefit

Move to apply: Inline Method to remove the delegation layer; if the class still plays a role, consider whether it should absorb the delegate's behavior instead

---

## Inappropriate Intimacy

Recognition signals:
- A class accesses the internal data structure of another class directly rather than through its interface
- Two classes navigate each other's private fields or reach through each other's internals
- Accessing a collaborator's concrete structure creates coupling that propagates: "si accedemos a la estructura de datos directamente, estamos acoplando el código que la usa a la estructura de datos concreta — es un caso de Inappropriate Intimacy" (refactorcotidiano)
- One class reconstructs or replicates logic that belongs to another

What it means:
- Encapsulation is broken between the two classes
- Changes to the internal representation of one class force changes in the other

Move to apply: Move Method to migrate the behavior to where the data lives; Extract Interface / Protocol to hide the internal representation behind a stable boundary

---

## Comments (as a symptom of unclear code)

Recognition signals:
- A comment restates what the code already says in plain English
- A comment explains what a block does rather than why
- A blank line with no comment separates two blocks inside a method that each have their own purpose
- A comment was written to compensate for a poor name (refactorcotidiano, Ch. "Cuando los comentarios confunden" — comments become unnecessary when a method is given an expressive name)
- A comment is out of date and contradicts the code — a "lying comment"

What it means:
- The code itself is not communicating its intent
- The comment is a workaround for a naming or structure problem, not a solution

Move to apply: Rename the variable, method, or class so the comment becomes redundant; Extract Method to give the block a name that replaces the comment

---

## Duplicate Code

Recognition signals:
- Two methods contain the same block of logic, perhaps with minor variation
- The same conditional appears in several places and must be updated together
- A bug fixed in one location is found again in another because the fix was not propagated

What it means:
- Knowledge is represented more than once; the second copy will drift from the first
- Every future change to the shared logic requires finding all copies

Move to apply: Extract Method to create a single named version; Move Method when the duplicated logic belongs to a specific object; Replace Conditional with Polymorphism when the duplication is variation by type or role

---

## Data Class

Recognition signals:
- The class contains only private fields with public getters and setters for each
- No method on the class transforms, validates, or makes a decision using its own data
- Other classes reach into this class to retrieve data and perform operations with it elsewhere
- Codigo Sostenible calls this the "anemic model": "una clase que tiene una serie de campos privados, setters y getters para todos ellos, y nada más, es lo que se denomina modelo anémico" (Codigo Sostenible, Ch. 6)

What it means:
- Behavior that belongs to the object is living outside it, in service or utility classes
- The class acts as a passive data container rather than an active participant in the domain
- Feature Envy in other classes is often a consequence of Data Class

Move to apply: Move Method to transfer behavior into the class; Introduce Value Object if the class represents an immutable domain concept; remove setters where mutation is not needed to enforce invariants

---

## Temporal Coupling in Version History

Recognition signals:
- The same files repeatedly change together for one business rule
- A Value Object, validator/ensurer, exception, and use case move in lockstep
- Fixing one concept requires remembering several distant representations of the same knowledge

What it means:
- Co-change can reveal duplicated knowledge or a responsibility split across the wrong boundaries
- The files may represent one concept that deserves a single owner
- The module or Aggregate boundary may not match the actual change boundary

How to investigate:
- Inspect version history or a co-change matrix over representative feature commits
- Exclude generated files, formatting commits, bulk migrations, and mechanical renames
- Confirm the signal against domain language, invariants, ownership, and runtime consistency

Move to apply: Move validation into the Value Object that owns intrinsic validity; Move Method behind the Aggregate Root for stateful rules; Extract Class or first-class collection when one concept is scattered. Treat temporal coupling as evidence, never as proof.

Source: [CodelyTV/aggregates-course](https://github.com/CodelyTV/aggregates-course), temporal-coupling lesson and history examples.
