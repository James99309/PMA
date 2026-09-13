# AT 知识库内容发布包

## 亚太数据中心关键通信中文培训

`assets/apac-dc-cn/` 保存 26 页课程画面、逐页中文讲义和原始 PPT。发布后形成三项相互关联的内容：

- 互动课件：`/wiki/play/apac-data-center-critical-comms-cn`
- Wiki 文章：由 26 页讲义析出，归入 `行业知识`，支持搜索、问答和页码深链
- PPT 下载：在“互动课程 → PPT 下载”中显示，原始文件保留讲义备注

本地只构建和检查，不写数据库：

```bash
python3 deploy/knowledge-content/publish_apac_dc.py
```

CN NAS 上完成正式发布：

```bash
./deploy/knowledge-content/publish-apac-dc-on-nas.sh --commit
```

该脚本仅适用于中国 NAS（SP8D / `pma_synology`），会使用现有 CN WebDAV 配置存放原始 PPT。

## APAC data center critical communications — English training

`assets/apac-dc-en/` contains the 26 formal presentation modules, their English
speaker notes, a PowerPoint-native cover and the complete 30-slide source PPT.
Slides 27–30 remain in the downloadable PPT as SIRIM interview backup material;
they are intentionally excluded from the formal interactive course.

- Interactive course: `/wiki/play/apac-data-center-critical-comms-en`
- Wiki article: derived from all 26 module notes under `Industry-Knowledge`
- PPT download: the original 30-slide deck, with its speaker notes intact

Build locally without storage or database writes:

```bash
python3 deploy/knowledge-content/publish_apac_dc.py --market sg
```

Publish from the SG NAS checkout:

```bash
./deploy/knowledge-content/publish-apac-dc-on-sg-nas.sh --commit
```

The SG wrapper fails closed unless the application identifies itself as OVS and
its database URL ends in `/pma_sa`.

## DG/TJ 08—2406—2022

把上海市工程建设规范《专用数字无线对讲通信系统工程技术标准》上架到 AT 知识库：
一个交互阅读器（互动课程）+ 一套可检索文章（文章库）。中英文各一份。

## 为什么需要它

`update.sh` 只管代码。这两样它管不到：

- **课件文件**：`app/course_assets/` 在 `.gitignore` 里（历史上放过 15MB 的 deck），git 不带
- **wiki 文章**：没有批量导入的 UI

以前靠手工 ssh + `docker exec` 拼命令，容易漏步骤、事后没法复查。这里把**输入**
（转换包源、译文、React UMD、封面）随包版本化，NAS 上 checkout 出来就能复现同一份产物；
**构建产物**（阅读器 html 约 900KB）仍然不进 git，按需重建。

## 用法

```bash
# 容器内，或本机已设好 DATABASE_URL 的环境
python3 deploy/knowledge-content/publish.py cn              # 预览：只构建，不写库
python3 deploy/knowledge-content/publish.py cn --commit     # 中文版上架
python3 deploy/knowledge-content/publish.py en --commit     # 英文版上架
```

必须显式 `DATABASE_URL`，防止误写另一边的库。幂等，可重复跑。

| target | 阅读器 | 文章 | topic |
|---|---|---|---|
| `cn` | `/wiki/play/dgtj08-2406-2022`（16 章 + 附录 A–N 全文） | 19 篇 | 行业知识 |
| `en` | `/wiki/play/twr-ibs-ref-en`（Evertac 技术设计参考） | 29 篇 | Industry-Knowledge |

## 英文版是 DRAFT

英文版**不是标准的翻译版**，是 Evertac 署名的技术设计参考：只抽与司法辖区无关的工程内容
（全文 784 条里 671 条，85%）。凡是引到中国频率划分 / GB 标准 / 中国消防公安体系的地方，
正文里就地标了 `[REF-CHECK]`，共 **73 处**，等着换成 IMDA/MCMC、IEC/SS、SCDF/BOMBA 的对应项。
填完之前文章顶部带 DRAFT 横幅。

REF-CHECK 清单在构建产物 `.build/md/REF-CHECK.md`（跑一次 `publish.py en` 即生成）。

## 目录

```
assets/
  src/          转换包源：dc.html + support.js + content.js + build/doc.json
                content.js 的检索索引已补到"条目"一级（原包只到"条"）
  en/           translations.json（907 条译文）+ glossary.json（614 条表格/图术语）
  vendor/       React 18.3.1 UMD —— 内网拉不到 unpkg，必须随包走
  covers/       两份课程卡封面
lib/            构建与入库模块（publish.py 逐步调用）
.build/         构建产物，gitignore
```

## 改内容后怎么重出

译文/术语改 `assets/en/*.json` → 重跑 `publish.py en --commit`。
译文只有这一份来源，文章、阅读器、课程卡会一起变。

## 已知坑（都已在代码里处理，改动时别踩回去）

1. **内联脚本不能放进 `<x-dc>` 模板区**。dc-runtime 启动后会 `fetch(location.href)`
   重新 `parseDcText` 整页 —— 这一步不是可有可无的：`encodeCase` 先把模板里的 `<table>`
   改写成 `<sc-raw-table>`，靠这次重解析 + `RAW_UNWRAP` 才还原成真表格。把 640KB 的
   content.js 塞进模板区会让重解析认错边界（整页渲染出 JS 源码）。
2. **support.js 源码里带着 `<x-dc` / `</x-dc>` 字面量**（正则与字符串常量），内联后会被
   `parseDcText` 的文本扫描当成模板起点。`_mask_xdc_markers()` 用 `\x64` 转义改写，
   运行时值不变但扫描不到。
3. **术语替换必须长串优先**，否则「射频」会先把「射频同轴电缆」切碎。
4. **wiki 检索只索引 `title + summary`**，正文不进索引。英文文章的 summary 必须是英文，
   否则英文提问召回为 0（实测中文摘要 + 英文提问 = 0 命中）。
5. **阅读器不是分页 deck**，`page_count=0`；播放页模板据此隐藏翻页/逐页说明/考核
   （考核接口对无分页课件本来就返回"无法出题"）。
