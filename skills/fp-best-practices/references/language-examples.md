# Language Examples

Use this file as an index to the language-specific functional programming references.

## Covered Languages

- `references/javascript-examples.md` — native ES2022+, Ramda, fp-ts
- `references/typescript-examples.md` — fp-ts, Effect-TS, branded types
- `references/haskell-examples.md` — pure FP reference, typeclasses, IO monad
- `references/elm-examples.md` — frontend FP, The Elm Architecture, decoders
- `references/clojure-examples.md` — LISP FP, threading macros, persistent data structures
- `references/fsharp-examples.md` — .NET functional-first, computation expressions
- `references/elixir-examples.md` — BEAM concurrency, OTP, pipe operator, `with`

## Shared Concept Set

Each language file covers the same concepts:

- Pure functions and referential transparency
- Function composition / pipe operator
- Currying and partial application
- Maybe / Option — explicit absence
- Either / Result — explicit failure
- Sum types / discriminated unions / tagged variants
- Immutable data transforms
- Higher-order functions (map, filter, reduce, flatMap)
- Side effect boundary (functional core / imperative shell)
- Dependency injection via function parameters

## How to Use This Reference

- Read the language file that matches the user's codebase first.
- If the user works across multiple languages, compare the same concept across files.
- Prefer concept-level consistency over syntax-level imitation.
- When adding a new concept, add it to every language file so the set stays aligned.
- Use `core-principles.md`, `function-composition.md`, `algebraic-data-types.md`, `managing-side-effects.md`, or `higher-order-functions.md` when an example raises a deeper FP design question.

## Suggested Reading Order

1. Start with the language the user is actively using.
2. Review pure functions, composition/pipe, and immutability first.
3. Compare Maybe/Option and Either/Result across one dynamic and one static language.
4. Compare the side effect boundary pattern across languages to see the common structure.
5. Return to `core-principles.md` when a design question goes beyond syntax.

## Quick Reference Table

| Language | Pipe | Compose | Option / Maybe | Either / Result | Ecosystem |
|---|---|---|---|---|---|
| JavaScript | `pipe` (Ramda, fp-ts) | `compose` (Ramda) | `fp-ts/Option` | `fp-ts/Either` | Ramda, Lodash/FP |
| TypeScript | `pipe` (fp-ts) | `flow` (fp-ts) | `fp-ts/Option` | `fp-ts/Either` | fp-ts, Effect-TS |
| Haskell | `&` | `.` | `Maybe` (built-in) | `Either` (built-in) | base, lens, mtl |
| Elm | `\|>` | `>>` / `<<` | `Maybe` (built-in) | `Result` (built-in) | elm/core |
| Clojure | `->` / `->>` | `comp` | `nil` + `some->` | maps + cond | clojure.core, spec |
| F# | `\|>` | `>>` | `Option` (built-in) | `Result` (built-in) | FSharpPlus, Giraffe |
| Elixir | `\|>` | manual `fn` | `{:ok, _}` / `nil` | `{:ok, _}` / `{:error, _}` | Enum, Stream, OTP |
