# Wiki 知识库分级权限设计方案

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 Wiki 知识库增加四级 scope（个人/部门/公司/系统），实现数据隔离、向上可见、去重检测和晋升审批。统一树形视图 + scope 标签过滤，无需 tab 切换。

**Architecture:** 在 KnowledgeRawFile 和 KnowledgeWikiArticle 上增加 `scope` + `owner_id` + `owner_department` 字段，查询时按当前用户的身份过滤可见范围。前端用统一树形目录按 topic 展开，每篇文章带 scope 彩色标签，顶部 toggle 按钮控制各 scope 的显隐。编译时高级 scope 的文章作为只读上下文注入。晋升通过审批表驱动。磁盘目录不分 scope（仅靠 DB 字段过滤）。

**Tech Stack:** Flask + SQLAlchemy + PostgreSQL + Alembic migration + Alpine.js + Tailwind

---

## 1. 四级 Scope 定义

```
┌─────────────────────────────────────────────────────────┐
│  system    │ 系统预置知识（产品手册、行业标准等）           │
├─────────────────────────────────────────────────────────┤
│  company   │ 全公司共享（经审批晋升的优质内容）            │
├─────────────────────────────────────────────────────────┤
│  department│ 部门内共享（部门成员贡献，部门经理管理）       │
├─────────────────────────────────────────────────────────┤
│  personal  │ 个人私有（仅自己和上级经理可见）              │
└─────────────────────────────────────────────────────────┘
```

### 1.1 可见性规则

| 用户身份 | 可见范围 |
|---------|---------|
| 普通成员 | system + company + 所属部门 department + 自己的 personal |
| 部门经理 | 同上 + **本部门所有成员的 personal** |
| admin/ceo | 所有 scope、所有部门、所有用户的内容 |

**原则**：
- 上级 scope 对所有人可见（system > company > department > personal）
- 同级 scope 互相隔离（部门A ≠ 部门B，个人A ≠ 个人B）
- 部门经理对成员个人库有**只读发现权**（用于发现优质内容并拉升）

### 1.2 写入权限

| 操作 | personal | department | company | system |
|------|----------|-----------|---------|--------|
| 上传原始文件 | 任何用户 | 部门成员 | admin/ceo | admin |
| 触发编译 | 文件所有者 | 部门经理 | admin/ceo | admin |
| 删除文件/文章 | 文件所有者 | 部门经理 | admin/ceo | admin |
| 晋升发起 | 所有者本人 | 部门经理 | admin/ceo | admin |

### 1.3 与现有权限系统的关系

PMA 已有 `User.role`（admin/ceo/user/dealer/service）、`User.department`、`User.is_department_manager` 字段，以及 `RolePermission.permission_level`（system/company/department/personal）模式。Wiki scope 复用这些已有字段做身份判断，不引入新的权限配置表。

---

## 2. 前端交互设计（统一树形视图）

### 2.1 核心理念：一棵树 + scope 标签 + toggle 过滤

**不用 tab 切换**。所有可见文章在同一棵树里按 topic 展开，每篇文章前面显示彩色 scope 标签：

```
┌──────────────────────────────────────────────────────────┐
│ 过滤: [✓ 系统] [✓ 公司] [✓ 部门] [✓ 个人]    🔍 搜索...  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ ▼ 研发                                                   │
│   ├── [系统] PNR2100 产品规格手册                          │
│   ├── [公司] PNR2100 终端交互接口文档                      │
│   ├── [部门] PNR2100 定位功能验收方案                      │
│   ├── [个人] 验收测试执行笔记                              │
│   └── [个人|张三] 信标调试记录           ← 经理可见         │
│                                                          │
│ ▼ 销售                                                   │
│   ├── [公司] EVERTAC 批价管理机制                          │
│   ├── [部门] 渠道商沟通话术                                │
│   └── [个人] 客户谈判要点                                  │
│                                                          │
│ ▼ HR                                                     │
│   └── [公司] 岗位确认书 — 市场执行统筹                     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Scope 标签样式

| Scope | 颜色 | 显示文字 | 说明 |
|-------|------|---------|------|
| system | 灰色 `bg-gray-100 text-gray-600` | `系统` | 所有人看到 |
| company | 蓝色 `bg-blue-100 text-blue-700` | `公司` | 所有人看到 |
| department | 绿色 `bg-green-100 text-green-700` | `部门` | 同部门看到 |
| personal (自己) | 紫色 `bg-purple-100 text-purple-700` | `个人` | 仅自己 |
| personal (他人) | 紫色+姓名 | `个人\|张三` | 仅经理看到 |

### 2.3 Toggle 过滤行为

顶部 4 个 toggle 按钮：
- **点击关闭**某个 scope → 该 scope 文章从列表**消失** + **问答时不作为上下文**
- **默认全部开启**
- 状态保存在 localStorage，刷新不丢失
- "个人"关闭 = 所有个人文章（含自己的）都隐藏

```javascript
// Alpine.js 状态
scopeFilter: {
    system: true,
    company: true,
    department: true,
    personal: true,
},
// 过滤后的文章列表
get filteredArticles() {
    return this.allArticles.filter(art => this.scopeFilter[art.scope]);
}
```

### 2.4 上传时的 Scope 选择

上传确认弹窗增加 scope 选择（pill 按钮，和 topic 选择同一行）：

```
┌─────────────────────────────────────────────────┐
│ 添加到知识库                                      │
│                                                 │
│ 文件：PNR2100验收方案.docx                       │
│                                                 │
│ 主题：[研发] [销售] [HR] [+ 新建]                │
│                                                 │
│ 范围：[● 个人] [○ 部门] [○ 公司]                │
│                                                 │
│ [取消]                        [添加到待编译]      │
└─────────────────────────────────────────────────┘
```

- 普通用户可选：个人、部门
- admin/ceo 可选：个人、部门、公司、系统
- 选"部门"需要用户有 `department` 字段（无部门的用户只能选个人/公司）

### 2.5 晋升交互

文章右键菜单或详情页操作栏：

```
[↑ 晋升到部门]    ← 个人文章，所有者可见
[↑ 晋升到公司]    ← 部门文章，部门经理可见
[↓ 降级到部门]    ← 公司文章，admin/ceo 可见
[分享给...]       ← 跨部门分享
```

经理在看到成员的 `[个人|张三]` 文章时，右键有"拉升到部门"（直接生效，无需张三同意）。

### 2.6 审批通知

侧栏树顶部，经理/admin 可见：

```
📋 待审批 (2)    ← 红色 badge
```

点击展开审批列表，逐条通过/拒绝。

---

## 3. 数据模型变更

### 3.1 KnowledgeRawFile 新增字段

```python
class KnowledgeRawFile(db.Model):
    __tablename__ = 'knowledge_raw_files'

    # ... 已有字段 ...

    # ── scope 相关（新增）──
    scope = Column(String(20), nullable=False, default='personal', index=True)
    # 'personal' / 'department' / 'company' / 'system'

    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    # 始终 = 上传者（晋升后不变，表示"贡献者"）

    owner_department = Column(String(100), nullable=True, index=True)
    # 上传者所属部门（冗余存储，避免每次 join user 表）
    # scope=department 时用于过滤
```

### 3.2 KnowledgeWikiArticle 新增字段

```python
class KnowledgeWikiArticle(db.Model):
    __tablename__ = 'knowledge_wiki_articles'

    # ... 已有字段 ...

    # ── scope 相关（新增）──
    scope = Column(String(20), nullable=False, default='personal', index=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner_department = Column(String(100), nullable=True, index=True)
```

### 3.3 新增：晋升申请表

```python
class KnowledgePromotionRequest(db.Model):
    """知识库内容晋升/降级申请"""
    __tablename__ = 'knowledge_promotion_requests'

    id = Column(Integer, primary_key=True)

    # 目标
    article_id = Column(Integer, ForeignKey('knowledge_wiki_articles.id'), nullable=False)
    from_scope = Column(String(20), nullable=False)
    to_scope = Column(String(20), nullable=False)

    # 申请人
    requested_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    request_note = Column(Text, nullable=True)

    # 审批
    status = Column(String(20), default='pending', index=True)
    # 'pending' / 'approved' / 'rejected'
    reviewed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    review_note = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=get_local_time)
```

### 3.4 新增：跨部门分享授权表

```python
class KnowledgeShareGrant(db.Model):
    """跨部门/跨人分享授权（不改变文章 scope，只扩展可见范围）"""
    __tablename__ = 'knowledge_share_grants'

    id = Column(Integer, primary_key=True)

    article_id = Column(Integer, ForeignKey('knowledge_wiki_articles.id'), nullable=False)
    grant_type = Column(String(20), nullable=False)
    # 'department' — 授权给一个部门
    # 'user' — 授权给一个人

    grant_target = Column(String(100), nullable=False)
    # grant_type='department' → 部门名
    # grant_type='user' → user_id (as string)

    granted_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=get_local_time)
```

### 3.5 磁盘目录（不变）

**决策：磁盘不分 scope 目录**，继续平铺：

```
storage/knowledge_base/
├── raw/{topic}/{date}-{filename}
└── wiki/
    ├── index.md          ← 合并所有 scope 的文章（按 scope 分区）
    ├── log.md
    └── {topic}/{slug}.md
```

scope 隔离完全靠 DB 字段。好处：
- 实现简单，不用迁移文件
- 晋升/降级只改 DB 字段，不动磁盘
- index.md 按 scope 分区显示

---

## 4. 查询过滤逻辑

### 4.1 核心过滤函数

```python
def get_visible_articles_query(user):
    """构建当前用户可见文章的 SQLAlchemy 查询条件。"""
    from sqlalchemy import or_

    conditions = [
        # 1. system — 所有人可见
        KnowledgeWikiArticle.scope == 'system',
        # 2. company — 所有人可见
        KnowledgeWikiArticle.scope == 'company',
    ]

    # 3. department — 本部门可见
    if user.department:
        conditions.append(
            (KnowledgeWikiArticle.scope == 'department') &
            (KnowledgeWikiArticle.owner_department == user.department)
        )

    # 4. personal — 自己的
    conditions.append(
        (KnowledgeWikiArticle.scope == 'personal') &
        (KnowledgeWikiArticle.owner_id == user.id)
    )

    # 5. 部门经理：本部门成员的 personal
    if user.is_department_manager and user.department:
        dept_user_ids = [u.id for u in User.query.filter_by(
            department=user.department
        ).all()]
        conditions.append(
            (KnowledgeWikiArticle.scope == 'personal') &
            (KnowledgeWikiArticle.owner_id.in_(dept_user_ids))
        )

    # 6. admin/ceo：看所有
    if user.role in ('admin', 'ceo'):
        return KnowledgeWikiArticle.query  # 无过滤

    # 7. 跨部门分享授权
    shared_article_ids = [g.article_id for g in KnowledgeShareGrant.query.filter(
        or_(
            (KnowledgeShareGrant.grant_type == 'user') &
            (KnowledgeShareGrant.grant_target == str(user.id)),
            (KnowledgeShareGrant.grant_type == 'department') &
            (KnowledgeShareGrant.grant_target == user.department),
        )
    ).all()]
    if shared_article_ids:
        conditions.append(KnowledgeWikiArticle.id.in_(shared_article_ids))

    return KnowledgeWikiArticle.query.filter(or_(*conditions))
```

### 4.2 前端 scope 过滤叠加

后端返回所有可见文章（带 `scope` 字段），前端再根据用户的 toggle 状态做二次过滤。这样 toggle 是纯前端操作，无需重新请求。

### 4.3 问答时的 scope 过滤

```python
def get_query_context(user, scope_filter: list[str]):
    """获取问答可用的文章上下文。
    
    scope_filter: 用户前端 toggle 开启的 scope 列表，
    例如 ['system', 'company', 'department']（关闭了 personal）
    """
    articles = get_visible_articles_query(user).filter(
        KnowledgeWikiArticle.scope.in_(scope_filter)
    ).all()
    return articles
```

---

## 5. 编译时的 Scope 隔离

### 5.1 上下文注入规则

编译某个 scope 内的文件时，Claude 能看到的"相关已有文章"：

| 正在编译的 scope | 可参考的文章（只读上下文） | 可修改的文章 |
|-----------------|------------------------|-------------|
| personal | 同用户 personal + 所属 department + company + system | 仅同用户 personal |
| department | 本部门 department + company + system | 仅本部门 department |
| company | company + system | 仅 company |
| system | system | 仅 system |

### 5.2 Prompt 调整

在 INGEST_SYSTEM prompt 中增加 scope 说明：

```
## Scope 规则（重要）

当前编译范围为 [{scope}] 级别。你只能对 [{scope}] 级别的文章执行 create/update 操作。
标记为 [只读] 的文章来自更高级别的知识库，你可以在 See Also 中引用它们，但不能修改。
如果新资料的内容与只读文章高度重叠，在 rationale 中说明，不要重复创建。
```

### 5.3 级联更新范围限制

`_apply_operations` 中增加校验：

```python
for op in operations:
    if op['action'] in ('create', 'update'):
        # 确保 Claude 没有试图修改其他 scope 的文章
        if op.get('_readonly'):
            logger.warning(f'[Ingest] Claude 试图修改只读文章 {op["slug"]}，跳过')
            continue
```

---

## 6. 晋升与降级机制

### 6.1 晋升路径与审批人

```
personal ──→ department ──→ company ──→ system
  │              │              │
  │ 发起人:      │ 发起人:       │ 发起人:
  │ 所有者本人    │ 部门经理      │ admin/ceo
  │              │              │
  │ 审批人:      │ 审批人:       │ 审批人:
  │ 部门经理     │ admin/ceo    │ admin(自审)
  └──────────────┴──────────────┘

快速通道（无需审批）：
- 部门经理直接拉取成员个人文章到部门
- admin/ceo 直接拉取任何文章到公司/系统
```

### 6.2 降级（反向操作）

| 降级方向 | 操作人 |
|---------|--------|
| system → company | admin |
| company → department | admin/ceo |
| department → personal | 部门经理（退回给原 owner） |

降级时 scope 字段回退，`owner_id` 和 `owner_department` 不变。

### 6.3 晋升执行逻辑

```python
def execute_promotion(article_id: int, to_scope: str, executor_id: int):
    """执行晋升/降级：只改 DB 字段，不动磁盘文件。"""
    art = KnowledgeWikiArticle.query.get(article_id)
    old_scope = art.scope
    art.scope = to_scope

    # 如果晋升到 department，确保 owner_department 正确
    if to_scope == 'department' and not art.owner_department:
        owner = User.query.get(art.owner_id)
        art.owner_department = owner.department

    # 关联的 raw files 也一起升级
    for raw_id in (art.source_raw_ids or []):
        raw = KnowledgeRawFile.query.get(raw_id)
        if raw and raw.scope == old_scope:
            raw.scope = to_scope

    db.session.commit()

    # 记录到 log.md
    storage.append_log('promotion', f'{old_scope} → {to_scope}: {art.title}')
```

---

## 7. 去重检测

### 7.1 时机

- **编译完成后**（不阻止编译，编译后异步检测）
- 检测范围：新文章 vs 上级 scope 同 topic 的已有文章

### 7.2 方法

用 Claude Haiku 做轻量判断（成本极低）：

```python
def check_duplicate_after_ingest(article: KnowledgeWikiArticle):
    """编译完成后检查是否与上级 scope 有重复。"""
    higher_scopes = _get_higher_scopes(article.scope)
    similar_articles = KnowledgeWikiArticle.query.filter(
        KnowledgeWikiArticle.scope.in_(higher_scopes),
        KnowledgeWikiArticle.topic == article.topic,
        KnowledgeWikiArticle.id != article.id,
    ).all()

    if not similar_articles:
        return None  # 无需检测

    # 组装 Haiku prompt
    prompt = f"""比较以下新文章和已有文章的摘要，判断是否有实质重复：

新文章：{article.title} — {article.summary}

已有文章：
{chr(10).join(f'- [{a.scope}] {a.title} — {a.summary}' for a in similar_articles)}

回复 JSON：{{"duplicates": [{{"article_id": int, "overlap": "high/partial/none", "reason": "..."}}]}}
"""
    # 调 Haiku（便宜、快速）
    resp = claude.complete(system="...", user=prompt, model=META_MODEL, max_tokens=1000)
    return parse_duplicate_result(resp.text)
```

### 7.3 重复提示（不阻止）

检测结果存入文章的新字段 `duplicate_hint`（JSON），前端文章列表中显示小图标：

```
├── [个人] PNR2100 验收笔记  ⚠️ 与[公司]《验收方案》部分重叠
```

点击查看详情，建议"查阅已有文章"或"申请合并"。

---

## 8. 跨部门分享

### 8.1 操作入口

文章右键菜单："分享给..." → 弹出选择框：

```
┌────────────────────────────────┐
│ 分享文章给                      │
│                                │
│ ○ 指定部门：[销售部 ▼]         │
│ ○ 指定人员：[搜索用户...]       │
│                                │
│ [取消]           [确认分享]     │
└────────────────────────────────┘
```

### 8.2 可见性

被分享的文章在目标用户/部门的树形列表中出现，带特殊标签：

```
├── [分享|研发部] PNR2100 接口文档    ← 研发部分享给销售部的
```

### 8.3 权限

分享只授予**只读**权限，不能修改/删除/再分享。

---

## 9. 数据迁移

### 9.1 Migration 脚本

```python
def upgrade():
    # 1. knowledge_raw_files 加字段
    op.add_column('knowledge_raw_files',
        sa.Column('scope', sa.String(20), server_default='company', nullable=False))
    op.add_column('knowledge_raw_files',
        sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('knowledge_raw_files',
        sa.Column('owner_department', sa.String(100), nullable=True))

    # 2. knowledge_wiki_articles 加字段
    op.add_column('knowledge_wiki_articles',
        sa.Column('scope', sa.String(20), server_default='company', nullable=False))
    op.add_column('knowledge_wiki_articles',
        sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('knowledge_wiki_articles',
        sa.Column('owner_department', sa.String(100), nullable=True))

    # 3. 现有数据迁移：设为 company scope
    op.execute("""
        UPDATE knowledge_raw_files
        SET scope = 'company', owner_id = added_by
    """)
    op.execute("""
        UPDATE knowledge_wiki_articles
        SET scope = 'company',
            owner_id = COALESCE(
                (SELECT added_by FROM knowledge_raw_files
                 WHERE id = ANY(knowledge_wiki_articles.source_raw_ids)
                 LIMIT 1),
                1
            )
    """)

    # 4. 设 NOT NULL（数据填充后）
    op.alter_column('knowledge_raw_files', 'owner_id', nullable=False)
    op.alter_column('knowledge_wiki_articles', 'owner_id', nullable=False)

    # 5. 创建索引
    op.create_index('ix_raw_scope_dept', 'knowledge_raw_files', ['scope', 'owner_department'])
    op.create_index('ix_article_scope_dept', 'knowledge_wiki_articles', ['scope', 'owner_department'])
    op.create_index('ix_article_scope_owner', 'knowledge_wiki_articles', ['scope', 'owner_id'])

    # 6. 创建新表
    op.create_table('knowledge_promotion_requests', ...)
    op.create_table('knowledge_share_grants', ...)
```

---

## 10. 实施任务分解

### Task 1: DB Migration（P0）

**Files:**
- Create: `migrations/versions/xxxx_wiki_scope_fields.py`
- Modify: `app/models/knowledge.py` — 加 scope/owner_id/owner_department 字段

**Steps:**
1. 在模型里加字段声明
2. `flask db migrate -m "wiki scope fields"`
3. 编辑生成的 migration 加入数据填充逻辑
4. `flask db upgrade`
5. 验证现有数据 scope='company'

### Task 2: 查询过滤（P0）

**Files:**
- Modify: `app/views/knowledge_wiki.py` — 所有 list/get 端点加 scope 过滤
- Create: `app/services/wiki/scope.py` — 过滤逻辑封装

**Steps:**
1. 实现 `get_visible_query(user, model_class)` 通用过滤
2. 修改 `list_articles`、`list_raw_files`、`get_tree` 端点
3. 修改 `query_endpoint` 加 scope_filter 参数
4. 测试：不同角色用户看到不同数据

### Task 3: 前端树形视图 + scope 标签（P0）

**Files:**
- Modify: `app/templates/knowledge/tw_wiki.html` — 侧栏改为统一树 + badge + toggle

**Steps:**
1. 添加 scope toggle 按钮栏
2. 文章列表项加 scope badge（彩色 pill）
3. Alpine.js `scopeFilter` 状态 + localStorage 持久化
4. 过滤逻辑：`filteredArticles` computed

### Task 4: 上传时 Scope 选择（P1）

**Files:**
- Modify: `app/templates/knowledge/tw_wiki.html` — 上传 modal 加 scope 选择
- Modify: `app/views/knowledge_wiki.py` — upload 端点接收 scope 参数

**Steps:**
1. Modal 加 scope pill 按钮组
2. 后端接收 scope，写入 raw_file 和后续 article
3. 权限校验：普通用户不能直接写 company/system

### Task 5: 编译 Scope 隔离（P2）

**Files:**
- Modify: `app/services/wiki/compiler.py` — 上下文注入按 scope 过滤
- Modify: `app/services/wiki/prompts.py` — 增加 scope 说明段

**Steps:**
1. `ingest_raw_file` 根据 raw.scope 确定可参考文章范围
2. 只读文章标记 `[只读]` 前缀
3. prompt 增加 scope 规则说明
4. `_apply_operations` 校验不越权修改

### Task 6: 晋升/降级流程（P3）

**Files:**
- Create: `app/services/wiki/promotion.py` — 晋升业务逻辑
- Modify: `app/views/knowledge_wiki.py` — 新增 promotion 端点
- Modify: `app/templates/knowledge/tw_wiki.html` — 晋升 UI

**Steps:**
1. 实现 `request_promotion` / `approve_promotion` / `reject_promotion`
2. 经理"快速拉取"（跳过审批直接执行）
3. 前端：右键菜单"晋升到..."、审批列表、红点通知
4. 降级同理

### Task 7: 跨部门分享（P3）

**Files:**
- Modify: `app/views/knowledge_wiki.py` — share 端点
- Modify: `app/templates/knowledge/tw_wiki.html` — 分享 UI

**Steps:**
1. "分享给..."弹窗（选部门/用户）
2. 创建 share_grant 记录
3. 查询过滤中加入 share_grant 条件
4. 树形列表中显示 `[分享|来源部门]` 标签

### Task 8: 去重检测（P4）

**Files:**
- Create: `app/services/wiki/dedup.py` — 去重逻辑
- Modify: `app/services/wiki/compiler.py` — 编译后触发检测

**Steps:**
1. 编译成功后异步调 Haiku 做相似度判断
2. 结果存入 article.duplicate_hint（JSON 字段）
3. 前端树形列表显示 ⚠️ 重复提示

---

## 11. 设计决策记录

| 问题 | 决策 | 理由 |
|------|------|------|
| 磁盘分目录 vs DB 过滤 | DB 字段过滤 | 实现简单，晋升/降级不动文件 |
| 部门经理看成员个人库 | 可以看，可以直接拉取 | 经理有管理职责 |
| 降级支持 | 支持 | 内容定位可能变化 |
| 跨部门共享 | 分享授权，不晋升到公司 | 避免公司级内容膨胀 |
| 个人库容量 | 不限制 | 先跑起来再说 |
| 前端导航 | 统一树形 + scope 标签 toggle | 比 tab 切换直观，不需上下文切换 |
| 去重处理 | 提醒不阻止 | 决策权留给人 |
