# Wiki Phase 2：管理面板重构 + 权限层级

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重构 Wiki 右侧管理面板为拖拽上传 + 编译队列 + 删除管理的体验；左侧文章支持删除操作；增加知识权限层级。

**Architecture:** 管理面板从"手动输 file_library_id"改为直接拖拽文件上传 → 上传列表 → 一键编译的流水线。文章删除通过左侧 `...` 菜单触发。知识权限分个人/部门/公司/系统四级。

**来源：** 2026-04-12 验收反馈

---

## 一、管理面板重构

### 1.1 右侧面板功能

**当前问题：**
- 需要手动填 `file_library_id`（用户不知道 ID）
- 编译操作和原始文件管理混在一起
- 没有拖拽上传

**目标体验：**

```
┌────────────────────────────────────┐
│ Wiki 管理                     [×]  │
├────────────────────────────────────┤
│                                    │
│  ┌──────────────────────────────┐  │
│  │    拖拽文件到这里上传         │  │
│  │    支持 PDF / DOCX / MD      │  │
│  │    [或点击选择文件]           │  │
│  └──────────────────────────────┘  │
│                                    │
│  Topic: [product ▼] [+ 新建]      │
│                                    │
│  ── 待编译队列 ──                   │
│  📄 手册v2.pdf          [编译]     │
│  📄 竞品分析.docx       [编译]     │
│                                    │
│  ── 已编译 ──                      │
│  ✅ 手册v1.pdf  → 3篇文章  [删]   │
│  ✅ 岗位确认书  → 1篇文章  [删]   │
│                                    │
│  ── 质检 ──                        │
│  [开始质检] □ 自动修复             │
│                                    │
└────────────────────────────────────┘
```

**关键改动：**
1. **拖拽上传区**：直接拖文件进虚线框，自动上传到 file_library + 创建 raw 记录
2. **Topic 选择器**：下拉已有 topic + 新建输入
3. **待编译队列**：上传后显示在这里，点"编译"按钮触发
4. **已编译列表**：显示已完成的 raw files + 关联的文章数 + 删除按钮
5. **只显示自己上传的**（非 admin 不能看别人的 raw files）

### 1.2 左侧文章目录 `...` 菜单

每篇文章标题右侧显示 `...` 按钮（hover 时出现），点击弹出菜单：
- 删除文章（仅 admin 或上传者）
- 重新编译（触发关联 raw file 的 re-ingest）
- 查看来源（显示 source_raw_ids 对应的原始文件名）

### 1.3 后端新增端点

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/wiki/upload-and-add` | 直接上传文件 → file_library + raw_file 一步完成 |
| DELETE | `/api/wiki/articles/<id>` | 删除文章（磁盘 + DB） |
| POST | `/api/wiki/articles/<id>/recompile` | 重新编译（找到 source_raw_ids 的 raw file 重跑 ingest） |

---

## 二、知识权限层级

### 2.1 Scope 模型

| scope | 可见范围 | 默认？ | 谁能设置 |
|-------|---------|--------|---------|
| `personal` | 仅上传者 | ✅ 默认 | 任何人 |
| `department` | 同部门成员 | | 上传者/部门管理 |
| `company` | 全公司 | | 部门管理/admin |
| `system` | 所有账户 | | admin/ceo |

### 2.2 数据模型变更

```python
# KnowledgeRawFile 新增
scope = Column(String(20), default='personal', nullable=False, index=True)
# scope: personal / department / company / system

# KnowledgeWikiArticle 新增
scope = Column(String(20), default='personal', nullable=False, index=True)
owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
# owner_id: 文章的所有者（编译触发者），用于 personal scope 过滤
```

### 2.3 查询过滤逻辑

```python
def _scope_filter(query, model, user):
    """根据 scope 和用户身份过滤查询"""
    if user.role in ('admin', 'ceo'):
        return query  # admin 看所有
    
    return query.filter(
        db.or_(
            model.scope == 'system',
            model.scope == 'company',
            db.and_(model.scope == 'department', model.owner_id.in_(
                # 同部门的用户 ID 列表
                db.session.query(User.id).filter_by(department_id=user.department_id)
            )),
            db.and_(model.scope == 'personal', model.owner_id == user.id),
        )
    )
```

### 2.4 影响的端点

所有查询端点都要加 scope 过滤：
- `GET /api/wiki/tree`
- `GET /api/wiki/articles`
- `GET /api/wiki/articles/<id>`
- `POST /api/wiki/query`（只检索用户可见的文章）
- `POST /api/wiki/lint`（只检查用户可见的文章）

### 2.5 迁移

```sql
ALTER TABLE knowledge_raw_files ADD COLUMN scope VARCHAR(20) DEFAULT 'personal' NOT NULL;
ALTER TABLE knowledge_wiki_articles ADD COLUMN scope VARCHAR(20) DEFAULT 'personal' NOT NULL;
ALTER TABLE knowledge_wiki_articles ADD COLUMN owner_id INTEGER REFERENCES users(id);
-- 已有数据默认为 admin 上传、company scope
UPDATE knowledge_raw_files SET scope = 'company';
UPDATE knowledge_wiki_articles SET scope = 'company', owner_id = (SELECT id FROM users WHERE role = 'admin' LIMIT 1);
```

---

## 三、实施顺序建议

| 批次 | 内容 | 估时 |
|------|------|------|
| A | 管理面板重构（拖拽上传 + 编译队列 + 已编译列表） | 2-3h |
| B | 左侧文章 `...` 菜单（删除 + 重新编译 + 查看来源） | 1-2h |
| C | 权限层级（scope 字段 + 过滤逻辑 + 迁移 + UI scope 选择器） | 2-3h |

---

## 四、YAGNI（不做）

- ❌ 不做文章编辑器（直接改 Markdown 文件用 git）
- ❌ 不做文章版本对比 UI
- ❌ 不做实时协作
- ❌ 不做文章评论/讨论
- ❌ 不做知识库搜索排序（当前全文检索够用）
