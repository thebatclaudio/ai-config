---
type: instructions
---

# 🔧 ai-config Local Layer — ai/

This file is loaded **only** when CWD is the `ai-config` repository. It extends
the root `AGENTS.md` with entries that are project-scoped (meta-tooling for
maintaining this framework). These agents/commands/skills are NOT installed
globally.

## Scope reminder

See root `AGENTS.md` section 1 (Scope & Layers) for the full explanation of
global vs. local. In short:

- **Global** entries (in `agents/`, `commands/`, `skills/`, `mcp/`) affect every
  project on this machine.
- **Local** entries (in `ai/`, same structure) affect only this repository. They
  contain framework-maintenance tooling: linters, validators, scaffolders.
  The installer exposes them to each coding tool via its git-ignored project
  folder (`.opencode/`, `.pi/`, `.claude/`).

## Local Agent Registry

| Name | Role | File |
|------|------|------|
| agents-curator | Lints AGENTS.md ↔ filesystem | `ai/agents/agents-curator.md` |
| setup-doctor | Validates symlinks, opencode.json, .env | `ai/agents/setup-doctor.md` |
| entry-scaffolder | Creates stubs for new entries | `ai/agents/entry-scaffolder.md` |

## Local Command Registry

| Name | Purpose | File |
|------|---------|------|
| `/scaffold` | Create stub + register in AGENTS.md | `ai/commands/scaffold.md` |
| `/sync` | Run setup.py + show recap | `ai/commands/sync.md` |
| `/audit-config` | Run all validators | `ai/commands/audit-config.md` |

## Local Skills

| Name | Entry | Purpose |
|------|-------|---------|
| agents-md-linter | `ai/skills/agents-md-linter/SKILL.md` | Validate AGENTS.md vs file table |
| setup-doctor | `ai/skills/setup-doctor/SKILL.md` | Check symlinks, config, env |
