---
name: csv-ledger
kind: skill
scope: global
description: "Append and query expenses in a CSV ledger (monthly totals, per-category totals). Use when recording spending or summarizing a budget."
---

# csv-ledger

Append and query expense entries in a CSV-based ledger. Default ledger: `BUDGET_LEDGER_LOCATION` from `.env`, else `~/Documents/ai-config/budget/ledger.csv`.

## How to use

`csv_ledger.py` lives next to this file (`<skill-dir>` = the directory containing this `SKILL.md`).
It is a stdlib-only Python library; import it from an inline script:

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0, "<skill-dir>")
from datetime import datetime
from pathlib import Path
from csv_ledger import ExpenseLedger, ExpenseEntry
l = ExpenseLedger(Path("~/Documents/ai-config/budget/ledger.csv").expanduser())
l.add_entry(ExpenseEntry(datetime.now(), 12.5, "food", "lunch", currency="EUR"))
print(l.total_by_category(datetime.now().year, datetime.now().month))
EOF
```

## API

- `ExpenseLedger(path)` — creates the file with headers if missing.
- `.add_entry(ExpenseEntry(date, amount, category, description, tags=None, currency="EUR"))`
- `.read_all()`, `.entries_by_month(y, m)`, `.entries_by_category(cat)`
- `.total_by_category(y, m) -> dict`, `.monthly_total(y, m) -> float`

## Used by

- `budget-coach`
- `/budget`
