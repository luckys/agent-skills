# Software Lifecycle Decisions

Use only the phases relevant to the requested change.

- **Requirements and design:** find the existing spec, domain vocabulary, architecture decisions, consumers, and operational constraints. Add a concise acceptance criterion where the requirement is missing. Compare alternatives when an interface or migration is costly to reverse; routine changes need no design ceremony.
- **Implementation:** work in thin behavior slices using the repository's conventions. When developing test-first, use Red–Green–Refactor with one behavior at a time. Documentation and mechanical low-risk changes need appropriate artifact checks rather than artificial failing tests.
- **Bug diagnosis:** reproduce the specific defect with a discriminating feedback loop before applying a fix. Use available evidence to investigate when full reproduction is unavailable and disclose what remains unproven. A build failure caused by an unrelated setup error does not reproduce a runtime defect.
- **Verification:** discover the repository's commands. Verify observable results with independently chosen expectations, and use the actual adapter for claims about persistence, isolation, or transport. Expand checks according to required gates and risk. Reuse valid evidence after review.
- **Code review:** establish the comparison range and acceptance source, then inspect correctness, regressions, contracts, and relevant security or operational effects. A read-only review preserves source files. Bring in a specialist only when needed and available; do not force parallel agents or a fixed review budget.
- **Delivery:** check rollout and recovery for the actual target environment. Consider compatibility, configuration, migrations, release metadata, and meaningful failure signals. Do not turn a review into deployment or automatically commit because an upstream workflow does so.
- **Operation and incidents:** define what working means and gather logs, metrics, traces, or user-visible evidence that answer the actual failure question. Keep sensitive values out of diagnostics. Separate incident containment from a broader redesign.
- **Migration and retirement:** coordinated internal callers can migrate together; independently deployed consumers require compatible stages. For persisted data, use an appropriate expansion/backfill/contraction sequence with restart and recovery evidence. A code revert is not a data rollback.
- **Handoff:** persist accepted scope, decisions, next task, changes, verification commands/results, and unresolved issues using existing project artifacts. State whether work is committed. A fresh session must check actual repository state before continuing.

Detailed specialist skills are selected locally by boost. Coverage of the lifecycle does not require every specialist skill to be globally discoverable.

Selectively adapted from the reviewed Matt Pocock, Addy Osmani, and pstack workflows. Source revisions and MIT notices are in [third-party-notices.md](third-party-notices.md).
