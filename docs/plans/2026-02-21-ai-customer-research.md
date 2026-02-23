# AI 客户网络调研 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在客户详情页添加 AI 调研功能，自动搜索客户公司的网络公开信息（公司概况、关键人物、在建项目、合作伙伴、风险预警），以结构化方式展示给销售人员。

**Architecture:** 后端使用 DuckDuckGo Search 获取搜索结果，再通过 Anthropic Claude API 将原始搜索结果结构化为 JSON。数据缓存在 Company 表的 JSON 字段中，30天自动过期刷新。前端在客户详情页 `full_width` slot 中展示可折叠的调研卡片组。

**Tech Stack:** `duckduckgo-search` (搜索), Anthropic Claude API (结构化), Flask JSON API (后端), Alpine.js + Tailwind (前端)

---

## Task 1: 安装搜索依赖

**Files:**
- Modify: `requirements.txt`

**Step 1: 添加 duckduckgo-search**

在 `requirements.txt` 末尾添加：
```
duckduckgo-search>=7.0.0
```

**Step 2: 安装依赖**

```bash
pip install duckduckgo-search
```

**Step 3: 验证安装**

```bash
python3 -c "from duckduckgo_search import DDGS; print('OK')"
```

---

## Task 2: 数据库迁移 — Company 表添加字段

**Files:**
- Modify: `app/models/customer.py` (Company 模型, ~Line 68 后添加)
- Create: `migrations/versions/e6f7a8b9c0d1_add_ai_research_fields.py`

**Step 1: 修改 Company 模型**

在 `app/models/customer.py` 的 Company 类中，`notes` 字段之后添加：
```python
    # AI 网络调研数据
    ai_research_data = db.Column(db.JSON, nullable=True)
    ai_research_updated_at = db.Column(db.DateTime, nullable=True)
```

**Step 2: 创建迁移文件**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db migrate -m "add ai research fields to companies"
```

**Step 3: 检查生成的迁移文件**

确认 upgrade() 包含：
```python
op.add_column('companies', sa.Column('ai_research_data', sa.JSON(), nullable=True))
op.add_column('companies', sa.Column('ai_research_updated_at', sa.DateTime(), nullable=True))
```

**Step 4: 本地执行迁移**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db upgrade
```

---

## Task 3: 创建 AI 调研服务

**Files:**
- Create: `app/services/ai_research_service.py`

**核心逻辑：**
1. `search_company(company_name)` — 用 DuckDuckGo 搜索 3-4 个维度的查询
2. `structure_with_ai(company_name, raw_results)` — 调用 Claude 将原始搜索结果结构化
3. `run_research(company_id)` — 编排完整流程，存入数据库

**AI 结构化输出的 JSON Schema：**
```json
{
  "company_profile": {
    "founded": "string",
    "headquarters": "string",
    "positioning": "string",
    "main_business": ["string"],
    "revenue": "string",
    "strategy": "string"
  },
  "executives": [
    {"name": "string", "title": "string", "background": "string", "risk_tag": "string|null"}
  ],
  "active_projects": [
    {"name": "string", "amount": "string", "type": "string", "partner": "string", "status": "string", "detail": "string"}
  ],
  "partners": {
    "general_contractors": ["string"],
    "ecosystem": ["string"],
    "key_customers": ["string"]
  },
  "risk_alerts": [
    {"level": "high|medium|low", "content": "string", "date": "string"}
  ],
  "sales_suggestions": ["string"]
}
```

**搜索查询策略（4次搜索）：**
1. `"{公司名}" 公司简介 业务范围 主营业务` — 基本面
2. `"{公司名}" 最新项目 中标 签约 2025 2026` — 项目信息
3. `"{公司名}" 高管 管理层 董事 总裁` — 关键人物
4. `"{公司名}" 风险 诉讼 处罚 负面 舆情` — 风险预警

**实现要点：**
- 复用 `ai_analysis_service.py` 的 Anthropic API 调用模式（headers, payload 格式）
- 搜索使用 `DDGS().text(query, max_results=8)` 每次取8条
- AI 调用 timeout=60s（内容较多需要更长时间）
- 错误处理：搜索失败不中断，AI 调用失败返回已有搜索结果

---

## Task 4: 添加 API 端点

**Files:**
- Modify: `app/views/customer.py`

**新增 2 个端点：**

### 4.1 获取缓存数据
```
GET /customer/api/company/<int:company_id>/ai-research
```
- 权限：`@permission_required('customer', 'view')`
- 返回：`{success, data: {research_data, updated_at, is_stale}}`
- `is_stale = True` 当 `updated_at` 距今 > 30 天

### 4.2 触发调研（同步）
```
POST /customer/api/company/<int:company_id>/ai-research
```
- 权限：`@permission_required('customer', 'view')`
- 调用 `ai_research_service.run_research(company_id)`
- 返回：`{success, data: {research_data, updated_at}}`
- 预计耗时 10-20秒（4次搜索 + 1次 AI 调用）

---

## Task 5: 前端集成 — tw_view.html

**Files:**
- Modify: `app/templates/customer/tw_view.html`

**位置：** `full_width` slot（两栏布局之上，参考 `tw_detail_layout.html:246`）

**实现要点：**
- 使用 Alpine.js `x-data` 管理状态（与页面已有的 Alpine 保持一致）
- 页面加载时调用 GET API 获取缓存数据
- 3种状态：空状态 / 加载中 / 展示结果
- 30天过期时自动调用 POST API 刷新

**Alpine.js 数据模型：**
```javascript
{
  state: 'idle',        // idle | loading | loaded | empty
  data: null,           // JSON research data
  updatedAt: null,      // ISO datetime string
  isStale: false,       // > 30 days

  init() { this.fetchCached() },
  fetchCached() { /* GET api */ },
  startResearch() { /* POST api */ },
  toggleSection(name) { /* 折叠/展开 */ },
}
```

**UI 组件（从原型移植）：**
1. 空状态卡片（虚线边框 + "开始 AI 调研" 按钮）
2. 加载状态（骨架屏 + 步骤文字）
3. 6个可折叠信息卡片：公司概况、关键人物、在建项目、合作伙伴、风险预警、AI 销售建议
4. 风险预警和合作伙伴并排两栏
5. 风险预警默认展开，其他默认收起

**重要：** Header 区域的 AI 调研按钮通过 `extra_actions` 参数添加，不修改 `tw_detail_layout.html` 通用组件。

---

## Task 6: Header 按钮集成

**Files:**
- Modify: `app/templates/customer/tw_view.html` (tw_detail_layout 调用处, ~Line 161)

在 `tw_detail_layout()` 的 `extra_actions` 参数中添加 AI 调研按钮：
```python
extra_actions=[
    {
        'show': true,
        'label': _('AI 调研'),
        'onclick': "document.querySelector('[x-data]').__x.$data.startResearch()",
        'icon': 'psychology',
        'color': 'info'
    }
]
```

注意：此按钮仅在 `state == 'empty'` 时需要，已有数据时由缓存逻辑管理。具体显示/隐藏逻辑由 Alpine.js 控制。

---

## Task 7: 国际化

**Files:**
- Modify: `app/translations/en/LC_MESSAGES/messages.po`

需要翻译的文本：
- `AI 网络调研` → `AI Web Research`
- `尚未进行网络调研` → `No web research yet`
- `开始 AI 调研` → `Start AI Research`
- `公司概况` → `Company Overview`
- `关键人物` → `Key Executives`
- `在建/近期项目` → `Active Projects`
- `合作伙伴` → `Partners`
- `风险预警` → `Risk Alerts`
- `AI 销售切入建议` → `AI Sales Suggestions`
- `AI 正在调研中...` → `AI researching...`
- `数据已超过30天，正在自动刷新...` → `Data is over 30 days old, auto-refreshing...`
- `更新于` → `Updated`
- `天前` → `days ago`
- `刚刚` → `just now`
- `高风险` → `High Risk`
- `中风险` → `Medium Risk`

编译：
```bash
pybabel compile -d app/translations
```

---

## 实现顺序

```
Task 1 (依赖安装)
  └→ Task 2 (数据库迁移)
      └→ Task 3 (核心服务)
          └→ Task 4 (API 端点)
              └→ Task 5 + 6 (前端集成)
                  └→ Task 7 (国际化)
```

## 注意事项

- **不需要** WebSocket 或 SSE — 使用同步 HTTP 请求 + 前端 loading 状态
- **不修改**通用组件 (`tw_detail_layout.html`, `tw_info_card.html` 等)
- DuckDuckGo 搜索**免费无需 API key**，但有频率限制，重度使用需考虑缓存策略
- AI 调用使用已有的 `ANTHROPIC_API_KEY` 环境变量
- 30天缓存阈值可在服务层配置为常量
