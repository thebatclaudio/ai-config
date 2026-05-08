---
type: command
trigger: "/plan-day"
---

# /plan-day

## Purpose

Build a structured daily schedule.

## Usage

```
/plan-day [date] [--priorities "item1, item2"]
```

## Parameters

- `date` — optional; date to plan (default: today).
- `--priorities` — optional; comma-separated list of top priorities.

## Behavior

Invokes the `@daily-planner` agent to analyze the day and create a time-blocked schedule. Considers fixed commitments (from calendar) and to-dos.

## Examples

**Input:** `/plan-day --priorities "Finish Q3 roadmap, Code review PRs"`

**Output:** A full day schedule with deep-work blocks, meeting buffers, and breaks.

**Input:** `/plan-day 2026-05-15`

**Output:** Schedule for May 15.

## See also

- `@daily-planner` agent for deeper exploration.
