# Podcast 素材上游 – 待制作

状态：**本地已完成并验证，未上传 GitHub。** 本文件里的 raw.githubusercontent 地址是仓库创建并推送后才会生效的预告地址，目前不可订阅。不要把占位地址当成已上线。

## 这是什么

每条 RSS 条目 = 一份待制作内容。入库最低标准：稳定唯一 GUID（isPermaLink=false）+ 标题 + 可下载音频 enclosure 或 content:encoded 完整文字稿至少一种；本批 5 条全部有完整文字稿，其中 4 条另有音频。

一条目可兼有音频、文字，不重复建三条。视频形态本批 0 条，见下。

## 本批数量（2026-10-24 北京时间采集核验）

- 总计：5 条
- 按主题：science-space（科学/太空）2 条；ocean-environment（海洋/环境）2 条；technology-ai（科技/AI）1 条
- 按形态：audio 4 条；text 5 条；video 0 条
- 按生产形态：full-episode 4 条；text-script 5 条；ready-clip 2 条（见下）
- 来源：NASA 官方播客 3 条（Curious Universe 2 条、Houston We Have a Podcast 1 条）；NOAA Ocean Podcast 2 条

## 条目一览

1. NASA's Curious Universe – Inside a Black Hole（science-space，audio+text，full-episode+text-script）
   原发布 2020-11-23，MP3 29,380,743 字节，audio/mpeg，时长 1203.9 秒，文字稿 3005 词。
2. NASA's Curious Universe – Encore: A Year In Mars Dune Alpha（science-space，audio+text，full-episode+text-script+ready-clip）
   Encore 发布 2026-10-20（最初 2023 年），MP3 39,402,865 字节，audio/mpeg，时长 1626.1 秒，文字稿 4177 词。
   ready-clip：Their Mars window is a TV，原集 224.0–255.0 秒，31.0 秒，原声，文件 clips/chapea-clip1-window.mp3。
3. NOAA Ocean Podcast Ep.66 – Rip Currents: Preparedness and Prevention（ocean-environment，audio+text，full-episode+text-script+ready-clip）
   原发布 2023-06-28（仅到日），M4A 16,026,456 字节，audio/mp4，时长 818.4 秒，文字稿 2752 词。
   ready-clip：原集 335.1–380.9 秒，45.8 秒，原声，文件 clips/noaa-rip-currents-clip-335-381.mp3（本批用 ffmpeg 从已验证整集截取并经 ffprobe 核验）。
4. NOAA Ocean Podcast Ep.71 – Coral Bleaching（ocean-environment，audio+text，full-episode+text-script）
   原发布 2023-12-05（仅到日），M4A 16,134,595 字节，服务器返回 MIME audio/mp4a-latm（见 SOURCES.md 的兼容提示），时长 997.0 秒，文字稿 2060 词。
5. Houston We Have a Podcast Ep.424 – AI at NASA（technology-ai，text 仅，text-script）
   发布 2026-05-29（仅到日；页内只写录制于 2026-05-05），文字稿 5521 词，封面为 NASA 官方单集缩略图。
   音频未入库：Megaphone 订阅源 ID 未能在官方来源中唯一核实，不猜 MP3 地址；故本条不进 audio feed，只进总 feed、technology-ai feed 与 text feed。

## 订阅地址

本地文件（已生成、可直接读）：
- 总 feed：`feed.xml`，JSON 版：`feed.json`
- 主题：`feeds/science-space.xml`、`feeds/ocean-environment.xml`、`feeds/technology-ai.xml`
- 形态：`feeds/audio.xml`、`feeds/text.xml`、`feeds/video.xml`（本批 0 条，空 feed 是如实结果）
- 生产形态（附加）：`feeds/ready-clip.xml`（2 条）

仓库创建并推送后（预告，非现时可用）：
- 仓库（建议，待用户决定）：`TikerBin/podcast-upstream`
- 总 RSS：`https://raw.githubusercontent.com/TikerBin/podcast-upstream/main/feed.xml`
- 总 JSON：`https://raw.githubusercontent.com/TikerBin/podcast-upstream/main/feed.json`
- 分类 RSS：`https://raw.githubusercontent.com/TikerBin/podcast-upstream/main/feeds/<science-space|ocean-environment|technology-ai|audio|video|text|ready-clip>.xml`

## 分类与 GUID 规则

- 主题：science-space、ocean-environment、technology-ai；按实际采集结果扩充，不为凑分类混入不合格内容。
- 形态：audio、video、text；一节目可多形态，但只建一条。
- GUID：基于来源稳定标识生成（例如 `urn:podcast:nasa.gov:curious-universe:inside-a-black-hole`），持久保存在 items.json；标题修改、重跑、跨主题/形态 feed 均不换 ID。
- pubDate：原发布时间；另存采集日（北京时间 2026-10-24）。仅到日的用当日 00:00 UTC 占位，并在 items.json 的 pub_date_precision 中注明，不伪造时刻。
- ready-clip：只有实际截取并经 ffprobe 校验的文件才能标；记录原集、起止秒、原声性质；整集不得冒充短片段。
- 不生成成片、不默认调用付费 TTS。语言、Logo、品牌色、默认封面、TTS 声音属于订阅级配置，不在每条重复。

## 权利规则（可听 ≠ 可重用）

本批全部为美国联邦政府官方播客（NASA / NOAA），一般不受版权保护，原则上可剪辑、转存、再分发，但不得暗示 NASA / NOAA 背书。
整集文字稿中标有音乐 cue 的（如 CHAPEA 的歌曲 cue、AI 集的 Intro/Outro Music），正式发布前需逐项再核该片段是否含第三方音乐；ready-clip 本身已核为原声讲话段、未加 BGM。
仅公开可听的商业播客、YouTube 仅链接、Spotify/小宇宙独占等，均单独列在 SOURCES.md 的“未入库”清单，不混进待制作 feed。

## 目录

- `items.json` – 唯一数据源（+ `excluded_not_in_feed` 未入库清单）
- `build_feed.py` – 生成 feed.xml / feed.json / feeds/*.xml（`--base-url` 为托管地址）
- `validate.py` – 独立验证脚本，见 VALIDATION.log
- `transcripts/*.txt` – 清洗后的完整文字稿（去导航/页脚，首末句已与官方页核对）；`transcripts/raw/` 为原始抓取留档
- `clips/*.mp3` – 仅 2 个 ready-clip 小文件（0.5–0.7 MB），整集大文件不进 Git，仍引用官方原地址
- `SOURCES.md` – 来源、授权、核验链接与未覆盖原因
- `VALIDATION.log` – 本批验证结果

## 新增 / 增量更新

1. 在 items.json 追加新条（新 GUID，绝不复用旧 ID），附 transcripts 文件与核验数据；
2. 跑 `python3 build_feed.py --base-url <真实托管地址>`；
3. 跑 `python3 validate.py`，通过后再推送；
4. 去重：以 guid + audio_url + source_url 三重比对，同源不重复入库。

## 未完成（明确说未完成）

- 未创建 GitHub 仓库，未推送任何文件，未有任何公开可订阅地址生效。
- 未做 Facebook 发布（本任务明确不发布到社交平台）。
- Houston Ep.424 音频未核实，未入库 audio feed。
- 视频形态 0 条，未覆盖原因见 SOURCES.md。
- Coral Bleaching 的 audio/mp4a-latm MIME 未做下游播放器兼容测试。
- 无定时增量采集 cron：本批为一次性小规模样本，后续重复采集需用户确认频率与仓库后再设。
