# Podcast 每日采集运行手册（cron：podcast-daily-upstream）

- 调度：每天 09:00 Asia/Shanghai（固定时区，不受美国夏令时影响），任务 ID `podcast-daily-upstream`，已启用。
- 授权：用户 2026-10-26 明确授权每日采集、片段制作、分类 RSS/JSON 更新、向 TikerBin/podcast-upstream 推送。不发布 Facebook，不生成视频成片，不安装/升级工具，不购买/开通服务，不改动 fb-reels/fb360 等其他任务。
- 工程：`~/workspace/podcast-upstream`，`items.json` 为唯一数据源；`build_feed.py` 生成总 feed 与分类 feed；`validate.py` 为独立验证；`daily_check.py` 为只读候选检查（不改 items.json）。

## 每日流程（按顺序，不跳步）

1. 锁：检查 `.daily.lock`（gitignore）。存在且未满 4 小时则退出；过期则删锁继续；结束必删锁。
2. 候选：跑 `python3 daily_check.py`。它只读 items.json，对比已入库来源 URL，输出 Curious Universe RSS 与 NOAA 索引的候选短名单（各最多 5 条，按发布时间倒序）。候选存在不是失败；两个源都抓不到才算源站失败。
3. 门槛（逐条，不合格不入库，记 rejected 不重复上报）：
   - 公开、稳定、来源清楚；仅限美国政府官方播客（NASA/NOAA）公有领域，且不得暗示官方背书。
   - 必须有官方完整文字稿（不是摘要/简介）或稳定可下载音频 enclosure；音频须 HEAD + 下载 ffprobe 核对 MIME、字节数、时长。
   - 不绕过登录/付费墙/下载限制；不猜 MP3 地址；YouTube 仅链接、商业播客、Spotify/小宇宙独占、仅页面链接的视频播客不入库。
   - 单集内第三方音乐 cue 正式发布前逐项再核，含音乐的片段不标 ready-clip。
   - 主题仅 science-space、ocean-environment、technology-ai；不为凑数放宽。
4. 补齐与增量：第一次运行可合理补齐此前未处理的新近单集，但每天最多新入库 2 个父集（按发布时间倒序、过门槛者优先），其余候选留待次日，避免一次涌入上百条旧单集。之后按成功游标增量：游标 = 已推送的 items.json GUID 集合 + `daily_state.local.json` 的 last_success（仅推送并 raw 核验通过后更新）。
5. ready-clip（优先，但不强求）：对新内容挑完整且可独立传播的 30–60 秒片段。ffmpeg 从已验证整集实际截取 MP3；本地 faster-whisper small.en（`~/workspace/podcast-reels-workflow/venv`，ffmpeg 16k 单声道 workaround）转写并逐句核对片段全文；片段为独立条目，GUID = 父集稳定 ID + 固定片段身份/时间边界（不含采集时间、不随标题改变），与父集 GUID 不同；记录父集 GUID、原来源、起止秒、语言、原声性质；标准 enclosure 为 GitHub clips 绝对直链，length 真实字节数，audio/mpeg，duration 为片段时长（ffprobe 与 end-start 误差 ≤0.2 秒）；content:encoded 只能是实际片段完整文案，不能是整集或摘要；封面用仓库默认封面 `images/default-cover.png` 兜底。无合适片段时只收合格整集/全文，不标 ready-clip；同父集重叠或语义重复片段不反复入库。
6. 去重：items.json + `daily_state.local.json` 持久保存来源稳定 ID、规范化来源 URL（去尾斜杠）、已处理父集与片段。同一来源/片段跨日期、重跑、标题变化不得重建 ID；同条跨主题/形态 feed 沿用同一 GUID；父集 production_kinds 不再回填 ready-clip，full-episode 与 ready-clip 不相交。rejected 列表每月 1 日复查一次（来源页有新文字稿/新音频时才重新评估）。
7. 构建与验证：先备份 feed 文件，再跑 `python3 build_feed.py --base-url https://raw.githubusercontent.com/TikerBin/podcast-upstream/main`，再跑 `python3 validate.py`（GUID 唯一、分类成员精确、RSS/JSON 一致、短音频字节/解码/时长、片段文案、封面直链），再重跑一次 build_feed.py 比对 GUID 集合不变、0 重复。若除 lastBuildDate 外 feed 内容与推送前完全一致，恢复原 feed 文件，不做无意义提交。
8. 推送（仅验证通过且确实有新增/修改时）：`git add` 相关文件（items.json、feed.xml、feed.json、feeds/*.xml、新 transcripts、clips/*.mp3、必要时 images/与说明），提交信息写清北京时间日期、新增父集数、新增 ready-clip 数、排重数、失败数，`git push origin main`（复用已配置凭据，不回显、不打印、不写入日志）。推送后立即 raw 核验：总 feed、7 个分类 feed、feed.json、新增 clips、默认封面全部 200，且远端 GUID/enclosure/文案/封面与本地一致；核验失败如实报告，不谎称成功。
9. 失败处理：任何一步失败（抓取、转写、截取、构建、验证、推送、raw 核验）都用 git checkout 恢复 feed 与 items.json 到最近成功推送状态，不强推，不标成功，不推进游标，记失败原因。源站抓取失败先重试最多 3 次（约 30 秒、60 秒间隔），仍失败记当日失败项，次日按游标重试。凭据失效、源站结构变化等需用户操作时必须上报，不得静默跳过。

## 状态与日志（不进 Git）

- `.gitignore` 已含：`daily_state.local.json`、`daily_runs.log`、`.daily.lock`、`transcripts/raw/`、`__pycache__/`。
- `daily_state.local.json` 格式：`{last_check_beijing, last_check_existing_total, last_check_candidates, last_success_beijing, last_success_sha, rejected: [{source_url, reason, date}]}`。它本身不单独提交；仅随有新增的 feed 提交一并更新（或留在本地，供次日去重与 rejected 复查）。
- `daily_runs.log`：每次运行一行（北京时间日期、新增父集/ready-clip、排重、失败、提交 SHA 或“无提交”、raw 核验结果）。
- goal:podcast-material-rss-upstream 的 hidden_files/ 可另存一份运行记录（若可写），不写成用户可见的 files/ 文档。

## 通知口径

- 有实际新增发布、失败、或需用户操作时报告：新增数、排重数、失败数、提交 SHA、总/分类订阅地址、核验结果、剩余问题。
- 无新增且无异常时保持安静：运行历史留一条简短记录即可，不发用户可见消息。
- 绝不把“准备完成”说成“已启用”或“已发布”；没有推送成功的 SHA 就不要声称发布成功。

## 已装工具（不安装、不升级）

- python3、curl、ffmpeg/ffprobe、PIL（封面）、本地 faster-whisper small.en（venv，见上）。
- 封面：全部条目默认 `images/default-cover.png`（1400×1400 PNG，原创设计，不冒充官方 Logo）。
- 已知限制（2026-10-24 复测）：NASA traffic.megaphone.fm 在本机后端 GET/Python Range 均成功，用户本机 SSL 失败属客户端环境问题，不换地址；珊瑚 M4A 的 CDN MIME 为 audio/mp4a-latm 但文件可全量解码，下游应按 .m4a 后缀/容器处理；Houston Ep.424 音频仍未核实，不入库 audio feed。
