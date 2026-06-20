# GEO Monitor — 设计文档

**日期**: 2026-04-28  
**状态**: 设计完成，待实施

---

## 背景

Evertac 营销团队需要监测品牌在 AI 搜索引擎中的曝光情况。买家越来越多通过 ChatGPT、Perplexity 等 AI 引擎直接获取产品推荐，传统 SEO 不足以覆盖这个场景。

GEO（Generative Engine Optimization）监控工具帮助营销团队：
1. 了解 Evertac 在 AI 搜索中的被引用情况
2. 跨语言/市场对比提及率差异
3. 发现内容缺口，指导内容生产

---

## 架构

### 技术栈
- **集成方式**: PMA 新 Blueprint (`geo_monitor`)，复用现有登录、权限、Tailwind 模板
- **AI 调用**: Mac Mini 代理 `https://100.110.41.83:8317`，Bearer token 认证
- **搜索能力**: Anthropic 原生 `web_search_20250305` 工具（已验证可用）
- **数据库**: PMA 现有 PostgreSQL，新增 geo_* 表

### 调用流程

```
定时任务 / 用户触发
    ↓
生成各语言 Query 版本（Claude API）
    ↓
并行调用 Mac Mini 代理（Claude + web_search）
    ↓
Claude 解析结果（Evertac 是否出现、排名、情感）
    ↓
存入数据库
    ↓
前端展示
```

### Mac Mini 代理
- 地址: `https://100.110.41.83:8317`
- 认证: `Authorization: Bearer sgnas-pma`（或新建专用 token）
- 工具: `{"type": "web_search_20250305", "name": "web_search"}`

---

## 市场配置

系统级配置，管理员开启一次，所有 Query 自动覆盖：

| 市场 | 语言 | 状态 |
|------|------|------|
| CN | 简体中文 | MVP 开启 |
| EN | 英文 | MVP 开启 |
| MY | 马来文 | 第二阶段 |
| ID | 印尼文 | 第二阶段 |
| TH | 泰文 | 第二阶段 |
| VN | 越南文 | 第二阶段 |

---

## Query 工作流

1. 用户输入一个**中文意图**（如"数据中心应急通讯设备推荐"）
2. Claude 自动生成各已启用语言的自然语言查询版本
3. 各语言版本独立跑批，结果并排对比
4. 支持单独排除某市场（可选，默认全覆盖）

---

## 数据模型

```
geo_intent          # 用户输入的监控意图
  - id
  - title           # 中文意图描述
  - frequency       # 跑批频率: daily / weekly
  - enabled
  - created_at

geo_query           # AI 生成的各语言 query 版本
  - id
  - intent_id
  - market          # cn / en / my / id ...
  - query_text      # 实际发送给 AI 的问题
  - excluded        # 是否排除此市场

geo_result          # 每次跑批结果
  - id
  - query_id
  - run_at
  - mentioned       # true / false / indirect
  - rank            # 排名（null 表示未提及）
  - sentiment       # positive / neutral / negative
  - ai_response     # 完整 AI 回答
  - cited_urls      # 引用的网页 URL 列表（JSON）
  - raw_response    # 原始 API 返回
```

---

## 前端页面（4页）

### 1. 概览页 `/geo/`
- 指标卡：监控意图数、各市场本周提及率、较上周变化
- 趋势折线图：按市场分色，时间范围可选
- 最近跑批结果表：意图 × 市场 × 结果，支持查看详情

### 2. 查询管理页 `/geo/intents/`
- 意图列表：显示覆盖市场、频率、状态
- 新增/编辑表单：输入意图，选择排除市场（可选），设置频率
- 每条意图可展开查看各语言 Query 版本

### 3. 手动测试页 `/geo/test/`
- 输入任意意图
- 选择测试市场（默认全选）
- 实时调用，流式展示各市场结果
- 高亮 Evertac 提及位置，显示引用来源

### 4. 设置页 `/geo/settings/`
- 目标市场开关
- Mac Mini 代理配置（地址、token）
- 跑批时间配置

---

## 实施范围（MVP）

### 包含
- CN + EN 两个市场
- 手动触发跑批 + 定时任务（每天/每周）
- 概览、查询管理、手动测试、设置 4 个页面
- 结果存储与历史查询

### 不包含（第二阶段）
- SEO 排名监控
- SEA 语言扩展（MY/ID/TH/VN）
- 邮件/通知提醒
- 竞品对比分析

---

## 导航入口

位置：**产品分区 → 产品分析 之后**

```
产品分区：
  - 产品列表
  - 系统图
  - 产品分析（现有）
  - GEO 监控 🆕
  - 规格模板
  ...
```

---

## 权限

复用 PMA 现有权限体系：
- 营销相关角色可访问 GEO 模块
- 设置页仅管理员可访问
