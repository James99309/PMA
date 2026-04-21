# 工作积分系统设计文档

**日期**: 2026-04-18  
**状态**: 设计阶段  
**替代**: 旧产品积分系统（UserPointsLedger + Product.points_coefficient 等字段）

---

## 一、背景与目标

### 现有问题
现有积分体系绑定在**产品价值**上（报价单产品积分、PM分类积分、SE项目积分），无法覆盖知识贡献、协作、日常工作质量等软性价值，且只有销售/PM/SE三类角色受益。

### 新目标
建立**全员行为积分系统**，将员工日常工作行为量化为积分：
- 覆盖所有员工（不区分角色）
- 激励知识共享、业务推进、内容创作等多维行为
- 作为绩效参考的量化依据（后期支持等级体系、积分商城）

---

## 二、废弃范围

以下旧系统内容全部废弃：

### 数据模型
- `app/models/user_points_ledger.py` — `UserPointsLedger` 表
- `Product` 模型上的字段：`points_coefficient_override`、`citation_coefficient`、`citation_count`
- `Product` 计算属性：`points_coefficient`、`points`、`points_tier`

### 业务逻辑
- `app/helpers/product_points.py` — 全部删除（`sync_quotation_points`、`sync_pm_category_points`、`sync_se_project_points`）

### 路由
- `GET /api/v1/user/product-points-summary`
- `POST /api/products/<id>/coefficient`

### 前端
- 报价单详情页的积分显示（`tw_quotation_detail.html`）
- 导航栏积分动画的**数据来源**替换为新系统（动画本身保留）

---

## 三、数据模型

### 3.1 行为配置表 `points_behavior_config`

```sql
id              SERIAL PRIMARY KEY
behavior_code   VARCHAR(64) UNIQUE NOT NULL   -- 唯一标识: wiki_share, project_create...
behavior_name   VARCHAR(128) NOT NULL          -- 显示名称: 共享Wiki文章
category        VARCHAR(32) NOT NULL           -- 分类: knowledge/business/task/content
points          INTEGER NOT NULL DEFAULT 10    -- 基础积分值
daily_cap       INTEGER NULL                   -- 每日同类行为积分上限（NULL=无限制）
is_active       BOOLEAN NOT NULL DEFAULT TRUE  -- 启用/禁用
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP DEFAULT NOW()
```

**预设行为配置**（初始数据）：

| behavior_code | behavior_name | category | points | daily_cap |
|---|---|---|---|---|
| `wiki_share` | 共享Wiki文章 | knowledge | 30 | 90 |
| `wiki_cited` | Wiki文章被引用 | knowledge | 10 | 50 |
| `project_create` | 新建项目 | business | 50 | — |
| `project_stage_advance` | 推进项目阶段 | business | 20 | — |
| `customer_create` | 发现新客户 | business | 40 | — |
| `daily_log_submit` | 提交工作日志 | content | 10 | 10 |
| `task_complete` | 完成任务 | task | 15 | — |

### 3.2 积分流水表 `points_transaction`

```sql
id            SERIAL PRIMARY KEY
user_id       INTEGER NOT NULL REFERENCES users(id)
behavior_code VARCHAR(64) NOT NULL REFERENCES points_behavior_config(behavior_code)
source_type   VARCHAR(64)    -- 来源对象类型: wiki_article / project / customer / log / task
source_id     INTEGER        -- 来源对象ID
points        INTEGER NOT NULL
memo          VARCHAR(256)   -- 说明文本，如"推进项目[客户A]至方案阶段"
year          SMALLINT NOT NULL
month         SMALLINT NOT NULL
created_at    TIMESTAMP DEFAULT NOW()
```

索引：`(user_id, year, month)`、`(year, month)` 用于排行榜聚合

### 3.3 用户积分汇总缓存 `user_points_summary`

```sql
user_id            INTEGER NOT NULL REFERENCES users(id)
year               SMALLINT NOT NULL
month              SMALLINT NOT NULL  -- 0=年度汇总，1-12=月度
total_points       INTEGER NOT NULL DEFAULT 0
behavior_breakdown JSONB              -- {"knowledge": 680, "business": 540, ...}
updated_at         TIMESTAMP DEFAULT NOW()
PRIMARY KEY (user_id, year, month)
```

异步更新（每次写入 `points_transaction` 后触发缓存刷新），避免排行榜实时全表聚合。

---

## 四、自动触发钩子

行为积分通过挂载在现有业务逻辑上的**服务函数**自动触发，无需用户操作。

### 触发点规划

| 触发位置 | 行为code | 触发时机 |
|---|---|---|
| `KnowledgeWikiArticle` 创建且 scope≥company | `wiki_share` | 文章晋升为 company/system scope 时 |
| `KnowledgeWikiArticle.outbound_refs` 被写入 | `wiki_cited` | 其他文章引用本文章时 |
| `Project` 创建 | `project_create` | 新建项目时 |
| `Project.stage` 更新 | `project_stage_advance` | 阶段向前推进时（非回退） |
| `Company/Contact` 创建 | `customer_create` | 新建客户/联系人时 |
| 日志提交 | `daily_log_submit` | 每日工作日志提交时 |
| `Task` 状态变更为 completed | `task_complete` | 任务标记完成时 |

### 积分服务模块

新建 `app/services/points_service.py`：

```python
def award_points(user_id, behavior_code, source_type=None, source_id=None, memo=None):
    """
    核心积分发放函数，所有触发点统一调用。
    - 检查 daily_cap（当日同类积分是否超上限）
    - 写入 points_transaction
    - 异步刷新 user_points_summary 缓存
    """
```

---

## 五、前端设计

### 5.1 积分页面 `/points/`

单页两栏布局，全员可访问：

```
┌─────────────────────────────────────────────────────┐
│  工作积分                    [本月] [季度] [本年]    │
├──────────────────────┬──────────────────────────────┤
│  🏆 积分排行榜        │  📋 我的积分明细              │
│                      │                              │
│  #1  张三   2,840    │  本月总计: 1,950 pts          │
│  #2  李四   2,210    │  排名 #3 / 42人               │
│  #3  [你]   1,950 ◀ │  知识 680 | 业务 540          │
│  #4  王五   1,720    │  任务 430 | 内容 300          │
│  #5  赵六   1,580    │  ─────────────────────────  │
│  ...                 │  今天   +20  推进项目[A]阶段  │
│                      │  昨天   +15  Wiki被引用 ×3   │
│  [全部] [销售] [技术] │  昨天   +10  提交日志         │
│  [市场] [运营]       │  3天前  +50  新建项目[B]      │
│                      │  [加载更多...]               │
└──────────────────────┴──────────────────────────────┘
```

**排行榜**（左栏）：
- 全员可见：总分 + 排名
- 不显示行为明细（隐私保护）
- 支持部门筛选
- 周期切换：本月 / 本季度 / 本年

**个人流水**（右栏）：
- 仅显示当前登录用户自己的明细
- 按分类小计（知识/业务/任务/内容）
- 流水按时间倒序，分页加载

### 5.2 导航栏积分动画

- 保留现有动画实现
- **数据来源**替换为新系统：从 `user_points_summary` 读取当前用户本月总分
- 获得积分时触发 `+N ✨` 飘起动画（现有机制对接新 API）

### 5.3 管理员配置页 `/admin/points-config/`

入口：系统配置菜单下

```
┌──────────────────────────────────────────────────────┐
│  积分行为配置                          [+ 新增行为]   │
├─────────────┬──────────┬──────┬───────┬──────────────┤
│ 行为名称     │ 分类     │ 积分 │ 日上限 │ 操作         │
├─────────────┼──────────┼──────┼───────┼──────────────┤
│ 共享Wiki文章 │ 知识贡献  │  30  │  90   │ [编辑] [禁用]│
│ Wiki被引用   │ 知识贡献  │  10  │  50   │ [编辑] [禁用]│
│ 新建项目     │ 业务推进  │  50  │   —   │ [编辑] [禁用]│
│ 推进项目阶段 │ 业务推进  │  20  │   —   │ [编辑] [禁用]│
│ 发现新客户   │ 业务推进  │  40  │   —   │ [编辑] [禁用]│
│ 提交工作日志 │ 内容创作  │  10  │  10   │ [编辑] [禁用]│
│ 完成任务     │ 任务达成  │  15  │   —   │ [编辑] [禁用]│
└─────────────┴──────────┴──────┴───────┴──────────────┘
```

- 行内编辑：点击编辑弹出模态框修改积分值/日上限
- 禁用行为：保留历史数据，新行为不再触发
- 新增行为：填写 behavior_code（唯一）、名称、分类、积分、日上限

---

## 六、积分周期与清零规则

| 周期 | 规则 |
|---|---|
| **记录粒度** | 按月记录（`year` + `month`） |
| **查看维度** | 本月 / 本季度（3个月汇总）/ 本年（12个月汇总） |
| **年度清零** | 每年1月1日，积分统计从0重新开始 |
| **历史归档** | 历史年度数据保留在 `points_transaction` 中，可查询往年数据 |

---

## 七、实施阶段

### Phase 1（核心）
1. 废弃旧积分系统（清理模型、路由、模板）
2. 数据库迁移（新建三张表 + 预置配置数据）
3. `points_service.py` 核心服务
4. 各触发点挂载钩子
5. 积分页面（排行榜 + 个人流水）
6. 导航栏数据源替换

### Phase 2（管理）
7. 管理员配置页

### Phase 3（后期）
- 等级体系（积分阈值解锁等级）
- 积分商城（积分兑换奖励）

---

## 八、技术注意事项

1. **防刷分**：`daily_cap` 在 `award_points` 中通过查询当日同类流水总和来判断
2. **幂等性**：同一 `source_type + source_id + behavior_code` 组合只允许触发一次（唯一约束或插入前检查）
3. **异步缓存**：`user_points_summary` 更新不阻塞主业务流程，允许短暂不一致
4. **权限**：积分配置页仅 `admin` 角色可访问；个人流水仅本人可见；排行榜全员可见
