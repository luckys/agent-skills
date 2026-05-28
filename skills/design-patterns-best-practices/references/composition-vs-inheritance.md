# Composition vs Inheritance

This is one of the most important design decisions in object-oriented systems.

## Prefer Composition When

- behavior can vary independently from the host object
- behavior should be replaceable at runtime
- multiple combinations of behavior are possible
- inheritance would force subclasses to inherit behavior they do not want
- the subtype relationship is doubtful or unstable

## Prefer Inheritance When

- the subtype genuinely satisfies the parent contract
- shared invariants are stable
- polymorphism is central and well understood
- composition would add ceremony without reducing coupling

## Red Flags for Inheritance

- overriding methods only to disable parent behavior
- subclasses that use only part of the parent API
- deep hierarchies
- parallel hierarchies created to combine multiple dimensions of variation

## A Useful Rule

If you are using inheritance mainly to reuse code, stop and re-evaluate. Reuse alone is usually not strong enough justification.
