# Four Rules of Simple Design

Source: [CodelyTV Four Rules of Simple Design course](https://github.com/CodelyTV/four_rules_of_simple_design-course)

Apply Kent Beck's rules in priority order. Higher rules constrain lower ones:

1. Passes the tests
2. Reveals intention
3. No duplication
4. Fewest elements

The repository presents rules 2 and 4 before duplication and adds test exercises afterward. Treat that as lesson organization, not a different priority order. Tests remain the safety constraint for every simplification.

## Passes The Tests

Use tests to preserve observable behavior while changing structure. Passing tests are necessary but not sufficient: a test can pass while asserting the wrong contract or replacing the collaborator whose real semantics contain the defect.

- Drive the public operation and assert its result, persisted state, emitted event, or boundary response.
- Do not spy on private helpers. Renaming, extracting, or inlining a helper must not break a behavioral test.
- Reproduce a defect at the boundary where it manifests before fixing it.
- Add lower-level tests only when they protect a distinct contract.

The course's email-update example is deliberately instructive: an interaction test verifies `save(updatedUser)` while the in-memory repository silently refuses replacement by a different object instance. The mock passes, but persisted state is still wrong.

Use `tdd-best-practices` for test design and `refactoring-best-practices` for safe change sequencing.

## Reveals Intention

### Use domain vocabulary

Prefer the language used by domain experts over generic technical terms. In the course, `block` becomes the domain term `ban`, with `isBanned` and `UserAlreadyBannedError` completing the same vocabulary.

Do not stop at renaming one method. Align commands, predicates, errors, paths, and tests so the concept has one name.

### Make state no richer than required

Replace a generic numeric `status` with the smallest honest model. A boolean such as `isBanned` is appropriate while the relevant domain state is truly binary. If transitions, reasons, or more states become behaviorally relevant, use an explicit state model instead.

### Encode absence semantics in the contract

The course distinguishes optional lookup from required lookup:

- `search` returns an optional value because absence is normal.
- `find` returns a value or raises a specific not-found error.

Use these words only if they fit the codebase's conventions. The general rule is to make absence explicit and consistent through the name, return type, and error behavior. A repository may remain nullable while an application-level finder translates absence into a domain error.

## No Duplication

Remove duplicated knowledge, not merely similar text.

### Literal duplication

Repeated email validation at multiple entry points is one rule expressed repeatedly. Move it to one authoritative validator or Value Object when email validity is intrinsic to that value.

### Structural duplication

Invoice and order calculators in the course have the same loop, threshold discount, and tax shape. First determine whether they implement the same pricing policy. If they do, extract and name that policy. If they can evolve independently, keep them separate despite similar syntax.

Do not default to a base class or trait. Inheritance can couple unrelated concepts and make coincidental similarity harder to undo. Prefer composition around a genuine shared decision.

### Conceptual duplication

Welcome email, SMS, and push workflows look alike, but each channel may have a different reason to change. Consolidate only the business decision that must remain synchronized; preserve channel-specific construction and delivery where they vary independently.

Ask: "Would one policy change require all copies to change together?" If not, the resemblance may not be duplication.

## Fewest Elements

Apply YAGNI after clarity and duplication have been addressed.

- Delete speculative states, fields, queries, counts, and deletion variants that serve no current behavior.
- Do not create mirror interfaces for passive records or one-method interfaces that merely rename an existing use case.
- Keep interfaces that establish dependency direction, isolate an external system, support substitutability, or define a stable client-owned port.
- Do not count implementations as the sole test. A repository can have one production adapter and still need an interface because the domain must not depend on infrastructure.
- Do not count a mock as proof that a production abstraction is useful; many languages can substitute collaborators without a dedicated interface.

Before adding or deleting an element, identify the current job it performs. "Maybe later" is not a job, but an architectural boundary or public contract can be.

## Working Sequence

1. Establish green behavioral tests at the affected boundary.
2. Improve names and contracts until the intent is explicit.
3. Identify duplicated decisions and give each one an authoritative owner.
4. Remove elements that no longer contribute behavior, clarity, or a necessary boundary.
5. Run tests after each small move and reassess the four rules.

## Course Counterexamples

Do not copy every example as target architecture. Several folders intentionally contain defects or excessive abstractions, and most local READMEs are framework boilerplate rather than lesson guidance.

- Do not generalize `search` and `find` into a universal naming law.
- Do not replace every status with a boolean.
- Do not merge independently evolving code because it looks alike.
- Do not remove every interface with one implementation.
- Do not accept passing mock tests as evidence that integration semantics work.
