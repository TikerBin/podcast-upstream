#!/usr/bin/env python3
"""Daily candidate check for podcast-upstream (read-only, never modifies items.json).
Reports: existing feed counts, candidates from verified public sources,
dedup counts, rejected-filtered counts, and a shortlist for the daily agent.
Exit 0 even when candidates exist (candidates are not failures);
exit 2 only when every source fetch fails (network/source outage).
Sources (no login/paywall bypass, no guessed MP3):
- NASA Curious Universe Megaphone RSS (official, public)
- NOAA Ocean Podcast index page (official, public HTML listing)
Fixed timezone: all run dates are Asia/Shanghai via ZoneInfo, never the
executor's local timezone, so a UTC-date rollover cannot misrecord the run.
Rejected handling: candidates matching a persistent rejected entry are
filtered BEFORE the shortlist is truncated, so persistently unqualified
candidates cannot occupy shortlist slots day after day. A rejected entry
becomes eligible again on its review_after date (default: first day of the
next month, Beijing time, per DAILY.md). Temporary network failures are
reported in failed_sources only and are NEVER recorded as rejections.
Usage:
  python3 daily_check.py [--state daily_state.local.json] [--shortlist 5]
  python3 daily_check.py --record-rejection --source-url URL --reason REASON [--rss-guid ID] [--review-after YYYY-MM-DD]
"""
import argparse
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo
BASE = os.path.dirname(os.path.abspath(__file__))
BEIJING = ZoneInfo("Asia/Shanghai")
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
def beijing_today():
    return datetime.now(BEIJING).date()
def utc_to_beijing_date(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(BEIJING).date()
def next_month_first_day(d):
    if d.month == 12:
        return date(d.year + 1, 1, 1)
    return date(d.year, d.month + 1, 1)
def parse_date(s):
    try:
        return date.fromisoformat(str(s)[:10])
    except Exception:
        return None
def noaa_date_key(url):
    m = re.search(r"/podcast/([a-z]+)(\d{2})/", url, re.I)
    if not m:
        return (0, 0)
    if m.group(1).lower() == "june":
        mon = 6
    elif m.group(1).lower() == "july":
        mon = 7
    else:
        months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
        mon = months.get(m.group(1).lower()[:4], 0)
    return (2000 + int(m.group(2)), mon)
def dedup_candidates(cands):
    """Dedup by normalised source URL first, then by rss_guid (when present).
    Keeps the first occurrence (callers sort newest-first before calling).
    Returns (deduped_list, duplicate_count)."""
    seen_urls, seen_guids, out, dups = set(), set(), [], 0
    for c in cands:
        u = norm_url(c.get("source_url"))
        g = (c.get("rss_guid") or "").strip()
        if (u and u in seen_urls) or (g and g in seen_guids):
            dups += 1
            continue
        if u:
            seen_urls.add(u)
        if g:
            seen_guids.add(g)
        out.append(c)
    return out, dups
def review_after_for(entry, today):
    ra = parse_date(entry.get("review_after")) if entry.get("review_after") else None
    if ra is not None:
        return ra
    d = parse_date(entry.get("date")) if entry.get("date") else None
    if d is not None:
        return next_month_first_day(d)
    return next_month_first_day(today)
def rejected_entry_matches(candidate, entry):
    if norm_url(candidate.get("source_url")) and norm_url(candidate.get("source_url")) == norm_url(entry.get("source_url")):
        return True
    cg = (candidate.get("rss_guid") or "").strip()
    eg = (entry.get("rss_guid") or "").strip()
    return bool(cg and eg and cg == eg)
def filter_rejected(candidates, rejected_list, today):
    """Filter BEFORE shortlist truncation. Returns (kept, filtered, due).
    kept: candidates not actively rejected, or whose review_after has passed.
    filtered: candidates suppressed by an active rejected entry.
    due: kept candidates whose rejected entry is due for monthly re-review."""
    rejected_list = rejected_list or []
    kept, filtered, due = [], [], []
    for c in candidates:
        match = None
        for entry in rejected_list:
            if rejected_entry_matches(c, entry):
                match = entry
                break
        if match is None:
            kept.append(c)
            continue
        ra = review_after_for(match, today)
        if today < ra:
            filtered.append(c)
        else:
            kept.append(c)
            due.append({"source_url": c.get("source_url"), "review_after": ra.isoformat(), "reason": match.get("reason", "")})
    return kept, filtered, due
def record_rejection(state, source_url, rss_guid, reason, review_after, today):
    """Upsert one rejected entry with a stable reason and review date.
    Never called for temporary network failures; only for a candidate the
    daily agent actually evaluated and found unqualified."""
    rejected = state.get("rejected") or []
    if review_after is None:
        review_after = next_month_first_day(today)
    entry = {
        "source_url": norm_url(source_url),
        "rss_guid": (rss_guid or "").strip(),
        "reason": reason,
        "date": today.isoformat(),
        "review_after": review_after.isoformat() if isinstance(review_after, date) else str(review_after),
    }
    for i, old in enumerate(rejected):
        if norm_url(old.get("source_url")) == entry["source_url"] or (entry["rss_guid"] and (old.get("rss_guid") or "").strip() == entry["rss_guid"]):
            rejected[i] = entry
            break
    else:
        rejected.append(entry)
    state["rejected"] = rejected
    return entry
def load_state(path):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}
def save_state(path, state):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
        f.write("\n")
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=os.path.join(BASE, "daily_state.local.json"))
    ap.add_argument("--shortlist", type=int, default=5)
    ap.add_argument("--record-rejection", action="store_true")
    ap.add_argument("--source-url", default="")
    ap.add_argument("--rss-guid", default="")
    ap.add_argument("--reason", default="")
    ap.add_argument("--review-after", default="")
    args = ap.parse_args()
    today = beijing_today()
    state = load_state(args.state)
    if args.record_rejection:
        if not args.source_url or not args.reason:
            print("ERROR: --record-rejection requires --source-url and --reason", file=sys.stderr)
            return 2
        ra = parse_date(args.review_after) if args.review_after else None
        entry = record_rejection(state, args.source_url, args.rss_guid, args.reason, ra, today)
        save_state(args.state, state)
        print(json.dumps({"recorded_rejection": entry, "rejected_total": len(state["rejected"])}, ensure_ascii=False, indent=1))
        return 0
    data = json.load(open(os.path.join(BASE, "items.json"), encoding="utf-8"))
    items = [i for i in data["items"] if i.get("status") == "active"]
    existing_src = set(norm_url(i["source_url"]) for i in items)
    existing_guids = set(i["guid"] for i in items)
    existing_rss_guids = set(i.get("_rss_guid") for i in items if i.get("_rss_guid"))
    rejected_list = state.get("rejected") or []
    out = {
        "date_beijing": today.isoformat(),
        "existing_total": len(items),
        "existing_guids": len(existing_guids),
        "sources": {},
        "candidates": [],
        "failed_sources": [],
    }
    total_filtered = 0
    total_due = []
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
                continue
            if link in existing_src:
                continue
            guid = txt(it, "guid")
            if guid and guid in existing_rss_guids:
                continue
            cands.append({
                "source": "nasa-curious-universe",
                "title": txt(it, "title"),
                "pub_date": txt(it, "pubDate"),
                "source_url": link,
                "rss_guid": guid,
            })
        def _pub_key(c):
            try:
                return parsedate_to_datetime(c["pub_date"])
            except Exception:
                return datetime.min.replace(tzinfo=timezone.utc)
        cands.sort(key=_pub_key, reverse=True)
        cands, dups = dedup_candidates(cands)
        kept, filtered, due = filter_rejected(cands, rejected_list, today)
        total_filtered += len(filtered)
        total_due.extend(due)
        out["sources"]["nasa-curious-universe"] = {"rss_items": len(rss_items), "candidates": len(kept), "candidates_before_rejected_filter": len(cands), "duplicates_removed": dups, "rejected_filtered": len(filtered), "review_due": len(due), "rss_no_link": no_link}
        out["candidates"].extend(kept[:args.shortlist])
        out["curious_total_candidates"] = len(kept)
    except Exception as e:
        # Temporary network/source failure: reported only, never recorded as a rejection.
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
            if "/nop" not in rel.lower():
                continue
            cands.append({"source": "noaa-ocean-podcast", "title": "", "pub_date": "", "source_url": full, "date_key": noaa_date_key(full)})
        cands.sort(key=lambda c: c["date_key"], reverse=True)
        for c in cands:
            c.pop("date_key", None)
        cands, dups = dedup_candidates(cands)
        kept, filtered, due = filter_rejected(cands, rejected_list, today)
        total_filtered += len(filtered)
        total_due.extend(due)
        out["sources"]["noaa-ocean-podcast"] = {"index_links": len(links), "candidates": len(kept), "candidates_before_rejected_filter": len(cands), "duplicates_removed": dups, "rejected_filtered": len(filtered), "review_due": len(due)}
        out["candidates"].extend(kept[:args.shortlist])
        out["noaa_total_candidates"] = len(kept)
    except Exception as e:
        out["failed_sources"].append({"source": "noaa-ocean-podcast", "error": type(e).__name__ + ": " + str(e)[:200]})
    out["rejected_filtered_total"] = total_filtered
    out["review_due"] = total_due
    # State (local only, gitignored; rejected list is preserved untouched here)
    state["last_check_beijing"] = out["date_beijing"]
    state["last_check_existing_total"] = len(items)
    state["last_check_candidates"] = out["candidates"]
    state["last_check_rejected_filtered"] = total_filtered
    state["last_check_review_due"] = total_due
    save_state(args.state, state)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print("SUMMARY: existing=%d curious_candidates=%s noaa_candidates=%s shortlist=%d rejected_filtered=%d review_due=%d failed_sources=%d" % (
        len(items), out.get("curious_total_candidates", "?"), out.get("noaa_total_candidates", "?"), len(out["candidates"]), total_filtered, len(total_due), len(out["failed_sources"])))
    if len(out["failed_sources"]) == 2:
        return 2
    return 0
if __name__ == "__main__":
    sys.exit(main())
