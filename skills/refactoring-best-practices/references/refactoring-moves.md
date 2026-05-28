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
