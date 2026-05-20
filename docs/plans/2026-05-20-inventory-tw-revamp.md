# 库存与结算系统 Tailwind 重构计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 以批价单为唯一结算入口、以新版 PO/Shipment 为唯一订单入口，把"库存"做成 Tailwind 化的、按公司分类的、入/出库流水可追溯到业务单据的独立模块。同时把无业务价值的老 `Settlement` / `/inventory/orders` 整套清掉，SN 改造为售后追溯工具。

**Architecture:** 数量账（核心）+ SN 账（售后追溯）双账分离。库存 = `(company_id, product_id)` 唯一。所有变动经 `InventoryTransaction` 流水化，带 `reference_type` + `reference_id` 反查业务单据。

**Tech Stack:** Flask + SQLAlchemy + PostgreSQL 17 + Alembic + Tailwind CSS + Alpine.js

**Branch:** `feature/order-shipment-chain`（直接在订单分支上继续，不另开分支 — 两边强耦合）

**范围排除:**
- 不动 `SettlementOrder` / `SettlementOrderDetail`（业务真在用 46 单 319 行，只改入口位置）
- 不重写已有的 Tailwind PO / Shipment 页面
- 不做 SN 出库追踪（用户明确不需要）

---

## Settled Decisions

| # | Decision | Choice |
|---|---|---|
| 1 | 库存导入语义 | 数量 = 绝对值（adjustment 语义） |
| 2 | UI 设计方式 | 沿用现有 Tailwind 风格，仅 2 张关键页画 mockup |
| 3 | 执行节奏 | 分批 UAT（Step 2 / 4 / 6 / 12 各一次 checkpoint） |
| 4 | SN 注册时机 | 创建发货单时写入（直接 `in_stock`） |
| 5 | SN 字符串去重 | 全局唯一（沿用现有 unique 约束） |
| 6 | `Product.has_serial_number` 默认 | True |
| 7 | SN 减库存联动 | 不联动，SN 永久保留 |

---

## Final Business Model

```
入库来源（增加 inventory.quantity）
─────────────────────────────────────
• 备货 PO 验收            → 厂商仓库       (existing, no change)
• 客户订单签收            → 客户仓库       (existing, no change)
• 期初导入 Excel          → 任意公司       (NEW, Task 4)
• 手动入库/调整           → 任意公司       (backend exists, NEW UI in Task 2)

出库来源（减少 inventory.quantity）
─────────────────────────────────────
• 批价结算单标 settled    → 目标公司仓库   (existing API, NEW entry in Task 6)
• 手动出库/调整           → 任意公司       (backend exists, NEW UI in Task 2)

SN 写入（与库存数量独立）
─────────────────────────────────────
• 创建发货单且产品 has_serial_number=True 时
  → 自动写入 product_serial_numbers 表
  → status='in_stock'，永不更新（Task 2.6 + Task 7）
```

---

## Existing Code Audit — 删除清单

### 数据模型

| File | Class | Action |
|---|---|---|
| `app/models/inventory.py:60` | `Settlement` | Delete |
| `app/models/inventory.py:89` | `SettlementDetail` | Delete |

### 路由（`app/routes/inventory.py`）

| Route | Function | Action |
|---|---|---|
| `/settlement` | `settlement_list` | Delete |
| `/settlement/create` | `create_settlement` | Delete |
| `/settlement/<id>` | `settlement_detail` | Delete |
| `/inventory_settlement/<id>` | `inventory_settlement` | Delete |
| `/settlement/<id>/execute` | `execute_settlement` | Delete |
| `/api/settlement/<id>` | `api_settlement` | Delete |
| `/settlement_orders` | `settlement_order_list` | Delete |
| `/settlement_process/<order_number>` | `settlement_process` | Delete |
| `/settlement_orders/export` | `export_settlements` | Move to pricing_order module |
| `/api/settlement_orders/filter` | filter | Delete |
| `/settlement_detail/<order_number>` | detail | Delete |
| `/orders` | `order_list` | Delete |
| `/orders/create` | `create_order` | Delete |
| `/orders/<id>` etc (10 routes) | order CRUD | Delete all |
| `/add_stock` | `add_stock`（老） | Delete |
| `/add_inventory_bulk` | bulk add | Delete |
| `/api/settle_product` | 旧 API | Delete |
| `/api/settle_product_to_company` | 新 API | **保留**，迁到批价单调用 |
| `/stock_action` | 入/出/调整 | **保留**，接新 UI |
| `/stock` / `/stock/<id>` | 列表/详情 | **重做** for Tailwind |
| `/api/stock/filter` | 筛选 | 保留 |

### Helper（`app/utils/inventory_helpers.py`）

| Function | Action |
|---|---|
| `update_inventory()` | **保留，核心** |
| `process_settlement()` | Delete |
| `generate_settlement_number()` | Delete |
| `generate_order_number()` | Delete |
| `get_inventory_status()` | Keep |
| `calculate_order_totals()` | Delete |

### 模板

| Template | Action |
|---|---|
| `create_settlement.html` | Delete |
| `settlement_detail.html` | Delete |
| `settlement_list.html` | Delete |
| `settlement_order_list.html` | Delete |
| `settlement_order_rows.html` | Delete |
| `settlement_process.html` | Delete |
| `settlement_rows.html` | Delete |
| `stock_settlements.html` | Delete |
| `order_list.html` | Delete |
| `order_detail.html` | Delete |
| `create_order.html` | Delete |
| `edit_order.html` | Delete |
| `add_stock.html` | Delete |
| `add_inventory.html` | Delete |
| `stock_list.html`（Bootstrap） | Delete |
| `tw_purchase_order_*.html` | Keep |

### 其他文件清理

| Location | Content |
|---|---|
| `app/views/customer.py:1452, 1612, 3553` | `Settlement.query.filter_by(company_id=...)` 级联删除 — 删除该代码块 |
| `app/templates/base.html:402, 423` | 导航菜单"订单管理"项 — 删 |
| `app/templates/components/tw_nav_menu.html:120` | 同上 — 删 |
| `app/permissions.py` | 检查 settlement 权限码，合并到 pricing_order |

---

## Tasks

### Task 1: 测试数据快照 + 清理脚本就位

**Files:**
- Create: `scripts/temp/snapshot_inventory_pre_refactor.sql`
- Create: `scripts/temp/reset_inventory_data.sql`

**Acceptance:**
- 快照 SQL 能完整导出 `inventory` + `inventory_transactions` + `settlements` + `settlement_details` + `product_serial_numbers` 当前数据到一个 .dump 文件
- 重置 SQL 跑完后这五张表 row count = 0
- 快照 + 重置可恢复回原状（来回各一次验证）

---

### Task 2: Tailwind 库存基础页（基础 CRUD）

**Files:**
- Create: `app/templates/inventory/tw_stock_list.html`
- Create: `app/templates/inventory/tw_company_inventory.html`
- Create: `app/templates/components/tw_stock_adjust_modal.html`
- Modify: `app/routes/inventory.py` — 新增路由 `/inventory/tw_stock`、`/inventory/tw_company/<id>`

**Acceptance:**
- `/inventory/tw_stock` 显示按公司分组库存，支持搜索/筛选公司/低库存预警
- 单公司详情页显示库存表格，每行有 入库 / 出库 / 设值 三个按钮
- 调整操作复用现有 `/stock_action` API（已就绪）
- 与老 `/inventory/stock` 并存（灰度阶段）

**Checkpoint:** UAT 1 — 让用户验证 UI 风格 / 调整流程后再进 Task 3

---

### Task 2.6: 发货时 SN 自动写入修复

**Files:**
- Modify: `app/routes/shipment_routes.py` (~line 881)

**Acceptance:**
- 创建带 SN 的发货单后，`product_serial_numbers` 表新增对应记录
- 字段关联：`shipment_id` + `sales_order_id` + `customer_id` + `product_id`
- `status = 'in_stock'`，`warehouse_in_date = now()`
- 已存在的 SN 字符串触发唯一约束报错（拒绝重复）

---

### Task 3: 库存流水页 + reference 反向链接

**Files:**
- Create: `app/templates/inventory/tw_transactions.html`
- Add: `app/routes/inventory.py::api_transactions`

**Acceptance:**
- 流水列表分页显示所有 `InventoryTransaction`，支持公司/产品/时间范围/类型筛选
- `reference_type='order'` → 链到 `/purchase-order/<id>`
- `reference_type='shipment'` → 链到 `/shipment/<id>`
- `reference_type='settlement'` → 链到对应批价单/结算单详情
- `reference_type='import'` → 显示"期初导入 batch #N"
- `reference_type='manual'` → 显示操作人 + 备注

---

### Task 3.5: 库存详情页"查看 SN"按钮

**Files:**
- Modify: `app/templates/inventory/tw_company_inventory.html`

**Acceptance:**
- 每行库存若 `product.has_serial_number=True` 且该库存关联 SN 记录数 > 0，显示"SN 清单"按钮
- 点击跳转 `/serial-numbers?inventory_id=<id>` 显示该库存关联的 SN（Task 11 提供页面）

---

### Task 4: Excel 导入工具

**Files:**
- Create: `app/templates/inventory/tw_inventory_import.html`
- Add: `app/routes/inventory.py::import_preview, import_commit, export_template`

**Acceptance:**
- `/inventory/tw_import` 显示上传页 + "下载模板"
- 上传 .xlsx 调 `import_preview`，返回三色分组 JSON：
  - 成功（产品 MN 匹配、公司匹配、数量合法）
  - 警告（已有库存 → 显示当前 → 目标值）
  - 失败（MN 找不到 / 公司找不到 / 数量非法），附行号 + 原因
- 预览页表格展示，三色高亮
- 用户点"确认导入" → `import_commit` 在单事务中写入
- 每行调 `update_inventory(transaction_type='adjustment', reference_type='import', reference_id=batch_id)`
- 流水描述：`期初导入 batch #N`

**Checkpoint:** UAT 2 — 用真实 Excel 跑一次导入

---

### Task 5: 客户公司详情页加库存 Tab

**Files:**
- Modify: `app/templates/customer/tw_view.html`（新加 tab）
- Modify: `app/views/customer.py`（tab 数据 fetch）

**Acceptance:**
- 客户公司详情页多一个"库存" tab
- 显示该公司下所有库存（沿用 Task 2 的 `tw_company_inventory.html` 组件，作为 partial 嵌入）

---

### Task 6: 批价单详情页"发起结算"卡片

**Files:**
- Modify: `app/templates/pricing_order/{pricing_detail_page}.html`（待 Task 6 开始时定位）
- Modify: `app/routes/pricing_order_routes.py` 详情视图

**Acceptance:**
- 批价单状态 = `approved` 时，详情页显示"待结算明细"卡片
- 每个 `SettlementOrderDetail` 一行，状态徽章：待结算 / 部分结算 / 已结算
- 待结算 / 部分结算的行有"选目标仓库"下拉 + "发起结算"按钮
- 点击 → 模态确认 → 调现有 `POST /inventory/api/settle_product_to_company`
- 成功后局部刷新该行状态

**Checkpoint:** UAT 3 — 完整结算路径走通

---

### Task 7: `Product.has_serial_number` 字段 + UI

**Files:**
- Modify: `app/models/product.py`（add column）
- Create: `migrations/versions/xxx_add_product_has_serial_number.py`
- Modify: `app/templates/product/{edit_page}.html`（checkbox）
- Modify: `app/templates/inventory/tw_purchase_order_detail.html`（发货模态：按标记联动 SN 输入显示）

**Acceptance:**
- 产品编辑页有"按 SN 管理"checkbox，默认 True
- 创建发货单时，若产品 `has_serial_number=False`，SN 输入区完全隐藏
- 老产品全部默认为 True（无须手动改）

---

### Task 8: 切流量 — 导航菜单更新

**Files:**
- Modify: `app/templates/base.html`
- Modify: `app/templates/components/tw_nav_menu.html`

**Acceptance:**
- 老菜单"订单管理"、"结算单管理"完全去掉
- 新菜单：库存 → 库存列表 / 流水 / 导入 / 序号管理器
- 旧路径仍可访问（Task 9 才删）

---

### Task 9: 代码删除

**Files:**
- Delete: `app/models/inventory.py::Settlement`、`SettlementDetail`
- Delete: `app/utils/inventory_helpers.py::process_settlement, generate_settlement_number, generate_order_number, calculate_order_totals`
- Delete: 老路由（共 21 个，见前述 audit 表）
- Delete: 老模板（14 个，见 audit 表）
- Modify: `app/views/customer.py:1452, 1612, 3553` 删除 `Settlement.query.filter_by` 级联代码块

**Acceptance:**
- `grep -rn 'class Settlement\b' app/` → 0 hit（排除 SettlementOrder / SettlementOrderDetail / SettlementOrderStatus）
- 服务启动无 ImportError / NameError
- 旧 URL `/inventory/orders`、`/inventory/settlement`、`/inventory/settlement_orders` 全部 404
- 全 grep `url_for('inventory.order_list'|'inventory.settlement_list'|...)` → 0 hit

---

### Task 10: 数据库迁移 + 测试数据清空

**Files:**
- Create: `migrations/versions/xxx_drop_legacy_settlement_tables.py`

**Acceptance:**
- `alembic upgrade head` 成功
- `\dt settlements settlement_details` → not exist
- `scripts/temp/reset_inventory_data.sql` 准备好（生产部署前手动跑）

---

### Task 11: 序号管理器 — 列表页

**Files:**
- Create: `app/templates/serial_number/tw_list.html`
- Create: `app/routes/serial_number_routes.py`（含蓝图注册）
- Modify: `app/__init__.py`（注册新蓝图）

**Acceptance:**
- `/serial-numbers/` 显示所有 SN（分页 + 模糊搜索 SN/产品/客户 + 日期过滤）
- 列：SN | 产品 | 客户公司 | 发货单 | 发货日期 | 状态
- 支持 query param `?inventory_id=` 过滤（给 Task 3.5 用）

---

### Task 12: 序号管理器 — 详情页

**Files:**
- Create: `app/templates/serial_number/tw_detail.html`
- Add: `app/routes/serial_number_routes.py::detail_view`

**Acceptance:**
- `/serial-numbers/<serial_number>` 显示完整履历卡片
- 内容：
  - 产品 / 当前所属公司 / 状态
  - 发货信息：发货单链接 + 日期 + 物流单号 + 签收日期
  - 来源订单：客户订单链接 + 采购订单链接（若可追） + 供应商
  - 质保信息（若有）
- 全部只读 + 关联单据链接可点

**Checkpoint:** UAT 4 — 全部新功能就位

---

### Task 13: 全链路 UAT + 回归

**Files:** N/A

**Acceptance:**
- 走通主流程：SO → 需求池 → PO → 供应商确认 → 测试报告 → 发货（含 SN）→ 签收 → 自动验收 → 批价审批 → 结算 → 库存扣减
- 走通：期初 Excel 导入 → 库存调整 → SN 查询
- 异常：删除发货回滚 `shipped_quantity` / 撤销 PO 回滚 `procured_quantity`
- 老 URL 全 404，新 UI 全部到位
- `pma_order_test` 跑完无报错

---

## Risk Points

1. `customer.py` 三处 `Settlement.query.filter_by(company_id=...).delete()` — 删除公司时连带删除老结算单的逻辑，直接删除代码块，无替代（SettlementOrder 由批价单流程管理）
2. `permissions.py` 可能有专用 `settlement` 权限码，需合并到 `pricing_order` 权限，避免角色冲突
3. 老 `/inventory/orders` 创建过 7 条 `PurchaseOrder` 数据 — **保留数据**，新版 PO 列表能看到，只删 UI 入口
4. Step 9 大批删除前，跑一次完整 `grep -rn "url_for('inventory.\(order\|settlement\)" app/` 确认无残留模板引用
5. 部署到 CN/SG NAS 时，迁移 + 数据清空脚本两侧都要跑
6. 老 `/inventory/orders` 数据库表 = `purchase_orders` (与新 PO 同表)，删除路由不会删数据
7. 现有 `pma_order_test` 库 33 行测试库存数据会保留到 Task 10 才清

---

## Deployment Order

```
CN NAS:
  1. git pull (拿到所有 task commits)
  2. flask db upgrade (跑 Task 7 + Task 10 的 migrations)
  3. 重启 docker
  4. 跑 scripts/temp/reset_inventory_data.sql（按需）

SG NAS:
  同 CN NAS 流程
```

---

## Sub-Skills Required

- `superpowers:test-driven-development` — Tasks 2/3/4/6/11/12 需要写测试（至少冒烟测试）
- `superpowers:verification-before-completion` — 每个 Task 完成前跑 acceptance criteria
- `huashu-design` — Task 4 / Task 6 之前出 2 张 mockup（可选）
