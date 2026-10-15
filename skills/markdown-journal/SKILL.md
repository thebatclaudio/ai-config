---
name: markdown-journal
kind: skill
scope: global
description: "Create, read, append to and list daily markdown journal entries. Use for journaling, mood check-ins and retrospectives."
---

# markdown-journal

Open and append daily markdown journal entries (`YYYY-MM-DD.md`). Default root: `~/Documents/opencode/journal/` (override with `journal_location`).

## How to use

`markdown_journal.py` lives next to this file (`<skill-dir>` = the directory containing this `SKILL.md`).
It is a stdlib-only Python library; import it from an inline script:

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0, "<skill-dir>")
from markdown_journal import MarkdownJournal
j = MarkdownJournal()
print(j.create_today_entry())
j.append_entry("## Evening\nGrateful for ...")
EOF
```

## API

- `MarkdownJournal(root=None)`
- `.today_path()`, `.create_today_entry(template=None) -> str`
- `.append_entry(content)`, `.get_entry(date=None)`, `.list_entries(limit=30)`

## Used by

- `journal-coach`
- `/journal`
