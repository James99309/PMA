# 互动课程系统：视频课程类型设计

**日期**：2026-07-29
**背景**：现有互动课程系统只支持 HTML deck 课件（iframe + 逐页翻页 + speaker-notes）。需要新增"视频课程"作为第二种播放形式，用于承载 ELV Keynote 讲述视频（英文，32.5 分钟，752MB）等媒介。

## 目标与范围

给"互动课程"增加**视频**和 **PPT 下载**两种内容类型，与现有 HTML 课件并存为三个 tab。

**做**：
- 视频课程：HTML5 原生播放器 + 章节跳转 + 看完记录
- PPT 下载：文件下载入口
- 视频/PPT 文件走 NAS WebDAV（不进代码库）
- 章节从视频 whisper 时间轴自动生成

**不做（YAGNI）**：
- 视频转码 / 多码率自适应
- 视频内知识析出 + 考核（HTML 课件才有）
- 字幕自动烧录（先留 `<track>` 接口）
- 断点续传上传

## 关键决策

| 决策 | 选择 | 理由 |
|---|---|---|
| 视频课程能力范围 | 播放 + 看完记录 | 不做考核/知识析出，保持轻量 |
| 视频存储与播放 | WebDAV + Range 流式代理 | SG NAS 仅 3.7G，整块进内存会 OOM |
| 大文件上传 | Tailscale 直传 NAS + 后台登记 | 绕开 nginx 50MB 限制和 Cloudflare 超时 |
| 章节来源 | 对英文视频跑 whisper 自动对齐 | 英文视频新录，无现成页时间点 |
| 入口展示 | 顶层列表页三 tab（视频/课件/PPT） | 三类内容各自独立池 |

## 数据模型

`InteractiveCourse` 加字段，不新建表：

```python
media_type = Column(String(20), nullable=False, default='html')
#   'html'  → 现有 deck 课件（默认，存量数据不受影响）
#   'video' → 视频课程
#   'ppt'   → PPT/PDF 下载文件
media_url  = Column(String(500), nullable=True)   # video/ppt: NAS WebDAV 相对路径；html: 留空
duration   = Column(Integer, nullable=True)        # 视频时长(秒)
file_size  = Column(Integer, nullable=True)        # 文件字节数(PPT 下载显示大小)
chapters   = Column(Text, nullable=True)           # 视频章节 JSON: [{"page":1,"start":0,"title":"..."}]
```

- **存量零影响**：`media_type` 默认 `'html'`，迁移回填所有现有行为 `'html'`，行为不变。
- **一张表三类型**：靠 `media_type` 分流，卡片墙/权限/owner/topic 全复用。
- **文件不进库**：video/ppt 文件在 NAS WebDAV，表存 `media_url`；HTML 课件继续走 `course_assets/`。
- **迁移幂等**：`ADD COLUMN IF NOT EXISTS`，符合 CN/SG 双实例部署规范。命名 `video_course_20260729.py`。

## 列表页（三 tab）

`/wiki/at` 互动课程区改为三 tab，后端按 `media_type` 分组：

```python
courses = InteractiveCourse.query.filter(...).all()
grouped = {
    'video': [c for c in courses if c.media_type == 'video'],
    'html':  [c for c in courses if c.media_type == 'html'],
    'ppt':   [c for c in courses if c.media_type == 'ppt'],
}
```

- **视频 tab**：卡片 = 封面 + 标题 + ⏱ 时长角标 → 视频播放页
- **互动课件 tab**：现有卡片墙原样不动 → 现有 iframe 播放器
- **PPT 下载 tab**：卡片 = 封面色 + 标题 + 📄 类型/大小 → 直接下载
- tab 切换纯 CSS/JS 显隐，不额外请求
- 权限沿用 `_course_is_public` / 登录可见 / admin 可管理
- 空 tab 显示占位提示

## 视频流式代理（技术核心）

新写支持 HTTP Range 的端点，避免整块进内存：

```python
@knowledge_wiki_bp.route('/wiki/play/<course_key>/video')
@login_required
def course_video(course_key):
    row = _find_course_row(course_key)          # media_type='video'
    client = get_synology_webdav_client()
    total = client.get_file_info(row.media_url)['size']
    range_header = request.headers.get('Range')
    if range_header:
        start, end = _parse_range(range_header, total)
        def generate():
            CHUNK = 1024 * 512
            pos = start
            while pos <= end:
                n = min(CHUNK, end - pos + 1)
                yield client.download_file_range(row.media_url, pos, pos + n - 1)
                pos += n
        return Response(stream_with_context(generate()), status=206, headers={
            'Content-Range': f'bytes {start}-{end}/{total}',
            'Accept-Ranges': 'bytes',
            'Content-Length': str(end - start + 1),
            'Content-Type': 'video/mp4',
        })
    # 无 Range：同样流式返回
```

- **内存恒定**：同时只持有 512KB，SG 内存安全。
- **拖动即时**：浏览器 seek 发 Range，服务器只取那段，`206 + Accept-Ranges` 让 `<video>` 原生支持拖动。
- **权限受控**：`@login_required`，不裸奔。
- **风险**：Cloudflare 隧道对长响应有隐性限制，长视频流可能中断 → 实测确认，扛不住则退回 Tailscale 内网播放。

## 视频播放页

新模板 `at_video_player.html`（不复用 iframe 外壳）：

- HTML5 `<video controls>`，`src` 指向 Range 端点，进度/音量/倍速/全屏全原生
- 右侧章节列表从 `chapters` JSON 渲染，点击 `video.currentTime = start` 跳转；`timeupdate` 高亮当前章节
- 字幕：`<track>` 接口预留（英文讲稿可生成 `.vtt`），非必需

## 看完记录

复用 `TrainingModuleState`，不新建表：

- 前端 `timeupdate` 每 15 秒节流上报 `currentTime/duration`
- 后端记 `last_position`；`progress_pct >= 0.9` 判 `completed`
- 续播：重开从 `last_position` 继续
- 管理端查学习记录，与 HTML 课程同一处

## 章节自动生成（一次性脚本）

对英文视频跑 whisper（带时间戳）→ 22 页英文讲稿与转写对齐 → 得每页起始秒 → 写入 `chapters`。产出后存库，播放时直接读。生成后人工抽查几个章节点，偏差手动微调。

## 上传登记流程

两步解耦：

1. **文件上 NAS**：本机视频经 Tailscale scp/rsync → SG NAS WebDAV 目录（如 `/volume1/web/pma-media/courses/`）。绕开 nginx 50MB + Cloudflare 超时。
2. **PMA 登记**：管理员在视频/PPT tab 点"登记" → 填元信息 + 文件路径 → 建 media_type 记录，视频触发 whisper 章节生成。

## 实施顺序

1. 数据模型 + 幂等迁移 → 验证存量 HTML 课程不变
2. Range 流式端点（先小 mp4 测通路）→ 验证拖动 + 内存不涨
3. 三 tab 列表 + 视频播放页 + 章节 → 本地放通、章节跳转
4. 看完记录（接 TrainingModuleState）
5. 登记入口（video/ppt 后台表单）
6. 章节自动生成脚本（whisper 对齐）
7. 部署：视频传 SG NAS → 登记 → 真机验证 Cloudflare 隧道扛不扛得住长视频流

## 风险清单

| 风险 | 应对 |
|---|---|
| Cloudflare 隧道可能中断长视频流 | 第 7 步实测；退回 Tailscale 内网播放 |
| SG NAS 内存紧张（3.7G 已 swap） | Range 流恒定 512KB 已规避；并发多路需观察 |
| whisper 对齐英文视频页边界可能不准 | 生成后人工抽查微调 |
| 存量 HTML 课程受影响 | media_type 默认 html + 迁移回填，零改动 |
