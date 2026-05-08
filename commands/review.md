---
type: command
trigger: "/review"
---

# /review

## Purpose

Run the code-reviewer agent on staged or specified changes.

## Usage

```
/review [--staged | --file <path>]
```

## Parameters

- `--staged` — review staged changes (default).
- `--file` — review a specific file.

## Behavior

Loads the diff or file content, invokes the `@code-reviewer` agent, and returns structured findings with severity levels.

## Examples

**Input:** `/review --staged`

**Output:** Full code review of staged changes with blocker/warning/suggestion/question categories and test coverage notes.

**Input:** `/review --file src/services/order.py`

**Output:** Review of the specified file with architectural feedback.

## See also

- `@code-reviewer` agent for more granular review requests.
