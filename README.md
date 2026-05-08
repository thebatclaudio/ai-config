# ai-config

Centralised, version-controlled OpenCode configuration. Edit agents, commands,
skills, and MCP servers in this repository — `setup.py` bridges them into the
local OpenCode runtime via symbolic links so every change is picked up live.

---

## Folder layout

```
ai-config/
├── agents/                # Agent definitions  (symlinked to <opencode>/agent)
├── commands/              # Slash commands     (symlinked to <opencode>/command)
├── skills/                # Reusable scripts   (symlinked to <opencode>/skill)
├── mcp/                   # MCP server configs (symlinked to <opencode>/mcp)
├── AGENTS.md              # Registry + operating manual (loaded as instructions)
├── opencode.json.example  # Template; {{BASE_PROJECT_PATH}} is substituted
├── .env.example           # Variable template — copy to `.env`
├── setup.py               # Automation script (idempotent, cross-platform)
└── requirements.txt       # python-dotenv
```

---

## Quick start

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

## How it works

1. **Read `.env`.** `setup.py` loads variables via `python-dotenv` without
   polluting the process environment.
2. **Render the template.** Every `{{KEY}}` token in `opencode.json.example`
   is replaced with the matching `.env` value (JSON-escaped). Missing tokens
   are warned about, never silently dropped.
3. **Merge into the active config.** The rendered JSON is deep-merged into
   the existing `opencode.json` at the OpenCode config directory:
   - **Existing values win** on collision (your manual edits are preserved).
   - **Lists** are unioned with order preserved and duplicates removed.
   - **Dicts** are merged recursively.
   - Every collision is reported in the end-of-run recap so you can decide
     whether to reconcile.
4. **Symlink the folders.** Local plural directories are linked into the
   singular paths OpenCode expects:

   | Local        | OpenCode target               |
   | ------------ | ----------------------------- |
   | `agents/`    | `<opencode-dir>/agent`        |
   | `commands/`  | `<opencode-dir>/command`      |
   | `skills/`    | `<opencode-dir>/skill`        |
   | `mcp/`       | `<opencode-dir>/mcp`          |

   Existing real directories are backed up before being replaced (only when
   `--force` is given). Existing correct symlinks are skipped.

5. **Recap.** A summary block prints created / skipped / replaced symlinks,
   any backups, and a `[WARN]` list of every merge collision.

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

`--uninstall` is conservative: it leaves real directories and unrelated
symlinks alone, removing only symlinks whose target lives inside this
repository.

---

## Cross-platform notes

- **Linux / macOS:** symlink creation works out of the box.
- **Windows:** creating symbolic links requires either Developer Mode
  (Settings → Privacy & security → For developers) or an elevated shell.
  When permission is denied for a directory link, `setup.py` automatically
  falls back to an NTFS directory junction so the bridge still works.

---

## Adding new entries

1. Drop a new file into the relevant folder:
   - Agent     → `agents/<kebab-case-name>.md`
   - Command   → `commands/<kebab-case-name>.md`
   - Skill     → `skills/<snake_case_name>.py`
   - MCP       → `mcp/<server-name>.json`
2. Document it in [`AGENTS.md`](./AGENTS.md) (registry table + doc block).
3. Commit. No further `setup.py` run is needed — the symlinks make the
   change visible to OpenCode immediately.

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

## Security

`.env` is git-ignored. Never commit API keys. Keep secrets out of files
inside `agents/`, `commands/`, `skills/`, and `mcp/` — reference them via
environment variables instead.
