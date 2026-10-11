# Evidence for Pattern Fit

Use when a pattern adds indirection, its variation is hypothetical, or several approaches could satisfy a public contract.

1. Describe the current change pressure and show a representative caller before selecting a pattern.
2. Compare the simplest direct solution with the proposed collaboration. For a costly boundary, consider another structurally different design.
3. Identify the knowledge each design centralizes, the facts callers must learn, and the changes it localizes. More classes or fewer lines are not proof of improvement.
4. Explain why any new seam is needed now: independently changing policy, external isolation, invariant ownership, substitution, or testability. A fixed number of implementations is not the decision rule.
5. Preserve the contract and verify the resulting behavior. A wrapper that only renames methods may still protect dependency direction; examine its role before removal.

Choose structures that remove invalid combinations or repeated rules. A state machine, union, or table can be simpler than a hierarchy for closed variants; a Strategy can fit genuinely interchangeable policies. Neither representation is mandatory.

For a significant choice, record the actual trade-off using the project's decision-document convention. Ordinary pattern choices do not need a new ADR or a design ceremony.

## Sources and adaptation

Adapted from Matt Pocock's `codebase-design`, Addy Osmani's `code-simplification`, and pstack's `principle-model-the-domain`. Retains this skill's problem-first pattern selection. See [third-party-notices.md](third-party-notices.md).
