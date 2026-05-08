---
type: command
trigger: "/post"
---

# /post

## Purpose

Draft a social-media post for a specific platform.

## Usage

```
/post [platform] <topic>
```

## Parameters

- `platform` — `x`, `linkedin`, `instagram`, `mastodon` (default: x).
- `topic` — what the post should be about.

## Behavior

Invokes the `@social-strategist` agent with the specified platform and topic. Returns a draft post with platform-appropriate formatting and timing recommendations.

## Examples

**Input:** `/post linkedin Just got promoted to Senior Engineer`

**Output:** A LinkedIn announcement post with celebratory tone, tags, and timing suggestions.

**Input:** `/post x "Excited about the new Python 3.15 features"`

**Output:** A short-form post optimized for Twitter/X.

## See also

- `@social-strategist` agent for multi-platform drafts and threads.
