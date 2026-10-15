"""
feed_fetcher.py

Fetch and normalize RSS/Atom/JSON feeds for news agents.
Handles various feed formats and deduplication.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin, urlparse


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


@dataclass
class Feed:
    """Represents a feed source."""
    title: str
    url: str
    items: List[FeedItem]
    last_updated: Optional[datetime] = None
    error: Optional[str] = None


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


def fetch_feed(url: str, timeout: int = 10) -> Feed:
    """
    Fetch a feed from a URL. Returns a Feed object.
    If fetching fails, returns a Feed with error set.

    This is a stub; real implementation would use feedparser or similar.
    """
    return Feed(
        title=url,
        url=url,
        items=[],
        error="Feed fetching requires feedparser library (not included in stub)",
    )


def merge_feeds(feeds: List[Feed], limit: Optional[int] = None) -> List[FeedItem]:
    """
    Merge multiple feeds into a single sorted list of items.
    Deduplicates by ID hash. Optionally limit to top N items.
    """
    all_items = []
    for feed in feeds:
        if feed.error:
            continue
        all_items.extend(feed.items)

    # Deduplicate
    deduped = deduplicate_items(all_items)

    # Sort by published date (newest first)
    deduped.sort(
        key=lambda x: x.published or datetime.min,
        reverse=True,
    )

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
