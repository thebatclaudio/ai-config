---
type: command
trigger: "/news"
---

# /news

## Purpose

Get a curated news digest on topics you care about.

## Usage

```
/news [topic] [--days N]
```

## Parameters

- `topic` — optional; filter news to a specific topic (e.g., "AI", "climate", "tech"). If omitted, shows all.
- `--days` — optional; how many days back to include (default 1).

## Behavior

Invokes the `@news-curator` agent with your configured feeds. Fetches and deduplicates stories, filters to the requested topic (if any), and presents them in a structured digest.

## Examples

**Input:** `/news AI --days 3`

**Output:** Curated digest of AI stories from the last 3 days, grouped by source.

**Input:** `/news`

**Output:** Full daily digest from all configured feeds.

## See also

- `@news-curator` agent for detailed control over the digest format.
- `~/.config/opencode/personal/feeds.toml` for configuring feeds.
