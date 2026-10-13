---
name: flow
description: Use when organizing a multi-step task, choosing the next lifecycle phase, checking delivery readiness, or handing work to another session. Routes software and other deliverables through proportionate evidence and verification without requiring a particular stack or a complete process for every task.
license: MIT
metadata:
  author: luckys
  version: "1.0.0"
---

# Flow

Identify the requested outcome, the current phase, and what would demonstrate completion. Enter at that phase rather than restarting discovery. Use project-local instructions and resources; run `boost` only when the resource setup itself needs work.

When explicitly invoked without additional instructions, recover the latest authorized task from the conversation and project artifacts, check the actual working state, and complete the next coherent unit through verification. If no intended task can be established, ask for the desired outcome. Additional instructions select the task or phase; they do not authorize unrelated external actions.

| Need | Next action and evidence |
|---|---|
| Discover or research | Resolve consequential uncertainty with actual artifacts or primary sources; distinguish evidence from assumptions. |
| Define | Record the outcome, audience, scope, and checkable acceptance criteria at the project's existing location. |
| Plan | Order dependent work in small verifiable units. Scale the plan to the task and preserve the user's constraints. |
| Execute | Complete one coherent unit, observe its result, and adjust based on evidence. Preserve unrelated work. |
| Verify | Use checks that can distinguish a plausible wrong result. Choose the required evidence for the artifact and risk. |
| Review | Compare the actual result with the requested scope and existing conventions. Separate confirmed defects from suggestions. |
| Deliver | Produce the authorized final artifact and record material limits. Publication, commits, and external actions require the applicable authorization. |
| Operate or maintain | Observe the declared success/failure signals; diagnose deviations and make scoped corrections. |
| Migrate or retire | Identify consumers, preserve required compatibility, and plan recovery before removing an old path. |
| Resume or hand off | Record durable decisions, artifact paths, working state, verification results, unresolved questions, and the next action. |

For implementation, bugs, release readiness, operations, or persisted-data migration, read `references/software.md`. For documents, analysis, research, or other deliverables, read `references/other-work.md`. Do not load both branches automatically.

Reuse successful checks while their evidence remains valid. Investigate a new failure rather than weakening the criterion. Report a limitation when the required check cannot run. Routine reversible decisions stay autonomous; ask about an ambiguity only when it changes a consequential outcome or authorization.

At a session boundary, link to existing specs and artifacts instead of duplicating them. Keep summaries concise and redact sensitive data. This skill coordinates phases; it does not impose a language, framework, architecture, test percentage, issue tracker, model roster, or mandatory delegation.
