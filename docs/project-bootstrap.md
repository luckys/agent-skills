# Boost: Analyze, Find, and Install Project Skills

Boost analyzes the project's stack, current and desired architecture, CI, deployment, observability and complete delivery lifecycle. It searches skills.sh, prioritizes compatible personal skills, reviews official upstream contents and adoption metrics, and installs complete relevant coverage as symbolic links. Run it from a fresh client session in the project directory:

| Client | Set up skills | Resume or organize work |
|---|---|---|
| Codex | `$boost` | `$flow` |
| OpenCode | `/boost` | `/flow` |
| Antigravity CLI | `/boost` | `/flow` |

A bare boost invocation authorizes the complete project setup. Optional text can refine it, for example `/boost preview only` or `/boost focus on frontend development`. Codex uses the `$` skill prefix rather than the deprecated custom slash-prompt mechanism. No additional product brief is required when the repository already exposes its stack.

## What Boost Does

1. Read project instructions, manifests, lockfiles, toolchain configuration, and representative source files. Distinguish declared version ranges from resolved versions and keep monorepo packages separate.
2. Use skills.sh as the single discovery index with the global upstream `find-skills` helper. Search the user's `luckys/agent-skills` catalog first, including owner-scoped CLI searches. No local personal working-copy comparison is needed.
3. Read candidate instructions and select by actual stack/version compatibility, required dependencies, and overlap. A suitable personal skill takes precedence over an equivalent community skill regardless of popularity. Search wider skills.sh results for gaps or incompatible personal candidates. Framework engineering and visual design are separate capabilities: prefer a suitable personal design skill, otherwise add Anthropic's `frontend-design` for user-facing web interfaces.
4. Download selected skills through the official CLI, using commands such as:

```bash
pnpx skills add luckys/agent-skills --skill oop-best-practices
pnpx skills add anthropics/skills --skill frontend-design
```

5. Create project symbolic links, check them, and report the detected stack and installed skills. The default command configures skills; application development continues through the regular agent or flow.

The wrapper adds explicit agent selection and noninteractive flags, uses staging to avoid partial project changes, and verifies downloaded content against the reviewed package. It never installs a skill from the personal working directory as a fallback. Preview does not download or change project resources.

## Global Resources and Storage

The manually managed global resources are `boost`, `flow`, and the upstream `find-skills` helper. The latter is installed from `vercel-labs/skills` through `pnpx skills add` and exposed globally through a symbolic link. Native system and plugin resources remain managed by their clients.

Review checkouts and source catalogs live outside discovery in `~/.local/share/agent-resources/`, or `$XDG_DATA_HOME/agent-resources` when configured. `prepare` initializes `remote-sources.json` with only the current official `luckys/agent-skills` source, ranked first. Additional shortlisted repositories are fetched after discovery through skills.sh. The original `~/.agents/resource-sources.json` preserves retired/native resources for explicit advanced use; it is not read by Boost's skill discovery or compared with the personal remote catalog.

Official CLI downloads are stored by repository, name, and fingerprint in `installed-skills/`. A project receives links such as:

```text
project/.agents/skills/frontend-design
  -> ~/.local/share/agent-resources/installed-skills/anthropics--skills/frontend-design/<content-hash>
```

`skills-lock.json` records official upstream provenance. `.agents/resource-lock.json` records Boost's review, source revision, rationale, target paths, and ownership. The three CLIs read the shared project directory. Links require this workstation's downloaded library; reproduce downloads and links on another machine rather than assuming absolute paths work in CI.

## Advanced Commands

Python 3.10 or newer, PyYAML, Git, Node.js, and pnpm/pnpx are required. Project manifests for unsupported ecosystems are read directly by the agent; inspection output is an initial inventory, not a claim that every lockfile format is parsed.

```bash
python3 -B ~/.agents/skills/boost/scripts/resources.py inspect --project "$PWD"
python3 -B ~/.agents/skills/boost/scripts/resources.py prepare
python3 -B ~/.agents/skills/boost/scripts/resources.py catalog --query "vue"
python3 -B ~/.agents/skills/boost/scripts/resources.py search "oop" --owner luckys
python3 -B ~/.agents/skills/boost/scripts/resources.py search "vue best practices" --json
python3 -B ~/.agents/skills/boost/scripts/resources.py fetch owner/repository
```

Inspect requirements, ADRs, deployment/IaC, CI and operational evidence as well as the stack. Distinguish existing code from documented target architecture and unresolved decisions. Review every detected capability, remaining direct dependency and all twelve lifecycle areas in the [selection reference](../skills/boost/references/selection.md). There is no fixed limit on project skills; one skill may cover several capabilities, while generic methodology does not replace runner or library guidance.

Prioritize compatible personal skills. For community alternatives, compare compatibility and quality before skills.sh installs, repository stars and published downloads. The JSON search preserves dated, rounded install counts and source URLs; downloads remain unknown when unpublished. Record these observations and the selection rationale. A Dockerfile proves container packaging, not a cloud provider; missing deployment or telemetry choices remain visible in the report.

Read candidates and write the selection JSON with complete `coverage`, explicit `omissions`, and `lifecycle` assessments, then preview, apply, and verify:

```bash
python3 -B ~/.agents/skills/boost/scripts/resources.py install --project "$PWD" --selection /absolute/path/selection.json
python3 -B ~/.agents/skills/boost/scripts/resources.py install --project "$PWD" --selection /absolute/path/selection.json --apply
python3 -B ~/.agents/skills/boost/scripts/resources.py doctor --project "$PWD"
```

For manual removal:

```bash
python3 -B ~/.agents/skills/boost/scripts/resources.py unlink --project "$PWD"
python3 -B ~/.agents/skills/boost/scripts/resources.py unlink --project "$PWD" --apply
```

Removal affects only owned, unchanged project links and their corresponding official CLI records; it preserves unrelated skills and cached downloads. User-modified links or packages stop removal. Native agents/reference workflows can still use a separate native-only selection and `link`; portable skills are rejected by that local-link entry point.

## Global Migration and Recovery

The earlier global cleanup archived the specialized resources outside automatic discovery. The short names and find-skills helper preserve the original restoration path, recorded in `~/.agents/global-setup.json` under `backup`.

```bash
python3 -B skills/boost/scripts/global_setup.py --restore /absolute/path/to/restore.json
python3 -B skills/boost/scripts/global_setup.py --restore /absolute/path/to/restore.json --apply
```

Restoration refuses changed managed links/configuration, missing backups, and collisions. The archive remains a reusable library; deleting it removes the retired resources. Do not rerun the initial cleanup to refresh project skills.

Run behavior checks from the repository root with `python3 -B -m unittest discover -s tests`. Native discovery and real remote installations are checked separately from mock-backed filesystem behavior. The [review](global-resource-review.md) records compatibility and validation limits, and [client details](../skills/boost/references/clients.md) explain native paths.
