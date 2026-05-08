---
type: command
trigger: "/scaffold"
---

# /scaffold

## Purpose

Create a new agent/command/skill/mcp stub file following the project conventions.

## Usage

```
/scaffold <type> <name> [--local]
```

## Parameters

- `type` — `agent`, `command`, `skill`, or `mcp`.
- `name` — the file name (kebab-case for agents/commands, snake_case for skills).
- `--local` — optional; create in `.opencode/` instead of the global folders.

## Behavior

Invokes the `@entry-scaffolder` agent to generate a stub file following the templates in AGENTS.md. Also offers to register the new entry in the appropriate table.

## Examples

**Input:** `/scaffold agent code-reporter`

**Output:** A new file `agents/code-reporter.md` with the full agent template filled in.

## See also

- `@entry-scaffolder` agent for deeper customization.
