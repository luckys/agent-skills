# Resource Selection

Search by observed needs. A package manifest can prove the presence of a framework; directory names alone cannot prove DDD, a deployment target, or a requirement for a testing tool. For monorepos, inspect the relevant package manifests instead of applying the root stack to every package. For an empty project, use the requested purpose and ask only about consequential missing choices.

Bootstrap covers the project, not just the next coding task. Review all direct dependencies, languages and runtime versions; distinguish core tools from incidental helpers and unused packages. The inspector provides `capabilities` and `unmapped_dependencies` as discovery hints. Read remaining manifests (including non-Node ecosystems) and representative code yourself; this inventory is not a universal technology detector. Add relevant missing capabilities through `additional_capabilities` with evidence. Installed test runners need tooling coverage as well as testing methodology. Explicit planned tools and architecture need skills compatible with the target, with current and target guidance clearly separated.

Prefer upstream `luckys/agent-skills` for OOP, DDD, FP, patterns, refactoring, REST, infrastructure and TDD when code or documented intent supports them. A folder called `domain` alone is insufficient; inspect aggregates, value objects, ports, invariants and dependency direction. Do not force DDD on every TypeScript project. Do not defer an evidenced capability to keep the list small or because no product change was requested. Cover every relevant capability with reviewed skills, retained verified skills, or a concrete omission such as an incompatible release, unused dependency, explicit scope exclusion or no suitable candidate after a documented search. A generic TDD skill does not replace Vitest API/configuration guidance; a Nuxt skill does not automatically cover Tailwind, Drizzle or Better Auth.

## Full lifecycle assessment

Review all twelve areas and record evidence, current state, intended state, skills and gaps:

| Area | Evidence and selection questions |
| --- | --- |
| Requirements | User stories, PRDs, constraints, acceptance criteria, research and planning conventions |
| Architecture | Current boundaries and patterns, desired architecture, ADRs, domain model, integration contracts |
| Implementation | Languages, framework/library versions, runtime, package manager, API and UI design |
| Testing | Unit, component, integration, contract, browser, database, performance and accessibility gates |
| Security | Authentication, authorization, privacy, secrets, dependency/supply-chain checks, threat model |
| CI | Pipeline provider, pinned actions, quality gates, artifacts and credentials |
| Deployment | Production target/provider, runtime constraints, container/serverless/edge, IaC, release and rollback |
| Observability | Logging, metrics, traces, health checks, alerts, SLOs and sensitive-data redaction |
| Operations | Backups/restore, incident handling, runbooks, scaling, reliability and disaster recovery |
| Maintenance | Reviews, refactoring, dependency upgrades, compatibility and technical debt |
| Migrations | Schema/data/API evolution, safe rollout, reconciliation and rollback constraints |
| Documentation | ADRs, onboarding, API docs, operations guides and handoff |

Inspect `.github/workflows`, other CI files, Docker/Compose, IaC, provider configuration and operational docs. Distinguish local services from production deployment. Treat roadmap examples as proposals, not chosen providers. When the target is unknown, record the unresolved choice and cover generic release/operations needs where useful; do not install provider-specific skills speculatively. Observability without a chosen vendor can use portable instrumentation guidance. A documented desired architecture is valid selection evidence even before its code exists. Ask asynchronously about a consequential unknown while continuing independent coverage.

## Popularity and quality

After semantic/version compatibility and personal precedence, compare source authority, maintenance, useful non-overlapping coverage, skills.sh installs, repository stars and available downloads. Prefer the better supported candidate among compatible alternatives; popularity is evidence of adoption, not correctness. No minimum count excludes personal skills. Record the displayed value when rounded (for example `40.4K`), metric source URL and observation timestamp; do not present it as an exact integer. `installs` and `downloads` are different metrics. Mark unpublished or inaccessible metrics unknown with a reason; do not invent zeroes. Read candidate contents before choosing a popular result: a Vitest 5 skill does not fully cover a Vitest 4 project merely because its search ranking is high.


Use skills.sh as the single discovery index, including the user's catalog at `https://www.skills.sh/luckys/agent-skills`. Search it first with `pnpx skills find <topic> --owner luckys` and retain that repository's results. Do not compare the local personal working copy. Select a compatible personal skill before a community equivalent even when its popularity is lower; an external alternative needs a concrete gap or version/scope incompatibility. Fetch originating repositories only to read shortlisted instructions and install their official packages.

Web UI projects should include a personal design skill when available and suitable, otherwise `anthropics/skills` → `frontend-design`, alongside an appropriate framework skill. React/Vue dependencies, peer dependencies, and component/HTML files are detected by inspect. Record a specific `omissions.frontend-design` reason for an explicit user exclusion, a backend-only scope, an equivalent personal design skill with a different name, or a framework dependency used without a user-facing interface. The installer rejects silent omission; it never adds an unreviewed design skill automatically.

A lifecycle area can use several reviewed skills, and one skill can cover several areas. Global `flow` coordinates lifecycle phases; it does not replace specialist CI, deployment, instrumentation or migration guidance. Assess every area even when no dedicated skill is necessary. Use `unknown` for an unresolved decision, `gap` when a suitable skill cannot be found, or `not-applicable` with evidence. These statuses are visible in the setup report and must not be reported as complete specialist coverage.

Inspect required sibling resources and external skill names. Matt's `implement` assumes TDD and commits; `code-review` assumes configured issue-tracker context and parallel agents. pstack orchestration can assume Cursor-specific rules, runners, and companion skills. Addy's agent profiles use Claude-specific tool names. Choose a portable equivalent or explicitly adapt the instructions and preserve the original attribution before installation. Do not make an incompatible profile appear portable by ignoring its permissions or dependencies.

Portable skills use `install` and the official `pnpx skills add` CLI. Cached checkouts are for reading and fingerprinting only. Native profiles and workflows use a separate native-only selection and `link`; those formats are not supported by the skills installer. Raw reference workflows are manually read under `.agents/workflows`, not advertised as native commands. Unsupported Claude/Gemini formats require adaptation first.

Selection example:

```json
{
  "clients": ["codex", "opencode", "antigravity"],
  "resources": [
    {
      "id": "personal:skill:rest-api-best-practices",
      "reviewed_sha256": "COPY_THE_EXACT_CATALOG_FINGERPRINT",
      "reason": "Existing HTTP contracts need REST design guidance.",
      "discovery": {
        "url": "https://skills.sh/luckys/agent-skills/rest-api-best-practices",
        "observed_at": "COPY_THE_ACTUAL_UTC_OBSERVATION_TIME",
        "installs_display": null,
        "stars_display": null,
        "downloads": null,
        "metrics_reason": "Replace unknown metrics with verified published values where available.",
        "comparison": "Personal compatible coverage takes precedence over equivalent community skills."
      }
    }
  ],
  "additional_capabilities": {"rest-api": "Existing server/api routes expose HTTP contracts."},
  "coverage": {
    "rest-api": {
      "resources": ["personal:skill:rest-api-best-practices"],
      "reason": "Portable HTTP contract guidance fits the existing routes."
    }
  },
  "notes": ["Extend this example with all detected capabilities and twelve lifecycle assessments."]
}
```

For each inspector capability and each `additional_capabilities` entry, provide `coverage.<capability>` with resource IDs and a scope/version rationale, or `omissions.<capability>` with a concrete reason. Include `lifecycle.<area>` for every table row with `status`, `reason`, optional `current`, `target`, `evidence`, and `resources`. The installer verifies these entries before downloading. IDs may refer to retained skills only when link targets and content fingerprints still match; include their compatibility rationale. Preserve earlier notes when extending a setup, but replace outdated omissions and assessments. The installer validates declared coverage and integrity; the agent remains responsible for semantic review.

The fingerprint covers supporting files, not just SKILL.md. Downloads made by `pnpx skills add` must match the reviewed fingerprint before activation; changed upstream contents require another review. The wrapper stores those official CLI downloads by repository, skill, and content hash under `~/.local/share/agent-resources/installed-skills`, then creates a symbolic link at the project's `.agents/skills/<name>`. This links upstream downloads, not the personal working directory or review checkout. `skills-lock.json` retains the official CLI's repository provenance. `.agents/resource-lock.json` additionally records versions, review, rationale, link targets, and ownership. `unlink --apply` removes owned unchanged links and their CLI records while preserving user changes and the shared downloaded packages. Another computer needs the same packages downloaded and links recreated.
