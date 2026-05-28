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

Note: rename is the safest refactoring move — it changes no behavior.

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

Note: methods that return values should have no side effects; methods that change state should return nothing.

## Split Phase

Use when:
- a method or class mixes two sequential concerns, such as parsing input and then processing it
- the second phase depends only on the output of the first phase, not on the raw input
- each phase has its own vocabulary and its own reasons to change
