---
type: command
trigger: "/changelog"
---

# /changelog

## Purpose

Generate a changelog from git commit history since the last tag.

## Usage

```
/changelog [tag-range]
```

## Parameters

- `tag-range` — optional; e.g., `v1.0.0..HEAD` (default: last tag to HEAD).

## Behavior

Groups commits since the reference tag into Conventional Commits categories (Features, Bug Fixes, Documentation, etc.). Uses the `git-historian` agent to build a formatted changelog entry.

## Examples

**Input:** `/changelog v1.2.0..HEAD`

**Output:**
```
## Changelog (v1.2.0 → v1.3.0)

### Features
- Add user settings endpoint (abc1234)
- Add dark mode toggle (def5678)

### Bug Fixes
- Fix 404 on empty user list (ghi9012)

### Chores
- Bump express from 4.18 to 4.21 (jkl2345)
```

## See also

- `@git-historian` agent for detailed change narrative.
