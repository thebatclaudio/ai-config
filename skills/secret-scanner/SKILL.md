---
name: secret-scanner
kind: skill
scope: global
description: "Scan a directory for accidentally committed secrets (API keys, tokens, credentials) using regex and entropy. Use before commits, reviews or publishing a repo."
---

# secret-scanner

Scan for accidentally committed secrets using regex and entropy analysis.

## How to use

`secret_scanner.py` lives next to this file (`<skill-dir>` = the directory containing this `SKILL.md`).
It is a stdlib-only Python library; import it from an inline script:

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0, "<skill-dir>")
from pathlib import Path
from secret_scanner import SecretScanner
s = SecretScanner()
print(s.summarize(s.scan_directory(Path("."))))
EOF
```

## API

- `SecretScanner(skip_dirs=None)`
- `.scan_directory(root, exclude_extensions=None) -> list[SecretFinding]`
- `.summarize(findings) -> str`, `SecretFinding.display()`

## Used by

- `code-reviewer`
- `dependency-auditor`
- `/review`
