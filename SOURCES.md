# 来源与授权清单（2026-10-24 北京时间核验，含当日修复复测）

## 入库条目核验表

| 条目 | 来源页 | 音频地址（enclosure） | HEAD / 下载核验 | 文字稿来源 |
|---|---|---|---|---|
| Inside a Black Hole | https://www.nasa.gov/podcasts/curious-universe/inside-a-black-hole/ | https://traffic.megaphone.fm/NATIONALAERONAUTICSANDSPACEADMINISTRATION3060455350.mp3?updated=1725385395 | 200，audio/mpeg，29,380,743 字节，ffprobe 1203.905 秒 | NASA 官方页全文，3005 词 |
| Encore: A Year In Mars Dune Alpha | https://www.nasa.gov/podcasts/curious-universe/encore-a-year-in-mars-dune-alpha/ | https://traffic.megaphone.fm/NATIONALAERONAUTICSANDSPACEADMINISTRATION6420899881.mp3 | 200，audio/mpeg，39,402,865 字节，ffprobe 1626.122 秒 | NASA 官方页全文，4177 词 |
| Rip Currents Ep.66 | https://oceanservice.noaa.gov/podcast/june23/nop66-rip-currents.html | https://cdn.oceanservice.noaa.gov/oceanserviceprod/podcast/june23/nop66-rip-currents.m4a | 官方地址 301 到 CDN 永久地址；200，audio/mp4，16,026,456 字节，ffprobe 818.434 秒 | NOAA 官方页 Transcript 全文，2752 词 |
| Coral Bleaching Ep.71 | https://oceanservice.noaa.gov/podcast/dec23/nop71-coral-bleaching.html | https://cdn.oceanservice.noaa.gov/oceanserviceprod/podcast/dec23/nop71-coral-bleaching.m4a | 官方地址 301 到 CDN 永久地址；200，audio/mp4a-latm，16,134,595 字节，ffprobe 997.042 秒 | NOAA 官方页 Transcript 全文，2060 词 |
| AI at NASA Ep.424 | https://www.nasa.gov/podcasts/houston-we-have-a-podcast/ai-at-nasa/ | 无（本批未核实，不猜） | 不适用 | NASA 官方页 Transcript 全文，5521 词 |

## 2026-10-24 修复复测（用户实测问题回应）

- ready-clip 旧模型问题：修复前 ready-clip.xml 里的 2 条仍是整集 GUID/title/content/enclosure（CHAPEA 39,402,865 字节/1626 秒，离岸流 16,026,456 字节/818 秒），_ready_clip 仅记相对路径。修复后片段为独立条目，见下表；父集 production_kinds 已去掉 ready-clip，ready-clip.xml 仅含 2 个片段条目。
- 片段核验表：

| 片段 | 独立 GUID | enclosure（仓库直链） | 字节 / 时长 / MIME | 片段文案 |
|---|---|---|---|---|
| CHAPEA window | urn:podcast:nasa.gov:curious-universe:encore-a-year-in-mars-dune-alpha:clip:window:224-255 | https://raw.githubusercontent.com/TikerBin/podcast-upstream/main/clips/chapea-clip1-window.mp3 | 551,621 字节 / 31.0 秒 / audio/mpeg，本地 ffprobe 与 raw HEAD 均一致 | 91 词，仅片段音频（faster-whisper small.en 转写，与工作流 .ass 逐字一致） |
| Rip 335.1–380.9s | urn:podcast:oceanservice.noaa.gov:podcast:june23:nop66-rip-currents:clip:335.1-380.9 | https://raw.githubusercontent.com/TikerBin/podcast-upstream/main/clips/noaa-rip-currents-clip-335-381.mp3 | 693,395 字节 / 45.8 秒 / audio/mpeg，本地 ffprobe 与 raw HEAD 均一致 | 138 词，仅片段音频（faster-whisper small.en 转写，与官方全文 Break the Grip / 90% / 约 100 起段落对应） |

- 封面：全部 11 条的 itunes:image 均为仓库自托管 `images/default-cover.png`（1400×1400 PNG，43,530 字节，原创几何设计，不冒充 NASA/NOAA Logo；另有同设计 SVG 源文件）。AI 集原 NASA 缩略图在本机后端 HEAD 为 200 image/png，但在用户本机返回 429，属不稳定链接，已不再用作封面；其他 4 父集此前无图，同样用此兜底。封面 URL 推送后实测 200（见推送验证）。
- NOAA 原音频复测（本机后端，2026-10-24）：两条 HEAD 200，Range 0–1023 返回 206、1024 字节；离岸流 audio/mp4、16,026,456 字节，珊瑚 audio/mp4a-latm、16,134,595 字节，与 items.json 一致。
- NASA 原音频复测（本机后端，2026-10-24）：curl 跟随重定向完整 GET 均 200——黑洞 29,380,743 字节 / 1203.905 秒（8.7 秒下载），CHAPEA 39,402,865 字节 / 1626.122 秒（12.9 秒下载）；Python urllib Range 0–1023 亦 206 成功、audio/mpeg、Content-Range 与总字节一致。结论：链接未失效，用户本机 Python SSL EOF / Node fetch 失败属用户端网络环境问题（代理/TLS/边缘节点差异），非链接失效；故未换地址、未破坏原来源。片段生产不依赖该域（片段为仓库自托管）。
- Coral M4A 解码复测（本机后端，2026-10-24）：整文件重新下载 16,134,595 字节，文件头 ftyp major brand `M4A `，ffprobe 格式 mov,mp4,m4a，音频 AAC 44.1kHz 立体声（另含 1 路 mjpeg 附属流，常见于带封面的 M4A），ffmpeg 全量解码零报错通过。结论：文件本身可解码，限制在 MIME 层——仅凭 MIME 判定的下游可能拒绝 audio/mp4a-latm；下游应按 .m4a 后缀/容器（ftyp M4A）处理，或忽略 mjpeg 附属流只取音频流。enclosure 仍如实写服务器 MIME，未擅自改写。

## 关键核验说明

- NASA 音频：enclosure 用 traffic.megaphone.fm 稳定地址，**不存**重定向后的 dcs 签名地址。签名地址每次请求都会变、很快过期；稳定地址本身可长期引用，后台下载时跟随 302 即可。字节数与 MIME 是跟随重定向后实测的，不是编造的。
- NOAA 音频：官方 oceanservice 地址返回 301 到 cdn.oceanservice.noaa.gov 永久地址；enclosure 直接用 CDN 地址，source_url 仍保留官方页。
- Coral Bleaching MIME 异常：同一 CDN 对离岸流返回 audio/mp4，对珊瑚白化返回 audio/mp4a-latm。enclosure 如实写服务器返回的 MIME，未改写。2026-10-24 已整文件解码通过（见上），但仅凭 MIME 判定的下游仍可能拒绝，需按 .m4a 后缀/容器处理——本批不擅自改写 MIME。
- 发布时间：黑洞与 CHAPEA Encore 的精确时刻来自 NASA Curious Universe Megaphone RSS（https://feeds.megaphone.fm/NATIONALAERONAUTICSANDSPACEADMINISTRATION8162188566）；NOAA 两集与 AI 集仅核到日，精度字段已注明。
- 权利：NASA / NOAA 均为美国政府作品，一般不受版权保护；本清单的“可再分发”指在不暗示官方背书、且正式发布前再核单集内第三方音乐的前提下可用于目标工作流。不是“任何政府播客都可无条件商用”的 blanket 结论。

## 未覆盖 / 未入库（单独列出，不混进待制作 feed）

- 视频播客：本批无官方稳定 MP4 + 音频/文案双齐的视频播客。NASA 部分单集的 YouTube 视频版只有页面链接，无合格 enclosure，且 YouTube 批量下载受平台条款限制，故不入库。
- 商业播客原声（Hard Fork、Acquired、AI Daily Brief 等）：有版权，仅公开可听不等于允许重用，故不入库。
- Spotify / 小宇宙独占、无公开 RSS 的节目：无官方公开音频直链，无法在不绕过登录/付费墙的前提下核验，故不入库。
- Houston Ep.424 音频：Megaphone 订阅源 ID 未能在官方来源中唯一核实，不猜地址；文字稿已入库，音频待后续核实。
- 其他 NASA / NOAA 单集：本批只做了 5 条小规模样本，未逐集全量扫描；后续增量采集按同一门槛逐集核验，不批量放行。

## 后续采集的门槛（复用）

公开、稳定、来源清楚、适合 Facebook Reels 科普动画选题；音频 enclosure 必须是长期稳定、可直接下载、MIME 与字节数实测；文字稿必须是完整文字稿，不是摘要；GUID 稳定；权利必须明确可用于目标工作流，否则只进未入库清单。
