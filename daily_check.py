#!/usr/bin/env python3
"""Daily candidate check for podcast-upstream (read-only, never modifies items.json).
Reports: existing feed counts, candidates from verified public sources,
dedup counts, and a shortlist for the daily agent to evaluate.
Exit 0 even when candidates exist (candidates are not failures);
exit 2 only when every source fetch fails (network/source outage).
Sources (no login/paywall bypass, no guessed MP3):
- NASA Curious Universe Megaphone RSS (official, public)
- NOAA Ocean Podcast index page (official, public HTML listing)
Usage: python3 daily_check.py [--state daily_state.local.json] [--shortlist 5]
"""
import argparse
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
BASE = os.path.dirname(os.path.abspath(__file__))
CURIOUS_RSS = "https://feeds.megaphone.fm/NATIONALAERONAUTICSANDSPACEADMINISTRATION8162188566"
NOAA_INDEX = "https://oceanservice.noaa.gov/podcast/"
NOAA_BASE = "https://oceanservice.noaa.gov"
UA = {"User-Agent": "podcast-upstream-daily-check"}
def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()
def txt(el, tag):
    if el is None:
        return ""
    node = el.find(tag)
    return (node.text or "").strip() if node is not None else ""
def norm_url(u):
    return (u or "").strip().rstrip("/")
def noaa_date_key(url):
    # /podcast/sep26/nop86-... -> (2026, 9); /podcast/june23/... -> (2023, 6)
    m = re.search(r"/podcast/([a-z]+)(\d{2})/", url, re.I)
    if not m:
        return (0, 0)
    months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "june": 6, "july": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
    mon = months.get(m.group(1).lower()[:4], 0)
    # june/july are 4 letters in the URL; the dict above handles them via [:4] on the key side too
    if m.group(1).lower() == "june":
        mon = 6
    if m.group(1).lower() == "july":
        mon = 7
    return (2000 + int(m.group(2)), mon)
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=os.path.join(BASE, "daily_state.local.json"))
    ap.add_argument("--shortlist", type=int, default=5)
    args = ap.parse_args()
    data = json.load(open(os.path.join(BASE, "items.json"), encoding="utf-8"))
    items = [i for i in data["items"] if i.get("status") == "active"]
    existing_src = set(norm_url(i["source_url"]) for i in items)
    existing_guids = set(i["guid"] for i in items)
    out = {
        "date_beijing": datetime.now().astimezone().strftime("%Y-%m-%d"),
        "existing_total": len(items),
        "existing_guids": len(existing_guids),
        "sources": {},
        "candidates": [],
        "failed_sources": [],
    }
    # Curious Universe RSS
    try:
        raw = fetch(CURIOUS_RSS)
        root = ET.fromstring(raw)
        ch = root.find("channel")
        rss_items = ch.findall("item") if ch is not None else []
        cands = []
        no_link = 0
        for it in rss_items:
            link = norm_url(txt(it, "link"))
            if not link:
                no_link += 1
            if not link or link in existing_src:
                continue
            cands.append({
                "source": "nasa-curious-universe",
                "title": txt(it, "title"),
                "pub_date": txt(it, "pubDate"),
                "source_url": link,
                "rss_guid": txt(it, "guid"),
            })
        def _pub_key(c):
            try:
                return parsedate_to_datetime(c["pub_date"])
            except Exception:
                return datetime.min.replace(tzinfo=None)
        cands.sort(key=_pub_key, reverse=True)
        out["sources"]["nasa-curious-universe"] = {"rss_items": len(rss_items), "candidates": len(cands), "rss_no_link": no_link}
        out["candidates"].extend(cands[:args.shortlist])
        out["curious_total_candidates"] = len(cands)
    except Exception as e:
        out["failed_sources"].append({"source": "nasa-curious-universe", "error": type(e).__name__ + ": " + str(e)[:200]})
    # NOAA index
    try:
        html = fetch(NOAA_INDEX).decode("utf-8", errors="ignore")
        links = sorted(set(re.findall(r'href="(/podcast/(?:[a-z]+\d{2})/[^"]+\.html)"', html, re.I)))
        cands = []
        for rel in links:
            full = norm_url(NOAA_BASE + rel)
            if full in existing_src:
                continue
            # Only Ocean Podcast episodes (nop*) in the main listing; skip other series pages
            if "/nop" not in rel.lower():
                continue
            cands.append({"source": "noaa-ocean-podcast", "title": "", "pub_date": "", "source_url": full, "date_key": noaa_date_key(full)})
        cands.sort(key=lambda c: c["date_key"], reverse=True)
        for c in cands:
            c.pop("date_key", None)
        out["sources"]["noaa-ocean-podcast"] = {"index_links": len(links), "candidates": len(cands)}
        out["candidates"].extend(cands[:args.shortlist])
        out["noaa_total_candidates"] = len(cands)
    except Exception as e:
        out["failed_sources"].append({"source": "noaa-ocean-podcast", "error": type(e).__name__ + ": " + str(e)[:200]})
    # State (local only, gitignored; never committed by itself)
    state = {}
    if os.path.exists(args.state):
        try:
            state = json.load(open(args.state, encoding="utf-8"))
        except Exception:
            state = {}
    state["last_check_beijing"] = out["date_beijing"]
    state["last_check_existing_total"] = len(items)
    state["last_check_candidates"] = out["candidates"]
    with open(args.state, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print("SUMMARY: existing=%d curious_candidates=%s noaa_candidates=%s shortlist=%d failed_sources=%d" % (
        len(items), out.get("curious_total_candidates", "?"), out.get("noaa_total_candidates", "?"), len(out["candidates"]), len(out["failed_sources"])))
    if len(out["failed_sources"]) == 2:
        return 2
    return 0
if __name__ == "__main__":
    sys.exit(main())
