#!/usr/bin/env python3
"""Build podcast upstream feeds from items.json + transcripts/*.txt.
Mirrors fb-reels/fb360: items.json is the only source of truth.
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
        if not it.get("title"):
            raise ValueError("%s: missing title" % iid)
        transcript = load_transcript(it)
        words = len(transcript.split())
        if words < 1000:
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
        for clip in it.get("ready_clips", []):
            p = os.path.join(BASE, clip["file"])
            if not os.path.exists(p):
                raise ValueError("%s: ready_clip missing %s" % (iid, clip["file"]))
            dur = ffprobe_duration(p)
            expect = clip["end_s"] - clip["start_s"]
            if abs(dur - expect) > 0.2:
                raise ValueError("%s: ready_clip %s != %s" % (iid, dur, expect))
            if clip.get("source_nature") != "original_audio":
                raise ValueError("%s: ready_clip must be original_audio" % iid)
            if "ready-clip" not in it.get("production_kinds", []):
                raise ValueError("%s: ready_clip without production kind" % iid)
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
    if it.get("ready_clips"):
        for c in it["ready_clips"]:
            desc += ("\n【ready-clip】" + c["title"] + "：原集 " + str(c["start_s"]) + "-" + str(c["end_s"]) + " 秒，" + str(c["duration_s"]) + " 秒，原声，未加 BGM，文件：" + c["file"])
    parts.append("<description>" + cdata(desc) + "</description>")
    parts.append("<content:encoded>" + cdata(transcript) + "</content:encoded>")
    parts.append("<_show>" + escape(it["show"]) + "</_show>")
    parts.append("<_episode_id>" + escape(it["episode_id"]) + "</_episode_id>")
    parts.append("<_source_url>" + escape(it["source_url"]) + "</_source_url>")
    parts.append("<_license>" + escape(it["license"]) + "</_license>")
    parts.append("<_rights_status>" + escape(it["rights_status"]) + "</_rights_status>")
    parts.append("<_collected_at_beijing>" + escape(it["collected_at_beijing"]) + "</_collected_at_beijing>")
    if it.get("audio_url"):
        parts.append("<_audio_verified>" + escape(it["audio_verified_method"]) + "</_audio_verified>")
    if it.get("ready_clips"):
        for c in it["ready_clips"]:
            parts.append("<_ready_clip>" + escape("%s|%s-%ss|%ss|%s" % (c["file"], c["start_s"], c["end_s"], c["duration_s"], c["source_nature"])) + "</_ready_clip>")
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
    if it.get("audio_url"):
        out["attachments"] = [{"url": it["audio_url"], "mime_type": it["audio_mime"], "size_in_bytes": it["audio_bytes"], "duration_in_seconds": it["audio_duration_s"]}]
    if it.get("cover_image"):
        out["image"] = it["cover_image"]
    if it.get("ready_clips"):
        out["_ready_clips"] = it["ready_clips"]
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
    total_desc = "待制作播客素材上游：每条 = 一份待制作内容，含可下载音频 enclosure 或完整文字稿至少一种。全部为美国政府官方播客（NASA / NOAA），公有领域、可剪辑但不得暗示官方背书。本批为小规模真实样本，未上传 GitHub 前 base-url 为占位地址，不可订阅。"
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
            title = "Podcast 素材上游 – ready-clip（已选短片段）"
            desc = "已实际截取并经 ffprobe 校验的 30-60 秒原声短片段条目；整集不得冒充短片段。"
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
