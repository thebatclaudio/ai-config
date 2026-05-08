---
type: instructions
---

# 🔧 ai-config Local Layer — .opencode/

This file is loaded **only** when CWD is the `ai-config` repository. It extends
the root `AGENTS.md` with entries that are project-scoped (meta-tooling for
maintaining this framework). These agents/commands/skills are NOT symlinked
into the global OpenCode config.

## Scope reminder

See root `AGENTS.md` section 1 (Scope & Layers) for the full explanation of
global vs. local. In short:

- **Global** entries (in `agents/`, `commands/`, `skills/`, `mcp/`) affect every
  project on this machine.
- **Local** entries (in `.opencode/`) affect only this repository. They contain
  framework-maintenance tooling: linters, validators, scaffolders.

## Local Agent Registry

| Name | Role | File |
|------|------|------|
| agents-curator | Lints AGENTS.md ↔ filesystem | `.opencode/agent/agents-curator.md` |
| setup-doctor | Validates symlinks, opencode.json, .env | `.opencode/agent/setup-doctor.md` |
| entry-scaffolder | Creates stubs for new entries | `.opencode/agent/entry-scaffolder.md` |

## Local Command Registry

| Name | Purpose | File |
|------|---------|------|
| `/scaffold` | Create stub + register in AGENTS.md | `.opencode/command/scaffold.md` |
| `/sync` | Run setup.py + show recap | `.opencode/command/sync.md` |
| `/audit-config` | Run all validators | `.opencode/command/audit-config.md` |

## Local Skills

| Name | Entry | Purpose |
|------|-------|---------|
| agents_md_linter | `.opencode/skill/agents_md_linter.py` | Validate AGENTS.md vs file table |
| setup_doctor | `.opencode/skill/setup_doctor.py` | Check symlinks, config, env |
