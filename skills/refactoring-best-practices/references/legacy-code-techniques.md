# Legacy Code Techniques

Use this reference when making changes to code that has no tests and where dependencies are hard to break.

## The Core Problem: Legacy Code

Legacy code — code without tests — is risky to change because there is no safety net. The two obstacles that come up most often are:

- Difficulty instantiating objects in a test harness due to tangled construction dependencies.
- Difficulty running methods in a test harness due to hidden side effects.

The goal is not to produce ideal design immediately. The goal is to make the next safe step possible: get a small piece of code under test, change it with confidence, and leave the system slightly more testable than you found it.

## Sensing and Separation

Two distinct reasons to break dependencies:

- **Sensing** — break a dependency so you can observe what the code actually computes. Use this when you need to verify that a value was set, a call was made, or a side effect occurred, but the code gives you no way to see it from the outside.
- **Separation** — break a dependency so you can get a piece of code into a test harness at all, even if you do not care about sensing its effects. Use this when the code cannot compile or run in isolation because it pulls in too much of the system.

Often you need both: you separate to get the code into a harness, then sense to verify behavior.

## The Seam Model

A seam is a place in the code where you can substitute one behavior for another without editing the code at that exact location. Every seam has an enabling point — the place where you make the choice to use one behavior or another.

Three types of seams:

- **Preprocessing seam** — a macro or conditional compilation directive that can replace a call before the compiler sees it. The enabling point is the build flag or include directive.
- **Link seam** — a function or class that can be replaced by pointing the linker or classpath at a different implementation. The enabling point is the makefile, build script, or classpath setting.
- **Object seam** — a method call on an object where the actual method executed depends on the runtime type. The enabling point is the place where you decide which object to create or pass. This is the most useful seam in object-oriented languages.

When a method call is made through a reference that can be varied — because it is passed as an argument, assigned from outside, or resolved through polymorphism — it is an object seam. When the object is constructed inside the same method that calls it, there is no enabling point and no seam.

## Faking Collaborators

To sense or separate, you often need to replace a real dependency with a fake. Fakes implement the same interface as the real collaborator but behave in a way that is controlled during the test. A fake has two sides: the side the class under test sees (the interface it expects), and the side the test sees (inspection methods that reveal what happened).

Use fakes when:

- A collaborator has side effects you cannot afford in a test (database writes, network calls, file system access).
- A collaborator produces values you need to control (clocks, random number generators, external APIs).
- You need to verify that a call was made with specific arguments.

## The Legacy Code Change Algorithm

When making any change in a legacy code base, follow this sequence:

1. **Identify change points** — find exactly where the code needs to change. If the design is unclear, explore it before cutting.
2. **Find test points** — find the places where you can write tests that will detect whether the change was made correctly or broke existing behavior. Test points are often close to the change points but not always the same.
3. **Break dependencies** — use the techniques below to get the code into a harness. Accept that the first incisions may leave the code looking slightly worse. The goal is a safe path into the code, not an ideal design.
4. **Write tests** — write characterization tests that pin the existing behavior, and write new tests that specify the intended change. Characterization tests document what the code actually does, not what you wish it did.
5. **Make changes and refactor** — with tests in place, make the change using test-driven development. Once the new behavior is covered, look for small refactoring opportunities in the surrounding code.

Breaking dependencies to get tests in place is different from refactoring. The dependency-breaking steps are done without tests protecting them; they must be done conservatively, with as few edits as possible, to minimize the chance of introducing new errors.

## Sprout Method

Use Sprout Method when you need to add new behavior and the new behavior can be expressed as a self-contained sequence of statements that does not need to be woven into the existing logic.

How it works: write the new behavior in a new, separately testable method. Call that method from the existing legacy method. Do not edit the legacy logic itself.

Steps:
1. Identify where the new behavior needs to be triggered in the existing method.
2. Write a call to a new method at that point and comment it out.
3. Identify what data the new method needs from the existing method and pass those values as arguments.
4. Determine whether the new method needs to return a value back to the existing method; if so, assign the return value to a variable.
5. Develop the new method using test-driven development.
6. Uncomment the call.

When to use it:
- The new behavior is a distinct piece of work with a clear boundary.
- You cannot yet get tests around the existing method, but you can test new code in isolation.
- Adding code inline would mix two unrelated concerns in the same method.

Tradeoffs:
- Advantage: new code is cleanly separated from old code. The interface between them is explicit and visible through the method signature.
- Advantage: you can write tests for the new behavior without touching or testing the legacy method.
- Disadvantage: you are deferring cleanup of the legacy method. The source method remains in a limbo state — untested, with a single call to the new method grafted onto it.
- If the legacy class itself cannot be instantiated, consider making the sprouted method a public static method that takes the required data as arguments.

## Sprout Class

Use Sprout Class when Sprout Method is not enough — when the legacy class itself cannot be instantiated in a test harness within a reasonable time, or when the new behavior represents a responsibility large enough to belong in a separate class.

Two situations that lead to Sprout Class:
- The new behavior would violate the existing class's responsibility, suggesting it belongs elsewhere by design.
- The existing class has so many creational or hidden dependencies that instantiating it in a test harness is not feasible now.

Steps:
1. Identify where the change needs to happen.
2. Name a new class that would own the new behavior. Write the code to instantiate it and call it at the change point, then comment it out.
3. Determine what data the new class needs and pass those values through the constructor.
4. Determine whether the new class needs to return values to the source method; if so, add a method for that.
5. Develop the new class test-first.
6. Uncomment the instantiation and call.

When to use it:
- Sprout Method is blocked because the source class cannot be instantiated.
- The new behavior requires its own data structures or has significant complexity that would clutter the source class.
- The new behavior has a distinct enough responsibility that it justifies a new concept.

Tradeoffs:
- Advantage: move forward with confidence without touching the source class.
- Advantage: the new class can be fully tested in isolation.
- Disadvantage: increases conceptual complexity. A new class that is clearly just a workaround for a hard-to-test parent class is harder to understand for someone learning the codebase. Over time, some sprouted classes absorb new related behavior and become genuine concepts; others remain awkward relics.

## Wrap Method

Use Wrap Method when you need to add behavior that must happen at the same time as an existing method call, but should not be tangled with that method's logic.

Temporal coupling — grouping code together only because it has to execute at the same time — produces methods that are hard to change independently later. Wrap Method explicitly separates the concerns.

Two forms:

**Form 1 — same public name:** Rename the existing method to something descriptive of what it actually does. Create a new method with the old name. The new method calls both the renamed original and the new behavior. Clients see no change in the interface.

Steps:
1. Identify the method to change.
2. Rename the existing method, preserving its signature exactly.
3. Create a new method with the original name that calls the renamed method.
4. Develop the new behavior using test-driven development and call it from the new method.

**Form 2 — new explicit name:** Keep the original method unchanged. Write the new behavior as a separate method. Create a third method that calls both. Expose this third method to callers who need the combined behavior.

When to use it:
- The new behavior is cleanly before or after the existing logic, not interleaved with it.
- You want to introduce a seam between two concerns that have always executed together.
- The existing method should not grow any larger.

Tradeoffs:
- Advantage: does not increase the size of existing methods.
- Advantage: makes the independence of the new behavior explicit.
- Disadvantage: renaming the original method to make room for the wrapper can produce a poor name. The renamed method often ends up describing only part of what it does.

## Wrap Class

Use Wrap Class — the Decorator pattern — when you need to add behavior around an entire class rather than a single method, or when the class cannot be instantiated in a test harness.

How it works: create a new class that holds a reference to the original class and implements the same interface. The new class adds the new behavior and delegates the original calls to the wrapped object.

When to use it:
- The new behavior needs to apply across many or all methods of the class.
- The original class cannot be changed (third-party, generated, or locked down).
- The behavior is a cross-cutting concern — logging, auditing, validation — that does not belong in the original class.
- You want to add tested behavior without touching untested production code.

Tradeoffs:
- Advantage: no modification to the original class. All new behavior is isolated in the wrapper.
- Advantage: the wrapper can be fully tested without the original class's dependencies.
- Disadvantage: introduces an extra layer that callers must be aware of. If every method must be delegated, it increases the amount of boilerplate.

## Extract and Override

Use Extract and Override when a dependency is hardcoded inside a method and there is no seam to replace it.

How it works: extract the dependency call into a new, overridable method on the class. In tests, subclass the class under test and override that method to substitute a fake or a controlled behavior.

Variants:
- **Extract and Override Call** — extract a single hardcoded call into a virtual method.
- **Extract and Override Factory Method** — extract object creation into a virtual factory method so tests can substitute a different object.
- **Extract and Override Getter** — extract access to a field or singleton into a getter method, then override the getter in a test subclass.

When to use it:
- A dependency cannot be injected through the constructor or a parameter.
- The dependency is created or accessed directly inside the method body.
- Subclassing is feasible and does not introduce other complications.

Decision rule: if the dependency is accessed in one place, extract that one call. If it is accessed through construction, extract a factory method. If it is a field or global accessed repeatedly, extract a getter.

## Parameterize Constructor

Use Parameterize Constructor when a class creates a hard dependency inside its constructor, making it impossible to substitute the dependency in a test.

How it works: add a new parameter to the constructor that accepts the dependency from outside. Provide a convenience constructor (or default argument) that supplies the production default, so existing callers do not break.

When to use it:
- The constructor calls `new` on a concrete class that is expensive, has side effects, or cannot be instantiated in a test harness.
- The dependency needs to vary between production and test.

Decision rule: prefer Parameterize Constructor over Introduce Static Setter when the dependency is per-instance and the class will be instantiated multiple times with different collaborators.

## Introduce Static Setter

Use Introduce Static Setter when the dependency is a global or singleton and there is no other way to replace it in a test.

How it works: add a static setter method on the singleton or global holder that allows a test to install a substitute before the code under test runs, and reset it afterward.

When to use it:
- The code accesses a global or singleton directly, with no parameter or constructor through which to inject a replacement.
- Parameterizing the constructor or method is too invasive given the time available.
- The singleton is used across many places and changing all call sites is not practical right now.

Tradeoffs:
- This technique makes the global nature of the dependency explicit rather than hiding it.
- Tests that use a static setter must restore the original state afterward, or they will interfere with each other.
- Prefer it only when cleaner injection is not feasible in the current context.

## Decision Rules: Choosing a Technique

Use this guidance when deciding which technique to apply:

- **Can you formulate the new behavior as a distinct, self-contained method?** Use Sprout Method.
- **Can you formulate the behavior but cannot instantiate the class?** Use Sprout Class.
- **Does the new behavior need to run at the same time as an existing method, but independently of its logic?** Use Wrap Method.
- **Does the new behavior apply across the whole class, or is the class not modifiable?** Use Wrap Class.
- **Is a dependency hardcoded inside a method body with no way to substitute it?** Use Extract and Override.
- **Is the dependency created in the constructor?** Use Parameterize Constructor.
- **Is the dependency a global or singleton accessed throughout the codebase?** Use Introduce Static Setter.

When in doubt, prefer the technique that requires the fewest edits to existing code. The first goal is a safe path to a test, not a clean design. Clean design follows once the code is under test.
