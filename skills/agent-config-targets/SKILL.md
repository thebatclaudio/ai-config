---
name: agent-config-targets
kind: skill
scope: global
description: "Reference of where and how each AI coding tool (OpenCode, pi, Claude Code) stores project instructions, agents, slash commands, skills and MCP servers, with frontmatter conversions. Use when creating or auditing AI-tool configuration for a project (onboarding, bootstrapping, scaffolding)."
---

# agent-config-targets

How to write AI-tool configuration for a project so it works in **whichever coding
tool(s) the user runs**. Use it from `@project-onboarder`, `@project-bootstrapper` and
`@entry-scaffolder`.

## 1. Pick the target tools

1. **Detect** what's in use:
   - Tool running now: env `OPENCODE=1` → OpenCode, `CLAUDECODE=1` → Claude Code, any `PI_*` var → pi.
   - Project folders already present: `.opencode/` or `opencode.json` → OpenCode;
     `.pi/` → pi; `.claude/`, `CLAUDE.md` or `.mcp.json` → Claude Code.
2. **Ask** the user to confirm the list (multi-select). Default: the detected tools.
3. Write **one shared source** where formats are compatible, and **native files per tool**
   only where they differ (agents, commands, MCP).

## 2. Shared pieces (write once)

| What | Path | Notes |
|---|---|---|
| Project instructions + local registry | `AGENTS.md` (repo root) | Read natively by OpenCode and pi. |
| Claude Code bridge | `CLAUDE.md` containing the single line `@AGENTS.md` | Only if Claude Code is a target. Claude Code does not read `AGENTS.md` itself. |
| Skills | `.agents/skills/<kebab-name>/SKILL.md` (+ bundled scripts) | pi reads `.agents/skills/`. For Claude Code add a symlink `.claude/skills → ../.agents/skills`. For OpenCode, check that its version discovers `.agents/skills/` (`opencode debug skill`); if not, symlink `.opencode/skill → ../.agents/skills`. |

Use relative symlinks so the repo stays portable. On Windows, or when symlinks are unwanted, copy the folders and say so in `AGENTS.md`.

`SKILL.md` frontmatter (all tools): `name` (= folder name, lowercase-hyphenated) and
`description` (what it does **and when to use it**). Reference bundled files by paths relative to
the skill folder.

## 3. Per-tool pieces

### Agents (`@name`)

| Tool | Path | Frontmatter |
|---|---|---|
| OpenCode | `.opencode/agent/<name>.md` | `description` (required), `mode: subagent` (or `primary`/`all`), optional `model`, `temperature`, `tools`/`permission` |
| Claude Code | `.claude/agents/<name>.md` | `name`, `description` (required); optional `tools: Read, Grep, Bash` (comma string; omit = inherit all), `model: sonnet\|opus\|haiku\|inherit` |
| pi | *no subagents*: write the agent as a skill `.agents/skills/<name>/SKILL.md` | `name`, `description` = "Agent @name. <role>" |

The body (role, workflow, output format, examples, constraints) is identical across tools.
Follow the agent template in the ai-config `AGENTS.md` §8.

### Slash commands (`/name`)

| Tool | Path | Frontmatter | Arguments |
|---|---|---|---|
| OpenCode | `.opencode/command/<name>.md` | `description`, optional `agent`, `model`, `subtask` | `$ARGUMENTS`, `$1`… |
| Claude Code | `.claude/commands/<name>.md` | `description`, `argument-hint`, optional `allowed-tools`, `model` | `$ARGUMENTS`, `$1`… |
| pi | `.pi/prompts/<name>.md` | `description`, `argument-hint` | `$ARGUMENTS` / `$@`, `$1`, `${1:-default}` |

`$ARGUMENTS` works in all three, so prefer it.

### MCP servers (project scope)

Same server, three shapes. Never inline secrets; use environment variables.

```jsonc
// Claude Code → .mcp.json      |  pi → .pi/mcp.json  (same shape)
{ "mcpServers": { "postgres": {
    "command": "npx", "args": ["-y", "@modelcontextprotocol/server-postgres", "${DATABASE_URL}"],
    "env": {} } } }

// OpenCode → opencode.json (project root)
{ "$schema": "https://opencode.ai/config.json",
  "mcp": { "postgres": {
    "type": "local", "enabled": true,
    "command": ["npx", "-y", "@modelcontextprotocol/server-postgres", "{env:DATABASE_URL}"],
    "environment": {} } } }
```

Remote servers: `{ "url": "https://…" }` (Claude Code / pi) and `{ "type": "remote", "url": "https://…" }` (OpenCode).
Env interpolation syntax differs: Claude Code `${VAR}`, OpenCode `{env:VAR}`. For pi, check `docs/mcp.md` (`pi mcp add --env`).

### Instruction-file precedence (for audits)

| Tool | Global | Project |
|---|---|---|
| OpenCode | `~/.config/opencode/AGENTS.md` + `instructions` in `opencode.json` | `AGENTS.md` (falls back to `CLAUDE.md`) |
| pi | `~/.pi/agent/AGENTS.md` | `AGENTS.md` / `CLAUDE.md` in cwd and parents |
| Claude Code | `~/.claude/CLAUDE.md` | `CLAUDE.md` or `.claude/CLAUDE.md` (supports `@path` imports) |

## 4. Rules

- Keep **one source of truth**: shared `AGENTS.md` and `.agents/skills/`, plus per-tool agent and command files generated from the same body.
- Never write tool-specific frontmatter keys into another tool's files (OpenCode can reject unknown agent keys such as Claude's `tools` string).
- Git: commit the project config folders. Don't commit tool runtime files (`.opencode/node_modules`, `.opencode/package*.json`, `.claude/settings.local.json`).
- pi loads project `.pi/` (and project skills) only after the user grants **project trust**. Tell them.
- These formats change. If something doesn't load, check the tool's current docs and say which version you verified against.
