---
name: repo-indexer
kind: skill
scope: global
description: "Build a lightweight file and symbol index of a repository and look up symbols. Use when navigating, explaining or refactoring an unfamiliar codebase."
---

# repo-indexer

Build a lightweight file/symbol index of a repository.

## How to use

`repo_indexer.py` lives next to this file (`<skill-dir>` = the directory containing this `SKILL.md`).
It is a stdlib-only Python library; import it from an inline script:

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0, "<skill-dir>")
from repo_indexer import RepoIndexer
r = RepoIndexer("."); r.index()
print(r.stats()); print(r.find_symbol("main"))
EOF
```

## API

- `RepoIndexer(repo_root)`, `.index(skip_dirs=None)`
- `.find_symbol(name)`, `.files_by_extension(".py")`
- `.file_count()`, `.symbol_count()`, `.stats() -> dict`

## Used by

- `refactor-surgeon`
- `project-onboarder`
- `/explain`
