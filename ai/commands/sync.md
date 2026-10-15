---
name: sync
kind: command
scope: local
description: "Run `setup.py` and show the recap, keeping the bridge fresh."
trigger: "/sync"
argument-hint: "[--target <tools>] [--layer <layer>] [--dry-run] [--force]"
---

# /sync

## Purpose

Run `setup.py` and show the recap, keeping the bridge fresh.

## Usage

```
/sync [--target <tools>] [--layer <layer>] [--dry-run] [--force]
```

## Parameters

- `--target` — optional; `auto` (default, detected tools), `all`, or a comma list (e.g. `opencode`).
- `--layer` — optional; `all` (default), `global`, or `local`.
- `--dry-run` — show what would happen without making changes.
- `--force` — replace existing real directories at symlink targets.

## Behavior

Runs `python setup.py` (or `python3 setup.py`) with the flags passed through. Captures and displays the full output, including the collision recap.

## Examples

**Input:** `/sync --dry-run`
**Output:** Recap showing what symlinks would be created/updated/skipped.

## See also

- `setup.py` script in the repository root.
