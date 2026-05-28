# Fran Iglesias Refactoring Guidance

This reference distills practical ideas from Fran Iglesias's articles tagged "refactoring" into heuristics for everyday code improvement.
It focuses on safe incremental steps, recognizing when to act, using tests as a safety net, and moving behavior to the right place.
OOP design principles, TDD workflows as primary focus, and DDD strategic modeling belong in separate references.

## Main Themes

Across these articles, several ideas repeat consistently:

- use code smells and metrics as objective signals, not subjective taste, to decide where to refactor
- extract behavior into value objects when primitives carry domain rules
- group data that travels together into a single concept
- decompose long methods by responsibility before looking for new classes
- shrink parameter lists by introducing parameter objects or value objects
- lift repeated conditions out of nested branches so each flow path is expressed once
- get tests in place before touching complex or legacy code — combinatory and snapshot techniques help reach coverage quickly
- refactoring immediately before or while making a change gives the best return on investment

## Metrics-Driven Refactoring

From `metric-driven-refactoring`:

- refactoring is a cost-control tool, not an aesthetic exercise — maintainable code costs less to change regardless of whether a human or an AI agent does the work
- quality is measurable through structural and cognitive complexity, cohesion, and coupling — these are concrete, not subjective
- code smells and object-calisthenics rules serve as cheap proxies for precise metrics: they let you spot problem areas without running a measurement suite
- cognitive complexity (Campbell 2018) is more sensitive than cyclomatic complexity because it penalizes nesting depth in addition to branching count; a sawtooth left margin is the visual signal
- the Maintainability Index combines Halstead volume, cyclomatic complexity, and lines of code into a single score; very low scores flag units that deserve immediate attention
- OO-specific CK metrics (coupling between objects, response for a class, depth of inheritance) add a relational dimension that per-method metrics miss
- a practical workflow: run metrics, identify three high-impact refactors ordered by their effect on complexity and coupling, justify the time investment before starting

Practical rule:

- if you cannot articulate why a unit is hard to change beyond "it feels messy," run cognitive complexity and coupling metrics — the numbers will tell you which problem is real and which refactor to prioritize

## Primitive Obsession

From `primitive-obsession`:

- primitive obsession occurs when domain concepts are modeled with raw language types, forcing validation, formatting, and business rules to scatter across the entire codebase
- scattered validation creates inconsistency: the same rule is written multiple times, drifts, and eventually produces bugs that are hard to trace
- the characteristic refactor is "Introduce Value Object": wrap the primitive, enforce invariants in the constructor or factory method, and let the object carry its own behavior
- a private constructor combined with a named factory (`Amount.valid(...)`) makes it impossible to create an invalid instance; callers cannot bypass the rule
- once the value object exists, domain-specific behavior (formatting, comparison, conversion) migrates into it naturally instead of living in services or utilities
- primitive obsession and data clump often appear together; recognize the difference — primitive obsession is about a single value that carries rules, data clump is about several values that always travel together

Practical rule:

- if you have to write the same validation for a field in more than one place, or if formatting logic branches on what "kind" a value is, wrap the value in an object and put the rule there

## Data Clump

From `data-clump`:

- a data clump is a group of fields that travel together through constructors, method signatures, and class fields — they are signaling an unnamed concept
- the smell does not cause bugs immediately, but every future change that affects those fields must be applied in multiple places, creating drift and inconsistency
- the refactor is "Introduce Value Object": identify the fields that belong together, create a class for them, give it a meaningful name, and let it carry any behavior that touches only those fields
- once the value object exists, adding new fields or changing formatting is a one-place change instead of a cascade — this is the concrete payoff
- value objects should attract behavior: if a method only uses fields from the value object, it belongs inside the value object

Practical rule:

- if the same three fields appear together in two or more constructors or method signatures, name the concept they represent and introduce a class for it

## Long Method

From `long-method`:

- a long method is doing several things at once; the first symptom is mixed levels of abstraction within the same method body
- the visual signal: comment blocks that group related lines are already candidate method extractions waiting to happen
- the refactoring sequence is: first "Extract Method" to isolate each responsibility into a private helper with a meaningful name; then look at what those helpers need and whether some naturally belong on separate collaborator classes ("Extract Class")
- extracting private methods clarifies the main method by hiding detail and making the high-level flow readable at a glance; only after that does "Extract Class" become safe because responsibilities are already named and bounded
- before extracting from complex legacy code, establish a safety net — even a single characterization test that exercises the main path is enough to start

Practical rule:

- if reading a method requires mentally tracking what "phase" you are in, extract each phase into a named private method; if extracted methods share more context with each other than with the parent class, extract a class

## Long Parameter List

From `long-parameter-list`:

- more than three or four parameters overloads working memory; positional parameters of the same type are also fragile because swapping two silently produces wrong results
- adding optional parameters with default values is a short-term fix that compounds future cost — every new optional parameter makes the list harder to document and test
- three refactors address this smell:
  - "Introduce Value Object" when a subset of the parameters represents a domain concept with its own rules (the tightest fix)
  - "Introduce Parameter Object" when the parameters lack that conceptual bond but the signature still needs to be stable and manageable
  - "Builder" when construction is complex and the object under construction needs a readable creation language
- parameter objects and value objects act as a shield: when the method's inputs change, you update the object rather than hunting for every call site

Practical rule:

- if adding a new parameter would push the list beyond four, first ask whether any existing parameters belong together as a concept; if yes, introduce a value object; if no, introduce a parameter object to keep the signature stable

## Uplift Conditional

From `a_case_for_uplift_conditional`:

- when the same condition appears in multiple nested or sequential branches, the code is expressing two tangled flows in one block instead of separating them
- "Uplift Conditional" pulls the dominating condition to the top level, producing two independent and flat code paths — one per branch of the lifted condition
- the technique is safe even without comprehensive test coverage: each small step (extract method, lift condition, merge duplicated branches) is individually obvious and preserves behavior
- the payoff is that each flow has a single location to modify; meaningful names can be applied per context; the behavior of each path is easy to reason about independently
- before applying, extract the tangled block into its own method to create a clear boundary; then lift the condition inside that method

Practical rule:

- if the same boolean condition appears in three or more branches of a single function, lift it to the top so the function has two flat sections; the duplication inside each section will then be easy to see and eliminate

## Golden Master and Approval Testing for Legacy Code

From `golden-cookbook-master-approval`:

- refactoring legacy code without tests is unsafe; the Golden Master technique provides a fast path to meaningful coverage even when business rules are opaque and scattered
- the approach: run the system under test with a large number of parameter combinations, capture all outputs as a snapshot, and treat any future deviation as a failing test
- "approval mode" keeps the snapshot always regenerating so you can examine output and tune the input combinations until you reach 100% code coverage; then approve and switch to normal snapshot mode
- once 100% branch coverage is confirmed, any refactor that changes observable behavior breaks at least one test — this is the safety net
- combinatory input generation replaces hand-crafted test cases: enumerate the distinct values for each input dimension and let the framework produce all combinations

Practical rule:

- before touching any legacy code that has no tests and complex conditional logic, use combinatory snapshot testing to get to full branch coverage first; only then start extracting and simplifying

## Economics of Refactoring and the 3P Pattern

From `Some-economics-of-refactoring` and `Breaking-out-of-legacy-with-3P`:

- the return on investment from refactoring is highest when it happens immediately before the change that benefits from it; delaying it to a "cleanup sprint" defers the benefit and makes it harder to justify
- the 3P pattern (Protect → Prepare → Produce) makes opportunistic refactoring part of the normal feature workflow:
  - Protect: add tests that capture existing behavior before any change
  - Prepare: refactor so the new feature can be introduced cleanly
  - Produce: implement the feature with TDD
- the developer who writes the protection tests is the first beneficiary of those tests; they understand the code best at that moment and can spot ill-conceived tests immediately
- this pattern keeps refactoring small and focused — only the code directly relevant to the current story is improved, preventing the scope from becoming a rewrite

Practical rule:

- do not start a feature in messy code without first protecting existing behavior with tests and preparing the structure to receive the change; the protection step is not overhead — it is how you avoid breaking things while delivering

## Everyday Refactoring Heuristics

When improving code, try this order:

1. make the problem objective — run cognitive complexity and coupling metrics or apply a code smell checklist before deciding where to act
2. get tests in place first — use characterization tests, Golden Master, or combinatory snapshot testing to create a safety net before touching the code
3. name the concept precisely — rename until the code explains itself without comments
4. eliminate primitive obsession — wrap any value that carries its own rules or formatting in a value object
5. collapse data clumps — identify fields that always travel together, give the concept a name, introduce a class
6. decompose long methods by responsibility — extract named private methods first, then extract classes from clusters of methods that belong together
7. shorten parameter lists — replace related parameters with value objects; replace unrelated ones with a parameter object or builder
8. lift repeated conditions — pull the dominant boolean to the top so each code path is flat and expressed once
9. refactor opportunistically, not in bulk — apply the 3P pattern so each story cleans only what it touches
10. use tests as a wall at your back — run the full suite after every small step; roll back immediately if anything turns red
