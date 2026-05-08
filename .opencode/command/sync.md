---
type: command
trigger: "/sync"
---

# /sync

## Purpose

Run `setup.py` and show the recap, keeping the bridge fresh.

## Usage

```
/sync [--dry-run] [--force]
```

## Parameters

- `--dry-run` — show what would happen without making changes.
- `--force` — replace existing real directories at symlink targets.

## Behavior

Runs `python setup.py` (or `python3 setup.py`) with the flags passed through. Captures and displays the full output, including the collision recap.

## Examples

**Input:** `/sync --dry-run`
**Output:** Recap showing what symlinks would be created/updated/skipped.

## See also

- `setup.py` script in the repository root.
