---
name: agents-md-linter
kind: skill
scope: local
description: "Validate that AGENTS.md registry tables match the files on disk (global and ai/ layers). Use when auditing this ai-config repository."
---

# agents-md-linter

Validate AGENTS.md ↔ filesystem consistency for this ai-config repository.

## How to use

Run from the repository root:

```bash
python3 ai/skills/agents-md-linter/agents_md_linter.py
```

Exit code 1 on errors. Prints `[ERROR]`, `[WARN]`, `[INFO]` lines.

## Used by

- `agents-curator`
- `/audit-config`
