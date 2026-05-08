# AGENTS.md

Authoritative registry and operating manual for every AI agent, command, skill,
and MCP server defined in this repository.

---

## ⚠️ Important Context for Every Session

**This repository is the source of truth for your global OpenCode configuration.** Its contents are symlinked into `~/.config/opencode/{agent,command,skill,mcp}` by `setup.py`, making them available everywhere on your machine.

**Key implication:** Any change you make here — a new agent, a tweaked prompt, a skill update — is **global**. It affects every project you work on.

**Local (project-scoped) overrides:** When working inside this repository itself, the `.opencode/` folder contains **project-only** entries that apply here and nowhere else. These allow you to extend or specialize the framework without polluting global state. They are discovered automatically by OpenCode when the project root is `ai-config/`.

---

## 1. Scope & Layers

### Global Layer (symlinked into `~/.config/opencode/`)

These entries are **available everywhere** and used across all your projects and personal workflows:

- **PERSONAL** — life management: budgeting, news, social posting, meal planning, journaling, decision-making, learning, trip planning, inbox management.
- **DEV** — code work: reviewing, committing, documentation, debugging, refactoring, dependency audits, prompt improvement.

### Local Layer (`.opencode/`, discovered when CWD is this repo)

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
budget_currency: "USD"           # default currency
journal_location: null           # overrides default ~/Documents/opencode/journal/
budget_ledger_location: null     # overrides default ~/Documents/opencode/budget/ledger.csv
```

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

### META Agents (Local, `.opencode/`)

| Name | Role | Model | Trigger | File |
|------|------|-------|---------|------|
| agents-curator | Lints AGENTS.md ↔ filesystem | *default* | `@agents-curator` | `.opencode/agent/agents-curator.md` |
| setup-doctor | Validates symlinks, opencode.json, .env | *default* | `@setup-doctor` | `.opencode/agent/setup-doctor.md` |
| entry-scaffolder | Creates new agent/command/skill/mcp stubs | *default* | `@entry-scaffolder` | `.opencode/agent/entry-scaffolder.md` |

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

### META Commands (Local, `.opencode/`)

| Name | Scope | Purpose | File |
|------|-------|---------|------|
| `/scaffold` | local | Create new agent/command/skill/mcp stub | `.opencode/command/scaffold.md` |
| `/sync` | local | Run setup.py and show recap | `.opencode/command/sync.md` |
| `/audit-config` | local | Run agents-curator + setup-doctor | `.opencode/command/audit-config.md` |

---

## 5. Skill Registry

### Global Skills (Reusable utilities)

| Name | Entry Point | Purpose |
|------|-------------|---------|
| git_diff_summarizer | `skills/git_diff_summarizer.py` | Parse diffs into structured chunks for any agent |
| conventional_commit | `skills/conventional_commit.py` | Format/lint Conventional Commits messages |
| feed_fetcher | `skills/feed_fetcher.py` | Fetch & normalize RSS/Atom/JSON feeds |
| csv_ledger | `skills/csv_ledger.py` | Append/query CSV-based ledger for budgets |
| markdown_journal | `skills/markdown_journal.py` | Open/append daily markdown journal |
| repo_indexer | `skills/repo_indexer.py` | Lightweight file/symbol index |
| secret_scanner | `skills/secret_scanner.py` | Regex+entropy scan for secrets |

### Local Skills (`.opencode/`)

| Name | Entry Point | Purpose |
|------|-------------|---------|
| agents_md_linter | `.opencode/skill/agents_md_linter.py` | Validate AGENTS.md ↔ files |
| setup_doctor | `.opencode/skill/setup_doctor.py` | Health-check symlinks, opencode.json, .env |

---

## 6. MCP Server Registry

All global; use in any project. No project-scoped MCPs in this version.

| Name | Transport | Source | Required Env Vars | Purpose |
|------|-----------|--------|-------------------|---------|
| filesystem | stdio | `@modelcontextprotocol/server-filesystem` | none | Sandboxed FS access (roots: `~/Projects`, `~/Documents`, `~/.config/opencode`) |
| git | stdio | `@modelcontextprotocol/server-git` | none | Structured git ops (log, diff, blame) |
| fetch | stdio | `@modelcontextprotocol/server-fetch` | none | Web fetch with HTML→markdown |
| memory | stdio | `@modelcontextprotocol/server-memory` | none | Cross-session knowledge graph (store: `~/.local/share/opencode/memory/store.json`) |
| sequential-thinking | stdio | `@modelcontextprotocol/server-sequential-thinking` | none | Multi-step reasoning |
| time | stdio | `@modelcontextprotocol/server-time` | none | Timezone-aware timestamps |

---

## 7. Conventions

| Concern | Rule |
|---------|------|
| File naming | `kebab-case.md` for agents/commands; `snake_case.py` for skills |
| One per file | Exactly one agent/command per file; skills may contain multiple functions |
| Frontmatter | Use OpenCode YAML frontmatter (see examples below) |
| Documentation | Every entry in section 3–6 must have a corresponding file and doc block (see 8) |
| Lifecycle | Add → document in this table → test locally → commit → push. Remove the row when retiring. |
| Scope clarity | Always mark entries as **global** or **local** (see section 1); do not mix scopes in a single file |

---

## 8. Agent Doc Block Template

Every agent file (`.md`) should follow this structure:

```yaml
---
type: agent
trigger: "@agent-name"
model: null     # null = OpenCode default; override if needed
tools: [read, edit, bash, ...]
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
type: command
trigger: "/command-name"
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
