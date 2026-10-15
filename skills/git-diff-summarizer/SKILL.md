---
name: git-diff-summarizer
kind: skill
scope: global
description: "Parse a unified git diff into per-file, per-hunk structured data with languages and stats. Use before reviewing, summarizing or describing code changes."
---

# git-diff-summarizer

Parse unified git diffs into structured chunks (files, hunks, change type, language, stats).

## How to use

`git_diff_summarizer.py` lives next to this file (`<skill-dir>` = the directory containing this `SKILL.md`).
It is a stdlib-only Python library; import it from an inline script:

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0, "<skill-dir>")
import subprocess
from git_diff_summarizer import parse_diff
s = parse_diff(subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True).stdout)
for f in s.files: print(f.summary())
EOF
```

## API

- `parse_diff(diff_text) -> DiffSummary`
- `DiffSummary.by_type(ChangeType.ADDED | MODIFIED | DELETED | RENAMED)`
- `FileDiff.language()`, `FileDiff.summary() -> dict`, `Hunk.added_lines()`, `Hunk.removed_lines()`

## Used by

- `code-reviewer`
- `git-historian`
- `/review`
- `/pr`
