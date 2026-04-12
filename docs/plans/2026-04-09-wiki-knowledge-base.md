# PMA Wiki 知识库实施方案（基于 Karpathy LLM Wiki 方法）

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 用 Karpathy 的 LLM Wiki 模式重构 PMA 知识库——放弃向量检索（RAG），改为 Claude 主动把原始文件编译为结构化 Markdown Wiki，供团队浏览和问答。

**Architecture:** 原始文件存于 `storage/knowledge_base/raw/<topic>/`，Claude Opus 4.6 读取后生成/更新 `storage/knowledge_base/wiki/<topic>/*.md` 下的文章，并维护 `wiki/index.md` 和 `wiki/log.md`。数据库只存元数据，文章内容存磁盘 Markdown 文件。前端独立页面 `/knowledge/wiki` 提供目录浏览、文章渲染和基于 Wiki 上下文的问答。

**Tech Stack:** Flask + SQLAlchemy + PostgreSQL（元数据 + 全文检索，不用 pgvector）+ Anthropic Python SDK + Claude Opus 4.6 1M 上下文 + Tailwind + Alpine.js + marked.js

**参考资料:**
- [Karpathy 原始 gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- [lucasastorian/llmwiki](https://github.com/lucasastorian/llmwiki) 开源实现
- [Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki) Skill 式实现

---

## 0. 背景与设计决策

### 0.1 为什么放弃现有 RAG 系统

PMA 当前知识库（`app/models/knowledge.py` + `app/services/knowledge_ai_service.py`）采用"切块 → 向量嵌入（智谱）→ 向量检索 → DeepSeek 回答"的 RAG 方案。问题：

1. **碎片化回答**：LLM 看到的是 chunk 片段，无法合成跨文档的理解
2. **交叉引用丢失**：产品 A 与 产品 B 的对比关系无法被向量检索捕捉
3. **黑盒**：用户无法浏览知识库到底有什么
4. **过度工程**：PMA 文档量小（<500 个），不需要向量检索的规模优势

**且目前知识库没有生产数据**，迁移成本接近零。

### 0.2 Karpathy 方法核心

| 组件 | 作用 |
|------|------|
| `raw/` | 不可变的原始文件，按 topic 分目录 |
| `wiki/` | LLM 维护的 Markdown 文章 |
| `wiki/index.md` | 全局目录（文章列表 + 摘要 + 更新日期） |
| `wiki/log.md` | 追加式操作日志 |

四个核心操作：
1. **Ingest** — 读原始文件 → 决定合并到已有文章 / 新建 → **级联更新**相关文章 → 刷新 index + log
2. **Query** — 读 index → 定位文章 → 基于文章回答（带引用）
3. **Lint** — 检查坏链接、孤岛文章、事实冲突、过期内容
4. **Initialize** — 首次建目录和索引

### 0.3 模型选型

| 操作 | 模型 | 原因 |
|------|------|------|
| Ingest | `claude-opus-4-6[1m]` | 质量决定整个 Wiki 基础，必须用最强模型 + 1M 上下文 |
| Query | `claude-opus-4-6[1m]` | Wiki 问答质量优先，团队规模小成本可控 |
| Lint | `claude-opus-4-6[1m]` | 跨文章推理，频次低 |
| 元数据（slug/title） | `claude-haiku-4-5-20251001` | 简单结构化任务 |

**独立于 CLI Agent**：CLI Agent 已配置 Sonnet 做数据库查询，Wiki 模块在自己的服务里硬编码 Opus，互不干扰。

### 0.4 权限模型

| 角色 | 权限 |
|------|------|
| admin / ceo | Ingest、Lint、Query、浏览 |
| 其他登录用户 | Query、浏览 |

### 0.5 磁盘目录约定

```
<PMA_ROOT>/storage/knowledge_base/
├── raw/
│   ├── product/
│   │   └── 2026-04-09-gp328p-datasheet.pdf
│   └── competitor/
│       └── 2026-04-09-hytera-brochure.pdf
└── wiki/
    ├── index.md
    ├── log.md
    ├── product/
    │   ├── gp328p-overview.md
    │   └── gp328p-applications.md
    └── competitor/
        └── hytera-vs-evertac.md
```

可通过环境变量 `WIKI_ROOT` 覆盖默认路径，便于 NAS 部署。

---

## Phase 1: 清理旧 RAG 系统

### Task 1.1: 数据库迁移 —— 删除旧 RAG 表

**Files:**
- Create: `migrations/versions/<timestamp>_drop_knowledge_chunks.py`

**操作：**
- 删除表：`knowledge_chunks`
- 删除列（如有）：`knowledge_documents.embedding`
- 保留：`knowledge_tags`、`knowledge_documents`、`knowledge_document_tags`（下一阶段改造）

**Migration 代码骨架：**

```python
"""drop legacy knowledge chunks

Revision ID: <auto>
Revises: <previous_head>
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 删除向量索引（如果存在）
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding")
    # 删除分块表
    op.drop_table('knowledge_chunks')

def downgrade():
    # 不提供回滚，向量数据已失效
    raise NotImplementedError("向量数据已废弃，不支持回滚")
```

**验证：**
```bash
flask db upgrade
psql -d pma -c "\d knowledge_chunks"  # 应返回 "Did not find any relation"
```

---

### Task 1.2: 删除 Embedding 相关代码

**Files:**
- Delete: `app/services/knowledge_ai_service.py` 中 `generate_embeddings()` 和 `_get_embedding_client()`
- Modify: `app/models/knowledge.py` — 删除 `KnowledgeChunk` 类和 `chunks` relationship
- Modify: `requirements.txt` — 移除 `pgvector`（如果没有其他地方用）

**验证：**
```bash
grep -r "generate_embeddings\|KnowledgeChunk\|pgvector" app/ --include="*.py"
# 应返回空
python -c "from app.models.knowledge import KnowledgeTag; print('ok')"
```

---

### Task 1.3: 提交清理阶段

```bash
git add -A
git commit -m "refactor(knowledge): 下线向量 RAG 系统准备迁移到 Wiki 模式"
```

---

## Phase 2: 新数据模型

### Task 2.1: 创建 KnowledgeRawFile 模型

**Files:**
- Modify: `app/models/knowledge.py`

**新增：**

```python
class KnowledgeRawFile(db.Model):
    """知识库原始文件登记表 —— 指向 file_library 的文件 + Wiki 元数据"""
    __tablename__ = 'knowledge_raw_files'

    id = Column(Integer, primary_key=True)
    file_library_id = Column(Integer, ForeignKey('file_library.id'), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)  # 如 "product" / "competitor"
    raw_path = Column(String(500), nullable=False)           # raw/product/2026-04-09-xxx.pdf
    title = Column(String(500), nullable=False)              # 用户看到的标题
    ingest_status = Column(String(20), default='pending', nullable=False, index=True)
    # ingest_status: pending / processing / ingested / error
    ingest_error = Column(Text, nullable=True)
    ingested_at = Column(DateTime, nullable=True)
    added_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=get_local_time)

    file_library = relationship('FileLibrary')
    adder = relationship('User', foreign_keys=[added_by])

    __table_args__ = (
        Index('ix_knowledge_raw_topic_status', 'topic', 'ingest_status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'file_library_id': self.file_library_id,
            'topic': self.topic,
            'raw_path': self.raw_path,
            'title': self.title,
            'ingest_status': self.ingest_status,
            'ingest_error': self.ingest_error,
            'ingested_at': self.ingested_at.isoformat() if self.ingested_at else None,
            'added_by': self.added_by,
            'adder_name': (self.adder.real_name or self.adder.username) if self.adder else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'file_name': self.file_library.original_filename if self.file_library else None,
        }
```

---

### Task 2.2: 创建 KnowledgeWikiArticle 模型

**Files:**
- Modify: `app/models/knowledge.py`

**新增：**

```python
class KnowledgeWikiArticle(db.Model):
    """Wiki 文章元数据 —— 内容存磁盘 Markdown 文件"""
    __tablename__ = 'knowledge_wiki_articles'

    id = Column(Integer, primary_key=True)
    topic = Column(String(100), nullable=False, index=True)      # "product"
    slug = Column(String(200), nullable=False)                    # "gp328p-overview"
    title = Column(String(500), nullable=False)                   # "GP328P 产品概述"
    file_path = Column(String(500), nullable=False, unique=True)  # wiki/product/gp328p-overview.md
    summary = Column(Text, nullable=True)                         # 用于 index.md 和全文检索
    content_length = Column(Integer, default=0)                   # 字符数，展示用

    # 来源追踪：哪些 raw 文件参与了这篇文章
    source_raw_ids = Column(JSON, nullable=True)  # [1, 5, 12]

    # 引用关系：本文指向的其他文章（相对 slug）
    outbound_refs = Column(JSON, nullable=True)   # ["product/gp538-overview"]

    # 标签（可选，未来用）
    # tags = relationship(...)

    last_compiled_at = Column(DateTime, nullable=True)
    compile_model = Column(String(100), nullable=True)           # 记录用了哪个模型，方便审计
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)

    __table_args__ = (
        Index('ix_wiki_article_topic_slug', 'topic', 'slug', unique=True),
        # 全文检索索引（迁移里手写 SQL 建立）
    )

    def to_dict(self, include_content=False):
        d = {
            'id': self.id,
            'topic': self.topic,
            'slug': self.slug,
            'title': self.title,
            'file_path': self.file_path,
            'summary': self.summary,
            'content_length': self.content_length,
            'source_raw_ids': self.source_raw_ids or [],
            'outbound_refs': self.outbound_refs or [],
            'last_compiled_at': self.last_compiled_at.isoformat() if self.last_compiled_at else None,
            'compile_model': self.compile_model,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_content:
            from app.services.wiki.storage import read_article_content
            d['content'] = read_article_content(self.file_path)
        return d
```

---

### Task 2.3: Alembic 迁移 + PG 全文检索索引

**Files:**
- Create: `migrations/versions/<timestamp>_create_wiki_tables.py`

**内容：**

```python
def upgrade():
    op.create_table(
        'knowledge_raw_files',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('file_library_id', sa.Integer(), sa.ForeignKey('file_library.id'), nullable=False),
        sa.Column('topic', sa.String(100), nullable=False),
        sa.Column('raw_path', sa.String(500), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('ingest_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('ingest_error', sa.Text()),
        sa.Column('ingested_at', sa.DateTime()),
        sa.Column('added_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime()),
    )
    op.create_index('ix_knowledge_raw_topic_status', 'knowledge_raw_files', ['topic', 'ingest_status'])
    op.create_index('ix_knowledge_raw_file_library_id', 'knowledge_raw_files', ['file_library_id'])

    op.create_table(
        'knowledge_wiki_articles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('topic', sa.String(100), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False, unique=True),
        sa.Column('summary', sa.Text()),
        sa.Column('content_length', sa.Integer(), server_default='0'),
        sa.Column('source_raw_ids', sa.JSON()),
        sa.Column('outbound_refs', sa.JSON()),
        sa.Column('last_compiled_at', sa.DateTime()),
        sa.Column('compile_model', sa.String(100)),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_index('ix_wiki_article_topic_slug', 'knowledge_wiki_articles', ['topic', 'slug'], unique=True)

    # PG 全文检索索引 —— title + summary 的 GIN 索引
    op.execute("""
        CREATE INDEX ix_wiki_article_fts ON knowledge_wiki_articles
        USING GIN (to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary, '')))
    """)

def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_wiki_article_fts")
    op.drop_table('knowledge_wiki_articles')
    op.drop_table('knowledge_raw_files')
```

**验证：**
```bash
flask db upgrade
psql -d pma -c "\d knowledge_wiki_articles"
psql -d pma -c "\d knowledge_raw_files"
```

**提交：**
```bash
git add -A
git commit -m "feat(knowledge): 新增 Wiki 知识库数据模型 + PG 全文检索索引"
```

---

## Phase 3: 存储层（文件 I/O）

### Task 3.1: 路径常量与解析

**Files:**
- Create: `app/services/wiki/__init__.py`
- Create: `app/services/wiki/paths.py`

**内容：**

```python
# app/services/wiki/paths.py
"""Wiki 磁盘路径管理"""
import os
from pathlib import Path
from flask import current_app


def get_wiki_root() -> Path:
    """返回 knowledge_base 根目录。可用 WIKI_ROOT 环境变量覆盖。"""
    env = os.environ.get('WIKI_ROOT', '').strip()
    if env:
        return Path(env)
    basedir = current_app.config.get('BASE_DIR') or os.path.dirname(current_app.root_path)
    return Path(basedir) / 'storage' / 'knowledge_base'


def get_raw_dir() -> Path:
    return get_wiki_root() / 'raw'


def get_wiki_dir() -> Path:
    return get_wiki_root() / 'wiki'


def get_index_path() -> Path:
    return get_wiki_dir() / 'index.md'


def get_log_path() -> Path:
    return get_wiki_dir() / 'log.md'


def raw_file_path(topic: str, filename: str) -> Path:
    return get_raw_dir() / topic / filename


def wiki_article_path(topic: str, slug: str) -> Path:
    return get_wiki_dir() / topic / f'{slug}.md'


def ensure_wiki_structure():
    """首次初始化目录结构"""
    get_raw_dir().mkdir(parents=True, exist_ok=True)
    get_wiki_dir().mkdir(parents=True, exist_ok=True)
    idx = get_index_path()
    if not idx.exists():
        idx.write_text('# PMA Wiki 知识库索引\n\n（尚未建立文章）\n', encoding='utf-8')
    log = get_log_path()
    if not log.exists():
        log.write_text('# 操作日志\n\n', encoding='utf-8')
```

---

### Task 3.2: 文件读写 helper

**Files:**
- Create: `app/services/wiki/storage.py`

**内容：**

```python
# app/services/wiki/storage.py
"""Wiki 文章、raw 文件、index/log 的 I/O"""
from datetime import datetime
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

from app.services.wiki.paths import (
    get_index_path,
    get_log_path,
    get_raw_dir,
    get_wiki_dir,
    raw_file_path,
    wiki_article_path,
)


# ── 文章读写 ──────────────────────────────────────────────

def read_article_content(file_path: str) -> str:
    """按相对路径读文章。file_path 是 'wiki/product/xxx.md' 格式。"""
    from app.services.wiki.paths import get_wiki_root
    abs_path = get_wiki_root() / file_path
    if not abs_path.exists():
        return ''
    return abs_path.read_text(encoding='utf-8')


def write_article(topic: str, slug: str, content: str) -> str:
    """写文章。返回相对路径（相对 wiki_root）。"""
    path = wiki_article_path(topic, slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    from app.services.wiki.paths import get_wiki_root
    return str(path.relative_to(get_wiki_root()))


def delete_article(topic: str, slug: str):
    path = wiki_article_path(topic, slug)
    if path.exists():
        path.unlink()


def list_topics() -> list[str]:
    wiki_dir = get_wiki_dir()
    if not wiki_dir.exists():
        return []
    return sorted([p.name for p in wiki_dir.iterdir() if p.is_dir()])


def list_articles_in_topic(topic: str) -> list[str]:
    topic_dir = get_wiki_dir() / topic
    if not topic_dir.exists():
        return []
    return sorted([p.stem for p in topic_dir.glob('*.md')])


# ── index.md 与 log.md ──────────────────────────────────

def read_index() -> str:
    idx = get_index_path()
    return idx.read_text(encoding='utf-8') if idx.exists() else ''


def write_index(content: str):
    get_index_path().write_text(content, encoding='utf-8')


def append_log(operation: str, details: str):
    """追加操作日志"""
    now = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    line = f'\n## {now} — {operation}\n\n{details}\n'
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('a', encoding='utf-8') as f:
        f.write(line)


# ── 原始文件 ──────────────────────────────────────────────

def save_raw_file(topic: str, filename: str, data: bytes) -> str:
    """把文件写入 raw/<topic>/<filename>，返回相对路径。"""
    path = raw_file_path(topic, filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    from app.services.wiki.paths import get_wiki_root
    return str(path.relative_to(get_wiki_root()))


def read_raw_file_text(raw_path: str) -> str:
    """读原始文件并提取文本。支持 PDF/DOCX/MD/TXT。"""
    from app.services.wiki.paths import get_wiki_root
    abs_path = get_wiki_root() / raw_path
    ext = abs_path.suffix.lower()
    if ext in ('.md', '.txt'):
        return abs_path.read_text(encoding='utf-8', errors='replace')
    if ext == '.pdf':
        from pypdf import PdfReader
        reader = PdfReader(str(abs_path))
        return '\n\n'.join(page.extract_text() or '' for page in reader.pages)
    if ext == '.docx':
        from docx import Document
        doc = Document(str(abs_path))
        return '\n\n'.join(p.text for p in doc.paragraphs)
    raise ValueError(f'不支持的文件类型: {ext}')
```

**依赖：**
- `pypdf`（已在 requirements）
- `python-docx`（可能需要新增）

**验证：** 手动测试
```python
from app.services.wiki.storage import save_raw_file, read_raw_file_text
save_raw_file('test', 'hello.md', b'# Hello\n\nWorld')
print(read_raw_file_text('raw/test/hello.md'))
```

---

### Task 3.3: 单元测试

**Files:**
- Create: `tests/wiki/test_storage.py`

**测试点：**
- `ensure_wiki_structure()` 在空目录下能建齐 raw/wiki/index.md/log.md
- `write_article()` + `read_article_content()` 往返一致
- `append_log()` 多次调用后累加
- `read_raw_file_text()` 对 md、pdf、docx 都能返回非空文本

**验证：**
```bash
pytest tests/wiki/test_storage.py -v
```

**提交：**
```bash
git add -A
git commit -m "feat(wiki): 实现 Wiki 存储层（路径管理 + 文件 I/O）"
```

---

## Phase 4: Claude 客户端与 Prompts

### Task 4.1: Wiki 专用 Claude 客户端

**Files:**
- Create: `app/services/wiki/claude_client.py`

**设计要点：**
- 不复用 `cli_agent/llm_client.py`（那个是流式 + 工具调用）
- Wiki 需要非流式、批量、简单的 text-in/text-out
- 硬编码 Opus 4.6 1M 模型

**内容：**

```python
# app/services/wiki/claude_client.py
"""Wiki 模块的 Claude 客户端（非流式，批量编译用）"""
import logging
import os

logger = logging.getLogger(__name__)


INGEST_MODEL = os.environ.get('WIKI_INGEST_MODEL', 'claude-opus-4-6[1m]')
QUERY_MODEL = os.environ.get('WIKI_QUERY_MODEL', 'claude-opus-4-6[1m]')
LINT_MODEL = os.environ.get('WIKI_LINT_MODEL', 'claude-opus-4-6[1m]')
META_MODEL = os.environ.get('WIKI_META_MODEL', 'claude-haiku-4-5-20251001')


class WikiClaudeClient:
    """封装 Anthropic SDK，用于 Wiki 编译/查询/质检"""

    def __init__(self, api_key: str | None = None):
        from anthropic import Anthropic
        key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not key:
            raise RuntimeError('未配置 ANTHROPIC_API_KEY')
        self.client = Anthropic(api_key=key)

    def complete(
        self,
        system: str,
        user: str,
        model: str,
        max_tokens: int = 16000,
        temperature: float = 0.2,
    ) -> tuple[str, dict]:
        """发起一次非流式请求，返回 (text, usage_dict)"""
        try:
            resp = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{'role': 'user', 'content': user}],
            )
            text = ''.join(
                block.text for block in resp.content if getattr(block, 'type', None) == 'text'
            )
            usage = {
                'input_tokens': resp.usage.input_tokens,
                'output_tokens': resp.usage.output_tokens,
                'model': model,
            }
            return text, usage
        except Exception as e:
            logger.exception('Wiki Claude 调用失败')
            raise
```

---

### Task 4.2: Ingest / Query / Lint 系统 Prompts

**Files:**
- Create: `app/services/wiki/prompts.py`

**内容：** 把所有系统 prompt 集中在一处，便于调试。

```python
# app/services/wiki/prompts.py
"""Wiki 各操作的 system prompts"""

INGEST_SYSTEM = """你是 PMA 知识库的 Wiki 编译器。你的任务是把一份新的原始资料整合到现有的 Markdown Wiki 中。

# 工作原则

1. **合并优先于新建**：如果新资料的主题与某篇已有文章高度重合，把新信息合并进去；只有主题确实全新时才创建新文章。
2. **级联更新**：新信息可能影响多篇相关文章，你需要同时更新所有受影响的文章。
3. **交叉引用**：在文章末尾用 "## See Also" 章节列出相关文章的链接，格式 `- [标题](../topic/slug.md)`。
4. **标注冲突**：如果新资料与现有内容矛盾，在文章里用 "> ⚠️ 冲突：..." 块标注双方说法和来源。
5. **不要输出"我修改了什么"之类的过程说明**，只输出最终文章内容。

# 输出格式

严格按以下 JSON 输出（不要包在代码块里，直接就是 JSON）：

```
{
  "operations": [
    {
      "action": "create" | "update" | "noop",
      "topic": "product",
      "slug": "gp328p-overview",
      "title": "GP328P 产品概述",
      "content": "# GP328P 产品概述\\n\\n...（完整的 Markdown 内容）",
      "summary": "GP328P 的核心规格、适用场景和价格定位",
      "source_raw_ids": [1, 5],
      "outbound_refs": ["product/gp538-overview", "competitor/hytera-vs-evertac"],
      "rationale": "合并了新的 IP67 认证信息到 '核心规格' 章节"
    }
  ],
  "index_update": "# PMA Wiki 知识库索引\\n\\n## product\\n- [GP328P 产品概述](product/gp328p-overview.md) - GP328P 的核心规格...\\n",
  "log_entry": "ingest gp328p-datasheet.pdf：更新了 product/gp328p-overview（新增 IP67 规格），级联更新 competitor/hytera-vs-evertac（对比表加一行）"
}
```

# 输入上下文

用户消息将按顺序提供：
1. 本次要吸收的原始资料文本
2. 当前 index.md 内容
3. 可能受影响的相关文章（全文）
4. 原始资料的元数据（topic、raw_id、filename）
"""

QUERY_SYSTEM = """你是 PMA 知识库的问答助手。你只能基于提供的 Wiki 文章内容回答问题。

# 规则

1. **只依据 Wiki**：不要编造 Wiki 中没有的信息。如果 Wiki 里没有答案，明确说"Wiki 中暂无相关记录"。
2. **带引用**：每个关键事实后面用 `[文章标题](topic/slug.md)` 标注来源。
3. **简洁**：优先直接回答，再补充细节。
4. **中文优先**。

# 输入

用户消息将包含：
1. 当前 index.md（帮你快速定位）
2. 若干相关文章的全文
3. 用户问题
"""

LINT_SYSTEM = """你是 PMA 知识库的质检员。检查整个 Wiki 并报告问题。

# 检查项

1. **坏链接**：outbound_refs 指向的文章不存在
2. **孤岛文章**：没有任何文章引用它
3. **事实冲突**：两篇文章对同一事实说法不一致
4. **过期内容**：标题或内容明显过时（如提到已停产的产品型号）
5. **缺摘要**：summary 为空

# 输出格式

```
{
  "issues": [
    {
      "severity": "error" | "warning" | "info",
      "type": "broken_link" | "orphan" | "conflict" | "outdated" | "missing_summary",
      "article": "product/gp328p-overview",
      "message": "指向 product/gp999 的链接不存在",
      "auto_fixable": true
    }
  ],
  "auto_fixes": [
    {
      "article": "product/gp328p-overview",
      "new_content": "（修复后的完整 Markdown）"
    }
  ],
  "summary": "检查完成，发现 3 个 error / 5 个 warning，2 个可自动修复"
}
```
"""
```

**提交：**
```bash
git add -A
git commit -m "feat(wiki): Claude 客户端 + Ingest/Query/Lint prompts"
```

---

## Phase 5: Ingest 编译服务

### Task 5.1: 编译主流程

**Files:**
- Create: `app/services/wiki/compiler.py`

**流程：**

```
1. 读取 raw 文件文本
2. 读取当前 index.md
3. 用 META_MODEL 做轻量分析，初步判断可能涉及哪些已有文章
4. 读取这些相关文章的全文
5. 组装 INGEST prompt，调用 INGEST_MODEL
6. 解析返回 JSON，执行 operations：
   - create：写新文件 + 插入 KnowledgeWikiArticle 记录
   - update：覆盖写文件 + 更新记录（last_compiled_at 等）
   - noop：仅日志
7. 覆盖写 index.md
8. 追加 log.md
9. 更新 KnowledgeRawFile.ingest_status = 'ingested'
```

**代码骨架：**

```python
# app/services/wiki/compiler.py
import json
import logging
from datetime import datetime

from app import db
from app.models.knowledge import KnowledgeRawFile, KnowledgeWikiArticle
from app.services.wiki import claude_client, prompts, storage
from app.services.wiki.paths import ensure_wiki_structure

logger = logging.getLogger(__name__)


class IngestError(RuntimeError):
    pass


def ingest_raw_file(raw_file_id: int) -> dict:
    """把一个原始文件编译入 Wiki。返回操作摘要。"""
    ensure_wiki_structure()

    raw = KnowledgeRawFile.query.get(raw_file_id)
    if not raw:
        raise IngestError(f'raw_file_id={raw_file_id} 不存在')

    raw.ingest_status = 'processing'
    db.session.commit()

    try:
        # 1. 读原始文本
        raw_text = storage.read_raw_file_text(raw.raw_path)
        if not raw_text.strip():
            raise IngestError('原始文件为空或无法提取文本')

        # 2. 当前 index
        index_md = storage.read_index()

        # 3. 粗筛相关文章 —— 第一版简单做：按 topic 取全部文章
        related_articles = KnowledgeWikiArticle.query.filter_by(topic=raw.topic).all()

        # 4. 组装相关文章全文
        related_context = []
        for art in related_articles:
            content = storage.read_article_content(art.file_path)
            related_context.append({
                'topic': art.topic,
                'slug': art.slug,
                'title': art.title,
                'content': content,
            })

        # 5. 组装 user prompt
        user_msg = _build_ingest_user_prompt(
            raw_text=raw_text,
            raw_meta={'raw_id': raw.id, 'topic': raw.topic, 'filename': raw.title},
            index_md=index_md,
            related_articles=related_context,
        )

        client = claude_client.WikiClaudeClient()
        response_text, usage = client.complete(
            system=prompts.INGEST_SYSTEM,
            user=user_msg,
            model=claude_client.INGEST_MODEL,
            max_tokens=32000,
        )

        # 6. 解析 + 执行
        result = _parse_ingest_response(response_text)
        _apply_operations(result['operations'], raw_id=raw.id)

        # 7. 写 index + log
        storage.write_index(result['index_update'])
        storage.append_log('ingest', f"{raw.title} | {result.get('log_entry', '')}")

        # 8. 更新 raw 状态
        raw.ingest_status = 'ingested'
        raw.ingested_at = datetime.utcnow()
        raw.ingest_error = None
        db.session.commit()

        return {
            'raw_id': raw.id,
            'operations': result['operations'],
            'usage': usage,
        }

    except Exception as e:
        db.session.rollback()
        raw.ingest_status = 'error'
        raw.ingest_error = str(e)[:2000]
        db.session.commit()
        raise


def _build_ingest_user_prompt(raw_text, raw_meta, index_md, related_articles) -> str:
    parts = [
        '## 原始资料元数据',
        json.dumps(raw_meta, ensure_ascii=False, indent=2),
        '',
        '## 原始资料正文',
        raw_text[:200000],  # 安全截断
        '',
        '## 当前 index.md',
        index_md,
        '',
        '## 相关已有文章',
    ]
    for art in related_articles:
        parts.append(f"\n### {art['topic']}/{art['slug']}.md — {art['title']}\n")
        parts.append(art['content'])
    return '\n'.join(parts)


def _parse_ingest_response(text: str) -> dict:
    text = text.strip()
    if text.startswith('```'):
        text = text.strip('`').split('\n', 1)[1] if '\n' in text else text
        if text.endswith('```'):
            text = text.rsplit('```', 1)[0]
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise IngestError(f'Claude 返回非法 JSON: {e}\n原文:\n{text[:2000]}')


def _apply_operations(operations: list, raw_id: int):
    for op in operations:
        action = op.get('action')
        topic = op['topic']
        slug = op['slug']
        if action == 'create':
            file_path = storage.write_article(topic, slug, op['content'])
            art = KnowledgeWikiArticle(
                topic=topic,
                slug=slug,
                title=op['title'],
                file_path=file_path,
                summary=op.get('summary'),
                content_length=len(op['content']),
                source_raw_ids=op.get('source_raw_ids', [raw_id]),
                outbound_refs=op.get('outbound_refs', []),
                last_compiled_at=datetime.utcnow(),
                compile_model=claude_client.INGEST_MODEL,
            )
            db.session.add(art)
        elif action == 'update':
            art = KnowledgeWikiArticle.query.filter_by(topic=topic, slug=slug).first()
            if not art:
                # 退化为 create
                file_path = storage.write_article(topic, slug, op['content'])
                art = KnowledgeWikiArticle(
                    topic=topic, slug=slug, title=op['title'],
                    file_path=file_path,
                )
                db.session.add(art)
            else:
                storage.write_article(topic, slug, op['content'])
                art.title = op['title']
                if op.get('summary'):
                    art.summary = op['summary']
                art.content_length = len(op['content'])
                # 合并 source_raw_ids
                existing = set(art.source_raw_ids or [])
                existing.update(op.get('source_raw_ids', [raw_id]))
                art.source_raw_ids = sorted(existing)
                art.outbound_refs = op.get('outbound_refs', art.outbound_refs)
                art.last_compiled_at = datetime.utcnow()
                art.compile_model = claude_client.INGEST_MODEL
        # noop 不处理
    db.session.commit()
```

---

### Task 5.2: 集成测试（一个端到端流程）

**Files:**
- Create: `tests/wiki/test_ingest_e2e.py`

**测试：** 用一个 fixture Markdown 文件走完整流程，mock Claude 返回预定义 JSON，断言：
- `KnowledgeWikiArticle` 记录被创建
- 文件写入磁盘正确位置
- `index.md` 被更新
- `log.md` 被追加
- `KnowledgeRawFile.ingest_status == 'ingested'`

**验证：**
```bash
pytest tests/wiki/test_ingest_e2e.py -v
```

**提交：**
```bash
git add -A
git commit -m "feat(wiki): Ingest 编译主流程 + 端到端测试"
```

---

## Phase 6: Query 问答服务

### Task 6.1: 问答主流程

**Files:**
- Create: `app/services/wiki/querier.py`

**流程：**

```
1. 读 index.md
2. 先用 PG 全文检索匹配最相关的 3-5 篇文章（title + summary 上的 GIN 索引）
3. 读这些文章的全文
4. 组装 QUERY prompt
5. 调用 QUERY_MODEL，非流式返回答案
6. 返回 {answer, cited_articles, usage}
```

**内容：**

```python
# app/services/wiki/querier.py
from sqlalchemy import text
from app import db
from app.models.knowledge import KnowledgeWikiArticle
from app.services.wiki import claude_client, prompts, storage


def query_wiki(question: str, top_k: int = 5) -> dict:
    index_md = storage.read_index()

    # PG 全文检索
    sql = text("""
        SELECT id, topic, slug, title, summary, file_path,
               ts_rank(
                   to_tsvector('simple', coalesce(title,'') || ' ' || coalesce(summary,'')),
                   plainto_tsquery('simple', :q)
               ) AS rank
        FROM knowledge_wiki_articles
        WHERE to_tsvector('simple', coalesce(title,'') || ' ' || coalesce(summary,''))
              @@ plainto_tsquery('simple', :q)
        ORDER BY rank DESC
        LIMIT :k
    """)
    rows = db.session.execute(sql, {'q': question, 'k': top_k}).fetchall()

    # 如果全文检索没命中，退化为取 topic 全部（避免完全空上下文）
    if not rows:
        rows = KnowledgeWikiArticle.query.limit(top_k).all()
        articles = [(a.id, a.topic, a.slug, a.title, a.summary, a.file_path) for a in rows]
    else:
        articles = [(r.id, r.topic, r.slug, r.title, r.summary, r.file_path) for r in rows]

    # 读全文
    context_parts = ['## 当前 index.md', index_md, '', '## 相关文章']
    cited = []
    for (aid, topic, slug, title, summary, file_path) in articles:
        content = storage.read_article_content(file_path)
        context_parts.append(f'\n### {topic}/{slug}.md — {title}\n')
        context_parts.append(content)
        cited.append({'id': aid, 'topic': topic, 'slug': slug, 'title': title})

    context_parts.extend(['', '## 用户问题', question])
    user_msg = '\n'.join(context_parts)

    client = claude_client.WikiClaudeClient()
    answer, usage = client.complete(
        system=prompts.QUERY_SYSTEM,
        user=user_msg,
        model=claude_client.QUERY_MODEL,
        max_tokens=4000,
    )

    return {
        'answer': answer,
        'cited_articles': cited,
        'usage': usage,
    }
```

---

### Task 6.2: 测试

**Files:**
- Create: `tests/wiki/test_querier.py`

**测试点：**
- 全文检索返回按相关度排序
- 无命中时退化策略
- mock Claude 返回，断言 answer 字段存在

**提交：**
```bash
git add -A
git commit -m "feat(wiki): Query 问答服务 + PG 全文检索"
```

---

## Phase 7: Lint 质检服务

### Task 7.1: 质检主流程

**Files:**
- Create: `app/services/wiki/linter.py`

**流程：**

```
1. 读全部文章元数据 + 全文
2. 组装到 LINT prompt 里（可能很大，用 1M 上下文）
3. 调 LINT_MODEL
4. 解析 JSON：
   - issues 写入 log.md
   - auto_fixes 覆盖文章文件
5. 返回报告
```

**代码骨架：**

```python
# app/services/wiki/linter.py
import json
from datetime import datetime

from app import db
from app.models.knowledge import KnowledgeWikiArticle
from app.services.wiki import claude_client, prompts, storage


def lint_wiki(apply_auto_fixes: bool = False) -> dict:
    articles = KnowledgeWikiArticle.query.all()
    parts = ['## 所有文章']
    for art in articles:
        content = storage.read_article_content(art.file_path)
        parts.append(f'\n### {art.topic}/{art.slug}.md — {art.title}\n')
        parts.append(f'summary: {art.summary or "(空)"}')
        parts.append(f'outbound_refs: {art.outbound_refs or []}')
        parts.append('---')
        parts.append(content)
    user_msg = '\n'.join(parts)

    client = claude_client.WikiClaudeClient()
    response, usage = client.complete(
        system=prompts.LINT_SYSTEM,
        user=user_msg,
        model=claude_client.LINT_MODEL,
        max_tokens=16000,
    )

    result = json.loads(response.strip().strip('`'))

    # 写日志
    storage.append_log('lint', result.get('summary', ''))

    # 应用自动修复
    if apply_auto_fixes:
        for fix in result.get('auto_fixes', []):
            topic, slug = fix['article'].split('/', 1)
            storage.write_article(topic, slug, fix['new_content'])
            art = KnowledgeWikiArticle.query.filter_by(topic=topic, slug=slug).first()
            if art:
                art.content_length = len(fix['new_content'])
                art.last_compiled_at = datetime.utcnow()
        db.session.commit()

    return {**result, 'usage': usage}
```

**提交：**
```bash
git add -A
git commit -m "feat(wiki): Lint 质检服务"
```

---

## Phase 8: API 路由

### Task 8.1: Wiki Blueprint

**Files:**
- Create: `app/views/knowledge_wiki.py`
- Modify: `app/__init__.py`（注册 blueprint）

**路由：**

| 方法 | 路径 | 功能 | 权限 |
|------|------|------|------|
| POST | `/api/wiki/raw-files` | 上传原始文件（指定 topic） | admin |
| GET  | `/api/wiki/raw-files` | 列出所有原始文件 | 登录 |
| POST | `/api/wiki/raw-files/<id>/ingest` | 触发编译 | admin |
| GET  | `/api/wiki/articles` | 文章列表（可按 topic 过滤） | 登录 |
| GET  | `/api/wiki/articles/<id>` | 文章详情（含 content） | 登录 |
| GET  | `/api/wiki/tree` | 返回 topic 树 + 文章列表 | 登录 |
| GET  | `/api/wiki/index` | 返回 index.md 内容 | 登录 |
| POST | `/api/wiki/query` | 问答 | 登录 |
| POST | `/api/wiki/lint` | 触发质检 | admin |
| GET  | `/wiki` | 前端主页面（渲染 tw_wiki.html） | 登录 |

**代码骨架：**

```python
# app/views/knowledge_wiki.py
import logging
from flask import Blueprint, request, jsonify, render_template, current_app
from flask_login import login_required, current_user

from app import db
from app.models.knowledge import KnowledgeRawFile, KnowledgeWikiArticle
from app.models.file_manager import FileLibrary
from app.services.wiki import compiler, querier, linter, storage
from app.services.wiki.paths import ensure_wiki_structure

logger = logging.getLogger(__name__)
wiki_bp = Blueprint('knowledge_wiki', __name__)


def _is_admin() -> bool:
    return current_user.role in ('admin', 'ceo')


# ── 页面路由 ──────────────────────────────────────────────

@wiki_bp.route('/wiki')
@login_required
def wiki_page():
    return render_template('knowledge/tw_wiki.html', is_admin=_is_admin())


# ── 原始文件 API ─────────────────────────────────────────

@wiki_bp.route('/api/wiki/raw-files', methods=['GET'])
@login_required
def list_raw_files():
    topic = request.args.get('topic')
    q = KnowledgeRawFile.query
    if topic:
        q = q.filter_by(topic=topic)
    items = q.order_by(KnowledgeRawFile.created_at.desc()).all()
    return jsonify({'success': True, 'data': [r.to_dict() for r in items]})


@wiki_bp.route('/api/wiki/raw-files', methods=['POST'])
@login_required
def upload_raw_file():
    if not _is_admin():
        return jsonify({'success': False, 'message': '仅管理员可上传原始资料'}), 403

    file_library_id = request.form.get('file_library_id', type=int)
    topic = (request.form.get('topic') or '').strip()
    title = (request.form.get('title') or '').strip()

    if not file_library_id or not topic:
        return jsonify({'success': False, 'message': 'file_library_id 和 topic 必填'}), 400

    fl = FileLibrary.query.get(file_library_id)
    if not fl:
        return jsonify({'success': False, 'message': '文件不存在'}), 404

    ensure_wiki_structure()

    # 从 file_library 拷贝到 raw/<topic>/
    import shutil
    from datetime import date
    safe_name = f"{date.today().isoformat()}-{fl.original_filename}"
    raw_rel = storage.save_raw_file(
        topic,
        safe_name,
        open(fl.file_path, 'rb').read(),
    )

    raw = KnowledgeRawFile(
        file_library_id=fl.id,
        topic=topic,
        raw_path=raw_rel,
        title=title or fl.original_filename,
        added_by=current_user.id,
    )
    db.session.add(raw)
    db.session.commit()
    return jsonify({'success': True, 'data': raw.to_dict()})


@wiki_bp.route('/api/wiki/raw-files/<int:raw_id>/ingest', methods=['POST'])
@login_required
def ingest_raw_file(raw_id):
    if not _is_admin():
        return jsonify({'success': False, 'message': '仅管理员可触发编译'}), 403
    try:
        result = compiler.ingest_raw_file(raw_id)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.exception('Ingest 失败')
        return jsonify({'success': False, 'message': str(e)}), 500


# ── 文章 API ──────────────────────────────────────────────

@wiki_bp.route('/api/wiki/articles', methods=['GET'])
@login_required
def list_articles():
    topic = request.args.get('topic')
    q = KnowledgeWikiArticle.query
    if topic:
        q = q.filter_by(topic=topic)
    items = q.order_by(KnowledgeWikiArticle.topic, KnowledgeWikiArticle.slug).all()
    return jsonify({'success': True, 'data': [a.to_dict() for a in items]})


@wiki_bp.route('/api/wiki/articles/<int:aid>', methods=['GET'])
@login_required
def get_article(aid):
    art = KnowledgeWikiArticle.query.get(aid)
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404
    return jsonify({'success': True, 'data': art.to_dict(include_content=True)})


@wiki_bp.route('/api/wiki/tree', methods=['GET'])
@login_required
def get_tree():
    """返回 topic -> [articles] 的树结构，用于前端侧栏"""
    tree = {}
    items = KnowledgeWikiArticle.query.order_by(
        KnowledgeWikiArticle.topic, KnowledgeWikiArticle.slug
    ).all()
    for art in items:
        tree.setdefault(art.topic, []).append({
            'id': art.id,
            'slug': art.slug,
            'title': art.title,
            'summary': art.summary,
            'updated_at': art.updated_at.isoformat() if art.updated_at else None,
        })
    return jsonify({'success': True, 'data': tree})


@wiki_bp.route('/api/wiki/index', methods=['GET'])
@login_required
def get_index():
    return jsonify({'success': True, 'content': storage.read_index()})


# ── 问答 API ──────────────────────────────────────────────

@wiki_bp.route('/api/wiki/query', methods=['POST'])
@login_required
def query():
    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    if not question:
        return jsonify({'success': False, 'message': '问题不能为空'}), 400
    try:
        result = querier.query_wiki(question)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.exception('Query 失败')
        return jsonify({'success': False, 'message': str(e)}), 500


# ── 质检 API ──────────────────────────────────────────────

@wiki_bp.route('/api/wiki/lint', methods=['POST'])
@login_required
def lint():
    if not _is_admin():
        return jsonify({'success': False, 'message': '仅管理员可触发质检'}), 403
    data = request.get_json(silent=True) or {}
    apply_fixes = bool(data.get('apply_auto_fixes'))
    try:
        result = linter.lint_wiki(apply_auto_fixes=apply_fixes)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.exception('Lint 失败')
        return jsonify({'success': False, 'message': str(e)}), 500
```

**注册 Blueprint：**

```python
# app/__init__.py
from app.views.knowledge_wiki import wiki_bp
app.register_blueprint(wiki_bp)
csrf.exempt(wiki_bp)  # 同其他 API
```

**提交：**
```bash
git add -A
git commit -m "feat(wiki): API 路由（raw-files / articles / tree / query / lint）"
```

---

## Phase 9: 前端 UI

### Task 9.1: Wiki 主页面模板

**Files:**
- Create: `app/templates/knowledge/tw_wiki.html`

**布局：**

```
┌──────────────┬────────────────────────────┐
│ 侧栏          │  正文区                      │
│              │                            │
│ 📁 product   │  📄 GP328P 产品概述          │
│   - overview │                            │
│   - apps     │  # GP328P ...               │
│ 📁 competitor│  ## 核心规格                  │
│              │  ...                       │
│              ├─────────────────────────────│
│              │  💬 问答区                    │
│              │  [输入框]                    │
│              │  AI: ...                   │
└──────────────┴────────────────────────────┘
```

**模板要点：**
- 继承 `tw_base.html`（PMA Tailwind 基础模板）
- 用 Alpine.js 管理状态（树、当前文章、问答历史）
- marked.js 渲染 Markdown
- 右上角"管理"按钮跳到原始文件管理（条件：`is_admin`）

**Alpine 数据结构：**

```javascript
{
  tree: {},                    // { topic: [{id, slug, title, summary}] }
  currentArticle: null,        // {id, title, content, ...}
  chatMessages: [],            // [{role, text, cited}]
  chatInput: '',
  loading: false,
  indexContent: '',
  showIndex: false,

  async loadTree() { ... },
  async openArticle(id) { ... },
  async sendQuestion() { ... },
}
```

**验证：**
- 打开 `/wiki`，侧栏能看到所有文章
- 点击文章，右侧渲染 Markdown
- 在问答框输入问题，回答出现在气泡里

---

### Task 9.2: Wiki 管理子页面（原始文件上传 + 编译）

**Files:**
- Create: `app/templates/knowledge/tw_wiki_admin.html`
- 新增路由 `GET /wiki/admin`（admin only）

**功能：**
- 从 PMA 文件管理器选择文件，设置 topic 和 title，"加入知识库原始资料"
- 原始文件列表，每行有 "开始编译" 按钮
- 编译状态实时刷新（轮询 `/api/wiki/raw-files`）
- "一键质检" 按钮调用 `/api/wiki/lint`

---

### Task 9.3: 菜单集成

**Files:**
- Modify: `app/templates/components/tw_sidebar.html`（或主菜单位置）

**新增菜单项：** "知识库 Wiki" → `/wiki`

**验证：** 登录后侧栏可见菜单，点击跳转成功

**提交：**
```bash
git add -A
git commit -m "feat(wiki): 前端 UI（主页面 + 管理页 + 菜单）"
```

---

## Phase 10: 验收与发布

### Task 10.1: 端到端手动测试清单

操作人：管理员账号

- [ ] 创建一个 topic（例如 "product"）
- [ ] 上传一份 GP328P 产品 PDF 作为 raw 资料
- [ ] 触发 Ingest，等待完成
- [ ] 打开 `/wiki`，侧栏看到 `product/gp328p-overview` 等文章
- [ ] 点击文章，Markdown 正确渲染
- [ ] 上传第二份 GP538 PDF，触发 Ingest
- [ ] 验证：GP328P 文章末尾的 "See Also" 可能被更新，加入 GP538 链接（级联更新验证）
- [ ] 在问答框问"GP328P 的 IP 等级"，回答带来源链接
- [ ] 触发 Lint，检查是否能识别无来源的论断
- [ ] 检查 `storage/knowledge_base/wiki/log.md` 里有完整操作记录

### Task 10.2: 环境变量文档

**Files:**
- Modify: `.env.example`

新增：

```
# Wiki 知识库
WIKI_ROOT=                              # 空则默认 <basedir>/storage/knowledge_base
WIKI_INGEST_MODEL=claude-opus-4-6[1m]
WIKI_QUERY_MODEL=claude-opus-4-6[1m]
WIKI_LINT_MODEL=claude-opus-4-6[1m]
WIKI_META_MODEL=claude-haiku-4-5-20251001
ANTHROPIC_API_KEY=                      # 必填
```

### Task 10.3: 部署 Checklist

- [ ] 本地跑 `flask db upgrade`
- [ ] SG NAS `docker exec pma flask db upgrade`
- [ ] SG NAS 创建目录：`mkdir -p /srv/pma/storage/knowledge_base/{raw,wiki}`
- [ ] 配置 `ANTHROPIC_API_KEY`（不走 anthropic-proxy，直连）
- [ ] 重启 PMA 容器
- [ ] 用管理员账号走一遍 10.1 清单

### Task 10.4: 最终提交与合并

```bash
git add -A
git commit -m "feat(wiki): 完成 Wiki 知识库系统 —— 替换旧 RAG 方案"
git push origin feature/wiki-knowledge-base
```

创建 PR 到 `main`，关联本设计文档。

---

## 附录 A: 关键设计权衡

### A.1 为什么文章内容存磁盘不存数据库？

- **可 git 版本化**：随时追溯谁改了什么
- **人类可直接编辑**：必要时管理员可以绕过 AI 改 Markdown
- **可移植**：未来迁移到其他系统不需要 dump 数据库
- **Karpathy 原则**：「文件夹里放 Markdown」
- **PG 只负责元数据和全文检索**，职责清晰

### A.2 为什么不用向量检索？

见 0.1 节。核心理由：PMA 文档量小，Wiki 编译后已经是结构化高质量内容，全文检索配合 Claude 1M 上下文足够。

### A.3 为什么 Query 也用 Opus？

Wiki 问答的价值在于基于整理好的知识给出深度回答，节省 Query 成本会牺牲这个核心价值。团队规模小（十几人），每天查询量估计 <500 次，Opus 成本可接受。

### A.4 Ingest 是同步还是异步？

**第一版做同步**，理由：
- 简单
- 编译一份文件 Claude 通常 30-60 秒，前端可以 loading spinner
- 不需要引入 Celery/RQ

未来文件量大时再改异步（启动后台 worker 跑 `compiler.ingest_raw_file(id)`）。

### A.5 级联更新会不会"越改越乱"？

风险存在。缓解措施：
1. **Lint 周期性质检**：每周人工触发一次
2. **log.md 可追溯**：每次 ingest 都记录改了什么
3. **git 版本化**：出问题可以回滚到上一次编译前

---

## 附录 B: 不做的事（YAGNI）

- ❌ 不做实时 Wiki 协作编辑
- ❌ 不做文章版本对比 UI（有 git 就够）
- ❌ 不做用户自定义 prompts
- ❌ 不做多语言 Wiki（先中文）
- ❌ 不做图片提取（PDF 里的图先不处理）
- ❌ 不做 Wiki 导出功能（手动拷贝 wiki/ 目录即可）
- ❌ 不做权限到 topic 级别（全员共享 Wiki）

这些都是未来需求真正出现时再做。

---

## 附录 C: 迁移顺序总结

```
Phase 1 (清理)  →  Phase 2 (schema)  →  Phase 3 (存储)
                                             ↓
Phase 4 (Claude 客户端 + prompts)  →  Phase 5 (Ingest)
                                             ↓
Phase 6 (Query)  →  Phase 7 (Lint)  →  Phase 8 (API)
                                             ↓
Phase 9 (UI)  →  Phase 10 (验收)
```

每个 Phase 结束都有提交节点，保证任何节点回滚都是干净状态。
