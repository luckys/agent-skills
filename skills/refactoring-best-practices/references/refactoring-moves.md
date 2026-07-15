# Refactoring Moves

## Extract Method

Use when:
- a method mixes several levels of abstraction
- a block has a clear name
- a decision or calculation is hidden in noise

## Move Method

Use when:
- a method uses more data from another object than from its own class
- callers need to pull data out before a decision can happen
- feature envy is visible

## Extract Class

Use when:
- the class has several reasons to change
- methods form cohesive clusters
- the object is carrying too much state

## Introduce Value Object

Use when:
- validation is repeated
- a primitive carries domain meaning
- formatting, parsing, comparison, or invariants belong to the value
- same-typed primitives can be accidentally swapped

Do not use when:
- the fields are unrelated transport data
- the rule depends on current time, tenant, repository state, or workflow
- a type alias, brand, enum, or Parameter Object already provides enough clarity
- the concept has no stable domain meaning yet

Safe sequence:
1. Characterize current behavior, errors, and serialized output.
2. Name one cohesive concept and separate intrinsic rules from contextual policy.
3. Add the Value Object beside the primitive API.
4. Convert primitives at one boundary and migrate callers incrementally.
5. Move duplicated validation, normalization, comparison, and behavior.
6. Add semantic equality, matching hashing, and defensive copies.
7. Verify persistence and transport round trips.
8. Remove obsolete primitive validation only after all feedback is green.

Use `oop-best-practices` for the target Value Object design contract.

## Introduce First-Class Collection

Use when:
- collection rules are duplicated
- filtering, ordering, uniqueness, or summary logic belongs to the collection
- the collection has domain language of its own

## Replace Conditional with Polymorphism

Use when:
- branching depends on role, type, or policy
- variation is stable enough to deserve explicit collaboration
- adding a new branch would keep spreading decision logic

Do not use when:
- the branching is tiny and local
- the variation is not stable
- the introduced abstraction would obscure the behavior more than clarify it

## Rename

Use when:
- a name no longer matches the concept it represents
- reading the code requires mental translation between the name and what it actually does
- the current name is an abbreviation or a generic word that carries no domain meaning
- the domain has evolved and the old name reflects an outdated understanding

Note: rename usually preserves runtime behavior, but can break reflection, serialization, DI conventions, database mappings, and public consumers. Search those boundaries before treating it as mechanical.

## Inline Method

Use when:
- a method body is as clear as its name and the name adds no abstraction
- the method is called only once and the indirection adds no value
- a method was extracted for a reason that no longer exists

Do not use when:
- the method name adds meaningful abstraction that the body alone does not convey
- the method has multiple callers that benefit from the shared name

## Extract Interface / Protocol

Use when:
- a class is used as a collaborator but callers depend on more than they actually need
- you want to substitute the collaborator in tests or extend behavior without changing existing code
- two unrelated classes could play the same role for a caller

Note: define the interface by what clients need, not by what the class exposes.

Do not extract a mirror interface merely because a class exists. Keep a single-implementation interface when it establishes a real port, dependency direction, public contract, or substitution boundary; implementation count alone is not decisive. Remove interfaces that only repeat a record, factory, or use-case surface without isolating change.

## Remove Speculative Elements

Use when:
- an enum contains states unsupported by current behavior
- a field has no rule, output, or current use case
- a repository predicts many query/count/delete variants
- an abstraction exists only for a hypothetical future

Safe sequence:
1. Search production, tests, serialization, reflection, DI, persistence mappings, and external consumers.
2. Protect any current observable contract.
3. Delete one element and run feedback.
4. Restore it only if a concrete consumer or boundary proves its job.

YAGNI does not authorize breaking public compatibility or removing deliberate architecture boundaries.

## Consolidate Duplicated Knowledge

Use when the same business decision must remain synchronized across multiple expressions. Extract a named policy or move the rule to its canonical owner.

Do not consolidate merely because code has the same shape. Invoice and order calculations may share one pricing policy, while email, SMS, and push workflows can evolve independently despite structural similarity. Prefer composition around a shared decision over a generic base class that couples unrelated concepts.

## Replace Temp with Query

Use when:
- a temporary variable stores the result of an expression that is computed once
- the expression can be given a meaningful name as a method
- callers would benefit from the named query instead of reading the raw expression

Do not use when:
- the computation is expensive and caching the result in a variable matters for performance

## Separate Query from Modifier

Use when:
- a method both returns a value and changes state, mixing a side effect with a return value
- callers cannot ask a question without causing a change in the system
- testing becomes hard because observing a result also mutates state

Note: prefer separation when it clarifies behavior, but treat this as a heuristic. Atomic operations such as `pop`, iterators, and fluent immutable APIs may legitimately return a result while changing or replacing state.

## Split Phase

Use when:
- a method or class mixes two sequential concerns, such as parsing input and then processing it
- the second phase depends only on the output of the first phase, not on the raw input
- each phase has its own vocabulary and its own reasons to change
