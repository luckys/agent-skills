# Domain Model Evidence

Use when terminology is ambiguous, lifecycle booleans conflict, or ownership is being reconsidered.

## Ground the language

Read the relevant glossary, context map, product rules, and accepted decisions if present. Use the project's existing locations; no filename or template is required. For a disputed term, record its meaning, the context in which it applies, and the synonyms that would confuse it with another concept.

Keep domain definitions separate from implementation choices. Different bounded contexts may legitimately use different meanings. Do not create a shared model merely because their field names match.

Compare a stated rule with the code and concrete scenarios: cancellation before payment, cancellation after settlement, replay of an old event, or a state restored from persistence. Distinguish intended policy, observed behavior, and an unresolved decision. Ask only about a real ambiguity that changes the model or contract.

## Make transitions explicit

List allowed transitions and their invariants before choosing a representation. Several flags that must change together suggest a state model, tagged union, or aggregate operation. Validate external representation at entry and reconstitution; enforce business invariants whenever behavior changes state. Static types do not prove permissions, balances, or concurrent state.

Execution order is not ownership. Organize around domain knowledge rather than separate load/validate/save models that repeat the same rule. Aggregate boundaries follow atomic consistency requirements, not table count or directory size.

## Capture decisions proportionately

Update existing language documentation when a meaning is resolved. An ADR is useful when a real trade-off is costly to reverse and surprising without its rationale. Document the decision, its reason, and material alternatives; create no empty glossary or ADR scaffolding.

## Sources and adaptation

Adapted from Matt Pocock's `domain-modeling` and pstack's `principle-model-the-domain` and `principle-boundary-discipline`. Keeps invariant enforcement and project-specific documentation conventions. See [third-party-notices.md](third-party-notices.md).
