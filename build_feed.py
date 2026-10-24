#!/usr/bin/env python3
"""Build podcast upstream feeds from items.json + transcripts/*.txt.
Model v2 (2026-10-24 fix): ready-clips are independent items, not parent
items with a _ready_clip side field. Parents carry full-episode only
(plus text-script where a full transcript exists); clips carry ready-clip
only. The two production sets are disjoint.
Usage: python3 build_feed.py [--base-url URL]
"""
import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape
BASE = os.path.dirname(os.path.abspath(__file__))
RAW_CLIPS_PREFIX = "https://raw.githubusercontent.com/TikerBin/podcast-upstream/main/clips/"
DEFAULT_COVER = "https://raw.githubusercontent.com/TikerBin/podcast-upstream/main/images/default-cover.png"
def load_items():
    with open(os.path.join(BASE, "items.json"), encoding="utf-8") as f:
        data = json.load(f)
    return data["items"]
def load_transcript(item):
    path = os.path.join(BASE, item["transcript_file"])
    with open(path, encoding="utf-8") as f:
        return f.read().strip()
def rfc2822(iso):
    dt = datetime.fromisoformat(iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return format_datetime(dt)
def ffprobe_duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path], text=True).strip()
    return float(out)
def validate(items):
    by_guid = {i["guid"]: i for i in items if i.get("status") == "active"}
    by_id = {i["id"]: i for i in items if i.get("status") == "active"}
    seen_guid, seen_id = set(), set()
    for it in items:
        if it.get("status") != "active":
            continue
        gid, iid = it.get("guid"), it.get("id")
        if not gid or gid in seen_guid:
            raise ValueError("duplicate/missing guid: %r" % (gid,))
        if not iid or iid in seen_id:
            raise ValueError("duplicate/missing id: %r" % (iid,))
        seen_guid.add(gid)
        seen_id.add(iid)
        if it.get("ready_clips"):
            raise ValueError("%s: old ready_clips model retired, use independent clip items" % iid)
        if not it.get("title"):
            raise ValueError("%s: missing title" % iid)
        if not it.get("cover_image"):
            raise ValueError("%s: missing cover_image" % iid)
        if it["cover_image"] == DEFAULT_COVER:
            p = os.path.join(BASE, "images/default-cover.png")
            if not os.path.exists(p):
                raise ValueError("%s: default cover file missing" % iid)
        transcript = load_transcript(it)
        words = len(transcript.split())
        if words < 50:
            raise ValueError("%s: transcript only %d words" % (iid, words))
        if it.get("transcript_word_count") != words:
            raise ValueError("%s: word count %s != file %d" % (iid, it.get("transcript_word_count"), words))
        has_audio = bool(it.get("audio_url"))
        if not has_audio and not transcript:
            raise ValueError("%s: neither audio nor transcript" % iid)
        if has_audio:
            if not it.get("audio_bytes") or it["audio_bytes"] <= 0:
                raise ValueError("%s: audio_bytes missing" % iid)
            if not it.get("audio_mime"):
                raise ValueError("%s: audio_mime missing" % iid)
            if not it.get("audio_duration_s"):
                raise ValueError("%s: audio_duration_s missing" % iid)
        if it.get("theme") not in ("science-space", "ocean-environment", "technology-ai"):
            raise ValueError("%s: unknown theme %r" % (iid, it.get("theme")))
        kinds = it.get("production_kinds", [])
        if "full-episode" in kinds and "ready-clip" in kinds:
            raise ValueError("%s: full-episode and ready-clip must be disjoint" % iid)
        if "ready-clip" in kinds:
            pg = it.get("_parent_guid")
            if not pg or pg not in by_guid:
                raise ValueError("%s: ready-clip parent guid missing/unknown" % iid)
            if pg == gid:
                raise ValueError("%s: clip guid equals parent guid" % iid)
            parent = by_guid[pg]
            if not it["audio_url"].startswith(RAW_CLIPS_PREFIX):
                raise ValueError("%s: clip enclosure must be raw GitHub clips URL" % iid)
            if it["audio_mime"] != "audio/mpeg":
                raise ValueError("%s: clip mime must be audio/mpeg" % iid)
            local = os.path.join(BASE, it["_clip_file"])
            if not os.path.exists(local):
                raise ValueError("%s: clip file missing %s" % iid)
            if os.path.getsize(local) != it["audio_bytes"]:
                raise ValueError("%s: clip local size != audio_bytes" % iid)
            dur = ffprobe_duration(local)
            expect = it["_clip_end_s"] - it["_clip_start_s"]
            if abs(dur - expect) > 0.2:
                raise ValueError("%s: clip duration %s != %s" % (iid, dur, expect))
            if abs(dur - it["audio_duration_s"]) > 0.2:
                raise ValueError("%s: clip duration != audio_duration_s" % iid)
            parent_words = len(load_transcript(parent).split())
            if words >= parent_words:
                raise ValueError("%s: clip transcript must be shorter than parent" % iid)
            if it["transcript_file"] == parent["transcript_file"]:
                raise ValueError("%s: clip transcript file equals parent" % iid)
            if it["audio_bytes"] == parent.get("audio_bytes"):
                raise ValueError("%s: clip bytes equal parent bytes" % iid)
        for cg in it.get("_child_clip_guids", []):
            if cg not in by_guid:
                raise ValueError("%s: child clip guid unknown %s" % (iid, cg))
            if by_guid[cg].get("_parent_guid") != gid:
                raise ValueError("%s: child clip parent mismatch" % iid)
def cdata(text):
    return "<![CDATA[" + text.replace("]]>", "]]]]><![CDATA[>") + "]]>"
def item_xml(it, base_url):
    transcript = load_transcript(it)
    parts = ["<item>"]
    parts.append("<title>" + escape(it["title"]) + "</title>")
    parts.append("<link>" + escape(it["source_url"]) + "</link>")
    parts.append('<guid isPermaLink="false">' + escape(it["guid"]) + "</guid>")
    parts.append("<pubDate>" + rfc2822(it["pub_date"]) + "</pubDate>")
    parts.append("<category>" + escape(it["theme"]) + "</category>")
    for form in it["forms"]:
        parts.append("<category>" + escape("form:" + form) + "</category>")
    for kind in it["production_kinds"]:
        parts.append("<category>" + escape("production:" + kind) + "</category>")
    parts.append("<language>" + escape(it["language"]) + "</language>")
    if it.get("cover_image"):
        parts.append('<itunes:image href="' + escape(it["cover_image"]) + '"/>')
    if it.get("audio_url"):
        parts.append('<enclosure url="' + escape(it["audio_url"]) + '" length="' + str(it["audio_bytes"]) + '" type="' + escape(it["audio_mime"]) + '"/>')
        parts.append("<itunes:duration>" + str(int(round(it["audio_duration_s"]))) + "</itunes:duration>")
    desc = ("【节目】" + it["show"] + "\n【主题】" + it["theme"] + "\n【形态】" + ", ".join(it["forms"]) + "\n【生产形态】" + ", ".join(it["production_kinds"]) + "\n【摘要】" + it["summary_cn"] + "\n【Reels 角度】" + it["reels_angle"] + "\n【许可证】" + it["license"] + "：" + it["license_basis"] + "\n【权利说明】" + it["rights_note"] + "\n【来源】" + it["source_url"] + "\n【采集日（北京时间）】" + it["collected_at_beijing"] + "\n【发布时间精度】" + it["pub_date_precision"] + "（" + it["pub_date_source"] + "）")
    if it.get("_parent_guid"):
        desc += ("\n【父集 GUID】" + it["_parent_guid"] + "\n【父集链接】" + it["_parent_source_url"] + "\n【片段】原集 " + str(it["_clip_start_s"]) + "-" + str(it["_clip_end_s"]) + " 秒，" + str(it["audio_duration_s"]) + " 秒，原声，未加 BGM，文件：" + it["_clip_file"])
    if it.get("_child_clip_guids"):
        desc += "\n【子片段 GUID】" + ", ".join(it["_child_clip_guids"])
    parts.append("<description>" + cdata(desc) + "</description>")
    parts.append("<content:encoded>" + cdata(transcript) + "</content:encoded>")
    parts.append("<_show>" + escape(it["show"]) + "</_show>")
    parts.append("<_episode_id>" + escape(it["episode_id"]) + "</_episode_id>")
    parts.append("<_source_url>" + escape(it["source_url"]) + "</_source_url>")
    parts.append("<_license>" + escape(it["license"]) + "</_license>")
    parts.append("<_rights_status>" + escape(it["rights_status"]) + "</_rights_status>")
    parts.append("<_collected_at_beijing>" + escape(it["collected_at_beijing"]) + "</_collected_at_beijing>")
    if it.get("audio_url"):
        parts.append("<_audio_verified>" + escape(it.get("audio_verified_method") or "") + "</_audio_verified>")
    if it.get("_parent_guid"):
        parts.append("<_parent_guid>" + escape(it["_parent_guid"]) + "</_parent_guid>")
        parts.append("<_parent_id>" + escape(it["_parent_id"]) + "</_parent_id>")
        parts.append("<_clip_start_s>" + str(it["_clip_start_s"]) + "</_clip_start_s>")
        parts.append("<_clip_end_s>" + str(it["_clip_end_s"]) + "</_clip_end_s>")
        parts.append("<_clip_source_nature>" + escape(it["_clip_source_nature"]) + "</_clip_source_nature>")
    if it.get("_child_clip_guids"):
        for cg in it["_child_clip_guids"]:
            parts.append("<_child_clip_guid>" + escape(cg) + "</_child_clip_guid>")
    parts.append("</item>")
    return "\n".join(parts)
def build_rss(items, base_url, title, description, self_path):
    parts = ['<?xml version="1.0" encoding="UTF-8"?>']
    parts.append('<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/">')
    parts.append("<channel>")
    parts.append("<title>" + escape(title) + "</title>")
    parts.append("<link>" + escape(base_url) + "</link>")
    parts.append("<description>" + escape(description) + "</description>")
    parts.append("<language>en</language>")
    parts.append("<lastBuildDate>" + format_datetime(datetime.now(timezone.utc)) + "</lastBuildDate>")
    if self_path:
        parts.append('<atom:link xmlns:atom="http://www.w3.org/2005/Atom" href="' + escape(base_url.rstrip("/") + "/" + self_path) + '" rel="self" type="application/rss+xml"/>')
    for it in items:
        parts.append(item_xml(it, base_url))
    parts += ["</channel>", "</rss>"]
    return "\n".join(parts) + "\n"
def item_json(it, base_url):
    transcript = load_transcript(it)
    out = {
        "id": it["guid"],
        "url": it["source_url"],
        "title": it["title"],
        "summary": it["summary_cn"],
        "content_text": transcript,
        "date_published": it["pub_date"],
        "tags": [it["theme"]] + ["form:" + f for f in it["forms"]] + ["production:" + k for k in it["production_kinds"]],
        "_item_id": it["id"],
        "_show": it["show"],
        "_episode_id": it["episode_id"],
        "_theme": it["theme"],
        "_forms": it["forms"],
        "_production_kinds": it["production_kinds"],
        "_source_url": it["source_url"],
        "_license": it["license"],
        "_rights_status": it["rights_status"],
        "_collected_at_beijing": it["collected_at_beijing"],
        "_transcript_word_count": it["transcript_word_count"],
    }
    if it.get("cover_image"):
        out["image"] = it["cover_image"]
    if it.get("audio_url"):
        out["attachments"] = [{"url": it["audio_url"], "mime_type": it["audio_mime"], "size_in_bytes": it["audio_bytes"], "duration_in_seconds": it["audio_duration_s"]}]
    if it.get("_parent_guid"):
        out["_parent_guid"] = it["_parent_guid"]
        out["_parent_id"] = it["_parent_id"]
        out["_clip_start_s"] = it["_clip_start_s"]
        out["_clip_end_s"] = it["_clip_end_s"]
        out["_clip_source_nature"] = it["_clip_source_nature"]
    if it.get("_child_clip_guids"):
        out["_child_clip_guids"] = it["_child_clip_guids"]
    return out
def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="https://example.invalid/podcast-upstream")
    args = ap.parse_args()
    base = args.base_url
    items = [i for i in load_items() if i.get("status") == "active"]
    validate(items)
    items.sort(key=lambda i: (i["pub_date"], i["id"]), reverse=True)
    total_desc = "待制作播客素材上游 v2：每条 = 一份待制作内容。父集标 full-episode，片段为独立条目、仅标 ready-clip，两集合不相交。片段 enclosure 为仓库自托管 clips 直链，不依赖整集音频。全部为美国政府官方播客（NASA / NOAA），公有领域、可剪辑但不得暗示官方背书。"
    write(os.path.join(BASE, "feed.xml"), build_rss(items, base, "Podcast 素材上游 – 待制作", total_desc, "feed.xml"))
    feed_json = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "Podcast 素材上游 – 待制作",
        "home_page_url": base,
        "feed_url": base.rstrip("/") + "/feed.json",
        "description": total_desc,
        "language": "en",
        "items": [item_json(i, base) for i in items],
    }
    write(os.path.join(BASE, "feed.json"), json.dumps(feed_json, ensure_ascii=False, indent=1) + "\n")
    feeds = {}
    for theme in ("science-space", "ocean-environment", "technology-ai"):
        feeds["feeds/%s.xml" % theme] = [i for i in items if i["theme"] == theme]
    for form in ("audio", "video", "text"):
        feeds["feeds/%s.xml" % form] = [i for i in items if form in i["forms"]]
    feeds["feeds/ready-clip.xml"] = [i for i in items if "ready-clip" in i["production_kinds"]]
    theme_names = {"science-space": "科学/太空", "ocean-environment": "海洋/环境", "technology-ai": "科技/AI"}
    for path, subset in feeds.items():
        kind = path.split("/")[1].replace(".xml", "")
        if kind in theme_names:
            title = "Podcast 素材上游 – %s" % theme_names[kind]
            desc = "主题 %s（%s）的待制作播客条目，GUID 与总 feed 完全一致。" % (kind, theme_names[kind])
        elif kind == "ready-clip":
            title = "Podcast 素材上游 – ready-clip（已选短片段，独立条目）"
            desc = "仅含独立片段条目：片段 enclosure 为仓库自托管 clips 直链，文案仅覆盖片段音频；整集不在此 feed，整集不得冒充短片段。"
        else:
            title = "Podcast 素材上游 – %s 形态" % kind
            if kind == "video" and not subset:
                desc = "视频形态本批 0 条：无官方稳定 MP4 + 音频/文案双齐的视频播客，YouTube 仅链接的条目按规则不入库，空 feed 是如实结果，不是缺文件。"
            else:
                desc = "形态 %s 的待制作播客条目，GUID 与总 feed 完全一致。" % kind
        write(os.path.join(BASE, path), build_rss(subset, base, title, desc, path))
    print("built feed.xml + feed.json (%d items) + %d filtered feeds (base=%s)" % (len(items), len(feeds), base))
    for path, subset in sorted(feeds.items()):
        print("  %s: %d" % (path, len(subset)))
if __name__ == "__main__":
    main()
