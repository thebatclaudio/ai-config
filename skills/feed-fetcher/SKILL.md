---
name: feed-fetcher
kind: skill
scope: global
description: "Fetch, parse, filter, dedupe and merge RSS/Atom/JSON feeds listed in feeds.toml. Use when building a news digest from configured feeds."
---

# feed-fetcher

Fetch the feeds in `~/.config/ai-config/feeds.toml`, parse them (RSS 2.0, RSS 1.0/RDF,
Atom, JSON Feed), filter by topic and date, and merge them newest first.
Stdlib only; reading `feeds.toml` needs Python 3.11+.

`feed_fetcher.py` lives next to this file (`<skill-dir>` = the directory containing this `SKILL.md`).

## CLI (preferred)

```bash
python3 <skill-dir>/feed_fetcher.py Batman --days 3          # readable list
python3 <skill-dir>/feed_fetcher.py "climate policy" --json  # items + per-feed status
python3 <skill-dir>/feed_fetcher.py --days 1 --limit 30      # everything from today
```

- `topic`: keywords; every word must appear in the title or summary (case-insensitive).
- `--days N`: the window; default `settings.default_days` from the config, else 1. Undated items are kept.
- `--config PATH`: another feeds file (also `$AI_CONFIG_FEEDS`).
- `--json`: `{days, topic, feeds: [{source, url, items, error}], items: [...]}`. A failed feed
  has `error` set and never aborts the run.

## Config: `feeds.toml`

```toml
[settings]
language = "en"
default_days = 1
categories = ["comics", "tech-ai"]

[[feeds]]
name = "CBR"                         # display/source name
url = "https://www.cbr.com/feed/"    # RSS, Atom or JSON Feed URL (required)
category = "comics"                  # used to group the digest
```

## Library

```python
import sys; sys.path.insert(0, "<skill-dir>")
from feed_fetcher import fetch_all, filter_items, merge_feeds, summarize_items
items = filter_items(merge_feeds(fetch_all()), "batman", days=2)
print(summarize_items(items, max_chars=2000))
```

- `load_feeds_config(path=None) -> (settings, feeds)`
- `fetch_all(path=None, timeout=15, max_workers=8) -> [Feed]` (concurrent, config order)
- `fetch_feed(url, timeout=10, source=None, category=None) -> Feed` (errors in `Feed.error`)
- `parse_feed(data: bytes, url, source=None, category=None) -> Feed`
- `filter_items(items, query=None, days=None)`, `merge_feeds(feeds, limit=None)`,
  `deduplicate_items(items)`, `summarize_items(items, max_chars=500)`
- `FeedItem(title, link, source, published, summary, author, category)`; dates are UTC-aware.

Deduplication is per source (title + link + source). Merging the same story reported by
several outlets is left to the agent.

## Used by

- `news-curator`
- `/news`
