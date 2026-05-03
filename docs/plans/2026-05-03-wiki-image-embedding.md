# Wiki 知识库图片内嵌实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让 wiki 文章在编译时把 raw 文件中的图片提取到 `_assets/` 并以 Markdown 引用内嵌到正文，使 AI 提取（GEO writer / search_wiki MCP）和前端阅读都能获得图文一体的知识，且支持后续手工替换图片不被重编译覆盖。

**Architecture:**
- 编译时图片落到 `storage/knowledge_base/wiki/<topic>/_assets/<slug>/img-N.{png,jpg}`，Markdown 用相对路径 `![caption](_assets/<slug>/img-N.png)` 内嵌引用
- `KnowledgeWikiArticle` 增加 `image_manifest` (JSON 清单) 和 `manually_edited` (覆盖保护) 两个字段
- 替换图片 = 覆盖文件 + 旧文件移到 `_assets/<slug>/.history/` + 置 `manually_edited=True`，Markdown 不动
- 一次性回填 7 篇旧文章（全量重 ingest，旧 .md 备份后覆盖）

**Tech Stack:** Flask + SQLAlchemy + Alembic, python-docx (zipfile 直读), PyMuPDF (已有), Anthropic SDK (已有), Tailwind 前端

**Out of scope (deferred):**
- L2 增删图（插入新图到段落 N 后、删除现有图）
- L3 拖拽式 Markdown 所见即所得编辑器
- raw 文件更新后的"增量"重编译（目前是全量替换）

---

## Phase 1 — 数据层基础

### Task 1: 添加 `image_manifest` 和 `manually_edited` 字段到 KnowledgeWikiArticle

**Files:**
- Modify: `app/models/knowledge.py:120-185` (KnowledgeWikiArticle)
- Create: `migrations/versions/xxxx_wiki_image_manifest.py`

**Step 1: 修改模型**

```python
# app/models/knowledge.py — KnowledgeWikiArticle 类内
image_manifest = Column(JSON, nullable=True)
# 结构: [{'index': 1, 'path': '_assets/<slug>/img-1.png',
#         'caption': str, 'source': {'type': 'docx_para', 'paragraph_index': 12},
#         'manually_replaced': False, 'replaced_at': None,
#         'sha256': str, 'size_bytes': int}, ...]

manually_edited = Column(Boolean, nullable=False, default=False, server_default='false')
```

`to_dict()` 中追加：
```python
'image_manifest': self.image_manifest or [],
'manually_edited': bool(self.manually_edited),
```

**Step 2: 生成迁移**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  flask db migrate -m "add image_manifest and manually_edited to wiki articles"
```

人工审查生成的 migration，确保 server_default='false' 用 `sa.text("false")` 写法。

**Step 3: 应用到本地**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db upgrade
```

**Step 4: 验证**

```bash
psql $DATABASE_URL -c "\d knowledge_wiki_articles" | grep -E "image_manifest|manually_edited"
```
Expected: 两列都存在，`manually_edited` 默认 `false`。

**Step 5: Commit**

```bash
git add app/models/knowledge.py migrations/versions/
git commit -m "feat(wiki): add image_manifest and manually_edited fields"
```

---

### Task 2: 资源目录与历史备份的 storage 辅助函数

**Files:**
- Modify: `app/services/wiki/paths.py` (添加 assets 路径辅助)
- Modify: `app/services/wiki/storage.py` (manifest 读写 + history 备份)
- Test: `tests/wiki/test_storage.py`

**Step 1: 写失败测试**

```python
# tests/wiki/test_storage.py 新增
def test_assets_dir_path(app):
    from app.services.wiki.paths import assets_dir_for_article
    p = assets_dir_for_article('product', 'gp328p')
    assert p.name == 'gp328p'
    assert p.parent.name == '_assets'
    assert p.parent.parent.name == 'product'

def test_save_article_image_creates_file_and_returns_relative_path(app, tmp_wiki):
    from app.services.wiki.storage import save_article_image
    rel = save_article_image('product', 'gp328p', 1, b'\x89PNG\r\n\x1a\n...', 'image/png')
    assert rel == '_assets/gp328p/img-1.png'
    abs_path = tmp_wiki / 'wiki' / 'product' / rel
    assert abs_path.exists()

def test_replace_article_image_backs_up_old_to_history(app, tmp_wiki):
    from app.services.wiki.storage import save_article_image, replace_article_image
    save_article_image('product', 'gp328p', 1, b'OLD', 'image/png')
    replace_article_image('product', 'gp328p', 1, b'NEW', 'image/png')
    abs_path = tmp_wiki / 'wiki' / 'product' / '_assets' / 'gp328p' / 'img-1.png'
    assert abs_path.read_bytes() == b'NEW'
    history = list((abs_path.parent / '.history').glob('img-1.png.*.bak'))
    assert len(history) == 1
    assert history[0].read_bytes() == b'OLD'
```

`tmp_wiki` fixture 使用现有 conftest 风格（参考 `tests/wiki/test_compiler.py` 的设置）。

**Step 2: 运行测试 → 失败**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  pytest tests/wiki/test_storage.py -k "image" -v
```
Expected: ImportError / AttributeError。

**Step 3: 实现**

```python
# app/services/wiki/paths.py
def assets_dir_for_article(topic: str, slug: str) -> Path:
    """返回某篇文章的 _assets 目录绝对路径，如 wiki/product/_assets/gp328p/"""
    return get_wiki_dir() / topic / '_assets' / slug

def article_image_relative_path(slug: str, index: int, ext: str) -> str:
    """返回相对 article .md 的 markdown 引用路径，如 _assets/gp328p/img-1.png"""
    return f'_assets/{slug}/img-{index}.{ext.lstrip(".")}'
```

```python
# app/services/wiki/storage.py
import hashlib
from datetime import datetime
from app.services.wiki.paths import assets_dir_for_article, article_image_relative_path

_MEDIA_TYPE_EXT = {
    'image/png': 'png', 'image/jpeg': 'jpg', 'image/jpg': 'jpg',
    'image/gif': 'gif', 'image/webp': 'webp',
}

def _ext_for_media(media_type: str) -> str:
    ext = _MEDIA_TYPE_EXT.get(media_type.lower())
    if not ext:
        raise ValueError(f'不支持的图片类型: {media_type}')
    return ext

def save_article_image(topic: str, slug: str, index: int, data: bytes, media_type: str) -> str:
    """保存图片到 _assets/<slug>/img-<index>.<ext>，返回相对 article 的路径。"""
    validate_topic_slug(topic, slug)
    if index < 1:
        raise ValueError('index 从 1 开始')
    ext = _ext_for_media(media_type)
    out_dir = assets_dir_for_article(topic, slug)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'img-{index}.{ext}'
    out_path.write_bytes(data)
    return article_image_relative_path(slug, index, ext)

def replace_article_image(topic: str, slug: str, index: int, data: bytes, media_type: str) -> str:
    """覆盖现有图片，旧文件备份到 .history/。返回相对路径。"""
    validate_topic_slug(topic, slug)
    ext = _ext_for_media(media_type)
    out_dir = assets_dir_for_article(topic, slug)
    out_path = out_dir / f'img-{index}.{ext}'
    if out_path.exists():
        history_dir = out_dir / '.history'
        history_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d-%H%M%S')
        backup = history_dir / f'img-{index}.{ext}.{ts}.bak'
        backup.write_bytes(out_path.read_bytes())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    return article_image_relative_path(slug, index, ext)

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
```

**Step 4: 运行测试 → 通过**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  pytest tests/wiki/test_storage.py -k "image" -v
```
Expected: 3/3 PASS。

**Step 5: Commit**

```bash
git add app/services/wiki/paths.py app/services/wiki/storage.py tests/wiki/test_storage.py
git commit -m "feat(wiki): asset path helpers + image save/replace with .history backup"
```

---

## Phase 2 — 编译器抽图能力

### Task 3: 从 .docx 提取图片（含段落锚点）

**Files:**
- Create: `app/services/wiki/docx_images.py`
- Test: `tests/wiki/test_docx_images.py`
- Test fixture: `tests/wiki/fixtures/sample_with_images.docx` (放一个含 2-3 张图的小测试文档)

**Step 1: 写失败测试**

```python
# tests/wiki/test_docx_images.py
from pathlib import Path
import pytest

FIXTURE = Path(__file__).parent / 'fixtures' / 'sample_with_images.docx'

def test_extract_returns_images_with_paragraph_anchors():
    from app.services.wiki.docx_images import extract_docx_images
    images = extract_docx_images(FIXTURE)
    assert len(images) >= 1
    img = images[0]
    assert isinstance(img['data'], bytes)
    assert img['media_type'].startswith('image/')
    assert 'paragraph_index' in img  # 出现在第几段(0-based)
    assert 'order' in img            # 全文档第几张图(1-based)

def test_extract_handles_docx_without_images(tmp_path):
    from docx import Document
    from app.services.wiki.docx_images import extract_docx_images
    p = tmp_path / 'no-img.docx'
    Document().save(p)
    assert extract_docx_images(p) == []
```

**Step 2: 运行 → 失败**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  pytest tests/wiki/test_docx_images.py -v
```

**Step 3: 实现**

```python
# app/services/wiki/docx_images.py
"""从 .docx 提取图片并标注其在文档段落流中的位置。

.docx 是 zip：
  word/media/image{N}.{ext}     ← 图片二进制
  word/document.xml             ← 段落流，<w:drawing> 锚点指向 image{N}
  word/_rels/document.xml.rels  ← rId → media 路径映射
"""
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'rels': 'http://schemas.openxmlformats.org/package/2006/relationships',
}

_EXT_TO_MEDIA = {
    'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
    'gif': 'image/gif', 'webp': 'image/webp', 'bmp': 'image/bmp',
}

def _parse_rels(zf: zipfile.ZipFile) -> dict[str, str]:
    """返回 rId → 'word/media/imageN.ext'"""
    try:
        data = zf.read('word/_rels/document.xml.rels')
    except KeyError:
        return {}
    root = ET.fromstring(data)
    out = {}
    for rel in root.findall('rels:Relationship', NS):
        if rel.attrib.get('Type', '').endswith('/image'):
            target = rel.attrib['Target']
            if not target.startswith('word/'):
                target = 'word/' + target.lstrip('/')
            out[rel.attrib['Id']] = target
    return out

def extract_docx_images(docx_path: str | Path) -> list[dict]:
    """提取 .docx 中所有图片，按出现顺序标注段落锚点。

    返回:
        [{
            'order': 1,                  # 文档内第几张图(1-based)
            'paragraph_index': 12,       # 出现在第几段(0-based, 在所有 <w:p> 中的序号)
            'data': bytes,
            'media_type': 'image/png',
            'original_name': 'image1.png',
        }, ...]
    """
    docx_path = Path(docx_path)
    out: list[dict] = []
    with zipfile.ZipFile(docx_path) as zf:
        rels = _parse_rels(zf)
        try:
            doc_xml = zf.read('word/document.xml')
        except KeyError:
            return []
        root = ET.fromstring(doc_xml)
        body = root.find('w:body', NS)
        if body is None:
            return []
        order = 0
        for para_idx, p in enumerate(body.findall('.//w:p', NS)):
            # 同段落内可能有多张图
            for blip in p.findall('.//a:blip', NS):
                rid = blip.attrib.get(f'{{{NS["r"]}}}embed')
                if not rid or rid not in rels:
                    continue
                media_path = rels[rid]
                try:
                    data = zf.read(media_path)
                except KeyError:
                    continue
                ext = media_path.rsplit('.', 1)[-1].lower()
                media_type = _EXT_TO_MEDIA.get(ext, 'image/png')
                order += 1
                out.append({
                    'order': order,
                    'paragraph_index': para_idx,
                    'data': data,
                    'media_type': media_type,
                    'original_name': media_path.rsplit('/', 1)[-1],
                })
    return out
```

**Step 4: 测试通过**

Expected: 2/2 PASS。

**Step 5: Commit**

```bash
git add app/services/wiki/docx_images.py tests/wiki/test_docx_images.py tests/wiki/fixtures/
git commit -m "feat(wiki): extract images from .docx with paragraph anchors"
```

---

### Task 4: 编译器把 .docx 图片落到 _assets 并把锚点信息塞进 prompt

**Files:**
- Modify: `app/services/wiki/storage.py:270` (`extract_raw_file_content`)
- Modify: `app/services/wiki/compiler.py` (text-mode 分支)
- Test: `tests/wiki/test_compiler.py` (新增 docx-with-images 测试)

**Step 1: 扩展 `RawFileContent` dataclass**

```python
# app/services/wiki/storage.py:262 周围
@dataclass
class RawFileContent:
    content_type: str       # 'text' | 'images'
    text: str = ''
    images: list = field(default_factory=list)
    total_pages: int = 0
    extracted_pages: int = 0
    embedded_images: list = field(default_factory=list)
    # embedded_images: text 模式下从 docx/pdf 嵌入图提取出来的图片清单，
    # 形如 [{'order':1,'paragraph_index':12,'data':bytes,'media_type':...}]
```

**Step 2: `extract_raw_file_content` 在 .docx 分支额外抽图**

```python
# app/services/wiki/storage.py — _extract_text_non_pdf 之后, 或在 extract_raw_file_content 中
def extract_raw_file_content(raw_path: str) -> RawFileContent:
    abs_path = (get_wiki_root() / raw_path).resolve()
    ext = abs_path.suffix.lower().lstrip('.')
    if ext == 'pdf':
        # ... existing PDF logic unchanged ...
        ...
    text = _extract_text_non_pdf(abs_path, ext)
    embedded = []
    if ext == 'docx':
        try:
            from app.services.wiki.docx_images import extract_docx_images
            embedded = extract_docx_images(abs_path)
        except Exception as e:
            logger.warning(f'[Storage] docx 抽图失败 {raw_path}: {e}')
    return RawFileContent(content_type='text', text=text, embedded_images=embedded)
```

**Step 3: 把图片信息塞进 ingest prompt**

修改 `app/services/wiki/prompts.py` 中 ingest system prompt（详见 Task 5）。

修改 `app/services/wiki/compiler.py:186` 附近 `_build_ingest_user_prompt` 调用，增加 embedded_images 参数：

```python
# compiler.py 中 _build_ingest_user_prompt 签名增加
def _build_ingest_user_prompt(
    *, raw_meta, raw_text, index_md, related_articles,
    embedded_images: list | None = None,
) -> str:
    ...
    if embedded_images:
        lines = ['## 原始文件中的嵌入图片']
        lines.append('以下图片按文档中出现的顺序排列，已被自动保存为可引用资源。')
        lines.append('**请在生成的 Markdown 中按以下规则插入图片引用**：')
        lines.append('- 用 `![简短中文说明](AUTO_IMG:N)` 占位符（N 是图片序号）')
        lines.append('- 把引用插在该图最相关的段落附近（不要全堆在文末）')
        lines.append('- 若某张图无意义可省略，不要为图编造内容')
        lines.append('')
        for img in embedded_images:
            lines.append(
                f'- 图 #{img["order"]}: 出现在原文第 {img["paragraph_index"]} 段附近, '
                f'类型 {img["media_type"]}'
            )
        prompt_section = '\n'.join(lines) + '\n\n'
        # 追加到 prompt 现有的 raw_text 区段之后
```

**Step 4: 编译器在 _apply_operations 之后落盘图片并替换占位符**

新增辅助函数 `_persist_embedded_images_and_rewrite_md(operations, embedded_images, raw)`：

```python
# compiler.py
def _persist_embedded_images_and_rewrite_md(
    operations: list[dict],
    embedded_images: list[dict],
    rollback_state: dict,
) -> dict[int, list[dict]]:
    """把 embedded_images 落到 _assets/，并用真实路径替换 operations 中
    `AUTO_IMG:N` 占位符。

    返回: {op_index: [manifest_entry, ...]}，供后续写入 KnowledgeWikiArticle.image_manifest
    """
    import re
    from app.services.wiki import storage
    pattern = re.compile(r'!\[([^\]]*)\]\(AUTO_IMG:(\d+)\)')
    manifests: dict[int, list[dict]] = {}
    for op_idx, op in enumerate(operations):
        action = (op.get('action') or '').lower()
        if action not in ('create', 'update'):
            continue
        body = op.get('body') or ''
        topic = op.get('topic')
        slug = op.get('slug')
        used: list[dict] = []

        def _sub(m):
            caption = m.group(1).strip()
            order = int(m.group(2))
            img = next((i for i in embedded_images if i['order'] == order), None)
            if not img:
                return ''  # 引用不存在的图就直接删掉占位符
            rel = storage.save_article_image(topic, slug, order, img['data'], img['media_type'])
            rollback_state['created_files'].append(f'wiki/{topic}/{rel}')
            used.append({
                'index': order,
                'path': rel,
                'caption': caption,
                'source': {'type': 'docx_para', 'paragraph_index': img.get('paragraph_index')},
                'manually_replaced': False,
                'replaced_at': None,
                'sha256': storage.sha256_bytes(img['data']),
                'size_bytes': len(img['data']),
            })
            return f'![{caption}]({rel})'

        op['body'] = pattern.sub(_sub, body)
        if used:
            manifests[op_idx] = used
    return manifests
```

把这个调用插在 `_parse_ingest_response` 之后、`_apply_operations` 之前。`_apply_operations` 写入 `KnowledgeWikiArticle` 时把对应的 manifest 存到 `image_manifest`。

**Step 5: 测试 + Commit**

新增 `test_compiler.py` 的集成测试（mock Claude 返回带 `AUTO_IMG:N` 的 JSON），验证：
- _assets/<slug>/img-1.png 文件落盘
- KnowledgeWikiArticle.image_manifest 长度 = 1 且 path 正确
- 写入的 .md 中 `![](AUTO_IMG:1)` 被替换为 `![](_assets/<slug>/img-1.png)`

```bash
git add -A && git commit -m "feat(wiki): compiler persists docx embedded images and rewrites refs"
```

---

### Task 5: 更新 ingest system prompt 说明图片占位符规则

**Files:**
- Modify: `app/services/wiki/prompts.py:get_ingest_system`

**Step 1: 在系统提示中加入图片规则段**

```python
# prompts.py — get_ingest_system 返回的字符串里追加一段
"""
## 图片处理规则
- 如果用户消息中提供了"嵌入图片"清单，请在生成的 Markdown body 中用占位符 
  `![简短中文说明](AUTO_IMG:N)` 引用，N 为清单中的图片序号
- **必须把图片引用放在与该图主题相关的段落附近**，不要全部堆在文末
- 不要凭空捏造图片，只引用清单中存在的序号
- caption（方括号里的中文说明）应当根据上下文为图片写一句简洁有信息量的描述，
  例如「PNR2100 后视图」「典型组网拓扑」，而非「图1」「示意图」这种空洞文字
"""
```

**Step 2: PDF Vision 模式同样适用**

PDF 走 vision 流程时，user message 是 image content blocks。修改方式：把 page-N 的图同样落到 `_assets/`，并在 user message 文本部分追加"图 #1 来自第 1 页, 图 #2 来自第 2 页 ..."的清单 + 同样的 `AUTO_IMG:N` 规则。

具体做法：在 `_build_ingest_vision_prompt`（compiler.py）中生成 image content block 之外，**额外**把每张图通过 `save_article_image` 预先落盘——但**这要求知道目标 topic/slug**，而 vision 模式下 slug 由 Claude 决定。

**解决方案**：vision 模式下先把图按 `_pending/<raw_id>/img-N.png` 暂存，编译完成后在 `_persist_embedded_images_and_rewrite_md` 阶段把暂存图重命名/移动到正式 `_assets/<topic>/<slug>/`。

**Step 3: Commit**

```bash
git add app/services/wiki/prompts.py app/services/wiki/compiler.py
git commit -m "feat(wiki): ingest prompt teaches Claude to use AUTO_IMG:N placeholders"
```

---

### Task 6: PDF Vision 模式图片暂存与正式化

**Files:**
- Modify: `app/services/wiki/storage.py` (新增 `_pending` 暂存路径)
- Modify: `app/services/wiki/compiler.py`

**Step 1: 暂存 + 正式化两个辅助**

```python
# storage.py
def stage_pending_image(raw_id: int, index: int, data: bytes, media_type: str) -> str:
    """把图片暂存到 wiki/_pending/<raw_id>/img-<index>.<ext>，返回相对 wiki_root 的路径"""

def promote_pending_to_article(raw_id: int, topic: str, slug: str) -> list[dict]:
    """把 _pending/<raw_id>/* 全部移到 _assets/<topic>/<slug>/，返回 manifest 条目列表"""

def cleanup_pending(raw_id: int) -> None:
    """编译失败或全部 noop 时清理暂存"""
```

**Step 2: vision 编译流程**

`compiler.py` 在 vision 分支：
- 调 `extract_raw_file_content` 拿到 N 张页图
- 用 `stage_pending_image` 把每张落到 `_pending/<raw_id>/`
- prompt 中说明"图 #1 来自第 1 页 ..."
- 解析 Claude 返回后，对每个 create/update op 调用 `promote_pending_to_article(raw.id, op.topic, op.slug)`
- 失败路径调用 `cleanup_pending(raw.id)`

**Step 3-5: 测试（mock vision 返回）+ Commit**

```bash
git commit -m "feat(wiki): vision mode persists page images via _pending staging"
```

---

## Phase 3 — 查询/输出端

### Task 7: querier 在 cited_articles 中返回 image_manifest

**Files:**
- Modify: `app/services/wiki/querier.py:96-102` (cited_articles 构造)
- Test: `tests/wiki/test_querier.py`

**Step 1: 测试**

```python
def test_cited_articles_include_image_manifest(app, mock_claude):
    art = make_article(image_manifest=[{'index':1,'path':'_assets/x/img-1.png','caption':'图1'}])
    db.session.commit()
    res = query_wiki('x', claude=mock_claude)
    cited = res['cited_articles'][0]
    assert cited['images'] == [{'index':1,'path':'_assets/x/img-1.png','caption':'图1'}]
```

**Step 2: 实现**

```python
# querier.py:96 周围
cited_articles.append({
    'id': art.id, 'topic': art.topic, 'slug': art.slug,
    'title': art.title, 'summary': art.summary,
    'images': [
        {'index': m['index'], 'path': m['path'], 'caption': m.get('caption', '')}
        for m in (art.image_manifest or [])
    ],
})
```

**Step 3-5: 测试 + commit**

```bash
git commit -m "feat(wiki): query_wiki returns image_manifest in cited_articles"
```

---

### Task 8: search_wiki MCP / internal API 暴露图片 URL

**Files:**
- Modify: `app/routes/internal_api.py` (search_wiki 路由)
- Modify: MCP server search_wiki tool（如已存在；位置 grep `search_wiki`）

**Step 1: 静态 URL 拼接策略**

引入新路由 `/wiki/asset/<int:article_id>/<path:rel>` 走 Flask（含权限校验，不要直接 `send_from_directory` 暴露整个 `_assets`）。

**Step 2: 实现路由（见 Task 9）后**

internal_api 在 search_wiki 响应里把 `images` 中的 `path` 转成 `url`：
```python
'images': [{
    'index': m['index'],
    'url': url_for('knowledge.serve_asset', article_id=art.id, rel=m['path']),
    'caption': m.get('caption', ''),
} for m in (art.image_manifest or [])]
```

**Step 3-5: Commit**

```bash
git commit -m "feat(wiki): search_wiki API returns asset URLs"
```

---

### Task 9: 鉴权过的 _assets 静态路由

**Files:**
- Modify: `app/views/knowledge.py`

**Step 1: 写测试 (含权限边界)**

```python
def test_asset_route_returns_image_for_owner(client, login_owner):
    rv = client.get(f'/knowledge/wiki/asset/{art.id}/_assets/x/img-1.png')
    assert rv.status_code == 200
    assert rv.mimetype == 'image/png'

def test_asset_route_403_for_other_user_when_personal_scope(client, login_other):
    rv = client.get(f'/knowledge/wiki/asset/{art.id}/_assets/x/img-1.png')
    assert rv.status_code == 403

def test_asset_route_blocks_path_traversal(client, login_owner):
    rv = client.get(f'/knowledge/wiki/asset/{art.id}/..%2F..%2Fetc%2Fpasswd')
    assert rv.status_code == 400
```

**Step 2: 实现**

```python
# app/views/knowledge.py
from flask import send_file, abort
from app.services.wiki.paths import get_wiki_dir

@bp.route('/wiki/asset/<int:article_id>/<path:rel>')
@login_required
def serve_asset(article_id, rel):
    art = KnowledgeWikiArticle.query.get_or_404(article_id)
    if not _user_can_view_article(current_user, art):
        abort(403)
    # 防穿越：只允许 _assets/<slug>/ 下的文件
    if '..' in rel or not rel.startswith(f'_assets/{art.slug}/'):
        abort(400)
    abs_path = (get_wiki_dir() / art.topic / rel).resolve()
    base = (get_wiki_dir() / art.topic).resolve()
    if not str(abs_path).startswith(str(base)):
        abort(400)
    if not abs_path.exists():
        abort(404)
    return send_file(abs_path)
```

`_user_can_view_article` 复用现有 wiki scope 权限（参考 `app/services/wiki/scope.py`）。

**Step 3-5: 测试 + Commit**

```bash
git commit -m "feat(wiki): authenticated route to serve _assets images"
```

---

## Phase 4 — 前端阅读 + 图片替换

### Task 10: tw_wiki.html 渲染内嵌图片

**Files:**
- Modify: `app/templates/knowledge/tw_wiki.html`

**Step 1: Markdown 渲染时改写图片 src**

前端用 marked / showdown 渲染 .md。在渲染前把相对路径 `_assets/<slug>/img-N.png` 改写为 `/knowledge/wiki/asset/<article_id>/_assets/<slug>/img-N.png`。

如已使用渲染钩子（renderer.image），直接重写即可：
```javascript
const renderer = new marked.Renderer();
renderer.image = (href, title, text) => {
  if (href.startsWith('_assets/')) {
    href = `/knowledge/wiki/asset/${currentArticleId}/${href}`;
  }
  return `<img src="${href}" alt="${text}" title="${title || ''}" class="my-3 rounded shadow-sm max-w-full"/>`;
};
```

**Step 2: 手工目测 7 篇文章在前端能正常显示图片**

**Step 3: Commit**

```bash
git commit -m "feat(wiki): render embedded images in tw_wiki article view"
```

---

### Task 11: 图片管理面板 (L1 替换)

**Files:**
- Modify: `app/templates/knowledge/tw_wiki.html`

**Step 1: 折叠面板 UI（仅文章 owner 或管理员可见）**

文章侧边栏增加 `<details>` 折叠区"图片管理"：列出 `image_manifest` 每张图的缩略图 + caption + "替换"按钮。点击替换 → 弹出文件选择 → 上传到 Task 12 的 API。

**Step 2: 替换成功后局部刷新 manifest（不刷整页）**

**Step 3: Commit**

```bash
git commit -m "feat(wiki): image management panel with replace button"
```

---

### Task 12: 替换图片 API endpoint

**Files:**
- Modify: `app/views/knowledge.py`
- Test: `tests/wiki/test_views_image_replace.py`

**Step 1: 写测试**

```python
def test_replace_image_overwrites_file_and_sets_manually_edited(client, login_owner, tmp_wiki):
    art = make_article_with_image(...)
    rv = client.post(
        f'/knowledge/wiki/{art.id}/image/1/replace',
        data={'image': (io.BytesIO(b'NEWPNG...'), 'new.png')},
        content_type='multipart/form-data',
    )
    assert rv.status_code == 200
    assert (tmp_wiki / 'wiki' / art.topic / '_assets' / art.slug / 'img-1.png').read_bytes().startswith(b'NEWPNG')
    db.session.refresh(art)
    assert art.manually_edited is True
    assert art.image_manifest[0]['manually_replaced'] is True
    history = list((tmp_wiki / 'wiki' / art.topic / '_assets' / art.slug / '.history').glob('img-1.png.*.bak'))
    assert len(history) == 1

def test_replace_image_rejects_non_image_file(client, login_owner): ...
def test_replace_image_403_for_non_owner(client, login_other): ...
def test_replace_image_404_for_missing_index(client, login_owner): ...
```

**Step 2: 实现**

```python
@bp.route('/wiki/<int:article_id>/image/<int:index>/replace', methods=['POST'])
@login_required
def replace_image(article_id, index):
    art = KnowledgeWikiArticle.query.get_or_404(article_id)
    if not _user_can_edit_article(current_user, art):
        abort(403)
    f = request.files.get('image')
    if not f or not f.mimetype.startswith('image/'):
        return jsonify({'success': False, 'message': '请上传图片文件'}), 400
    manifest = art.image_manifest or []
    entry = next((m for m in manifest if m['index'] == index), None)
    if not entry:
        abort(404)
    data = f.read()
    if len(data) > 10 * 1024 * 1024:  # 10MB cap
        return jsonify({'success': False, 'message': '图片过大'}), 400
    from app.services.wiki import storage
    new_rel = storage.replace_article_image(art.topic, art.slug, index, data, f.mimetype)
    entry['path'] = new_rel
    entry['manually_replaced'] = True
    entry['replaced_at'] = datetime.utcnow().isoformat()
    entry['sha256'] = storage.sha256_bytes(data)
    entry['size_bytes'] = len(data)
    art.image_manifest = manifest
    art.manually_edited = True
    db.session.commit()
    return jsonify({'success': True, 'image': entry})
```

**Step 3-5: 测试通过 + Commit**

```bash
git commit -m "feat(wiki): API endpoint to replace article image with backup"
```

---

## Phase 5 — 防覆盖 + 回填

### Task 13: 编译器尊重 manually_edited 标记

**Files:**
- Modify: `app/services/wiki/compiler.py` (_apply_operations 中 update 分支)

**Step 1: 测试**

```python
def test_ingest_skips_update_for_manually_edited_articles(...):
    art = make_article(manually_edited=True)
    res = ingest_raw_file(raw.id, claude=mock_claude_returning_update_op_for_same_slug)
    assert any(op['skipped_reason'] == 'manually_edited' for op in res['operations'])
    db.session.refresh(art)
    assert art.content == old_content  # 未被覆盖
```

**Step 2: 实现**

```python
# compiler.py — _apply_operations 中处理 update 时
existing = KnowledgeWikiArticle.query.filter_by(topic=topic, slug=slug).first()
if existing and existing.manually_edited and not force:
    op['skipped_reason'] = 'manually_edited'
    op['action'] = 'noop'
    continue
```

`ingest_raw_file` 增加 `force: bool = False` 参数，默认 False；前端"重新编译"按钮可选 force=True 并提示用户。

**Step 3-5: Commit**

```bash
git commit -m "feat(wiki): compiler skips manually_edited articles unless force=True"
```

---

### Task 14: 一次性回填脚本：重新 ingest 7 篇旧文章

**Files:**
- Create: `scripts/temp/backfill_wiki_with_images.py`

**Step 1: 实现**

```python
#!/usr/bin/env python3
"""把 storage/knowledge_base/raw/ 下所有文件全量重新 ingest，
让旧 wiki 文章带上嵌入图。

执行前会备份 wiki/ 整目录到 wiki_backup_<timestamp>/。
"""
import sys, os, shutil
from datetime import datetime
# ... 标准路径修正 ...

from app import create_app, db
from app.models.knowledge import KnowledgeRawFile, KnowledgeWikiArticle
from app.services.wiki.compiler import ingest_raw_file
from app.services.wiki.paths import get_wiki_dir

def main():
    app = create_app()
    with app.app_context():
        # 1. 备份 wiki/
        ts = datetime.now().strftime('%Y%m%d-%H%M%S')
        backup = get_wiki_dir().parent / f'wiki_backup_{ts}'
        shutil.copytree(get_wiki_dir(), backup)
        print(f'✓ wiki/ 已备份到 {backup}')

        # 2. 删除现有 wiki articles + .md (保留 index.md/log.md)
        confirm = input('确认清空 knowledge_wiki_articles 表 + 删除 wiki/<topic>/*.md ? [y/N] ')
        if confirm.lower() != 'y':
            return
        KnowledgeWikiArticle.query.delete()
        db.session.commit()
        for topic_dir in get_wiki_dir().iterdir():
            if topic_dir.is_dir() and not topic_dir.name.startswith('_'):
                for md in topic_dir.glob('*.md'):
                    md.unlink()
                # _assets 目录保留 → 实际是空的

        # 3. 逐个 raw 重新 ingest
        raws = KnowledgeRawFile.query.order_by(KnowledgeRawFile.id).all()
        print(f'共 {len(raws)} 个 raw 文件待编译')
        for raw in raws:
            print(f'\n--- ingesting raw_id={raw.id} {raw.title} ---')
            try:
                raw.ingest_status = 'pending'
                db.session.commit()
                result = ingest_raw_file(raw.id)
                print(f'  ✓ {len(result["operations"])} 个 operations')
            except Exception as e:
                print(f'  ✗ 失败: {e}')

if __name__ == '__main__':
    main()
```

**Step 2: 试跑（先用 1-2 个 raw 试水）**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  python3 scripts/temp/backfill_wiki_with_images.py
```

**Step 3: 验收 7 篇文章**

逐篇打开 `tw_wiki.html` 阅读，检查：
- [ ] 图片是否正确显示
- [ ] 图片是否插在合适的段落附近（不全堆在文末）
- [ ] caption 是否信息密度合理（非"图1""示意图"）
- [ ] image_manifest 字段是否非空
- [ ] manually_edited 应当为 False

**Step 4: 不通过则回滚 + 调 prompt**

如果任何一篇质量不达标 → 删 wiki/ 中该篇 .md → 调整 prompt 中"图片处理规则"措辞 → 重跑该篇。

**Step 5: Commit (脚本可保留在 scripts/temp/，1 个月后清理)**

```bash
git add scripts/temp/backfill_wiki_with_images.py
git commit -m "chore(wiki): one-shot script to backfill articles with embedded images"
```

---

### Task 15: 端到端验收

**Step 1: search_wiki MCP 调用确认带图**

用 GEO writer 或直接调 `/internal_api/wiki/search` 提问一个能命中带图文章的问题，确认响应 JSON 中 `cited_articles[].images` 非空且 url 可访问。

**Step 2: 手工替换一张图，验证全链路**

1. 在文章详情页选一张图点"替换"，上传新图
2. 刷新页面：图变了
3. 检查 `_assets/<slug>/.history/` 里有 `img-N.png.*.bak`
4. 检查 DB `manually_edited=True`、`image_manifest[].manually_replaced=True`
5. 模拟管理员重跑该 raw 的 ingest（不带 force）：返回 `skipped_reason='manually_edited'`，图未被覆盖

**Step 3: 列一份验收清单贴在 PR 描述中**

**Step 4: Commit/PR**

```bash
git push origin <branch>
gh pr create --title "Wiki: 知识库图片内嵌 + 替换能力" ...
```

---

## 风险与回滚

| 风险 | 应对 |
|------|------|
| Claude 不按规则插 `AUTO_IMG:N` 占位符 | prompt 多轮 few-shot 调教；Task 14 试跑 1-2 篇先看效果 |
| .docx XML 解析在边缘格式上崩溃 | 抽图失败时降级（捕获异常，按"无图"继续编译） |
| 图片体积过大撑爆 prompt | 不在 prompt 里塞图本体，只塞元信息（顺序+段落+类型） |
| 旧 .md 重新生成后正文质量倒退 | Task 14 先全量备份 wiki/，验收不过可整目录还原 |
| 路径穿越攻击（恶意上传文件名） | Task 9 严格校验 `_assets/<slug>/` 前缀 + resolve 后检查在 base 之内 |
| 替换图体积过大占满磁盘 | 上传 10MB cap + .history 定期清理（可后续做） |

---

## 完成定义 (Definition of Done)

- [ ] 7 篇旧文章全部带上至少 1 张内嵌图（其中 docx 含图的文章 100% 命中）
- [ ] search_wiki 响应中 `cited_articles[].images` 字段已上线，GEO writer 能消费
- [ ] 文章详情页能显示图、能替换图、替换后旧版本可在 .history 找回
- [ ] 替换过的文章再次 ingest 时**不会**被覆盖（除非 force）
- [ ] 单元测试 + 集成测试覆盖：抽图、保存、替换、权限、防穿越、防覆盖
