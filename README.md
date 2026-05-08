# ai-config

Centralised, version-controlled configuration for your OpenCode runtime. Edit agents, commands, skills, and MCP servers in one place — `setup.py` bridges them into OpenCode via symlinks so every change is picked up live.

---

## Table of Contents

- [Folder layout](#folder-layout)
- [Global vs. Local layers](#global-vs-local-layers)
- [Quick start](#quick-start)
- [How it works](#how-it-works)
- [CLI reference](#cli-reference)
- [Adding new entries](#adding-new-entries)
- [Cross-platform notes](#cross-platform-notes)
- [Contributing](#contributing)
- [License](#license)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

---

## 📁 Folder layout

```
ai-config/
├── agents/           # Global agent definitions  (→ <opencode>/agent)
├── commands/         # Global slash commands     (→ <opencode>/command)
├── skills/           # Global reusable scripts   (→ <opencode>/skill)
├── mcp/              # Global MCP server configs (→ <opencode>/mcp)
├── .opencode/        # Local entries (this repo only — auto-discovered)
│   ├── AGENTS.md     #   Local-scope instructions addendum
│   ├── agent/        #   Meta agents (curator, doctor, scaffolder)
│   ├── command/      #   Meta commands (scaffold, sync, audit)
│   ├── skill/        #   Meta skills (linter, doctor)
│   └── mcp/          #   (empty — no project-only MCPs this round)
├── AGENTS.md         # Registry + operating manual (loaded as instructions)
├── opencode.json.example  # Template; {{BASE_PROJECT_PATH}} is substituted
├── .env.example      # Variable template — copy to `.env`
├── setup.py          # Automation script (idempotent, cross-platform)
└── requirements.txt  # python-dotenv
```

---

## Global vs. Local layers

This repository has **two layers** of configuration.

### Global layer (root folders)

`agents/`, `commands/`, `skills/`, `mcp/` are **symlinked** into `~/.config/opencode/{agent,command,skill,mcp}` by `setup.py`. This makes every entry available in every project you work on — your personal agents (budget coach, news curator) and dev agents (code reviewer, git historian) are always accessible.

### Local layer (`.opencode/`)

Files under `.opencode/` are **not** symlinked globally. OpenCode discovers them automatically when your current working directory is this repository. They contain **meta-tooling** — agents and commands that maintain the framework itself:

- `@agents-curator` — lints AGENTS.md vs. the filesystem.
- `@setup-doctor` — validates symlinks, config, and `.env`.
- `@entry-scaffolder` — creates new agent/command/skill stubs.
- `/scaffold` — shortcut to scaffold a new entry.
- `/sync` — re-run `setup.py` without leaving the chat.
- `/audit-config` — run curator + doctor in one command.

---

## 🚀 Quick start

```bash
# 1. Provide your environment values
cp .env.example .env
$EDITOR .env                 # set BASE_PROJECT_PATH and any API keys

# 2. Install the single Python dependency
pip install -r requirements.txt

# 3. Generate config + symlinks
python setup.py
```

Re-run `python setup.py` at any time — it is idempotent.

---

## ⚙️ How it works

1. **Read `.env`.** `setup.py` loads variables via `python-dotenv` without polluting the process environment.
2. **Render the template.** Every `{{KEY}}` token in `opencode.json.example` is replaced with the matching `.env` value (JSON-escaped). Missing tokens are warned about, never silently dropped.
3. **Merge into the active config.** The rendered JSON is deep-merged into the existing `opencode.json` at the OpenCode config directory:
   - **Existing values win** on collision (your manual edits are preserved).
   - **Lists** are unioned with order preserved and duplicates removed.
   - **Dicts** are merged recursively.
   - Every collision is reported in the end-of-run recap so you can decide whether to reconcile.
4. **Symlink the folders.** Local plural directories are linked into the singular paths OpenCode expects:

   | Local        | OpenCode target               |
   | ------------ | ----------------------------- |
   | `agents/`    | `<opencode-dir>/agent`        |
   | `commands/`  | `<opencode-dir>/command`      |
   | `skills/`    | `<opencode-dir>/skill`        |
   | `mcp/`       | `<opencode-dir>/mcp`          |

   Existing real directories are backed up before being replaced (only when `--force` is given). Existing correct symlinks are skipped.

5. **Recap.** A summary block prints created / skipped / replaced symlinks, any backups, and a `[WARN]` list of every merge collision.

The OpenCode config directory is resolved with this precedence:

1. `--opencode-dir <path>` CLI flag
2. `OPENCODE_CONFIG_DIR` (in `.env` or process env)
3. Platform default
   - **Linux / macOS:** `~/.config/opencode` (or `$XDG_CONFIG_HOME/opencode`)
   - **Windows:** `%APPDATA%\opencode`

---

## CLI reference

```text
python setup.py                       # generate config + symlinks
python setup.py --dry-run             # show planned actions, change nothing
python setup.py --force               # back up & replace existing real dirs
python setup.py --uninstall           # remove only symlinks pointing into this repo
python setup.py --opencode-dir PATH   # override the OpenCode config directory
```

`--uninstall` is conservative: it leaves real directories and unrelated symlinks alone, removing only symlinks whose target lives inside this repository.

---

## Adding new entries

### Global entries (available everywhere)

1. Drop a new file into the relevant root folder:
   - Agent     → `agents/<kebab-case-name>.md`
   - Command   → `commands/<kebab-case-name>.md`
   - Skill     → `skills/<snake_case_name>.py`
   - MCP       → `mcp/<server-name>.json`
2. Document it in [`AGENTS.md`](./AGENTS.md) (registry table + doc block).
3. Commit. No further `setup.py` run is needed — the symlinks make the change visible to OpenCode immediately.

### Local entries (this repo only)

1. Place the file under `.opencode/` instead:
   - Agent     → `.opencode/agent/<kebab-case-name>.md`
   - Command   → `.opencode/command/<kebab-case-name>.md`
   - Skill     → `.opencode/skill/<snake_case_name>.py`
   - MCP       → `.opencode/mcp/<server-name>.json`
2. Document it in [`.opencode/AGENTS.md`](./.opencode/AGENTS.md).
3. Commit. OpenCode discovers `.opencode/` automatically when CWD is this repo.

---

## Cross-platform notes

- **Linux / macOS:** symlink creation works out of the box.
- **Windows:** creating symbolic links requires either Developer Mode (Settings → Privacy & security → For developers) or an elevated shell. When permission is denied for a directory link, `setup.py` automatically falls back to an NTFS directory junction so the bridge still works.

---

## 🤝 Contributing

Contributions are welcome! Additions follow a simple workflow:

1. **Scaffold** a new entry using `/scaffold` or by hand.
2. **Place** it in the right directory — root folders for global entries, `.opencode/` for repo-scoped ones.
3. **Document** it in the corresponding `AGENTS.md` registry table with a full doc block.
4. **Run** `/audit-config` to validate everything is in sync.
5. **Commit** and push.

Before submitting, check that `setup.py` still runs without errors and that your entry follows the naming conventions (`kebab-case.md` for agents/commands, `snake_case.py` for skills). See `AGENTS.md` for the full conventions reference.

---

## License

This project does not currently include a license file. If you'd like to use, adapt, or distribute it, please open an issue to discuss terms. When you're ready to pick a license, [choosealicense.com](https://choosealicense.com/) is a great place to start.

---

## Troubleshooting

| Symptom                                                         | Fix                                                           |
| --------------------------------------------------------------- | ------------------------------------------------------------- |
| `[ERROR] '.env' not found`                                      | `cp .env.example .env` and edit it.                           |
| `[ERROR] The 'python-dotenv' package is required`               | `pip install -r requirements.txt`.                            |
| `[ERROR] Failed to create symlink ... WinError 1314`            | Enable Developer Mode on Windows or run as administrator.     |
| `[WARN] Refusing to replace existing real path`                 | Re-run with `--force` (the original is backed up).            |
| Merge-collision warnings in recap                               | Edit the active `opencode.json` to reconcile, or remove the conflicting key from your existing config and re-run. |

---

## 🔒 Security

`.env` is git-ignored. Never commit API keys. Keep secrets out of files inside `agents/`, `commands/`, `skills/`, and `mcp/` — reference them via environment variables instead.
