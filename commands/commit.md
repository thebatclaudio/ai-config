---
type: command
trigger: "/commit"
---

# /commit

## Purpose

Suggest a Conventional Commits message based on staged changes.

## Usage

```
/commit [--scope <scope>] [--type <type>]
```

## Parameters

- `--scope` — optional; scope for the commit (e.g., "api", "ui").
- `--type` — optional; override the detected type (feat, fix, docs, etc.).

## Behavior

Analyzes staged changes using `git diff --staged`, parses them via the `git_diff_summarizer` skill, and generates a Conventional Commits message using the `conventional_commit` skill. Displays the message and the suggested type/scope for user approval.

## Examples

**Input:** `/commit`

**Output:**
```
Suggested commit message:

feat(api): add user settings endpoint

Adds GET /api/users/:id/settings with validation and caching.
Includes tests for valid, invalid, and empty responses.

---
Type: feat | Scope: api | Subject: add user settings endpoint
Ready? [y/n/e] (y=accept, n=reject, e=edit)
```

## See also

- `@git-historian` agent for commit explanations and PR bodies.
