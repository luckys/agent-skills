# Comparative Skill Review

Review date: October 11, 2026.

This repository provides greater subject depth in DDD, OOP, patterns, and FP than the selected external skills. The other repositories offer stronger instructions for some operational decisions: evaluating an interface from the caller's perspective, demonstrating a defect, migrating consumers and data, or recovering from an uncertain remote outcome. The changes combine those contributions with this repository's conditional reference structure.

This conclusion assesses content and organization. It does not establish that an agent produces better results with one collection than another.

## Scope and Provenance

The eight existing skills and the local references relevant to each overlap were reviewed. The three upstream repositories contained 38, 25, and 52 `SKILL.md` files for Matt Pocock, Addy Osmani, and pstack, respectively. The 23 external files used for adaptations and four additional files used to compare organization and workflows were read in detail. The inventory does not imply an exhaustive review of the bodies of all 115 external skills.

`skills.sh` was used as a directory; the repositories supplied the content. The conclusions apply to these revisions, not future versions:

| Source | Reviewed Revision |
|---|---|
| [Matt Pocock](https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336) | `49dd158d1076134a641b33efb035946536778336` |
| [Addy Osmani](https://github.com/addyosmani/agent-skills/tree/1be8e34187e34647bb83adc3a1323b26ae6f6abe) | `1be8e34187e34647bb83adc3a1323b26ae6f6abe` |
| [Cursor pstack](https://github.com/cursor/plugins/tree/11713c683fe4add4fd403ea880580abbc9e0875f/pstack/skills) | `11713c683fe4add4fd403ea880580abbc9e0875f` |

The [source manifest](upstream-review-sources.json) records paths, SHA-256 hashes, revisions, and mappings for each skill. Each skill folder includes the required attribution and MIT notices so they accompany an individual installation. No code from the external repositories was executed.

## Overlaps and Applied Changes

The overlaps are partial: the selected sources do not replace the full GoF/PoEAA catalog, strategic and tactical DDD coverage, or language-specific FP references.

| Existing Skill | Selected Upstream Contribution | Applied Improvement |
|---|---|---|
| `oop-best-practices` | Matt: `codebase-design`; pstack: `principle-minimize-reader-load` | [Interface depth](../skills/oop-best-practices/references/interface-depth.md): caller knowledge, the deletion test, and the cost of indirection and state. Retains justified ports with a single adapter. |
| `design-patterns-best-practices` | Matt: `codebase-design`; Addy: `code-simplification`; pstack: `principle-model-the-domain` | [Evidence for pattern fit](../skills/design-patterns-best-practices/references/pattern-fit-evidence.md): actual change pressure, a representative caller, and comparison with a direct solution before adding a pattern. |
| `ddd-best-practices` | Matt: `domain-modeling`; pstack: domain modeling and boundary discipline | [Model evidence](../skills/ddd-best-practices/references/model-evidence.md): vocabulary per context, rules checked against scenarios, explicit transitions, and proportionate decision records. |
| `refactoring-best-practices` | Matt: `DEEPENING.md`; Addy: simplification and migration; pstack: `blast-radius` and caller migration | [Compatibility and migration](../skills/refactoring-best-practices/references/compatibility-and-migration.md): distinguish coordinated internal changes from public contracts; expand, backfill in restartable batches, and contract; plan data recovery. |
| `fp-best-practices` | Addy: simplification; pstack: type discipline and reader load | [Typed boundaries](../skills/fp-best-practices/references/typed-boundaries.md): exhaustiveness, actual partiality, validation of external representations, and private accumulators compatible with observable purity. |
| `infrastructure-design` | Addy: interfaces and migration; pstack: idempotency and state separation | [Retries and concurrency](../skills/infrastructure-design/references/retry-and-concurrency.md): stable operation identity, atomic claims, outbox records in the same transaction, crash windows, and reconciliation of unknown outcomes. |
| `rest-api-best-practices` | Addy: interfaces and migration; pstack: idempotency and caller migration | [Retry contracts](../skills/rest-api-best-practices/references/retry-contracts.md): bind key, actor, and request; authorize replays; define in-flight requests, expiry, and observable compatibility. |
| `tdd-best-practices` | All three TDD proposals; pstack: behavior testing and evidence | [Feedback and evidence](../skills/tdd-best-practices/references/behavioral-feedback.md): discover the project's commands, implement behavior slices, use independent expected values, and reproduce a defect before fixing it. |

The eight names are retained and their versions updated to `1.1.0`. The new references have specific loading conditions. Descriptions decrease from 3,401 to 2,265 characters in total, a 33.4% reduction. This measures those fields' character counts, not session tokens or activation accuracy.

## Which Approaches to Retain

**This repository:** separating entry points from references suits a broad knowledge library. Its coverage by language and pattern addresses details that the workflow repositories do not develop. Its weakness was that some general recommendations needed selection criteria and evidence examples to prevent applying a technique merely out of habit.

**Matt Pocock:** adopt caller-first analysis and interfaces that hide knowledge, rather than measuring quality by class or line counts. His [writing guide for agents](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/productivity/writing-for-agents/SKILL.md) explains how access conditions determine which information is consulted. This repository already uses that approach; descriptions have been shortened and precise conditions added. Reorganizing the entire collection around his vocabulary is unnecessary.

**Addy Osmani:** his interface, TDD, and migration skills include more concrete operational checks in the adapted areas. These checks are useful without turning a small improvement into a complete product lifecycle. His [meta-skill](https://github.com/addyosmani/agent-skills/blob/1be8e34187e34647bb83adc3a1323b26ae6f6abe/skills/using-agent-skills/SKILL.md) can chain several workflows; this specialized library requires fewer preliminary steps for a specific technical question. Some selected files mix processes, examples, and tools that belong outside this repository's entry points.

**pstack:** its short principles provide useful review questions about states, types, repetition, and consumers. Its larger workflows depend on other skills, Cursor rules, and model runners, as shown in [architect](https://github.com/cursor/plugins/blob/11713c683fe4add4fd403ea880580abbc9e0875f/pstack/skills/architect/SKILL.md). That organization was not transferred to skills intended for Codex, antigravity-cli, and OpenCode. The technical principles are retained with an adjusted scope.

## Filtered Rules

- Matt's TDD requires agreeing every test boundary with the user in advance. Normal test placement remains autonomous; clarification is reserved for consequential contract ambiguity. His two-adapter criterion does not replace a port's justification through isolation or dependency direction. See [TDD](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/engineering/tdd/SKILL.md) and [deepening](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/engineering/codebase-design/DEEPENING.md).
- The approximate test distribution and browser tools in [Addy's TDD](https://github.com/addyosmani/agent-skills/blob/1be8e34187e34647bb83adc3a1323b26ae6f6abe/skills/test-driven-development/SKILL.md) do not become quotas or dependencies. Risk, project commands, and required checks govern verification.
- [pstack's removal of legacy APIs](https://github.com/cursor/plugins/blob/11713c683fe4add4fd403ea880580abbc9e0875f/pstack/skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) applies to controlled consumers. Public or independently deployed consumers require a compatible migration. An added field or enum value can also break strict readers.
- [pstack's idempotency guidance](https://github.com/cursor/plugins/blob/11713c683fe4add4fd403ea880580abbc9e0875f/pstack/skills/principle-make-operations-idempotent/SKILL.md) is supplemented with actual storage and provider guarantees. A local PID does not establish distributed exclusion, and a timeout does not establish that a payment failed.
- Recommendations to delete internal tests are conditional on preserving useful evidence. A test that fails after a refactor can reveal a real regression. Red–Green–Refactor and real-adapter verification of persistence or transport guarantees are retained.

## Local Contradictions Corrected

1. **REST:** the absolute ban on verbs contradicted the cancellation example. HTTP operation names such as `/getUsers` are distinguished from domain tasks such as `/orders/{id}/cancel`.
2. **DDD:** table count no longer determines aggregate boundaries; invariant consistency does.
3. **FP:** observable mutation is distinguished from a private accumulator. A loop can preserve purity and avoid unnecessary copying.
4. **TDD:** a failing test requires investigation of behavior and setup before attributing the failure to implementation coupling.
5. **Infrastructure:** the outbox example receives the transaction shared with the aggregate instead of opening another. A reliable broker alone does not make a write and publication atomic. Durability is distinguished from asynchronous delivery, and sensitive payload logging is restricted.

## Validation and Limitations

All eight skills pass the `skill-creator` frontmatter validator. Checks cover 117 local reference paths and 145 source hashes, the eight per-skill notices, and preservation of the original `LICENSE`. `git diff --check` passes and new files contain no trailing whitespace. Code examples and illustrative paths that are not links are excluded from link analysis.

The static consistency review uses scenarios such as a payment timeout, external consumers during migration, an aggregate persisted across several tables, a private accumulator, and a test failing after a refactor.

These checks are structural and constitute a static review of instructions. No comparative benchmarks or activation and outcome trials were run in Codex, antigravity-cli, and OpenCode; the documented outbox fragment was not tested against PostgreSQL. Further optimization should be informed by representative tasks with and without these references, measuring outcome quality, activation, and context cost.

The changes are limited to existing skills, the README, repository guidance, and this documentation. They do not install new skills or change global configuration. External areas without a local counterpart remain outside this first overlap review. Repository prose and quoted guidance are written in English.
