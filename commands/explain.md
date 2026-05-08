---
type: command
trigger: "/explain"
---

# /explain

## Purpose

Get a plain-language walkthrough of a file, function, or code snippet.

## Usage

```
/explain <target>
```

## Parameters

- `target` — a file path, function name, or line range (e.g., `src/services/order.py`, `calculate_total`, `order.py:15-30`).

## Behavior

Uses the `repo_indexer` skill to locate symbols and read the code. Produces a structured explanation of what the target does, its inputs/outputs, how it fits into the broader architecture, and any notable patterns or concerns.

## Examples

**Input:** `/explain calculate_total`

**Output:** Explanation of the function: parameters, return type, logic flow, callers, and side effects.

**Input:** `/explain src/services/order.py`

**Output:** File-level overview with key classes/functions, architectural role, and dependencies.

## See also

- `@code-reviewer` agent for deeper analysis.
