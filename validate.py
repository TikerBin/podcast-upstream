#!/usr/bin/env python3
"""Independent validation for podcast-upstream feeds (not the builder)."""
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
BASE = os.path.dirname(os.path.abspath(__file__))
NS = {"content": "http://purl.org/rss/1.0/modules/content/"}
def guids(path):
    root = ET.parse(path).getroot()
    ch = root.find("channel")
    out = []
    for it in ch.findall("item"):
        g = it.find("guid")
        assert g is not None and g.get("isPermaLink") == "false", path
        assert it.find("title") is not None and it.find("title").text
        assert it.find("pubDate") is not None
        enc = it.find("enclosure")
        cont = it.find("content:encoded", NS)
        assert enc is not None or (cont is not None and len(cont.text or "") > 5000), path
        out.append((g.text, enc))
    return out
def head(url):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "podcast-upstream-validate"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.headers.get("Content-Type"), r.headers.get("Content-Length")
    except Exception as e:
        return None, None, str(e)
def main():
    items = json.load(open(os.path.join(BASE, "items.json"), encoding="utf-8"))["items"]
    by_guid = {i["guid"]: i for i in items if i["status"] == "active"}
    total = guids(os.path.join(BASE, "feed.xml"))
    assert len(total) == len(by_guid) == 5, (len(total), len(by_guid))
    assert len(set(g for g, _ in total)) == 5
    print("feed.xml: XML OK, 5 items, GUID unique, all isPermaLink=false")
    for path in sorted(os.listdir(os.path.join(BASE, "feeds"))):
        if not path.endswith(".xml"):
            continue
        gs = guids(os.path.join(BASE, "feeds", path))
        assert len(gs) == len(set(g for g, _ in gs)), path
        for g, _ in gs:
            assert g in by_guid, (path, g)
        print("feeds/%s: XML OK, %d items, GUIDs all in total feed" % (path, len(gs)))
    for g, enc in total:
        it = by_guid[g]
        if enc is None:
            print("%s: no enclosure (text-only, OK: full transcript %d words)" % (it["id"], it["transcript_word_count"]))
            continue
        assert int(enc.get("length")) == it["audio_bytes"], (it["id"], enc.get("length"), it["audio_bytes"])
        assert enc.get("type") == it["audio_mime"], (it["id"], enc.get("type"), it["audio_mime"])
        status, ctype, clen = head(it["audio_url"])
        print("%s: enclosure length/type match items.json; HEAD -> status=%s type=%s length=%s (items: %s/%s)" % (it["id"], status, ctype, clen, it["audio_mime"], it["audio_bytes"]))
        assert status == 200, it["id"]
        assert clen is not None and int(clen) == it["audio_bytes"], it["id"]
        # MIME: allow server family match; coral returns audio/mp4a-latm exactly, others audio/mpeg/audio/mp4
        assert ctype == it["audio_mime"], (it["id"], ctype, it["audio_mime"])
    fj = json.load(open(os.path.join(BASE, "feed.json"), encoding="utf-8"))
    assert len(fj["items"]) == 5
    assert set(x["id"] for x in fj["items"]) == set(by_guid)
    print("feed.json: 5 items, GUID set matches feed.xml")
    print("VALIDATION PASSED")
if __name__ == "__main__":
    main()
