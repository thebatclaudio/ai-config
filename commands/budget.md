---
type: command
trigger: "/budget"
---

# /budget

## Purpose

Log an expense, see spending summaries, or follow up on savings goals.

## Usage

```
/budget add <amount> <category> [description]
/budget summary [month]
/budget categories
/budget goals
```

## Behavior

Quickly records an expense in the CSV ledger (using the `csv_ledger` skill), then invokes the `@budget-coach` agent to provide context on the spending. If no arguments are given, opens an interactive budget session.

## Examples

**Input:** `/budget add 34.50 groceries "Weekly shop at Trader Joe's"`

**Output:**
```
✓ Logged: $34.50 on 2026-05-08 → Groceries
  Description: Weekly shop at Trader Joe's

This week's grocery total: $89.50
Last week at this time: $72.00 (+24%)
```

**Input:** `/budget summary May`
**Output:** Shows a category breakdown for May.

## See also

- `@budget-coach` agent for deeper financial advice.
