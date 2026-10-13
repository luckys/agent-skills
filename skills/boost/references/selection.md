# Resource Selection

Search by observed needs. A package manifest can prove the presence of a framework; directory names alone cannot prove DDD, a deployment target, or a requirement for a testing tool. For monorepos, inspect the relevant package manifests instead of applying the root stack to every package. For an empty project, use the requested purpose and ask only about consequential missing choices.

Prefer the upstream `luckys/agent-skills` skills for OOP, DDD, FP, patterns, refactoring, REST, and TDD when they fit. Add only the relevant subset. For example, a simple documentation edit does not need a domain-modeling skill. An installed test runner is evidence for its tooling skill; future plans are not. Use skills.sh to discover complementary capabilities outside the personal repository, not only alternatives to its existing names.

Use skills.sh as the single discovery index, including the user's catalog at `https://www.skills.sh/luckys/agent-skills`. Search it first with `pnpx skills find <topic> --owner luckys` and retain that repository's results. Do not compare the local personal working copy. Select a compatible personal skill before a community equivalent even when its popularity is lower; an external alternative needs a concrete gap or version/scope incompatibility. Fetch originating repositories only to read shortlisted instructions and install their official packages.

Web UI projects should include a personal design skill when available and suitable, otherwise `anthropics/skills` → `frontend-design`, alongside an appropriate framework skill. React/Vue dependencies, peer dependencies, and component/HTML files are detected by inspect. Record a specific `omissions.frontend-design` reason for an explicit user exclusion, a backend-only scope, an equivalent personal design skill with a different name, or a framework dependency used without a user-facing interface. The installer rejects silent omission; it never adds an unreviewed design skill automatically.

A lifecycle phase can be covered by an existing skill, a reviewed upstream workflow packaged as a skill, or the concise global lifecycle reference. Do not install every phase just because the lifecycle exists. Select additional resources for recurring or currently requested work. Keep setup, research, planning, implementation, verification, review, delivery, operations, migration, and handoff available through conditional pointers.

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
      "reason": "The requested work changes an existing HTTP contract."
    }
  ],
  "notes": ["No framework was inferred from a folder name."]
}
```

The fingerprint covers supporting files, not just SKILL.md. Downloads made by `pnpx skills add` must match the reviewed fingerprint before activation; changed upstream contents require another review. The wrapper stores those official CLI downloads by repository, skill, and content hash under `~/.local/share/agent-resources/installed-skills`, then creates a symbolic link at the project's `.agents/skills/<name>`. This links upstream downloads, not the personal working directory or review checkout. `skills-lock.json` retains the official CLI's repository provenance. `.agents/resource-lock.json` additionally records versions, review, rationale, link targets, and ownership. `unlink --apply` removes owned unchanged links and their CLI records while preserving user changes and the shared downloaded packages. Another computer needs the same packages downloaded and links recreated.
