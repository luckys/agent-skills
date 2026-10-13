# Client Compatibility

Initial compatibility verified on 2026-10-11 against Codex 0.162.1, OpenCode 1.19.0, and Antigravity CLI (agy) 1.2.14. Short names were installed and OpenCode 2.0.27's interactive command menu was checked on 2026-10-13. Recheck native documentation after CLI upgrades.

| Resource | Codex | OpenCode | Antigravity CLI |
|---|---|---|---|
| Project skills | `.agents/skills/<name>/SKILL.md` | `.agents/skills/<name>/SKILL.md` | `.agents/skills/<name>/SKILL.md` |
| Personal global skills | `~/.agents/skills` | `~/.agents/skills` | `~/.gemini/antigravity-cli/skills` |
| Project agents | `.codex/agents/*.toml` | `.opencode/agents/*.md` | `.agents/agents/*.md` |
| Personal global agents | `~/.codex/agents` | `~/.config/opencode/agents` | `~/.gemini/config/agents` |
| Project workflow entry | A skill or explicit reference | A skill or `.opencode/commands/*.md` | A skill; legacy workflow indexing is being retired |

The global Antigravity skill and agent directories differ. Its IDE global skills use `~/.gemini/config/skills`, which is not the CLI path. Centralize source material under `.agents` and bridge only paths the installed tools actually discover. There is no common native agent format across all three.

Invocation from a project:

- Codex: `$boost` for setup and `$flow` for the current task. Custom slash prompts are deprecated and use `/prompts:<name>`; do not claim bare `/boost` or `/flow` is registered in Codex.
- OpenCode: `/boost` for setup and `/flow` for the current task. The command wrappers use the `boost` primary agent and the regular `build` agent respectively, so flow does not remain constrained to setup.
- Antigravity CLI: `/boost` and `/flow` are exposed from the two globally linked skills through its automatic slash-command conversion.

OpenCode's two command files are thin wrappers; maintained behavior lives in the shared skills. Existing project context files keep their client-specific precedence; bootstrap does not replace them.

OpenCode 2 keeps the same Markdown command directories and portable skill compatibility paths. Its root CLI no longer accepts `--agent` or `--pure`; select an agent through `/agents`, and use `opencode debug agents` for profile discovery. Before selecting a legacy OpenCode profile, review its V2 migration requirements, especially `permission` versus `permissions` and renamed actions. A supported file location does not prove that every profile field is compatible.

Sources: [Codex agents](https://developers.openai.com/codex/subagents/), [Codex app-server](https://developers.openai.com/codex/app-server/), [Codex custom prompts](https://developers.openai.com/codex/custom-prompts/), [OpenCode skills](https://opencode.ai/docs/skills/), [OpenCode agents](https://opencode.ai/docs/agents/), [OpenCode commands](https://opencode.ai/docs/commands/), [Antigravity skills](https://www.antigravity.google/docs/skills), [Antigravity agents](https://www.antigravity.google/docs/subagents), [workflow migration](https://www.antigravity.google/docs/migration/workflows-to-skills/).

Current OpenCode 2 sources: [commands](https://dev.opencode.ai/v2/docs/commands/), [skills](https://dev.opencode.ai/v2/docs/skills/), [migration](https://dev.opencode.ai/v2/docs/migrate-v1/).
