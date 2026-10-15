"""
Offline tests for skills/feed-fetcher/feed_fetcher.py (no network).

    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "skills" / "feed-fetcher"))

from feed_fetcher import (  # noqa: E402
    Feed, FeedItem, fetch_feed, filter_items, load_feeds_config, merge_feeds, parse_feed,
)

RSS = b"""<?xml version="1.0"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel><title>Comics Daily</title>
    <item><title>The Batman Part II gets a new director</title>
      <link>https://example.com/batman</link>
      <description>&lt;p&gt;Big &amp;amp; bold news&lt;/p&gt;</description>
      <dc:creator>Jane Doe</dc:creator>
      <pubDate>Wed, 15 Oct 2026 22:32:00 +0000</pubDate></item>
    <item><title>Superman sequel update</title><link>https://example.com/superman</link>
      <pubDate>Mon, 06 Oct 2026 10:00:00 GMT</pubDate></item>
  </channel></rss>"""

ATOM = b"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Dev Blog</title>
  <entry><title type="html">Python &lt;b&gt;3.14&lt;/b&gt; released</title>
    <link rel="replies" href="https://example.com/comments"/>
    <link rel="alternate" href="https://example.com/py314"/>
    <author><name>Guido</name></author>
    <published>2026-10-15T09:00:00Z</published>
    <summary>Release notes</summary></entry>
</feed>"""

RDF = b"""<?xml version="1.0"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel><title>Old School</title></channel>
  <item><title>RDF item</title><link>https://example.com/rdf</link>
    <dc:date>2026-10-14T08:00:00+02:00</dc:date></item>
</rdf:RDF>"""

JSONFEED = json.dumps({
    "version": "https://jsonfeed.org/version/1.1", "title": "JSON News",
    "items": [{"id": "1", "url": "https://example.com/j1", "title": "Gotham at night",
               "content_text": "Batman spotted", "date_published": "2026-10-15T12:00:00Z",
               "author": {"name": "Ann"}}],
}).encode()

NOW = datetime(2026, 10, 16, 0, 0, tzinfo=timezone.utc)


class ParseTests(unittest.TestCase):
    def test_rss(self):
        feed = parse_feed(RSS, "https://example.com/rss", category="comics")
        self.assertIsNone(feed.error)
        self.assertEqual(feed.title, "Comics Daily")
        first = feed.items[0]
        self.assertEqual(first.title, "The Batman Part II gets a new director")
        self.assertEqual(first.link, "https://example.com/batman")
        self.assertEqual(first.summary, "Big & bold news")
        self.assertEqual(first.author, "Jane Doe")
        self.assertEqual(first.category, "comics")
        self.assertEqual(first.published, datetime(2026, 10, 15, 22, 32, tzinfo=timezone.utc))

    def test_atom_prefers_alternate_link(self):
        item = parse_feed(ATOM, "u", source="My Blog").items[0]
        self.assertEqual(item.title, "Python 3.14 released")
        self.assertEqual(item.link, "https://example.com/py314")
        self.assertEqual(item.author, "Guido")
        self.assertEqual(item.source, "My Blog")

    def test_rdf_and_timezone_normalized(self):
        item = parse_feed(RDF, "u").items[0]
        self.assertEqual(item.published, datetime(2026, 10, 14, 6, 0, tzinfo=timezone.utc))

    def test_json_feed(self):
        feed = parse_feed(JSONFEED, "u")
        self.assertEqual(feed.title, "JSON News")
        self.assertEqual(feed.items[0].summary, "Batman spotted")
        self.assertEqual(feed.items[0].author, "Ann")

    def test_bad_input_sets_error(self):
        self.assertIn("not a valid", parse_feed(b"<html><body", "u").error)
        self.assertIn("unexpected root", parse_feed(b"<html></html>", "u").error)
        self.assertIn("invalid JSON", parse_feed(b"{nope", "u").error)


class FilterMergeTests(unittest.TestCase):
    def items(self):
        return parse_feed(RSS, "a").items + parse_feed(JSONFEED, "b").items + [
            FeedItem(title="Undated Batman story", link="x", source="c")]

    def test_topic_and_days(self):
        hits = filter_items(self.items(), "batman", days=1, now=NOW)
        self.assertEqual([i.link for i in hits],
                         ["https://example.com/batman", "https://example.com/j1", "x"])
        self.assertEqual(filter_items(self.items(), "superman", days=1, now=NOW), [])
        self.assertEqual(len(filter_items(self.items(), "superman", days=30, now=NOW)), 1)
        self.assertEqual(len(filter_items(self.items(), "batman director", now=NOW)), 1)

    def test_merge_sorts_mixed_dated_and_undated(self):
        feeds = [Feed(title="a", url="a", items=self.items()), Feed(title="bad", url="b", error="x")]
        merged = merge_feeds(feeds)
        self.assertEqual(merged[0].link, "https://example.com/batman")
        self.assertEqual(merged[-1].link, "x")
        self.assertEqual(len(merge_feeds(feeds + feeds)), len(merged))


class FetchConfigTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.dir)

    def test_fetch_local_file_and_errors(self):
        path = self.dir / "feed.xml"
        path.write_bytes(RSS)
        feed = fetch_feed(path.as_uri(), source="Local", category="comics")
        self.assertIsNone(feed.error)
        self.assertEqual(len(feed.items), 2)
        self.assertEqual(feed.items[0].source, "Local")
        missing = fetch_feed((self.dir / "nope.xml").as_uri())
        self.assertTrue(missing.error.startswith("fetch failed"))

    def test_load_config(self):
        cfg = self.dir / "feeds.toml"
        cfg.write_text('[settings]\ndefault_days = 3\n\n[[feeds]]\nname = "A"\nurl = "https://a"\n'
                       '\n[[feeds]]\nname = "no url"\n')
        settings, feeds = load_feeds_config(cfg)
        self.assertEqual(settings["default_days"], 3)
        self.assertEqual([f["name"] for f in feeds], ["A"])


if __name__ == "__main__":
    unittest.main()
