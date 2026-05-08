---
type: command
trigger: "/decide"
---

# /decide

## Purpose

Walk through a structured decision-making process for a choice.

## Usage

```
/decide <question>
```

## Parameters

- `question` — the decision you're facing, described in natural language.

## Behavior

Invokes the `@decision-helper` agent to guide you through framing options, establishing criteria, scoring, and a recommendation with a sleep-on-it reminder.

## Examples

**Input:** `/decide Should I accept the startup job offer or stay at my current company?`

**Output:** A decision matrix with weighted criteria, scoring, tensions, and a recommendation.

**Input:** `/decide Hike or read this Saturday?`

**Output:** A lightweight, fast framework for a low-stakes decision.

## See also

- `@decision-helper` agent for deeper exploration and decision history.
