# Typed Boundaries and Practical Purity

Use when unions, brands, decoders, or a functional rewrite risk adding ceremony without improving correctness.

## Model the actual partiality

Choose a discriminated union when variants require different data, and make matching exhaustive with the language's supported mechanism. An unhandled new variant should produce a compile-time signal where possible, rather than disappear into a permissive default.

Use stronger input types where an operation cannot answer for every input. A first-element operation needs absence handling or a non-empty collection; a sum can accept an empty collection and return zero. Encode only the distinctions that prevent actual misuse.

Keep semantic identifiers distinct when mixing them would be a meaningful bug. Derive wire types from the authoritative schema when practical instead of maintaining a parallel definition. Runtime casts do not validate JSON, database rows, configuration, or third-party replies.

## Parse, then apply domain behavior

Validate external shape once at the trust boundary and translate to internal types. Domain constructors and state transitions still enforce their invariants; parsing does not prove current permissions or concurrent business state. Decoders and functions must use the same source of truth for the shape.

Use Option/Result or native equivalents where absence or failure is part of the contract. Preserve an established null/error convention when converting it would cause unrelated churn, and translate at boundaries rather than adding a new FP library solely for syntax.

## Preserve purity without obscuring the algorithm

A function can use a private mutable accumulator and remain observably pure if it neither mutates caller-owned data nor leaks the mutable state. Avoid repeated copying inside a reduce when a local loop is clearer or materially cheaper. Choose pipelines, named intermediates, or loops by comprehension and cost, not by line count.

Test the returned result with independently chosen values and include empty/boundary cases. When mutation is local, include a check that caller-owned input remains unchanged if that is part of the contract.

## Sources and adaptation

Adapted from pstack's `principle-type-system-discipline` and `principle-minimize-reader-load`, and Addy Osmani's `code-simplification`. Most ADT/purity theory already exists in this skill; this reference adds decision criteria rather than another tutorial. See [third-party-notices.md](third-party-notices.md).
