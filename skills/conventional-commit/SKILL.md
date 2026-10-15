---
name: conventional-commit
kind: skill
scope: global
description: "Parse, lint and suggest Conventional Commits messages. Use when writing, validating or fixing a commit message, or picking a commit type for a change."
---

# conventional-commit

Format, lint and suggest Conventional Commits messages (`<type>(<scope>): <subject>`).

## How to use

`conventional_commit.py` lives next to this file (`<skill-dir>` = the directory containing this `SKILL.md`).
It is a stdlib-only Python library; import it from an inline script:

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0, "<skill-dir>")
from conventional_commit import lint_commit_message, suggest_commit_type
print(lint_commit_message("feat(api): add pagination"))
print(suggest_commit_type("fix crash when list is empty"))
EOF
```

## API

- `parse_commit_message(msg) -> ConventionalCommit | None`
- `lint_commit_message(msg) -> list[str]` — empty list means valid.
- `suggest_commit_type(change_description) -> (type, confidence)`
- `ConventionalCommit(...).to_string()`, `.is_breaking()`

## Used by

- `git-historian`
- `/commit`
- `/changelog`
