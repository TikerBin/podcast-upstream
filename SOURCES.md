# 来源与授权清单（2026-10-24 北京时间核验）

## 入库条目核验表

| 条目 | 来源页 | 音频地址（enclosure） | HEAD / 下载核验 | 文字稿来源 |
|---|---|---|---|---|
| Inside a Black Hole | https://www.nasa.gov/podcasts/curious-universe/inside-a-black-hole/ | https://traffic.megaphone.fm/NATIONALAERONAUTICSANDSPACEADMINISTRATION3060455350.mp3?updated=1725385395 | 200，audio/mpeg，29,380,743 字节，ffprobe 1203.905 秒 | NASA 官方页全文，3005 词 |
| Encore: A Year In Mars Dune Alpha | https://www.nasa.gov/podcasts/curious-universe/encore-a-year-in-mars-dune-alpha/ | https://traffic.megaphone.fm/NATIONALAERONAUTICSANDSPACEADMINISTRATION6420899881.mp3 | 200，audio/mpeg，39,402,865 字节，ffprobe 1626.122 秒 | NASA 官方页全文，4177 词 |
| Rip Currents Ep.66 | https://oceanservice.noaa.gov/podcast/june23/nop66-rip-currents.html | https://cdn.oceanservice.noaa.gov/oceanserviceprod/podcast/june23/nop66-rip-currents.m4a | 官方地址 301 到 CDN 永久地址；200，audio/mp4，16,026,456 字节，ffprobe 818.434 秒 | NOAA 官方页 Transcript 全文，2752 词 |
| Coral Bleaching Ep.71 | https://oceanservice.noaa.gov/podcast/dec23/nop71-coral-bleaching.html | https://cdn.oceanservice.noaa.gov/oceanserviceprod/podcast/dec23/nop71-coral-bleaching.m4a | 官方地址 301 到 CDN 永久地址；200，audio/mp4a-latm，16,134,595 字节，ffprobe 997.042 秒 | NOAA 官方页 Transcript 全文，2060 词 |
| AI at NASA Ep.424 | https://www.nasa.gov/podcasts/houston-we-have-a-podcast/ai-at-nasa/ | 无（本批未核实，不猜） | 不适用 | NASA 官方页 Transcript 全文，5521 词 |

## 关键核验说明

- NASA 音频：enclosure 用 traffic.megaphone.fm 稳定地址，**不存**重定向后的 dcs 签名地址。签名地址每次请求都会变、很快过期；稳定地址本身可长期引用，后台下载时跟随 302 即可。字节数与 MIME 是跟随重定向后实测的，不是编造的。
- NOAA 音频：官方 oceanservice 地址返回 301 到 cdn.oceanservice.noaa.gov 永久地址；enclosure 直接用 CDN 地址，source_url 仍保留官方页。
- Coral Bleaching MIME 异常：同一 CDN 对离岸流返回 audio/mp4，对珊瑚白化返回 audio/mp4a-latm。enclosure 如实写服务器返回的 MIME，未改写。下游播放器若不认 audio/mp4a-latm，需在订阅级做一次兼容测试，或在测试通过后统一改写并注明——本批不擅自改写。
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
