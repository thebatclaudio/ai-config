---
type: command
trigger: "/onboard"
---

# /onboard

## Purpose

Analyze the current project and generate a comprehensive plan to make it OpenCode-ready with tailored agents, commands, skills, and MCPs.

## Usage

```
/onboard [--global] [--quick]
```

## Parameters

- `--global` — allow proposing global entries (default: local `.opencode/` only).
- `--quick` — skip clarifying questions and generate a plan directly from the project scan.

## Behavior

1. Scans the project directory — reading `README.md`, config files (e.g. `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`), source file extensions, build and test tooling, CI/CD config, and any existing `.opencode/` folder.
2. Invokes the `@project-onboarder` agent to analyze the scan results.
3. The agent presents a project analysis summary and asks clarifying questions about workflow priorities, scope preferences, and sensitive operations.
4. Based on the analysis and user answers, the agent generates a plan with proposed agents, commands, skills, and MCPs for the project's stack.
5. The plan is presented to the user for confirmation before any files are created.
6. Once confirmed, all files are created in `.opencode/` (or globally if `--global` was used).

## Examples

**Input:** `/onboard`

**Output:** Project analysis, clarifying questions, a full onboarding plan with tables, and an implementation recap after confirmation.

**Input:** `/onboard --quick`

**Output:** Skips clarifying questions and directly generates a plan from the project scan.

## See also

- `@project-onboarder` agent — the agent that performs the analysis and plan generation.
- `/scaffold` — create individual stub files (agent/command/skill/mcp) manually.
- `@entry-scaffolder` agent — for fine-grained manual scaffolding.
