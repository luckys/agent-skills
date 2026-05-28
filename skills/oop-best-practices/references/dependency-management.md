# Dependency Management

Use this reference when deciding what to depend on, how to pass collaborators, and how to control coupling between objects.

## Recognizing Dependencies

A class has a dependency on another whenever it knows:

- the name of another class
- the name of a message it intends to send to someone other than itself
- the arguments that message requires
- the order of those arguments

Each piece of knowledge is a coupling point. If the depended-on thing changes, the depending class may be forced to change too. The goal is not to eliminate dependencies — objects must collaborate — but to keep each class knowing just enough to do its job and not one thing more.

Coupling between objects accumulates quietly. If a class creates its own collaborators, those collaborators' class names, argument lists, and argument order all become hidden dependencies. Hidden dependencies are more dangerous than explicit ones because they are easy to miss and hard to extract.

## Dependency Direction

When two classes must be coupled, the direction of the dependency matters. Choose to depend on things that change less often than you do.

Three truths govern this choice:

- some classes are more likely than others to have changes in requirements
- concrete classes are more likely to change than abstract ones
- changing a class that has many dependents causes widespread consequences

If you apply these ideas to your design choices:

- if a class is concrete and volatile, then depend on an abstraction in front of it rather than on the class directly
- if a class is abstract and stable, then it is a safe target for many dependents
- if a class is both concrete and has many dependents, it is in a dangerous position — changes to it ripple everywhere

Abstract classes and interfaces attract dependents precisely because they are stable. Concrete classes tend to change. High-level business logic should not depend on low-level infrastructure; the dependency should point toward the abstraction, not toward the implementation. This is the dependency inversion principle: a class with a high level of abstraction should not depend on a class with a low level of abstraction.

## Inject vs Create

When a class needs a collaborator, it faces a choice: create the collaborator internally or receive it from outside.

Creating a collaborator internally:

- hard-codes the collaborator's class name inside the depending class
- binds the depending class to a specific implementation
- makes substituting the collaborator impossible without modifying the class
- hides the dependency from callers

Injecting a collaborator:

- reduces the dependency to a single expectation: that the injected object responds to a certain message
- makes the dependency explicit and visible at the call site
- allows any compatible object to be passed, without the class knowing or caring which class it belongs to
- makes the class easier to test and easier to reuse in different contexts

The rule is: if the class only needs to send a message to a collaborator, it does not need to know the collaborator's class name. The responsibility for knowing which class to instantiate belongs elsewhere — in a factory, a composition root, or the calling context.

If you are constrained and cannot inject the dependency, isolate instance creation to a single location inside the class rather than scattering it. Centralizing creation limits the reach of the dependency and makes it easier to change later.

## Isolating Volatile Dependencies

Some dependencies are unavoidable — a class must reach a specific external system, a specific format, or a specific third-party interface. When that external thing is volatile, isolate it behind a stable wrapper.

Rules for isolation:

- if an external class name appears in multiple methods, extract the access to a single method inside your class — callers use your method, not the external interface directly
- if a message chain reaches deep into another object's internals, wrap the chain in a method that expresses the intent rather than the navigation path
- if you depend on something you do not own and cannot change, create a thin boundary layer that your code depends on and that translates to the external interface — your code never touches the external shape directly

The goal is that a change to the external thing requires a change only in the wrapper, not throughout the class or the application.

## Argument Order and Named Parameters

Positional arguments create an additional form of dependency: the depending class must know not only what arguments a message takes but also the order in which to pass them. This order is invisible in the call, fragile under refactoring, and easy to get wrong.

Heuristics for reducing argument-order coupling:

- if a method takes more than one or two arguments, prefer named or keyword arguments over positional ones
- named arguments make the call site self-documenting and allow the receiver to reorder, add, or remove parameters without breaking callers
- if you must depend on a method with positional arguments that you do not own, wrap it in a single factory method inside your codebase — all calls go through the wrapper, so argument-order coupling is confined to one place
- if an argument has a sensible default, embed the default in the parameter definition rather than in every call site

Trading positional coupling for name coupling is a good trade. Names are more stable than positions and communicate intent at the point of use.

Parameters themselves are a weaker form of coupling than permanent references. Passing a collaborator as a parameter ties the objects together only for the duration of the call. A stored reference ties them together for the object's lifetime. Prefer parameters over stored references where it is natural to do so.

## Warning Signs

Watch for these patterns — each is a signal that dependencies are harder to manage than they need to be:

- a hardcoded class name inside a method body is a hidden dependency; it means the class cannot collaborate with anything else
- creating an instance deep inside a complex method mixes object construction with business logic; extract or inject it
- a chain of messages that navigates through multiple objects to reach behavior is a coupling chain — each intermediate object is now a dependency; ask whether a message can be introduced closer to where the behavior lives
- two classes that each depend on the other form a circular dependency; circular dependencies complicate maintenance, prevent independent deployment, and tend to cause initialization problems
- a class that depends on many other concrete classes has high coupling; changes anywhere in that network can force changes here
- a class that many other classes depend on is a stability bottleneck; if it is concrete, it is risky; if it must change often, the consequences are wide
