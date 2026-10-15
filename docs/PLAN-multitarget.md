# Plan: make ai-config tool-agnostic (OpenCode · pi · Claude Code · …)

Status: **Phases 0–3 done** — phases 4–6 pending.

## Goal

One canonical, tool-neutral source of agents, commands, skills, MCP servers and
instructions, rendered into each coding agent's native format by small adapters.

## Current coupling to OpenCode

| Area | Coupling |
|---|---|
| `setup.py` | Hard-wired to `~/.config/opencode`, `opencode.json.example`, plural→singular dir map |
| `.opencode/` | META layer lives in an OpenCode-only folder (+ `@opencode-ai/plugin` package.json) |
| `skills/*.py` | Python helpers, *not* Agent Skills (`<name>/SKILL.md`) as pi/Claude Code define them |
| `mcp/*.json` | Symlinked into `~/.config/opencode/mcp`, which OpenCode does not read (see Phase 0 findings) |
| Prompt bodies | ~82 mentions of OpenCode / `.opencode/`; data paths like `~/Documents/opencode/…`, `~/.config/opencode/personal/feeds.toml`; onboarder/bootstrapper only emit `.opencode/` |
| pi support | Out-of-repo script `~/.pi/agent/sync-opencode.py` |

## Target architecture

```
ai-config/
├── AGENTS.md                 # neutral instructions + registry
├── agents/*.md               # canonical agents (neutral frontmatter)
├── commands/*.md             # canonical commands
├── skills/<name>/            # Agent Skills: SKILL.md + bundled snake_case.py
├── mcp/*.json                # canonical server defs (command/args/env/url)
├── ai/                       # local layer (replaces .opencode/), same structure
├── installer/
│   ├── core.py               # env, merge, backup, symlink, recap (from setup.py)
│   ├── catalog.py            # loads canonical items + dependency-free frontmatter parser
│   ├── migrations.py         # tool-neutral data moves
│   └── adapters/{base,opencode,pi,claude}.py
├── tests/                    # unittest suite for the installer
├── dist/<target>/            # generated output (gitignored)
└── setup.py                  # thin CLI: --target opencode,pi,claude | auto
```

### Mapping

| Canonical | OpenCode | pi | Claude Code |
|---|---|---|---|
| `AGENTS.md` | `instructions` in `opencode.json` | `~/.pi/agent/AGENTS.md` symlink | `~/.claude/CLAUDE.md` with `@…/AGENTS.md` import |
| `agents/` | `agent/*.md` (`mode: subagent`) | `skills/<name>/SKILL.md` (no subagents) | `~/.claude/agents/*.md` (`name`, `description`, `tools`, `model`) |
| `commands/` | `command/*.md` | `prompts/*.md` (`description`, `argument-hint`, `$ARGUMENTS`) | `~/.claude/commands/*.md` (same fields) |
| `skills/<n>/SKILL.md` | `skill/` (to verify) | `~/.agents/skills` or `~/.pi/agent/skills` | `~/.claude/skills/` |
| `mcp/*.json` | merged into `opencode.json` → `mcp` (`type: local`, `command: [...]`) | merged into `~/.pi/agent/mcp.json` → `mcpServers` | `claude mcp add-json --scope user` |
| `ai/` | `.opencode/` | `.pi/` | `.claude/` |

### Canonical frontmatter

```yaml
---
name: code-reviewer
kind: agent            # agent | command
scope: global          # global | local
description: Reviews diffs for correctness, security, style, tests.
trigger: "@code-reviewer"
tools: [read, grep, bash]   # abstract, mapped per adapter
model: default
targets:                    # optional per-tool overrides
  opencode: { mode: subagent }
  claude:   { tools: "Read, Grep, Bash" }
  pi:       { disable-model-invocation: false }
---
```

## Phases

### 0. Safety net — ✅ done
- [x] Tag `pre-multitarget` on `d087abd`.
- [x] Snapshot installed state → `.snapshots/pre-multitarget/` (gitignored; `MANIFEST.sha256`).
      Secrets/sessions (`auth.json`, `.credentials.json`, sessions, node_modules) excluded.
- [x] Verify OpenCode MCP loading.
- [x] Add `dist/` and `.snapshots/` to `.gitignore`.

**Findings**
- Tools installed: OpenCode 1.14.48, pi (`~/.pi/agent/bin/pi`), Claude Code (`~/.local/bin/claude`).
- **OpenCode loads no MCP servers** (`opencode mcp list` → "No MCP servers configured"); the
  `~/.config/opencode/mcp` symlink is ignored and `opencode.json` has `"mcp": {}`. Phase 4 fixes this.
- OpenCode loads all 19 agents as mode `all` (not `subagent`). Name comes from the filename:
  `agents/onboard.md` → `onboard`, but AGENTS.md calls it `project-onboarder`. Rename the file in Phase 1.
- `~/.config/opencode/opencode.json` also has a user-added `plugin` entry
  (`@ex-machina/opencode-anthropic-auth`); the merge must keep preserving it.
- `~/.claude` has no agents/commands/skills/CLAUDE.md → clean slate, no conflicts.

### 1. Restructure source — ✅ done
- [x] Helpers → `skills/<kebab-name>/{SKILL.md,<snake_name>.py}`.
      **Deviation:** scripts are bundled *inside* each skill folder instead of a top-level
      `scripts/`. A skill folder is then self-contained, so relative paths keep working when
      tools symlink or copy it (the portable Agent Skills form).
- [x] `.opencode/` → `ai/` with the root's plural layout (`ai/agents`, `ai/commands`,
      `ai/skills/<name>/`, `ai/mcp`). OpenCode runtime files (`package.json`, `node_modules`)
      dropped.
- [x] `agents/onboard.md` → `agents/project-onboarder.md` (OpenCode now names it correctly).
- [x] Canonical frontmatter on 22 agents + 18 commands (`name`, `kind`, `scope`,
      `description`, `trigger`, `argument-hint`); bodies byte-identical.
- [x] Path references updated in AGENTS.md (registries, §7 conventions, §8–9 templates),
      ai/AGENTS.md, entry-scaffolder, agents-curator, /scaffold.
- [x] Linter fixed (pre-existing bugs): it now scans `ai/`, matches MCP rows by name,
      resets per `##` section, and reports missing files (before, it only recorded paths
      that existed, so missing files were never reported). Green; negative-tested.
- [x] **Temporary shim:** git-ignored `.opencode/{agent,command,skill}` → `../ai/*` so
      OpenCode keeps the local layer until the adapter generates it (Phase 4).
      `.opencode/`, `.pi/`, `.claude/` are now git-ignored.

**Verified:** OpenCode lists 19 global agents (incl. `project-onboarder`) and 3 local
agents in this repo. `~/.pi/agent/sync-opencode.py` output is identical to the snapshot.
All 7 skill examples execute. Setup doctor is healthy.

**Known stale until later phases:** README.md paths (Phase 5); "OpenCode" wording and
`.opencode/` targets in onboarder/bootstrapper (Phase 2); setup_doctor is OpenCode-only
(Phase 5). The new `skills/` folders aren't exposed to pi/Claude yet (Phase 4).

### 2. Neutralize content — ✅ done
- [x] **Data moved** (decision #2): `~/Documents/opencode/budget/ledger.csv` →
      `~/Documents/ai-config/budget/ledger.csv` (checksum-verified, old dir removed).
      New defaults: journal `~/Documents/ai-config/journal/`, feeds `~/.config/ai-config/feeds.toml`
      (new `feeds_location` pref), memory `~/.local/share/ai-config/memory/store.json`.
      Updated in agents, commands, skills, `markdown_journal.py`, AGENTS.md §2 (new data table).
- [x] **Bug fix:** `mcp/memory.json` set `OPENCODE_MEMORY_STORE`, which server-memory ignores.
      Now `MEMORY_FILE_PATH` (the server expands `~` itself). Filesystem MCP root
      `~/.config/opencode` → `~/.config/ai-config`.
- [x] **New skill `agent-config-targets`**: one reference for per-tool paths, frontmatter,
      MCP shapes, instruction precedence, and tool detection. Projects share `AGENTS.md` and
      `.agents/skills/`; agents, commands and MCP are written natively per tool.
- [x] `project-onboarder`, `project-bootstrapper`, `/onboard`, `/bootstrap` are multi-tool: they
      detect and confirm target tools (new `--tools` flag) and write via `agent-config-targets`.
      Examples rewritten (OpenCode+Claude Code; pi-only).
- [x] AGENTS.md intro/registry made tool-neutral, with an honest transition note.
- **Deviation:** no `{{TOOL_NAME}}` token. Neutral wording ("your coding agent") reads fine in
  every tool and keeps canonical files usable as-is (OpenCode still reads them via symlink).

**Verified:** linter green; frontmatter `description` matches Role/Purpose in all 40 files;
skill names match folders; all MCP JSON valid; OpenCode loads 19 agents and **now discovers
8 skills**; pi re-synced with the new content.

**Carried forward:**
- Phase 3: installer `migrate-data` step (old → new data paths) for other machines; create
  `~/.local/share/ai-config/memory/` before starting the memory server.
- Phase 4: pi doesn't see repo `skills/` yet (`agent-config-targets` is referenced by the pi
  onboarder skill but not installed). Expand `~` / `{{BASE_PROJECT_PATH}}` in MCP args per tool.
- Phase 5: setup-doctor, `.env.example`, README still OpenCode-only.

### 3. Split the installer — ✅ done
- [x] `installer/core.py`: everything reusable from the old `setup.py` (env, `{{TOKEN}}`
      rendering, deep merge, atomic JSON write + backup, symlinks with Windows junction
      fallback, scoped uninstall, per-target `Report` + recap).
      Change: an unchanged JSON config is no longer rewritten and backed up on every run.
- [x] `installer/catalog.py`: loads `agents/`, `commands/`, `skills/*/SKILL.md`, `mcp/*.json`
      for the global (root) and local (`ai/`) layers, validates name/kind/scope/description.
      Includes a small YAML-subset frontmatter parser (scalars, quoted strings, flow
      lists/maps, nested blocks for `targets:`), so there is no PyYAML dependency and parsing
      is deterministic.
- [x] `installer/migrations.py`: idempotent data moves (old OpenCode paths → ai-config),
      checksum-verified, never overwrites (conflict → warn, keep both), creates the memory dir.
- [x] `installer/adapters/base.py`: `Adapter` contract: `detect()`, `default_config_dir()`,
      `config_dir()` (CLI > env var > default), `install()` = `install_instructions` →
      `install_items` → `install_mcp`, `install_local()`, `uninstall()`, `uninstall_local()`,
      `add_arguments()` (per-tool `--<tool>-dir`).
- [x] `installer/adapters/opencode.py`: ports today's behavior 1:1 and owns the local
      `.opencode/` links (replacing the manual Phase 1 shim).
- [x] `setup.py` is now a thin CLI: `--target auto|all|<list>`, `--layer all|global|local`,
      `--dry-run`, `--force`, `--uninstall`, `--list`, `--skip-migrate`, `--opencode-dir`.
- [x] `tests/test_installer.py`: 17 tests (parser, catalog validity, merge, token
      rendering, migrations incl. conflict/dry-run/symlinked legacy path, OpenCode install/idempotency/uninstall,
      user-key preservation, refusal without `--force`).
- [x] setup-doctor also compiles `installer/`.
- **Deviations:** `--layer` instead of `--local` (local layer installs by default since it only
  touches git-ignored folders). Rendering into `dist/<target>/` moves to Phase 4, the first
  time an adapter needs to transform files. Added `--list` and `--skip-migrate`.

**Verified:** old and new `setup.py` run in sandboxes produce identical trees and a
byte-identical `opencode.json`. Re-runs are no-ops (no backup spam). Uninstall removes
only repo links and is idempotent. The real run on this machine changed nothing (exit 0).
Doctor healthy, linter green.

### 4. Adapters (in order)
1. OpenCode — same output as the snapshot, plus a working `mcp` block and `mode: subagent`.
2. pi — absorb `sync-opencode.py`, add `mcp.json`; then delete the old script.
3. Claude Code — agents, commands, skills, `CLAUDE.md` import, MCP via the `claude` CLI.

### 5. META layer and docs
- Linter and doctor check every enabled target.
- Scaffolder writes canonical files only.
- `/sync` → `setup.py --target all`.
- Rewrite AGENTS.md (neutral, §Targets matrix) and README (per-tool quick start, "add an adapter").

### 6. Verification
- `--dry-run` for each target; diff OpenCode output against the snapshot.
- pi: `/reload`, `/review`, `/skill:code-reviewer`, `pi mcp list`.
- Claude Code: `/agents`, `/review`, `claude mcp list`.
- Uninstall idempotency; pytest for each adapter's frontmatter conversion.

## Open decisions (need answers before the phase in brackets)
1. pi agents: skills only, or also add a subagent extension later? [4]
2. ~~Existing data~~ → **moved to `~/Documents/ai-config/`** (decided, done).
3. ~~Local layer folder name~~ → **`ai/`** (decided).
4. Claude Code MCP: write `~/.claude.json` via `claude mcp`, or only print the commands? [4]

## Rollback
`git checkout pre-multitarget && python setup.py` restores the OpenCode install.
Pre-refactor files are in `.snapshots/pre-multitarget/`.
