# Global Resource Review

Reviewed on 2026-10-11 for Codex 0.162.1, OpenCode 1.19.0, and Antigravity CLI 1.2.14. The objective is a small, generally useful global surface with project-specific resources selected on demand.

## Global Decision

| Resource | Global decision | Reason |
|---|---|---|
| `boost` skill and one client-adapted agent | Keep | Discover and select project resources without assuming a stack or process. |
| `flow` skill | Keep | Route the current phase through proportionate evidence; serve software, research, analysis, and other deliverables. |
| Official `find-skills` helper | Keep | Requested discovery companion, downloaded from `vercel-labs/skills` and globally exposed through a symbolic link. |
| Separate global discovery, context, planning, interview, implementation, and handoff skills | Retire to library | Useful capabilities, but their overlapping catalogs and prescribed workflows are unnecessary globally. Load fuller guidance when a project needs it. |
| Framework, language, architecture, testing, browser, and dependency-tool skills | Retire to library | Selection depends on observed project technologies, contracts, and current work. |
| Stack-specific coding and review agents | Retire to library | Their prompts assume technologies, absolute personal rule paths, and specialist delegation. Keep available for compatible projects. |
| Feature, bugfix, refactor, review, and release commands | Retire to library | They impose review/delegation/commit flows that should be project decisions. |
| Native Codex system and installed plugin resources | Preserve | Client-managed capabilities have a separate lifecycle. Removing manually installed globals does not disable artifact plugins or platform tools. |

The current manually managed global set has three skills: `boost`, `flow`, and the explicitly requested upstream `find-skills` discovery helper. Setup has a precise trigger; recurring work can use the lifecycle coordinator; discovery reuses the official helper. Specialized skills are selected for the project's detected technologies and versions.

## Local Inventory

The migration retires 39 skill directories, 12 Claude aliases, the global directory links exposing seven OpenCode agent profiles and five commands, and the previous skills CLI lock file. It does not delete their contents. The OpenCode files remain in `~/Software/ai-config-files`; only their global directory aliases move into the archive. No project symlinks pointing into the old global skill directory were found in the inspected `~/Projects` and `~/Software` trees.

| Retired skill group | Names |
|---|---|
| General process and discovery | `context-engineering`, `find-skills`, `idea-refine`, `incremental-implementation`, `interview-me`, `planning-and-task-breakdown`, `skill-creator`, `source-driven-development`, `spec-driven-development` |
| Design, architecture, and code evolution | `api-and-interface-design`, `code-simplification`, `ddd-best-practices`, `design-patterns-best-practices`, `fp-best-practices`, `improve-codebase-architecture`, `infrastructure-design`, `oop-best-practices`, `refactoring-best-practices`, `rest-api-best-practices` |
| Testing and performance | `performance-optimization`, `tdd`, `tdd-best-practices`, `vitest` |
| UI, frameworks, and tools | `agent-browser`, `frontend-design`, `frontend-ui-engineering`, `migrate-oxlint`, `nestjs-best-practices`, `next-best-practices`, `nuxt`, `nuxt-modules`, `nuxt-ui`, `pnpm`, `react-components`, `vercel-composition-patterns`, `vercel-react-best-practices`, `vue`, `vue-best-practices`, `vueuse` |

The `react-components` directory declares the nonportable name `react:components`; the selector flags it for adaptation instead of silently installing it. The personal repository's eight design skills take preference over their older installed copies when applicable.

Retired OpenCode agents: `backend-coder`, `frontend-coder`, `code-reviewer`, `debugger`, `devops-engineer`, `qa-engineer`, and `security-analyst`. Retired commands: `feature`, `bugfix`, `refactor`, `review`, and `release-check`. Their referenced personal rules exist in `~/Software/ai-config-files`; project selection must check those dependencies rather than treating the profiles as standalone.

## Requested Upstream Sources

The repository inventories and selected lifecycle instructions were inspected. This is a compatibility and scope review, not a full behavioral evaluation of every upstream skill.

| Source and pinned revision | Inventory | Useful project candidates and global conclusion |
|---|---|---|
| [Matt Pocock](https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336) `49dd158d1076134a641b33efb035946536778336` | 38 skill files | Requirements/planning, architecture, TDD, diagnosis, review, and handoff. `implement` assumes TDD and commits; `code-review` assumes tracker context and delegation. Keep selected ideas in the generic lifecycle; install fuller workflows only for suitable projects. |
| [Addy Osmani](https://github.com/addyosmani/agent-skills/tree/1be8e34187e34647bb83adc3a1323b26ae6f6abe) `1be8e34187e34647bb83adc3a1323b26ae6f6abe` | 25 skills, four agent profiles, nine root TOML commands | Strong coverage of research, specs, implementation, review, release, observability, and migration. Separate phases are good project candidates. The profiles and command wrappers require client-specific adaptation. |
| [pstack](https://github.com/cursor/plugins/tree/11713c683fe4add4fd403ea880580abbc9e0875f/pstack) `11713c683fe4add4fd403ea880580abbc9e0875f` | 52 skills and two agent profiles | Outcome orientation, verifiable units, and context discipline fit the small global lifecycle. Larger orchestration assumes Cursor behavior, companion skills, and stylistic rules; keep it opt-in. |
| [skills.sh](https://www.skills.sh/) | Search index, not a single portable package | Search for the actual need, identify the originating repository, pin it, read its contents and dependencies, and then select. Install counts are not a compatibility or quality verdict. |

Matt's `agents/openai.yaml` files are skill interface metadata, not native custom-agent profiles. GitHub Actions files are repository CI, not agent workflows. Addy's root TOML commands and `.claude/commands` wrappers represent the same operations; avoid installing both. Addy's four profiles are code reviewer, security auditor, test engineer, and web performance auditor. They are specialized roles, not a minimal global set.

pstack's `comment-sicko` imposes an aggressive comment-deletion policy and companion `/how` and `/why` skills. `poteto-agent` depends on the complete `poteto-mode` and principle tree and Cursor routing. Neither is a generally appropriate global agent for the three requested CLIs.

A live `skills find "software lifecycle"` query also returned broader knowledge-pack and orchestration candidates. No extra global bundle was installed from those results: its contents and client dependencies must be reviewed for the actual project. The search integration is verified, while these additional search hits are not endorsed.

## Lifecycle Coverage

| Phase | Global baseline | Potential project specialization |
|---|---|---|
| Discovery and research | Outcome, uncertainty, evidence, primary sources | Interview, idea refinement, source-driven development, domain research |
| Definition and design | Scope, acceptance criteria, existing contracts | PRD/specs, API design, architecture, DDD, FP/OOP |
| Planning and implementation | Ordered verifiable units, observed feedback | Detailed task breakdown, framework tooling, TDD |
| Verification and review | Meaningful checks, actual diff, confirmed findings | Test-runner skills, security, accessibility, browser and performance audits |
| Delivery and operation | Authorized artifact, recovery, observable results | Shipping, CI/CD, infrastructure, instrumentation, incident response |
| Migration, retirement, and handoff | Consumers, compatibility, restartability, durable state | Data migration, deprecation, formal release and handoff workflows |
| Other processes | Artifact-appropriate evidence and delivery checks | Research, document, spreadsheet, presentation, and other domain resources |

The baseline coordinates work; specialized validation still belongs to the project or artifact tool. It does not claim to replace a security audit, production runbook, or native document renderer.

## Client Compatibility

`.agents/skills` is the shared project skill path. Global skill and native agent paths differ; small symlink adapters preserve each client's actual format. See the [client path table and official references](../skills/boost/references/clients.md).

OpenCode uses primary-agent Markdown and a native command wrapper. Codex uses a TOML custom agent. Antigravity uses an ADL Markdown agent and its CLI skill path. No adapter overrides models, tool permissions, sandbox settings, MCP configuration, or credentials. Legacy Antigravity workflows are replaced by skills rather than introducing a new global workflow directory.

## Verification Record

- All 42 local behavior tests passed, covering source subdirectories, short-name migration, official CLI installation, symbolic links, rollback, content drift, frontend coverage, language/toolchain/resolved-version inventory, personal-source priority, owner-scoped discovery, and the absence of local-catalog fallbacks.
- Both new skill packages passed Codex's skill-creator structural validator.
- Codex `skills/list` discovered both shared globals with user scope and no errors; its system/plugin resources remain separately available.
- The initial OpenCode 1 review used `--pure debug skill` and `--pure agent list` with the original long names. On 2026-10-13, OpenCode had upgraded to 2.0.27: `debug agents` discovered `boost`, and its interactive slash menu displayed both `/boost` and `/flow`. Only menu text was entered; no model prompt was submitted. Do not reuse the V1 debug commands with V2.
- Antigravity `agy agent` discovered `boost` after the rename; its CLI skill bridge resolves to the same two shared skills. There is no separate skill-list subcommand in the installed CLI, so skill-path compatibility is based on its official documentation and filesystem verification.
- skills.sh search returned live results. The fetch helper downloaded Matt Pocock's source into the pinned cache without changing the main source registry.
- A temporary Express fixture installed the actual personal REST skill, passed `doctor`, and removed its owned link successfully. Preview created no project files.
- The live global restore preflight passed. The archive records 54 retired filesystem entries: 39 skills, 12 Claude aliases, two OpenCode directory aliases, and the old lock file.
- The resulting catalog contained 248 candidates across the six registered sources. Three skill packages were flagged for invalid portable metadata instead of being installed silently: pstack's `make-bot-ui` and `poteto-mode`, and the retired `react-components` package.

No model turn was started for these native discovery checks. Resource-selection quality, custom-agent behavior during an actual model turn, and every upstream dependency have not been benchmarked. Project bootstrap must review the actual selected contents each time rather than treating this inventory as blanket approval.

## Official Source Installation Update

Boost now follows the requested stack-analysis workflow: inspect languages, frameworks, libraries, and versions; use global find-skills and the official repositories/skills.sh to discover the best fitting skills; download through `pnpx skills add`; and link those upstream packages into the project. The earlier local personal working-copy installation path is no longer used for portable skills.

Discovery uses skills.sh as its single index and checks the user's `luckys/agent-skills` catalog first. A live owner-scoped OOP search returned `luckys/agent-skills@oop-best-practices`. A compatible personal skill takes precedence over an equivalent community skill regardless of popularity; other sources address actual gaps or incompatibilities. Prepare now initializes only the official personal source, and shortlisted external repositories are fetched afterward for reading. It does not load or compare the local personal catalog.

Actual remote integration checks used temporary Vue/TypeScript and React/TypeScript projects. The Vue fixture downloaded `oop-best-practices` from `luckys/agent-skills` and `frontend-design` from `anthropics/skills`; the React fixture downloaded `frontend-design`. Both fixtures had symbolic project links pointing into the upstream download store, passed doctor, reused their links on a second run, and removed only their owned links successfully. These checks exercise the real official CLI; they do not benchmark an autonomous model's selection judgment.

The global find-skills package was downloaded with `pnpx skills add vercel-labs/skills --skill find-skills --global --agent codex opencode --yes --json`, verified against its official source, and exposed through a managed symlink. The original global restoration manifest was updated to track this helper and the CLI lock change; its preflight still passes.

The OpenCode 2 interface also reported startup failures in three pre-existing plugins: `opencode-background-agents`, `opencode-pty`, and `opencode-plugin-goal`. The short commands appeared in the menu despite those failures. Updating those plugins is a separate compatibility task; this change does not modify their configuration or credentials.
