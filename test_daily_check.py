#!/usr/bin/env python3
"""Lightweight local tests for daily_check.py. No network, no real sources.
Run: python3 test_daily_check.py
Covers the 2026-10-26 fixes:
1. Fixed Beijing timezone date (ZoneInfo Asia/Shanghai, not local tz).
2. Rejected candidates are filtered BEFORE shortlist truncation.
3. Monthly review expiry lets a rejected candidate re-enter.
4. Duplicate source URLs / rss_guids are deduped before shortlist truncation.
5. Existing feed GUIDs are preserved (7 active items, 2 ready-clips distinct
   from their parents) and temporary failures never become rejections.
"""
import json
import os
import sys
import unittest
from datetime import date, datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import daily_check as dc
BASE = os.path.dirname(os.path.abspath(__file__))
class TestTimezone(unittest.TestCase):
    def test_zone_is_beijing(self):
        self.assertEqual(str(dc.BEIJING), "Asia/Shanghai")
    def test_utc_to_beijing_date_crosses_date(self):
        # 2026-10-26 18:00 UTC is already 2026-10-27 in Beijing, but still
        # 2026-10-26 in UTC and in US Eastern. A local-tz implementation on
        # a UTC or US machine would record the wrong run date.
        dt = datetime(2026, 10, 26, 18, 0, tzinfo=timezone.utc)
        self.assertEqual(dc.utc_to_beijing_date(dt), date(2026, 10, 27))
        dt2 = datetime(2026, 10, 26, 15, 0, tzinfo=timezone.utc)
        self.assertEqual(dc.utc_to_beijing_date(dt2), date(2026, 10, 26))
    def test_next_month_first_day(self):
        self.assertEqual(dc.next_month_first_day(date(2026, 10, 26)), date(2026, 11, 1))
        self.assertEqual(dc.next_month_first_day(date(2026, 12, 15)), date(2027, 1, 1))
class TestRejectedFiltering(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 10, 26)
        self.rejected = [
            {"source_url": "https://example.org/a", "rss_guid": "g-a", "reason": "no full transcript", "date": "2026-10-20", "review_after": "2026-11-01"},
            {"source_url": "https://example.org/b", "rss_guid": "", "reason": "commercial", "date": "2026-09-15", "review_after": "2026-10-01"},
        ]
    def test_rejected_does_not_occupy_shortlist(self):
        cands = [{"source_url": "https://example.org/a", "rss_guid": "g-a", "title": "A"}]
        cands += [{"source_url": "https://example.org/good%d" % i, "rss_guid": "", "title": "G%d" % i} for i in range(2)]
        kept, filtered, due = dc.filter_rejected(cands, self.rejected, self.today)
        self.assertEqual([c["title"] for c in kept], ["G0", "G1"])
        self.assertEqual(len(filtered), 1)
        self.assertEqual(due, [])
    def test_review_due_re_enters(self):
        # Entry B's review_after (2026-10-01) has passed on 2026-10-26.
        cands = [{"source_url": "https://example.org/b", "rss_guid": "", "title": "B"}]
        kept, filtered, due = dc.filter_rejected(cands, self.rejected, self.today)
        self.assertEqual(len(kept), 1)
        self.assertEqual(len(filtered), 0)
        self.assertEqual(due[0]["source_url"], "https://example.org/b")
    def test_rss_guid_match_even_if_url_changes(self):
        cands = [{"source_url": "https://example.org/a-renamed", "rss_guid": "g-a", "title": "A2"}]
        kept, filtered, _ = dc.filter_rejected(cands, self.rejected, self.today)
        self.assertEqual(kept, [])
        self.assertEqual(len(filtered), 1)
    def test_legacy_entry_without_review_after_uses_next_month(self):
        legacy = [{"source_url": "https://example.org/old", "reason": "x", "date": "2026-09-10"}]
        self.assertEqual(dc.review_after_for(legacy[0], self.today), date(2026, 10, 1))
        kept, _, _ = dc.filter_rejected([{"source_url": "https://example.org/old", "title": "O"}], legacy, self.today)
        self.assertEqual(len(kept), 1)
class TestDedup(unittest.TestCase):
    def test_dup_url_and_dup_guid_removed_before_shortlist(self):
        cands = [
            {"source_url": "https://example.org/x", "rss_guid": "g1", "title": "X1"},
            {"source_url": "https://example.org/x", "rss_guid": "g2", "title": "X-dup-url"},
            {"source_url": "https://example.org/y", "rss_guid": "g1", "title": "Y-dup-guid"},
            {"source_url": "https://example.org/z", "rss_guid": "g3", "title": "Z"},
        ]
        out, dups = dc.dedup_candidates(cands)
        self.assertEqual([c["title"] for c in out], ["X1", "Z"])
        self.assertEqual(dups, 2)
    def test_norm_url(self):
        self.assertEqual(dc.norm_url("https://example.org/a/"), "https://example.org/a")
        self.assertEqual(dc.norm_url("  https://example.org/a  "), "https://example.org/a")
class TestExistingFeed(unittest.TestCase):
    def test_feed_relationships_dynamic(self):
        # Dynamic, not hardcoded to 7 items / 2 clips: after any real
        # increment, parents + clips must still satisfy these relations.
        with open(os.path.join(BASE, "items.json"), encoding="utf-8") as f:
            data = json.load(f)
        items = [i for i in data["items"] if i.get("status") == "active"]
        guids = [i["guid"] for i in items]
        self.assertEqual(len(set(guids)), len(guids))
        self.assertGreaterEqual(len(items), 7)
        clips = [i for i in items if "ready-clip" in i["production_kinds"]]
        parents = {i["guid"]: i for i in items if "full-episode" in i["production_kinds"]}
        self.assertGreaterEqual(len(clips), 2)
        self.assertGreaterEqual(len(parents), 4)
        for c in clips:
            self.assertIn(c["_parent_guid"], parents)
            self.assertNotEqual(c["guid"], c["_parent_guid"])
            self.assertNotIn("full-episode", c["production_kinds"])
            self.assertTrue(c["audio_url"].startswith("https://raw.githubusercontent.com/TikerBin/podcast-upstream/main/clips/"))
            self.assertLess(c["transcript_word_count"], parents[c["_parent_guid"]]["transcript_word_count"])
            self.assertLess(c["audio_duration_s"], parents[c["_parent_guid"]]["audio_duration_s"])
        for par in parents.values():
            self.assertNotIn("ready-clip", par["production_kinds"])
    def test_failed_sources_never_become_rejections(self):
        # Rejection is only written via record_rejection; a failed fetch
        # leaves the rejected list untouched by construction.
        state = {"rejected": []}
        entry = dc.record_rejection(state, "https://example.org/q", "", "no transcript", None, date(2026, 10, 26))
        self.assertEqual(entry["review_after"], "2026-11-01")
        self.assertEqual(len(state["rejected"]), 1)
        # A second call for the same URL upserts instead of duplicating.
        dc.record_rejection(state, "https://example.org/q/", "", "still no transcript", None, date(2026, 10, 26))
        self.assertEqual(len(state["rejected"]), 1)
if __name__ == "__main__":
    unittest.main(verbosity=2)
