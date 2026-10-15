# AGENTS.md

Authoritative registry and operating manual for every AI agent, command, skill,
and MCP server defined in this repository.

---

## ⚠️ Important Context for Every Session

**This repository is the source of truth for your global AI coding-agent configuration** — tool-neutral agents, commands, skills, MCP servers and instructions. `setup.py` installs them into each coding tool you use (OpenCode, pi, Claude Code, …), making them available everywhere on your machine.

> Transition note: per-tool installer adapters are being built (see `docs/PLAN-multitarget.md`). Today `setup.py` installs into OpenCode and Claude Code; pi is still synced by `~/.pi/agent/sync-opencode.py`.

**Key implication:** Any change you make here — a new agent, a tweaked prompt, a skill update — is **global**. It affects every project you work on.

**Local (project-scoped) overrides:** When working inside this repository itself, the `ai/` folder contains **project-only** entries that apply here and nowhere else. These allow you to extend or specialize the framework without polluting global state. The installer exposes them to each coding tool through its project folder (e.g. `.opencode/`), which is generated and git-ignored.

---

## 1. Scope & Layers

### Global Layer (repo root, installed into every configured tool)

These entries are **available everywhere** and used across all your projects and personal workflows:

- **PERSONAL** — life management: budgeting, news, social posting, meal planning, journaling, decision-making, learning, trip planning, inbox management.
- **DEV** — code work: reviewing, committing, documentation, debugging, refactoring, dependency audits, prompt improvement.

### Local Layer (`ai/`, active when CWD is this repo)

These entries are **available only when you're inside the `ai-config/` project**:

- **META** — framework maintenance: linting AGENTS.md, validating symlinks & config, scaffolding new entries, syncing setup.

---

## 2. Voice & Preferences (Seed with your values; agents prompt you on first use)

```yaml
timezone: null                    # e.g., "Europe/Rome"
language: null                    # e.g., "English" or "Italian" or ["English", "Italian"]
tone: null                        # e.g., "professional", "casual", "mixed"
social_handles: {}               # { "twitter": "@handle", "linkedin": "...", ... }
content_interests: []            # topics for news-curator
diet_restrictions: []            # for meal-planner
budget_currency: "EUR"           # default currency
journal_location: null           # overrides default ~/Documents/ai-config/journal/
budget_ledger_location: null     # overrides default ~/Documents/ai-config/budget/ledger.csv
feeds_location: null             # overrides default ~/.config/ai-config/feeds.toml
```

Personal data lives in tool-neutral locations, so every coding agent (OpenCode, pi, Claude Code, …) shares the same journal, ledger, feeds and memory:

| Data | Default |
|------|---------|
| Journal | `~/Documents/ai-config/journal/YYYY-MM-DD.md` |
| Budget ledger | `~/Documents/ai-config/budget/ledger.csv` |
| News feeds | `~/.config/ai-config/feeds.toml` |
| MCP memory store | `~/.local/share/ai-config/memory/store.json` |

---

## 3. Agent Registry

### PERSONAL Agents (Global)

| Name | Role | Model | Trigger | File |
|------|------|-------|---------|------|
| budget-coach | Expense tracking, categorization, savings advice | *default* | `@budget-coach` or `/budget` | `agents/budget-coach.md` |
| news-curator | Daily/topical news digest from feeds | *default* | `@news-curator` or `/news` | `agents/news-curator.md` |
| social-strategist | Platform-specific post/thread drafting | *default* | `@social-strategist` or `/post` | `agents/social-strategist.md` |
| inbox-zero | Email/message triage, draft replies | *default* | `@inbox-zero` | `agents/inbox-zero.md` |
| daily-planner | Schedule building from calendar + todos | *default* | `@daily-planner` or `/plan-day` | `agents/daily-planner.md` |
| meal-planner | Weekly menus, grocery lists, budget-aware | *default* | `@meal-planner` | `agents/meal-planner.md` |
| trip-planner | Itineraries, packing lists, travel briefs | *default* | `@trip-planner` | `agents/trip-planner.md` |
| journal-coach | Reflective prompts, mood tracking, retrospectives | *default* | `@journal-coach` or `/journal` | `agents/journal-coach.md` |
| learning-tutor | Spaced-repetition study plans, quizzes | *default* | `@learning-tutor` or `/learn` | `agents/learning-tutor.md` |
| decision-helper | Pros/cons, scoring, sleep-on-it rec | *default* | `@decision-helper` or `/decide` | `agents/decision-helper.md` |

### DEV Agents (Global)

| Name | Role | Model | Trigger | File |
|------|------|-------|---------|------|
| code-reviewer | Correctness, security, style, test coverage | *default* | `@code-reviewer` or `/review` | `agents/code-reviewer.md` |
| git-historian | Suggests Conventional Commits, PR bodies | *default* | `@git-historian` | `agents/git-historian.md` |
| docs-writer | READMEs, ADRs, docstrings | *default* | `@docs-writer` | `agents/docs-writer.md` |
| debug-detective | Root-cause from stack traces, logs | *default* | `@debug-detective` | `agents/debug-detective.md` |
| refactor-surgeon | Targeted refactors with diffs, no rewrites | *default* | `@refactor-surgeon` | `agents/refactor-surgeon.md` |
| dependency-auditor | CVE, outdated, unused in any ecosystem | *default* | `@dependency-auditor` | `agents/dependency-auditor.md` |
| prompt-engineer | Critiques & improves prompts | *default* | `@prompt-engineer` | `agents/prompt-engineer.md` |
| project-onboarder | Analyzes projects and scaffolds AI-tool config for OpenCode / pi / Claude Code | *default* | `@project-onboarder` or `/onboard` | `agents/project-onboarder.md` |
| project-bootstrapper | Discovery → research → stack proposal → scaffold a new project + its AI-tool config | *default* | `@project-bootstrapper` or `/bootstrap` | `agents/project-bootstrapper.md` |

### META Agents (Local, `ai/`)

| Name | Role | Model | Trigger | File |
|------|------|-------|---------|------|
| agents-curator | Lints AGENTS.md ↔ filesystem | *default* | `@agents-curator` | `ai/agents/agents-curator.md` |
| setup-doctor | Validates symlinks, opencode.json, .env | *default* | `@setup-doctor` | `ai/agents/setup-doctor.md` |
| entry-scaffolder | Creates new agent/command/skill/mcp stubs | *default* | `@entry-scaffolder` | `ai/agents/entry-scaffolder.md` |

---

## 4. Command Registry

### PERSONAL Commands (Global)

| Name | Scope | Purpose | File |
|------|-------|---------|------|
| `/budget` | global | Quick expense entry + monthly summary | `commands/budget.md` |
| `/news` | global | Show headlines on topic | `commands/news.md` |
| `/post` | global | Draft a post for a social platform | `commands/post.md` |
| `/plan-day` | global | Build today's schedule | `commands/plan-day.md` |
| `/journal` | global | Open today's journal entry with prompts | `commands/journal.md` |
| `/decide` | global | Walk through a decision | `commands/decide.md` |
| `/learn` | global | Start/resume a study session | `commands/learn.md` |

### DEV Commands (Global)

| Name | Scope | Purpose | File |
|------|-------|---------|------|
| `/commit` | global | Suggest a Conventional Commits message | `commands/commit.md` |
| `/pr` | global | Draft PR title + body | `commands/pr.md` |
| `/review` | global | Run code-reviewer on staged changes | `commands/review.md` |
| `/explain` | global | Plain-language walkthrough of code | `commands/explain.md` |
| `/changelog` | global | Group commits into a changelog entry | `commands/changelog.md` |
| `/pimp-readme` | global | Analyze and rewrite README.md with improved structure, tone, and emoji | `commands/pimp-readme.md` |
| `/onboard` | global | Analyze project and generate an AI-tool onboarding plan (multi-tool) | `commands/onboard.md` |
| `/bootstrap` | global | Bootstrap a brand-new project: discovery, research, stack pick, scaffold | `commands/bootstrap.md` |

### META Commands (Local, `ai/`)

| Name | Scope | Purpose | File |
|------|-------|---------|------|
| `/scaffold` | local | Create new agent/command/skill/mcp stub | `ai/commands/scaffold.md` |
| `/sync` | local | Run setup.py and show recap | `ai/commands/sync.md` |
| `/audit-config` | local | Run agents-curator + setup-doctor | `ai/commands/audit-config.md` |

---

## 5. Skill Registry

Skills follow the [Agent Skills](https://agentskills.io) layout: one folder per skill with a `SKILL.md` (frontmatter `name` + `description`) and any bundled scripts next to it.

### Global Skills (Reusable utilities)

| Name | Skill | Script | Purpose |
|------|-------|--------|---------|
| git-diff-summarizer | `skills/git-diff-summarizer/SKILL.md` | `skills/git-diff-summarizer/git_diff_summarizer.py` | Parse diffs into structured chunks for any agent |
| conventional-commit | `skills/conventional-commit/SKILL.md` | `skills/conventional-commit/conventional_commit.py` | Format/lint Conventional Commits messages |
| feed-fetcher | `skills/feed-fetcher/SKILL.md` | `skills/feed-fetcher/feed_fetcher.py` | Fetch, parse, filter and merge RSS/Atom/JSON feeds from `feeds.toml` (stdlib CLI + library) |
| csv-ledger | `skills/csv-ledger/SKILL.md` | `skills/csv-ledger/csv_ledger.py` | Append/query CSV-based ledger for budgets |
| markdown-journal | `skills/markdown-journal/SKILL.md` | `skills/markdown-journal/markdown_journal.py` | Open/append daily markdown journal |
| repo-indexer | `skills/repo-indexer/SKILL.md` | `skills/repo-indexer/repo_indexer.py` | Lightweight file/symbol index |
| secret-scanner | `skills/secret-scanner/SKILL.md` | `skills/secret-scanner/secret_scanner.py` | Regex+entropy scan for secrets |
| agent-config-targets | `skills/agent-config-targets/SKILL.md` | — | Per-tool paths and frontmatter for OpenCode / pi / Claude Code project config |

### Local Skills (`ai/`)

| Name | Skill | Script | Purpose |
|------|-------|--------|---------|
| agents-md-linter | `ai/skills/agents-md-linter/SKILL.md` | `ai/skills/agents-md-linter/agents_md_linter.py` | Validate AGENTS.md ↔ files |
| setup-doctor | `ai/skills/setup-doctor/SKILL.md` | `ai/skills/setup-doctor/setup_doctor.py` | Health-check symlinks, opencode.json, .env |

---

## 6. MCP Server Registry

All global; use in any project. No project-scoped MCPs in this version.

| Name | Transport | Source | Required Env Vars | Purpose |
|------|-----------|--------|-------------------|---------|
| filesystem | stdio | `@modelcontextprotocol/server-filesystem` | none | Sandboxed FS access (roots: `~/Projects`, `~/Documents`, `~/.config/ai-config`) |
| git | stdio | `mcp-server-git` (PyPI, via `uvx`) | none | Structured git ops (log, diff, blame) |
| fetch | stdio | `mcp-server-fetch` (PyPI, via `uvx`) | none | Web fetch with HTML→markdown |
| memory | stdio | `@modelcontextprotocol/server-memory` | none | Cross-session knowledge graph (store: `~/.local/share/ai-config/memory/store.json`) |
| sequential-thinking | stdio | `@modelcontextprotocol/server-sequential-thinking` | none | Multi-step reasoning |
| time | stdio | `mcp-server-time` (PyPI, via `uvx`) | none | Timezone-aware timestamps |

---

## 7. Conventions

| Concern | Rule |
|---------|------|
| File naming | `kebab-case.md` for agents/commands; `kebab-case/` folder with `SKILL.md` for skills; bundled scripts in `snake_case.py` |
| One per file | Exactly one agent/command per file; one skill per folder (scripts may contain multiple functions) |
| Frontmatter | Canonical, tool-neutral YAML: `name` (= file/folder name), `kind` (`agent`/`command`/`skill`), `scope` (`global`/`local`), `description`, plus `trigger` for agents/commands and optional `argument-hint` for commands. Tool-specific fields go under `targets.<tool>`. |
| Layout | Global: `agents/`, `commands/`, `skills/`, `mcp/` at repo root. Local: same structure under `ai/`. |
| Documentation | Every entry in section 3–6 must have a corresponding file and doc block (see 8) |
| Lifecycle | Add → document in this table → test locally → commit → push. Remove the row when retiring. |
| Scope clarity | Always mark entries as **global** or **local** (see section 1); do not mix scopes in a single file |

---

## 8. Agent Doc Block Template

Every agent file (`.md`) should follow this structure:

```yaml
---
name: agent-name
kind: agent
scope: global            # or local
description: "One sentence: what it does and when to use it."
trigger: "@agent-name"
---

# agent-name

## Role

One paragraph: who this agent is, what it provides, the value to the user.

## When to invoke

- Bullet list of situations and user needs.

## Operating principles

1. Numbered, directive rules for behavior.
2. Constraints and boundaries.
3. Tone and approach.

## Workflow

Step-by-step process the agent follows:
1. Gather inputs.
2. Analyze/transform.
3. Validate/refine.
4. Return structured output.

## Output format

Exact structure: headings, sections, code blocks, formatting.

## Examples

### Example 1 — <scenario>

**User:** [what they ask]

**Agent:** [full response]

### Example 2 — <edge case or nuance>

**User:** [what they ask]

**Agent:** [full response]

## Constraints

- What the agent must NOT do.
- Limits and disclaimers.
- When to decline or ask for clarification.
```

---

## 9. Command Doc Block Template

Every command file (`.md`) should follow this structure:

```yaml
---
name: command-name
kind: command
scope: global            # or local
description: "One sentence describing the command."
trigger: "/command-name"
argument-hint: "[argument] [--flag]"
---

# /command-name

## Purpose

One-sentence description.

## Usage

```
/command-name [argument] [--flag]
```

## Parameters

- `argument` — description.
- `--flag` — optional, what it does.

## Behavior

What the command does, what agents or skills it invokes, what it returns.

## Examples

### Example 1 — <scenario>

**Input:** ...

**Output:** ...

### Example 2 — <variant>

**Input:** ...

**Output:** ...

## See also

- Related agents, commands, or skills.
```

---

## 10. Operational Notes

- **Secrets:** Never hard-code API keys. Reference them via `.env` or environment variables.
- **Determinism:** Prefer pinned model IDs over moving tags (where applicable).
- **Audit trail:** Significant prompt changes should be summarized in the commit message.
- **Merge collisions:** When `setup.py` reports config merge collisions, reconcile them — divergence is a smell.
- **Testing:** Before committing a new agent/command, invoke it manually and verify behavior.
- **Scope discipline:** Global entries affect all projects. Local entries affect only `ai-config/`. Don't blur the boundary.
