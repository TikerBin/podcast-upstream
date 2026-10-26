#!/usr/bin/env python3
"""Independent validation for podcast-upstream feeds (not the builder).
No hardcoded total: counts are derived from items.json and each filtered
feed must equal the exact GUID set implied by its filter. Cover remote HEAD
is checked separately after push (pre-push local validation checks the
local cover file only, via build_feed).
"""
import json
import os
import urllib.request
import xml.etree.ElementTree as ET
BASE = os.path.dirname(os.path.abspath(__file__))
NS = {"content": "http://purl.org/rss/1.0/modules/content/"}
def parse_items(path):
    root = ET.parse(path).getroot()
    ch = root.find("channel")
    out = {}
    for it in ch.findall("item"):
        g = it.find("guid")
        assert g is not None and g.get("isPermaLink") == "false", path
        assert it.find("title") is not None and it.find("title").text
        assert it.find("pubDate") is not None
        enc = it.find("enclosure")
        cont = it.find("content:encoded", NS)
        assert enc is not None or (cont is not None and len(cont.text or "") > 100), path
        img = it.find("{http://www.itunes.com/dtds/podcast-1.0.dtd}image")
        assert img is not None and img.get("href"), path + " missing itunes:image"
        out[g.text] = {"enc": enc, "content": cont.text if cont is not None else "", "image": img.get("href"), "title": it.find("title").text}
    return out
def head(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "podcast-upstream-validate"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.headers.get("Content-Type"), r.headers.get("Content-Length")
    except Exception as e:
        return None, None, str(e)
def main():
    data = json.load(open(os.path.join(BASE, "items.json"), encoding="utf-8"))
    items = [i for i in data["items"] if i.get("status") == "active"]
    by_guid = {i["guid"]: i for i in items}
    total = parse_items(os.path.join(BASE, "feed.xml"))
    assert set(total) == set(by_guid), "total GUID set != items.json"
    print("feed.xml: XML OK, %d items, GUID set == items.json, all isPermaLink=false, all have itunes:image" % len(total))
    # filtered feeds must equal exact filter sets, not just subsets
    def expected(filter_fn):
        return set(i["guid"] for i in items if filter_fn(i))
    checks = {
        "feeds/science-space.xml": lambda i: i["theme"] == "science-space",
        "feeds/ocean-environment.xml": lambda i: i["theme"] == "ocean-environment",
        "feeds/technology-ai.xml": lambda i: i["theme"] == "technology-ai",
        "feeds/audio.xml": lambda i: "audio" in i["forms"],
        "feeds/video.xml": lambda i: "video" in i["forms"],
        "feeds/text.xml": lambda i: "text" in i["forms"],
        "feeds/ready-clip.xml": lambda i: "ready-clip" in i["production_kinds"],
    }
    for path, fn in checks.items():
        gs = parse_items(os.path.join(BASE, path))
        exp = expected(fn)
        assert set(gs) == exp, (path, set(gs), exp)
        print("%s: XML OK, %d items, exact filter set" % (path, len(gs)))
    # enclosure + content + clip/parent disjointness
    for g, info in total.items():
        it = by_guid[g]
        assert info["image"] == it["cover_image"], (it["id"], "cover mismatch")
        enc = info["enc"]
        if it.get("audio_url"):
            assert enc is not None, it["id"]
            assert int(enc.get("length")) == it["audio_bytes"], (it["id"], enc.get("length"), it["audio_bytes"])
            assert enc.get("type") == it["audio_mime"], (it["id"], enc.get("type"), it["audio_mime"])
            status, ctype, clen = head(it["audio_url"])
            print("%s: enclosure match; HEAD %s %s %s (items %s/%s)" % (it["id"], status, ctype, clen, it["audio_mime"], it["audio_bytes"]))
            assert status == 200, it["id"]
            assert clen is not None and int(clen) == it["audio_bytes"], it["id"]
            assert ctype == it["audio_mime"], (it["id"], ctype, it["audio_mime"])
        else:
            assert enc is None, it["id"]
        # content text must equal transcript file content
        with open(os.path.join(BASE, it["transcript_file"]), encoding="utf-8") as f:
            t = f.read().strip()
        assert info["content"].strip() == t, (it["id"], "content != transcript file")
        if it.get("_clip_srt_file"):
            import re as _re
            srt_path = os.path.join(BASE, it["_clip_srt_file"])
            assert os.path.exists(srt_path), it["id"]
            srt_text = open(srt_path, encoding="utf-8").read()
            ends = _re.findall(r"-->\s*\d+:\d+:(\d+\.\d+)", srt_text)
            assert ends, it["id"]
            assert float(max(ends)) <= it["audio_duration_s"] + 1.0, (it["id"], max(ends), it["audio_duration_s"])
            print("%s: SRT OK, %s, last end %ss <= duration %ss" % (it["id"], it["_clip_srt_file"], max(ends), it["audio_duration_s"]))
        if "ready-clip" in it["production_kinds"]:
            assert "full-episode" not in it["production_kinds"], it["id"]
            parent = by_guid[it["_parent_guid"]]
            assert it["guid"] != parent["guid"]
            assert it["audio_bytes"] != parent["audio_bytes"]
            assert it["audio_duration_s"] < parent["audio_duration_s"]
            assert it["transcript_word_count"] < parent["transcript_word_count"]
            assert it["audio_url"].startswith("https://raw.githubusercontent.com/TikerBin/podcast-upstream/main/clips/")
            print("%s: clip OK, parent %s, %ds, %d bytes, %d words (< parent %d words)" % (it["id"], parent["id"], it["audio_duration_s"], it["audio_bytes"], it["transcript_word_count"], parent["transcript_word_count"]))
        if "full-episode" in it["production_kinds"]:
            assert "ready-clip" not in it["production_kinds"], it["id"]
    fj = json.load(open(os.path.join(BASE, "feed.json"), encoding="utf-8"))
    assert set(x["id"] for x in fj["items"]) == set(by_guid)
    for x in fj["items"]:
        rss = total[x["id"]]
        assert x["content_text"].strip() == rss["content"].strip(), x["id"]
        if by_guid[x["id"]].get("audio_url"):
            assert x["attachments"][0]["url"] == by_guid[x["id"]]["audio_url"], x["id"]
            assert x["attachments"][0]["size_in_bytes"] == by_guid[x["id"]]["audio_bytes"], x["id"]
    print("feed.json: %d items, GUID set + content + attachments match feed.xml" % len(fj["items"]))
    print("VALIDATION PASSED (no hardcoded total)")
if __name__ == "__main__":
    main()
