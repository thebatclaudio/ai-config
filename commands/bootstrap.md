---
name: bootstrap
kind: command
scope: global
description: "Start a brand-new project from a verbal description: discover requirements through conversation, research current best practices and AI tooling online, recommend a tech stack, then scaffold the repository and its AI coding-agent configuration for your tool(s)."
trigger: "/bootstrap"
argument-hint: "[idea] [--tools <list>]"
---

# /bootstrap

## Purpose

Start a brand-new project from a verbal description: discover requirements through conversation, research current best practices and AI tooling online, recommend a tech stack, then scaffold the repository and its AI coding-agent configuration for your tool(s).

## Usage

```
/bootstrap [idea] [--tools opencode,pi,claude]
```

## Parameters

- `idea` — optional one-liner description of what you want to build. If omitted, the agent will ask.
- `--tools` — comma-separated target coding tools. Default: the tool running now, confirmed during discovery.

## Behavior

1. Invokes the `@project-bootstrapper` agent.
2. The agent holds a discovery conversation (product, users, shape, ops, team, AI surface area) until it has enough signal.
3. The agent researches candidate frameworks, libraries, and AI-tooling patterns online (via the `fetch` MCP) and cites sources.
4. The agent proposes a stack, repository layout, and a tailored AI-tool config (agents, commands, skills, MCPs) for each target tool.
5. After explicit user confirmation, the agent scaffolds the repository, writes config files, and initializes `AGENTS.md` plus each target tool's native config (see the `agent-config-targets` skill).
6. No files are written before the user confirms the plan.

## Examples

**Input:** `/bootstrap`

**Output:** Discovery questions, then — after answers — research notes, a stack proposal, AI-tool config plan, and (post-confirmation) the scaffolded project.

**Input:** `/bootstrap a real-time collaborative note app, solo dev, free tier`

**Output:** Skips the broadest questions, asks only the gaps, then proceeds to research and proposal.

## See also

- `@project-bootstrapper` agent — performs discovery, research, and scaffolding for new projects.
- `@project-onboarder` / `/onboard` — for **existing** projects that need AI-tool config added.
- `/scaffold` — create individual stub files manually after the project exists.
