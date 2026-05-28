# Method Design

Use this reference when writing or reviewing methods to ensure they are intention-revealing, single-level, well-composed, and easy to understand without reading their internals.

## Composed Method

- Divide every non-trivial method into a sequence of named steps, each at one level of abstraction.
- If a method mixes high-level orchestration with low-level implementation details, it is doing more than one thing.
- Each step in a composed method should read like a sentence describing what happens, not how.
- If you cannot name a step clearly, that step is either at the wrong level or doing too much.
- The body of the top-level method becomes a readable summary; readers should be able to understand the intent without reading the helpers.
- Extract helpers even when there is no reuse — the goal is clarity and isolation, not deduplication.
- If you feel the need to add blank lines between blocks of code inside a method to visually separate them, each block is a candidate for extraction into a named method.

## Intention-Revealing Names

- Name a method after what it accomplishes, not after the mechanism it uses to accomplish it.
- If you name a method after its current implementation, you tie the name to the implementation and cannot change one without invalidating the other.
- A name that reflects intent survives internal changes; a name that reflects implementation becomes a lie after every refactor.
- Name a method one level of abstraction higher than the thing it returns or does — this isolates callers from implementation decisions.
- If you cannot name a method without describing its implementation, that method likely does not yet represent a stable concept.
- Prefer full descriptive names over abbreviated ones; the cost of a long name is paid once, the cost of an unclear name is paid every time someone reads it.
- When two methods differ only in mechanism but not in purpose, they should share a name — varying implementation through polymorphism rather than naming.

## Single Level of Abstraction

- A method should operate at one level of abstraction throughout its body.
- If a method mixes orchestration calls (calling other methods by name) with inline computations or raw data manipulation, it has mixed levels.
- High-level steps belong in the top-level method; low-level details belong in helpers named at the appropriate level.
- If reading a method requires you to context-switch between understanding the overall intent and tracking local variable manipulation, the abstraction levels are mixed.
- Introduce an intermediate method to bridge levels rather than collapsing different levels into one body.
- Apply this rule recursively: each helper should itself be at one level of abstraction.

## Guard Clauses

- Use an early return to handle edge cases, precondition violations, and absent values at the top of a method.
- Guard clauses separate exceptional and degenerate cases from the main path, making the main path easier to read.
- If a method's main logic is nested inside one or more conditional checks, invert those conditions into early returns.
- Place all guard clauses at the top of the method body, before any main-flow logic begins.
- If a guard clause grows complex, extract it into a named predicate method whose name explains what condition is being guarded against.
- Prefer a single early return per guard over a large else block — readers should not need to track an open branch while reading the main flow.
- Guard clauses communicate: "these are the abnormal situations; everything below this point is the normal case."

## Explaining Messages

- When a method contains an inline expression whose purpose is not obvious from its syntax, extract it into a separate method and send that method as a message.
- The extracted method exists to explain purpose, not to avoid repetition — it may only have one caller.
- Naming the extracted method after what the expression means transforms opaque logic into self-documenting code.
- If you feel the urge to write an inline comment explaining what an expression does, that is a signal to extract it as a named method instead.
- The pattern applies to boolean conditions, arithmetic expressions, and string manipulations equally — anything that requires mental effort to decode belongs in a named method.
- An explaining method is not a helper in the reuse sense; it is a vocabulary choice that makes the calling method readable at a glance.

## Method Length

- There is no universally correct line count, but a method that cannot fit on one screen is a strong signal to examine it for extraction opportunities.
- Cyclomatic complexity is a more reliable guide than raw line count: each conditional branch adds mental load that can be reduced by extraction.
- If understanding a method requires holding more than a few things in working memory simultaneously, it is too long.
- A method with many lines that each do one simple named thing may be acceptable; a method with a few dense lines that each require analysis is not.
- A method that has grown to handle more than one conceptual case probably needs to be split rather than refactored inline.
- The goal is not minimizing lines of code; it is maximizing the ratio of meaning to effort for the reader.
- If you can read a method from top to bottom and understand what it does without pausing, it is the right size.

## Visibility and Cohesion

- Public methods form a contract with callers; keep this surface small and stable.
- Every method added to the public interface increases the coupling between a class and its callers and reduces the freedom to change internals.
- Methods that exist only to support other methods in the same class should be private; they are implementation details, not contracts.
- Protected methods signal to subclasses: "this is intentionally open for override, but not for external use." Use protected deliberately, not as a default.
- If a private method grows complex enough to feel like it deserves its own tests, it is a candidate for extraction into a collaborating class with a well-defined public interface.
- The cohesion of a method set is visible in its public surface: if public methods change for different reasons, the class has more than one responsibility.
- Hiding helper methods behind private visibility also protects callers from implementation changes — if a helper is only private, refactoring it never breaks external code.
