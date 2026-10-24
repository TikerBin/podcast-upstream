# Podcast 素材上游 – 待制作

状态：**已上线。** 仓库为公开仓 `TikerBin/podcast-upstream`，下述 raw.githubusercontent 地址为真实可订阅地址。2026-10-24 修复后为 7 条（5 父集 + 2 独立片段），已推送并验证。

## 这是什么

每条 RSS 条目 = 一份待制作内容。入库最低标准：稳定唯一 GUID（isPermaLink=false）+ 标题 + 可下载音频 enclosure 或 content:encoded 完整文字稿至少一种；本批 7 条全部有文字稿，其中 6 条另有音频。2026-10-24 修复前 ready-clip 只是父集上的附带字段（ready-clip.xml 里仍是整集 enclosure），修复后片段是独立条目，见“条目一览”第 6、7 条。

一条目可兼有音频、文字，不重复建三条。视频形态本批 0 条，见下。

## 本批数量（2026-10-24 北京时间采集核验，修复后）

- 总计：7 条 = 5 父集 + 2 独立片段
- 按主题：science-space（科学/太空）3 条（父集 2 + 片段 1）；ocean-environment（海洋/环境）3 条（父集 2 + 片段 1）；technology-ai（科技/AI）1 条
- 按形态：audio 6 条（父集 4 + 片段 2）；text 7 条；video 0 条
- 按生产形态：full-episode 4 条；text-script 5 条（父集文字稿用途标签，与时长标签正交）；ready-clip 2 条（仅片段，父集不再标 ready-clip，full-episode 与 ready-clip 两集合不相交）
- 来源：NASA 官方播客 3 父集；NOAA Ocean Podcast 2 父集；片段均出自上述父集，不另算来源

## 条目一览

1. NASA's Curious Universe – Inside a Black Hole（science-space，audio+text，full-episode+text-script）
   原发布 2020-11-23，MP3 29,380,743 字节，audio/mpeg，时长 1203.9 秒，文字稿 3005 词。
2. NASA's Curious Universe – Encore: A Year In Mars Dune Alpha（science-space，audio+text，full-episode+text-script）
   Encore 发布 2026-10-20（最初 2023 年），MP3 39,402,865 字节，audio/mpeg，时长 1626.1 秒，文字稿 4177 词。子片段见第 6 条。
3. NOAA Ocean Podcast Ep.66 – Rip Currents: Preparedness and Prevention（ocean-environment，audio+text，full-episode+text-script）
   原发布 2023-06-28（仅到日），M4A 16,026,456 字节，audio/mp4，时长 818.4 秒，文字稿 2752 词。子片段见第 7 条。
4. NOAA Ocean Podcast Ep.71 – Coral Bleaching（ocean-environment，audio+text，full-episode+text-script）
   原发布 2023-12-05（仅到日），M4A 16,134,595 字节，服务器返回 MIME audio/mp4a-latm；2026-10-24 已整文件下载并经 ffmpeg 全量解码通过（ftyp M4A，AAC 44.1kHz 立体声，997.0 秒），见 SOURCES.md 的兼容提示：下游应按 .m4a 后缀/容器处理，不能只凭 MIME 判定。文字稿 2060 词。
5. Houston We Have a Podcast Ep.424 – AI at NASA（technology-ai，text 仅，text-script）
   发布 2026-05-29（仅到日；页内只写录制于 2026-05-05），文字稿 5521 词，封面为仓库自托管默认封面（原 NASA 缩略图在用户本机返回 429，本机后端 HEAD 为 200，属不稳定链接，已改用自托管兜底，不冒充官方 Logo）。
   音频未入库：Megaphone 订阅源 ID 未能在官方来源中唯一核实，不猜 MP3 地址；故本条不进 audio feed，只进总 feed、technology-ai feed 与 text feed。
6. 片段：Their Mars window is a TV — clip from Encore: A Year In Mars Dune Alpha（science-space，audio+text，ready-clip 仅）
   独立 GUID `urn:podcast:nasa.gov:curious-universe:encore-a-year-in-mars-dune-alpha:clip:window:224-255`，与父集 GUID 不同；父集 GUID 见 items.json 的 _parent_guid。
   片段 enclosure 为仓库直链 `https://raw.githubusercontent.com/TikerBin/podcast-upstream/main/clips/chapea-clip1-window.mp3`，audio/mpeg，551,621 字节，31.0 秒，原集 224.0–255.0 秒，原声。
   片段文案仅 91 词（本地 faster-whisper small.en 转写片段音频，与 2026-10-24 工作流 .ass 逐字一致，并与官方全文窗户段落对应），不是全文 4177 词，也不是摘要。
7. 片段：Break the Grip of the Rip: swim parallel, not back — clip from Rip Currents（ocean-environment，audio+text，ready-clip 仅）
   独立 GUID `urn:podcast:oceanservice.noaa.gov:podcast:june23:nop66-rip-currents:clip:335.1-380.9`，与父集 GUID 不同。
   片段 enclosure 为仓库直链 `https://raw.githubusercontent.com/TikerBin/podcast-upstream/main/clips/noaa-rip-currents-clip-335-381.mp3`，audio/mpeg，693,395 字节，45.8 秒，原集 335.1–380.9 秒，原声（片段开头为原音频中断句，如实保留）。
   片段文案仅 138 词（本地 faster-whisper small.en 转写片段音频，与官方全文 Break the Grip / 90% / 每年约 100 起段落对应），不是全文 2752 词，也不是摘要。

## 订阅地址

本地文件（已生成、可直接读）：
- 总 feed：`feed.xml`，JSON 版：`feed.json`
- 主题：`feeds/science-space.xml`、`feeds/ocean-environment.xml`、`feeds/technology-ai.xml`
- 形态：`feeds/audio.xml`、`feeds/text.xml`、`feeds/video.xml`（本批 0 条，空 feed 是如实结果）
- 生产形态（附加）：`feeds/ready-clip.xml`（2 条，仅独立片段，不含整集）

仓库创建并推送后（已生效）：
- 仓库：`TikerBin/podcast-upstream`
- 总 RSS：`https://raw.githubusercontent.com/TikerBin/podcast-upstream/main/feed.xml`
- 总 JSON：`https://raw.githubusercontent.com/TikerBin/podcast-upstream/main/feed.json`
- 分类 RSS：`https://raw.githubusercontent.com/TikerBin/podcast-upstream/main/feeds/<science-space|ocean-environment|technology-ai|audio|video|text|ready-clip>.xml`

## 分类与 GUID 规则

- 主题：science-space、ocean-environment、technology-ai；按实际采集结果扩充，不为凑分类混入不合格内容。
- 形态：audio、video、text；一节目可多形态，但只建一条。
- GUID：基于来源稳定标识生成（例如 `urn:podcast:nasa.gov:curious-universe:inside-a-black-hole`），持久保存在 items.json；标题修改、重跑、跨主题/形态 feed 均不换 ID。片段 GUID = 父集稳定 ID + 固定片段 ID/时间边界（例如 `...:encore-a-year-in-mars-dune-alpha:clip:window:224-255`），不含采集时间、不随标题改变，与父集 GUID 不同。
- pubDate：原发布时间；另存采集日（北京时间 2026-10-24）。仅到日的用当日 00:00 UTC 占位，并在 items.json 的 pub_date_precision 中注明，不伪造时刻。片段 pubDate 继承父集原发布时间，片段建模日另存在 _clip_created_beijing。
- ready-clip：只有实际截取并经 ffprobe 校验的文件才能标；片段为独立条目，标准 enclosure 为仓库自托管 clips 直链（audio/mpeg、真实字节数、片段时长），content:encoded 仅为片段文案；记录父集 GUID、原集链接、起止秒、原声性质；整集仅标 full-episode，片段仅标 ready-clip，两集合不相交。
- 封面：全部 7 条均使用仓库自托管默认封面 `images/default-cover.png`（1400×1400 PNG，43,530 字节，原创几何设计，不冒充 NASA/NOAA Logo；另有同设计 SVG 源文件）。原 NASA 缩略图因用户本机 429 不稳定，已不再作为任何条目的封面；无官方封面的条目同样用此兜底，itunes:image 均指向该 PNG。
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
- `clips/*.mp3` – 仅 2 个 ready-clip 小文件（0.5–0.7 MB），整集大文件不进 Git，仍引用官方原地址；片段 enclosure 即这些文件的 raw 直链
- `images/default-cover.png`（+ `default-cover.svg`）– 仓库自托管默认封面，全部条目的 itunes:image 兜底
- `SOURCES.md` – 来源、授权、核验链接与未覆盖原因
- `VALIDATION.log` – 本批验证结果

## 新增 / 增量更新

1. 在 items.json 追加新条（新 GUID，绝不复用旧 ID），附 transcripts 文件与核验数据；
2. 跑 `python3 build_feed.py --base-url <真实托管地址>`；
3. 跑 `python3 validate.py`，通过后再推送；
4. 去重：以 guid + audio_url + source_url 三重比对，同源不重复入库。

## 未完成（明确说未完成）

- 未做 Facebook 发布（本任务明确不发布到社交平台）。
- Houston Ep.424 音频未核实，未入库 audio feed。
- 视频形态 0 条，未覆盖原因见 SOURCES.md。
- Coral Bleaching：文件已全量解码通过，但 CDN MIME 仍为 audio/mp4a-latm；仅凭 MIME 判定的下游播放器仍可能拒绝，需按 .m4a 后缀/容器处理（见 SOURCES.md）。该限制未消除，只是已明确。
- NASA traffic.megaphone.fm 整集音频：本机后端 2026-10-24 实测 GET 200、Python Range 206 均成功，用户本机 Python SSL EOF / Node fetch 失败属用户端网络环境问题，非链接失效；故未换地址。片段生产不依赖该域（片段为仓库自托管）。
- 无定时增量采集 cron：本次只修已发现问题，未新增定时采集。
