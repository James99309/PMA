# 角色化仪表盘设计（AT Dashboard 按角色显示卡片 + KPI）

> 状态：设计稿，待用户确认后实施
> 日期：2026-06-10
> 背景：当前 AT 仪表盘对所有角色显示同一套 7 张卡（待办/KPI/销售漏斗/我的项目/我的报价/报销/工作日志）与同一套 KPI，全部面向销售。解决方案/产品经理、财务关注的内容完全不同。

## 一、现状（问题）

- `build_dashboard()`（`app/helpers/at_dashboard_helpers.py`）**不分角色，7 张卡数据全算**。
- `role_layout(user)` 存在，但只换顺序、不隐藏卡片，且 **`layout` 变量传进模板后从未被引用 → 实际是死代码**。模板 `main/at_dashboard.html` 写死 7 张卡固定顺序。
- KPI（`_build_kpis` / `_kpi_one_period`）固定 4 指标：销售额 / 植入额 / 新项目 / 新客户，所有角色一样。
- **没有「任务」「植入」独立卡片**（植入目前只是 KPI 里一个数字）。

## 二、目标

按角色显示**不同卡片 + 不同 KPI**。映射**写死在代码**（扩展 `role_layout`，真正接进模板；映射稳定，YAGNI，不做配置化）。

## 三、角色 → 卡片映射

| 角色组 | 角色 key | 显示卡片 | KPI 口径 |
|---|---|---|---|
| **销售（默认）** | sales, sales_manager, sm, sales_director, business_admin, channel_manager, 及未列出角色 | 待办 · KPI · 销售漏斗 · 我的项目 · 我的报价 · 报销 · 工作日志 | 销售口径（现状） |
| **解决方案经理** | solution_manager | 待办 · KPI(SM) · **任务** · **植入** · 工作日志 | 解决方案口径 |
| **产品经理** | product_manager | 待办 · KPI(PM) · **任务** · **植入** · 工作日志 | 产品口径 |
| **财务** | finance, finance_director, finace_director | 待办 · KPI(财务) · **报销**(全公司进度) · 工作日志 | 财务口径 |
| **总览** | ceo, admin | 全部卡片 | 全口径（现状 4 指标） |

- 「待办」「工作日志」所有角色保留（个人事务面板）。
- 解决方案/产品经理**不显示** 销售漏斗 / 我的项目 / 我的报价 / 报销。
- 财务的「报销」卡 = 全公司报销进度（非个人）。

## 四、角色 KPI 定义（均按 月/季/年 切换，沿用现有粒度）

### 销售（默认）/ 总览
维持现状：`{m}销售额 / 植入额 / 新项目 / 新客户`（带 target 同比）。

### 解决方案经理（solution_manager）
| 指标 | 取数 |
|---|---|
| 任务数 / 完成数 | `Task.assignee_id==我` 计数 + `status='completed'` 计数 |
| **植入产品金额** | `Quotation.implant_total_amount` 合计，范围 = **我创建的报价（owner_id==我）∪ 我审核确认的报价**（`QuotationConfirmationTask.assignee_id==我 AND status='confirmed'` 对应的 quotation），**按 quotation 去重** |
| 项目参与度（复合，4 个计数平铺） | 报价确认 `QuotationConfirmationTask(assignee=我, status='confirmed')` · 图纸 `SystemDiagram(owner_id=我)` · 报价制作 `Quotation(owner_id=我)` · 项目跟进 `Action(owner_id=我)` |

### 产品经理（product_manager）
> **负责产品 = 我管理的「产品分类」下的所有产品**，关联是分类级 `ProductCategory.manager_id==我`（产品分类管理页给每个分类指派 PM），**不是** `Product.owner_id`。`User.managed_categories` backref 可直接取我管理的分类。

| 指标 | 取数 |
|---|---|
| 任务数 / 完成数 | 同上 |
| **负责产品植入度** | `QuotationDetail.implant_subtotal` 合计，链路：`QuotationDetail.product_mn == Product.product_mn` → `Product.category_id ∈ 我管理的分类(ProductCategory.manager_id==我)`；可附「被植入次数」 |

### 财务（finance / finance_director / finace_director）
| 指标 | 取数 |
|---|---|
| 待审批报销数 | `Expense` 处于待财务审批/待支付状态的计数 |
| 本期报销总额 | `Expense` 本期金额合计（按结算货币）|
| 已支付 / 未支付额 | 已支付总额 vs 已批未付总额 |

## 五、新卡片规格

### 「任务」卡（解决方案经理 + 产品经理）
- 我的任务列表，状态 tab：进行中 / 待开始 / 待审核 / 已完成（对应 Task.effective_status）。
- 行：任务标题 · 所属项目 · 截止日 · 进度；点击进任务详情。
- 数据：`Task.assignee_id==当前用户`，非删除。

### 「植入」卡（按角色不同内容）
- **解决方案经理 = 「我的植入」（按报价单）**：行 = 报价号 · 客户 · 植入额 · 状态；范围 = 我创建 ∪ 我确认（与 KPI 植入额一致，去重）。
- **产品经理 = 「产品植入度」（我管理分类下的产品）**：行 = 产品名（或按分类汇总）· 被植入次数 · 植入总额；按植入总额降序。范围 = 我管理的分类（`ProductCategory.manager_id==我`）下的产品。可选按分类（基站/天线…）汇总展示。

## 六、架构改动

1. **`role_layout(user)` 升级**为单一事实源，返回：
   ```python
   {
     'cards': ['todo','kpi','task','implant','worklog'],  # 显示哪些卡 + 顺序
     'kpi_variant': 'solution',  # default|solution|product|finance|overview
   }
   ```
2. **`build_dashboard()` 按需计算**：只为 `cards` 里出现的卡构建数据（解决方案/产品经理不再算 funnel/projects/quotes/expense → 顺带提速）。
3. **模板 `at_dashboard.html` 接通 layout**：每张卡包一层 `{% if 'funnel' in layout.cards %}`…（或按 `layout.cards` 循环渲染卡片块）。废弃"写死 7 卡"。
4. **新增 builder**：`_build_tasks(user)`、`_build_implant(user, variant)`；KPI 增加 `_kpi_variant_*`（solution / product / finance），`_build_kpis` 按 `kpi_variant` 选择。
5. **新卡模板**：`components/at_dash_task_card.html`、`at_dash_implant_card.html`（复用现有 dash-card 视觉 + scope chip 风格）。

## 七、数据源（全部已核实存在）

| 用途 | 模型/字段 |
|---|---|
| 任务计数/完成 | `Task.assignee_id`, `status`('completed'), `completed_at`, `effective_status` |
| 产品经理负责产品 | `ProductCategory.manager_id`（分类级 PM）→ `Product.category_id`；`User.managed_categories` backref |
| 植入额（报价级） | `Quotation.implant_total_amount`, `owner_id` |
| 植入额（明细级，按产品/分类）| `QuotationDetail.implant_subtotal` + `product_mn` join `Product.product_mn` → `Product.category_id` → `ProductCategory.manager_id` |
| 报价确认 | `QuotationConfirmationTask.assignee_id`, `status`('confirmed'), `quotation_id` |
| 图纸绘制 | `SystemDiagram.owner_id`, `created_at` |
| 项目跟进 | `Action.owner_id`, `project_id`, `created_at` |
| 财务报销 | `Expense`（状态 + 金额 + 支付）|

## 八、注意事项

- **权限/数据范围**：所有"我的"口径用 `owner_id==user`；财务"全公司报销"沿用 `access_control` 报销特殊规则（财务可见全部）；不得越权。
- **性能**：按需计算后，经理/财务页比现状更快（少算 3-4 张销售卡）。
- **i18n**：新卡/新 KPI 文案当前先与现有 AT 页一致（硬编码中文），统一翻译留待 `feat/at-i18n` 分支批量处理（见 memory `project-at-pages-i18n-gap`）。
- **product_mn 字符串 join** 为弱关联：若同一产品历史料号变更可能漏算，可接受；后续如需精确可在明细落 product_id。

## 九、实施阶段

1. P1：`role_layout` 升级 + 模板接通（先用现有卡做显隐，验证销售/财务/经理看到的卡集合正确）。
2. P2：KPI 变体（solution/product/finance）+ `_build_kpis` 分流。
3. P3：新卡 `_build_tasks` / `_build_implant` + 模板。
4. P4：本地各角色实测（gxh=销售、解决方案/产品/财务测试账号）→ 提交 → 部署 CN。

## 十、测试

- 各角色登录看到的卡集合与本表一致；不该出现的卡确实不渲染（非仅隐藏）。
- KPI 数字与手工 SQL 抽样核对（任务完成数、植入额去重、产品经理 product_mn join）。
- 性能：经理/财务页 `build_dashboard` 不再触发 funnel/projects/quotes 查询。
