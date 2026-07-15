# OOP Good Practices: Course Observations

Source: reviewed lessons and history from [CodelyTV/object_oriented_programming-good_practices-course](https://github.com/CodelyTV/object_oriented_programming-good_practices-course). The repository contains progressive and occasionally overwritten educational snapshots; treat the guidance below as corrected interpretation, not a claim that every proposed refactoring appears in the final tree.

## Law of Demeter as Knowledge Coupling

The TypeScript finder reaches through `User -> UserFullName -> UserName/UserLastName -> value` to format a name. The problem is not the number of dots by itself: the finder knows the nested representation and changes when that representation changes.

Move the smallest stable capability to the concept that owns it. In this case `UserFullName.formatted()` is usually more cohesive than putting presentation on `User`. A finder may then ask for the semantic result without knowing the nested fields. Fluent APIs, immutable DTO mapping, and chains returning the same object are not automatically Demeter violations.

Value Objects do not improve encapsulation when every caller still traverses their public `.value` graph. Introduce them for meaning, invariants, type distinction, or behavior, and expose the narrow semantic operation that callers actually need.

## Tell, Do Not Ask

The Python example contrasts direct inspection/mutation of `saved_products` with `add_to_saved_products` and `remove_from_saved_products`. The useful lesson is ownership of the decision: duplicate and removal policy belong with the object or collection that owns membership.

Do not infer more than the code guarantees. Python list membership uses object equality; because the course `Product` lacks semantic equality, the implementation prevents the same instance from being added twice, not two different instances with the same product ID. ID-based uniqueness requires explicit equality or lookup by ID.

Tell, Do Not Ask does not ban queries. Queries are appropriate for orchestration, authorization inputs, read models, and presentation. Move a decision when a caller repeatedly interprets another object's owned state. Keep CLI/HTTP/localized rendering in presenters or adapters rather than moving every display string into a domain entity.

## Named Construction and Cohesion

The final Java snapshot assembles `UserId`, `UserFullName`, default access level, and registration time inside `UserRegistrar`; despite the directory name, it no longer contains the historical `User.register(...)` factory. Treat it as a construction-knowledge smell and an exercise, not as a finished named-constructor example.

A named constructor is useful when its name expresses a lifecycle event or stable variant and it centralizes defaults/invariants that callers should not know. It is not useful merely to hide `new`. Private construction centralizes supported creation paths; each path must still validate its own invariants.

When creation needs ambient dependencies such as a clock, choose deliberately:

- let the application obtain time and pass an explicit `Instant` to a cohesive domain factory;
- use a dedicated factory when several external collaborators participate;
- avoid making the Aggregate depend directly on infrastructure just to preserve a named constructor.

Do not proliferate factories for speculative variants. Let repeated, stable construction knowledge earn the abstraction.

## Collections and Identity

Keep invariant-bearing mutable collections private. Expose intention-revealing mutations and immutable snapshots or semantic queries when callers need reads. Introduce a first-class collection when membership, uniqueness, ordering, capacity, selection, or aggregation forms a real concept; a transported read-only list does not need a wrapper.

Define identity explicitly. For saved products, decide whether duplicates mean the same instance, product ID, SKU, or complete value. Return an outcome or typed failure for duplicate/absent operations when callers need to react; silent no-op is a policy, not a universal default.

## Dependencies and Substitutability

Constructor-injected repository roles in the course improve dependency direction. The Java fake, however, discards saves and always misses on search, so it satisfies signatures without the useful behavioral contract. Liskov substitution includes observable behavior, not compilation alone.

Use a stateful fake when save-then-find semantics matter, create/reset it per test, and share the same lifecycle-scoped instance across commands and queries. Time, randomness, and environment are dependencies too; inject them when their values affect behavior or tests.

Do not create an interface for every class. Extract a role at a volatile/I/O boundary, when multiple implementations exist, or when a client needs a narrower capability.

## Cross-Language Enforcement

- **TypeScript:** `readonly` is shallow and compile-time only; public nested fields still leak representation. Structural mocks can conform accidentally, and runtime payloads still need validation.
- **Python:** privacy is conventional, lists and wrappers remain mutable unless protected, and collection membership depends on `__eq__`. Return tuples/copies for immutable views and avoid binary `float` for authoritative money.
- **Java:** records provide shallow immutability and value equality, while `LocalDateTime.now()` is ambient and timezone-free. Prefer `Clock` plus `Instant` for deterministic audit time unless civil local time is the domain concept.

## Review Questions

- Which decision or invariant is scattered outside the object that owns it?
- Does a message chain leak volatile structure or merely map stable data?
- Does a wrapper add meaning/behavior, or only another `.value` hop?
- Is collection uniqueness based on the correct identity?
- Does a named constructor express a real creation intent and enforce its contract?
- Does a fake preserve the collaborator's essential behavioral semantics?
- Is presentation being confused with domain behavior?
- Is a numeric style rule revealing a design problem, or creating artificial objects?

## Course Caveats

Do not copy length-only UUID validation, arbitrary universal name lengths, public mutable Python collections, float money, domain-owned display formatting, hard-coded current time, a non-persisting fake repository, broad `RuntimeException` catch-to-empty responses, or the final Java snapshot as proof of named constructors. Protect observable behavior with tests before applying these refactorings; use static architecture checks only for an intentional structural boundary, not to assert dot counts.
