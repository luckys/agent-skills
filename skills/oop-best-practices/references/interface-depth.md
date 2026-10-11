# Interface Depth and Reader Load

Use when callers coordinate too many steps, a change crosses several wrappers, or an abstraction hides little knowledge.

## Evaluate from a caller

Write one representative call and the facts its author must know: types, valid states, sequencing, failure modes, configuration, and cost. Count those facts, not implementation lines. A short signature can hide a difficult temporal protocol.

Ask what happens if the abstraction is removed. If its policy and coordination scatter across callers, it is doing useful work. If only forwarding disappears, check whether it still protects a trust boundary, dependency direction, observability, or an independently changing dependency before inlining it.

Review both the indirections a reader must follow and the mutable state they must remember. Reducing one while increasing the other may make the design worse.

## Compare designs when the boundary is costly

For a substantial interface decision, sketch a direct implementation and a design that encapsulates the policy. Compare caller complexity, ownership of invariants, error handling, testability, and cost of change. A small change rarely needs multiple designs.

Keep external contracts small while allowing cohesive internal collaborators. Interface depth does not justify merging independent domains into a large object. A port can be useful for dependency inversion or external isolation even with one production adapter; two implementations are evidence of variation, not a prerequisite.

## Verify the boundary

Test the behavior available to a caller. Keep internal test seams private. Observe state transitions through meaningful methods or queries; use adapter integration tests for persistence and transport guarantees. An interaction assertion is useful when the external effect itself is the contract, including its payload and multiplicity.

## Sources and adaptation

Adapted from Matt Pocock's `codebase-design` and pstack's `principle-minimize-reader-load`. The fixed vocabulary and two-adapter requirement are not adopted. See [third-party-notices.md](third-party-notices.md).
