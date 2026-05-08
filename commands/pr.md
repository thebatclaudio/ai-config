---
type: command
trigger: "/pr"
---

# /pr

## Purpose

Draft a PR title and body from commits on the current branch.

## Usage

```
/pr [base-branch]
```

## Parameters

- `base-branch` — optional; target branch (default: main).

## Behavior

Gathers commit history from the current feature branch relative to `base`. Groups commits by type (feat, fix, chore) and generates a PR body with a summary, change list, and testing notes. Output is ready to pipe into `gh pr create`.

## Examples

**Input:** `/pr main`

**Output:**
```
## PR Title — feat(api): add user settings endpoint

### Summary
Adds a new user settings endpoint with input validation, caching, and full test coverage.

### Changes

**Features:**
- Add GET /api/users/:id/settings
- Add PUT /api/users/:id/settings with validation

**Fixes:**
- Handle missing user gracefully (404 instead of 500)

### Testing
- Added 4 unit tests, 2 integration tests
- Manual: curl GET/PUT with valid + invalid payloads
```

## See also

- `@git-historian` agent for deeper narrative generation.
