---
type: command
trigger: "/journal"
---

# /journal

## Purpose

Open or continue today's journal entry.

## Usage

```
/journal [type]
```

## Parameters

- `type` — optional; `checkin`, `standard`, `retro`, `free` (default: standard).

## Behavior

Opens today's entry using the `markdown_journal` skill and invokes the `@journal-coach` agent with the appropriate template. If today's entry already exists, resumes from where you left off.

## Examples

**Input:** `/journal checkin`

**Output:** A quick 3-question check-in prompt.

**Input:** `/journal retro`

**Output:** A weekly retrospective template with mood tracking and reflection prompts.

## See also

- `@journal-coach` agent for guided journal sessions.
- Journal files stored in `~/Documents/opencode/journal/YYYY-MM-DD.md`.
