---
name: fp-best-practices
description: Functional Programming guidance for writing and reviewing clean, composable code. Use when naming functions or types, designing pure functions, applying function composition or pipe, choosing between algebraic data types (Maybe, Option, Either, Result), controlling side effects or IO boundaries, using higher-order functions (map, filter, reduce, flatMap), applying currying or partial application, avoiding mutation and shared state, or reviewing FP code in JavaScript, TypeScript, Python, Go, Rust, Haskell, Elm, Clojure, F#, or Elixir.
license: MIT
metadata:
  author: luckys
  version: "1.0.0"
---

# FP Best Practices

Use this skill for everyday functional programming decisions that shape composability, predictability, and long-term maintainability.

Use it especially when the task benefits from:

- clearer separation between pure logic and side effects
- smaller functions composed into pipelines
- types that make illegal states unrepresentable
- data transformations over mutations
- referential transparency and easier testing

## Working Style

1. Write functions for the next reader, not just for the runtime.
2. Keep side effects at the edges; keep the core pure.
3. Prefer small, composable functions over clever all-in-one implementations.
4. Use types and names to reveal intent.
5. Let the data structure do the work when it can.

## Review Workflow

1. Identify the transformation.
   - What data goes in? What comes out?
   - What domain concept is this function modeling?

2. Check purity.
   - Does this function have side effects (I/O, mutation, randomness)?
   - Can the side effects be pushed to the boundary?

3. Check composition.
   - Is this function doing one thing?
   - Can it be expressed as a composition of smaller functions?
   - Is it reusable in other pipelines?

4. Check types and edge cases.
   - Are null/undefined/error cases handled explicitly via ADTs?
   - Is the return type honest about what might fail?

5. Apply the lightest useful improvement.
   - extract function
   - introduce pipe/compose
   - replace null with Maybe/Option
   - replace throws with Either/Result
   - push side effect to boundary
   - replace loop with map/filter/reduce

## Additional Review Lenses

### Purity and referential transparency

- A pure function returns the same result for the same inputs, always.
- Pure functions are trivially testable, composable, and parallelizable.
- Impure operations (I/O, logging, random, time) belong at the edges of the system.

### Composition over imperative sequencing

- Prefer expressing pipelines over step-by-step instructions.
- Small functions combined with `pipe` or `compose` reveal the shape of the transformation.
- Point-free style removes noise when the data flow is already clear from the pipeline.

### Algebraic data types over null and exceptions

- Use `Maybe`/`Option` when a value may legitimately be absent.
- Use `Either`/`Result` when an operation may fail and the caller needs the error.
- Model domain variants as tagged union types (sum types) rather than optional fields.

### Immutability as the default

- Never mutate data in place — produce new values instead.
- Use `Object.freeze`, `readonly`, immutable records, or persistent data structures.
- Mutation is a side effect. Treat it as one.

### Higher-order functions as vocabulary

- `map` transforms each element of a structure without leaving the structure.
- `filter` selects elements by predicate.
- `reduce`/`fold` collapses a structure into a single value.
- `flatMap`/`chain` sequences computations that each return a wrapped value.

## Day-to-Day Rules

- Prefer pure functions. Extract impure operations to the boundary.
- Name functions by the transformation they perform, not the mechanism.
- Use `pipe` (left-to-right) or `compose` (right-to-left) to express data flow.
- Replace `null` with `Maybe`/`Option` when absence is meaningful.
- Replace `throw` with `Either`/`Result` when callers need to handle failures.
- Curry functions when partial application makes call sites cleaner.
- Prefer immutable data structures. Mutate only at system boundaries.
- Use `map`/`filter`/`reduce` over imperative loops by default.
- Keep functions small — one transformation, one level of abstraction.
- Avoid hidden state (closures that mutate captured variables are side effects).

## Good Signals

- Every function can be tested with just its inputs — no setup needed.
- Pipelines read like a description of the problem.
- Illegal states cannot be constructed from the types.
- Side effects are localized to clearly named edge functions.
- Changing one transformation does not break unrelated pipelines.

## Warning Signs

- Functions that mutate their inputs or external state.
- `null` or `undefined` passed as a meaningful sentinel value.
- Exceptions used for normal control flow.
- Long functions that mix data fetching, transformation, and output.
- Mutable shared state threaded through function parameters.
- `for` loops where `map`/`filter`/`reduce` would make intent clearer.
- Deeply nested callbacks or `.then()` chains that mix logic with I/O.

## References

- Read `references/core-principles.md` for the fundamental FP principles: purity, immutability, referential transparency, and composition.
- Read `references/naming-and-abstractions.md` when naming or abstraction quality is the main issue.
- Read `references/function-composition.md` for pipe, compose, currying, partial application, and point-free style.
- Read `references/algebraic-data-types.md` for Maybe/Option, Either/Result, tagged unions, and making illegal states unrepresentable.
- Read `references/managing-side-effects.md` for IO boundaries, Reader/Writer/State patterns, and effect systems.
- Read `references/higher-order-functions.md` for map, filter, reduce, flatMap, transducers, and functor/monad patterns.
- Read `references/language-examples.md` for an index of language-specific example files and a quick reference table.
- Read `references/javascript-examples.md` for examples in JavaScript (native, Ramda, fp-ts).
- Read `references/typescript-examples.md` for examples in TypeScript (fp-ts, Effect-TS, branded types).
- Read `references/python-examples.md` for examples in Python (functools, itertools, returns, pattern matching 3.10+).
- Read `references/go-examples.md` for examples in Go (first-class functions, generics, functional options, `(value, error)`).
- Read `references/rust-examples.md` for examples in Rust (Iterator trait, Option/Result, enums, newtype, `?` operator).
- Read `references/haskell-examples.md` for examples in Haskell (pure FP reference, typeclasses, IO monad).
- Read `references/elm-examples.md` for examples in Elm (frontend FP, The Elm Architecture, decoders).
- Read `references/clojure-examples.md` for examples in Clojure (threading macros, persistent data structures).
- Read `references/fsharp-examples.md` for examples in F# (computation expressions, discriminated unions, pipelines).
- Read `references/elixir-examples.md` for examples in Elixir (pipe operator, pattern matching, `with`, OTP).

## Related Skills

- Use `oop-best-practices` when the codebase mixes FP and OOP and object design is in question.
- Use `refactoring-best-practices` when introducing FP into an existing imperative codebase.
- Use `design-patterns-best-practices` when evaluating whether a pattern maps to a functional equivalent.
- Use `tdd-best-practices` for test-driving pure functions and effect boundaries.

## Source Influences

This skill is synthesized from ideas emphasized in:

- *Mostly Adequate Guide to Functional Programming* — Brian Lonsdorf (Professor Frisby)
- *Professor Frisby's Mostly Adequate Guide to Functional Programming*
- *Haskell Programming from First Principles* — Allen & Moronuki
- *Structure and Interpretation of Computer Programs* — Abelson & Sussman
- *Functional Programming in Scala* — Chiusano & Bjarnason
- *Domain Modeling Made Functional* — Scott Wlaschin
- *Grokking Simplicity* — Eric Normand
- fp-ts, Effect-TS, and Ramda library documentation
