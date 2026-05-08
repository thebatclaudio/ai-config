---
type: command
trigger: "/learn"
---

# /learn

## Purpose

Start or resume a study session on any topic.

## Usage

```
/learn <topic> [--level beginner|intermediate|advanced]
```

## Parameters

- `topic` — what you want to learn (e.g., "python", "kubernetes", "guitar").
- `--level` — optional; your current familiarity (default: beginner).

## Behavior

Invokes the `@learning-tutor` agent to create a study plan on the topic. If a study plan already exists (from memory), resumes from where you left off and quizzes you on previously covered material.

## Examples

**Input:** `/learn python --level beginner`

**Output:** A 5-week study plan covering Python fundamentals, with a session 1 guide and quiz.

**Input:** `/learn kubernetes`

**Output:** A study plan with modules, estimated time, and a quiz to establish your starting level.

## See also

- `@learning-tutor` agent for custom study sessions and progress tracking.
