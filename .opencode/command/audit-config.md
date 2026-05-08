---
type: command
trigger: "/audit-config"
---

# /audit-config

## Purpose

Run all config validators: AGENTS.md linter + setup health check.

## Usage

```
/audit-config
```

## Behavior

Consecutively invokes the `@agents-curator` and `@setup-doctor` agents. Collects their reports into a single config health summary.

## Examples

**Input:** `/audit-config`
**Output:** Combined report: AGENTS.md audit results + symlink/config health check.

## See also

- `@agents-curator` for AGENTS.md linting.
- `@setup-doctor` for config health checks.
