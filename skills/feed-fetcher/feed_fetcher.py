"""
feed_fetcher.py

Fetch, parse, filter and normalize RSS/Atom/JSON feeds for news agents.
Stdlib only (``tomllib`` needs Python 3.11+ for the feeds config).

Library:
    load_feeds_config(path=None) -> (settings, feed_entries)
    fetch_feed(url, ...) -> Feed            # one feed; errors go in Feed.error
    fetch_all(path=None, ...) -> [Feed]     # every feed in feeds.toml, concurrently
    parse_feed(data, url, ...) -> Feed      # RSS 2.0, RSS 1.0 (RDF), Atom, JSON Feed
    filter_items(items, query=None, days=None)
    merge_feeds(feeds, limit=None), deduplicate_items(items), summarize_items(items)

CLI:
    python3 feed_fetcher.py [TOPIC] [--days N] [--config PATH] [--limit N] [--json]
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_CONFIG = Path("~/.config/ai-config/feeds.toml")
USER_AGENT = "Mozilla/5.0 (compatible; ai-config-feed-fetcher/1.0)"
MAX_BYTES = 10 * 1024 * 1024
EPOCH = datetime.min.replace(tzinfo=timezone.utc)


@dataclass
class FeedItem:
    """Represents a single item (article/post) from a feed."""
    title: str
    link: str
    source: str
    published: Optional[datetime] = None
    summary: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None

    def id_hash(self) -> str:
        """Generate a unique hash for deduplication."""
        content = f"{self.title}|{self.link}|{self.source}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["published"] = self.published.isoformat() if self.published else None
        return d


@dataclass
class Feed:
    """Represents a feed source."""
    title: str
    url: str
    items: List[FeedItem] = field(default_factory=list)
    last_updated: Optional[datetime] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _clean(text: Optional[str]) -> str:
    """Strip HTML tags and entities, collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    """RFC 822 (RSS) or ISO 8601 (Atom/JSON) -> aware UTC datetime."""
    if not value:
        return None
    value = value.strip()
    for parse in (parsedate_to_datetime, lambda v: datetime.fromisoformat(v.replace("Z", "+00:00"))):
        try:
            dt = parse(value)
        except (TypeError, ValueError, IndexError):
            continue
        if dt is not None:
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    return None


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _xml_item(el: ET.Element, source: str, category: Optional[str]) -> FeedItem:
    children: Dict[str, ET.Element] = {}
    for child in el:
        children.setdefault(_local(child.tag), child)

    def text(*names: str) -> str:
        for name in names:
            node = children.get(name)
            if node is not None and (node.text or len(node)):
                return "".join(node.itertext())
        return ""

    link = ""
    for child in el:
        if _local(child.tag) != "link":
            continue
        href = child.get("href") or (child.text or "").strip()
        if href and child.get("rel") in (None, "alternate"):
            link = href
            break
        link = link or href

    published = None
    for name in ("pubDate", "published", "updated", "date", "issued"):
        published = _parse_date(text(name))
        if published:
            break

    return FeedItem(
        title=_clean(text("title")),
        link=link,
        source=source,
        published=published,
        summary=_clean(text("description", "summary", "content", "encoded")) or None,
        author=_clean(text("creator", "author")) or None,
        category=category,
    )


def parse_feed(data: bytes, url: str, source: Optional[str] = None,
               category: Optional[str] = None) -> Feed:
    """Parse RSS 2.0, RSS 1.0 (RDF), Atom or JSON Feed bytes into a Feed."""
    stripped = data.lstrip()
    if stripped[:1] == b"{":
        try:
            doc = json.loads(stripped)
        except json.JSONDecodeError as exc:
            return Feed(title=source or url, url=url, error=f"invalid JSON feed: {exc}")
        name = source or doc.get("title") or url
        items = [
            FeedItem(
                title=_clean(it.get("title")),
                link=it.get("url") or it.get("external_url") or "",
                source=name,
                published=_parse_date(it.get("date_published") or it.get("date_modified")),
                summary=_clean(it.get("summary") or it.get("content_text") or it.get("content_html")) or None,
                author=_clean((it.get("author") or {}).get("name")) or None,
                category=category,
            )
            for it in doc.get("items") or []
        ]
        return Feed(title=name, url=url, items=items)

    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        return Feed(title=source or url, url=url, error=f"not a valid RSS/Atom feed: {exc}")

    kind = _local(root.tag)
    if kind not in ("rss", "feed", "RDF"):
        return Feed(title=source or url, url=url, error=f"unexpected root element <{kind}>")

    channel = next((e for e in root.iter() if _local(e.tag) == "channel"), root)
    feed_title = next((_clean(e.text) for e in channel if _local(e.tag) == "title"), "")
    name = source or feed_title or url
    entries = [e for e in root.iter() if _local(e.tag) in ("item", "entry")]
    updated = next((_parse_date(e.text) for e in channel
                    if _local(e.tag) in ("lastBuildDate", "updated")), None)
    return Feed(title=name, url=url, items=[_xml_item(e, name, category) for e in entries],
                last_updated=updated)


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def fetch_feed(url: str, timeout: int = 10, source: Optional[str] = None,
               category: Optional[str] = None) -> Feed:
    """
    Fetch and parse a feed. Never raises for network/parse problems:
    on failure the returned Feed has no items and ``error`` set.
    """
    request = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/feed+json, "
                  "application/xml;q=0.9, */*;q=0.8",
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as exc:
        return Feed(title=source or url, url=url, error=f"HTTP {exc.code}")
    except (urllib.error.URLError, OSError, ValueError) as exc:
        reason = getattr(exc, "reason", exc)
        return Feed(title=source or url, url=url, error=f"fetch failed: {reason}")
    if len(data) > MAX_BYTES:
        return Feed(title=source or url, url=url, error="response larger than 10 MB")
    return parse_feed(data, url, source=source, category=category)


def load_feeds_config(path: Optional[os.PathLike] = None) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Read feeds.toml -> (settings, feeds). ``path`` defaults to $AI_CONFIG_FEEDS
    or ~/.config/ai-config/feeds.toml. Each feed needs at least ``url``.
    """
    try:
        import tomllib
    except ImportError as exc:  # Python < 3.11
        raise RuntimeError("reading feeds.toml needs Python 3.11+ (tomllib)") from exc
    cfg = Path(path or os.environ.get("AI_CONFIG_FEEDS") or DEFAULT_CONFIG).expanduser()
    with cfg.open("rb") as fh:
        doc = tomllib.load(fh)
    feeds = [f for f in doc.get("feeds") or [] if isinstance(f, dict) and f.get("url")]
    return dict(doc.get("settings") or {}), feeds


def fetch_all(path: Optional[os.PathLike] = None, timeout: int = 15, max_workers: int = 8) -> List[Feed]:
    """Fetch every feed in feeds.toml concurrently, in config order."""
    _, entries = load_feeds_config(path)
    if not entries:
        return []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        return list(pool.map(
            lambda f: fetch_feed(f["url"], timeout=timeout, source=f.get("name"), category=f.get("category")),
            entries,
        ))


# ---------------------------------------------------------------------------
# Filtering, merging, summarizing
# ---------------------------------------------------------------------------

def filter_items(items: List[FeedItem], query: Optional[str] = None, days: Optional[float] = None,
                 now: Optional[datetime] = None) -> List[FeedItem]:
    """
    Keep items matching every word of ``query`` (case-insensitive, title or
    summary) and, when ``days`` is set, published within the last N days.
    Undated items are kept by the date filter (they can't be ruled out).
    """
    words = [w.lower() for w in (query or "").split()]
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=days) if days else None
    out = []
    for item in items:
        haystack = f"{item.title} {item.summary or ''}".lower()
        if any(w not in haystack for w in words):
            continue
        if cutoff and item.published and item.published < cutoff:
            continue
        out.append(item)
    return out


def deduplicate_items(items: List[FeedItem]) -> List[FeedItem]:
    """
    Remove duplicate items based on ID hash.
    Returns items in the order they first appeared.
    """
    seen = set()
    deduped = []
    for item in items:
        item_id = item.id_hash()
        if item_id not in seen:
            seen.add(item_id)
            deduped.append(item)
    return deduped


def merge_feeds(feeds: List[Feed], limit: Optional[int] = None) -> List[FeedItem]:
    """
    Merge multiple feeds into a single list, newest first (undated last).
    Deduplicates by ID hash. Optionally limit to top N items.
    """
    all_items = [item for feed in feeds if not feed.error for item in feed.items]
    deduped = deduplicate_items(all_items)
    deduped.sort(key=lambda x: x.published or EPOCH, reverse=True)
    return deduped[:limit] if limit else deduped


def summarize_items(items: List[FeedItem], max_chars: int = 500) -> str:
    """
    Generate a text summary of feed items.
    """
    lines = []
    for item in items:
        lines.append(f"• {item.title}")
        if item.author:
            lines.append(f"  by {item.author}")
        if item.summary:
            summary_text = item.summary[:200] + ("…" if len(item.summary) > 200 else "")
            lines.append(f"  {summary_text}")
        lines.append(f"  {item.link}")
        lines.append("")

    result = "\n".join(lines)
    return result[:max_chars] + ("…" if len(result) > max_chars else "")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch configured feeds and print matching items.")
    parser.add_argument("topic", nargs="*", help="keywords; every word must appear in title or summary")
    parser.add_argument("--days", type=float, default=None, help="only items from the last N days "
                        "(default: settings.default_days, else 1)")
    parser.add_argument("--config", default=None, help=f"feeds file (default: {DEFAULT_CONFIG})")
    parser.add_argument("--limit", type=int, default=None, help="max items to print")
    parser.add_argument("--json", action="store_true", help="print JSON (items + per-feed status)")
    args = parser.parse_args(argv)

    try:
        settings, _ = load_feeds_config(args.config)
    except FileNotFoundError as exc:
        print(f"feeds config not found: {exc.filename}", file=sys.stderr)
        return 2
    days = args.days if args.days is not None else float(settings.get("default_days", 1))

    feeds = fetch_all(args.config)
    items = filter_items(merge_feeds(feeds), " ".join(args.topic), days=days)
    if args.limit:
        items = items[:args.limit]

    status = [{"source": f.title, "url": f.url, "items": len(f.items), "error": f.error} for f in feeds]
    if args.json:
        json.dump({"days": days, "topic": " ".join(args.topic) or None, "feeds": status,
                   "items": [i.to_dict() for i in items]}, sys.stdout, indent=2, ensure_ascii=False)
        print()
    else:
        for item in items:
            when = item.published.strftime("%Y-%m-%d %H:%M") if item.published else "undated"
            print(f"[{when}] {item.source}: {item.title}\n    {item.link}")
        failed = [s for s in status if s["error"]]
        print(f"\n{len(feeds)} feeds, {sum(s['items'] for s in status)} items scanned, "
              f"{len(items)} shown (last {days:g} day(s)).", file=sys.stderr)
        for s in failed:
            print(f"  failed: {s['source']} — {s['error']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
