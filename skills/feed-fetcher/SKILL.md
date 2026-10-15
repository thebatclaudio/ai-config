---
name: feed-fetcher
kind: skill
scope: global
description: "Normalize, dedupe, merge and summarize RSS/Atom/JSON feed items. Use when building a news digest from configured feeds."
---

# feed-fetcher

Normalize, deduplicate, merge and summarize RSS/Atom/JSON feed items.

> ⚠️ `fetch_feed()` is currently a **stub** (returns an empty feed with an error). Fetch content with your web-fetch tool or the `fetch` MCP server, build `FeedItem`s, then use the helpers below.

## How to use

`feed_fetcher.py` lives next to this file (`<skill-dir>` = the directory containing this `SKILL.md`).
It is a stdlib-only Python library; import it from an inline script:

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0, "<skill-dir>")
from feed_fetcher import merge_feeds, summarize_items
# feeds = [...]  # list[Feed] built from fetched content
# print(summarize_items(merge_feeds(feeds, limit=20)))
EOF
```

## API

- `FeedItem(...)`, `Feed(title, url, items, error=None)`
- `deduplicate_items(items)`, `merge_feeds(feeds, limit=None)`
- `summarize_items(items, max_chars=500) -> str`
- `fetch_feed(url, timeout=10)` — stub, see warning above.

## Used by

- `news-curator`
- `/news`
