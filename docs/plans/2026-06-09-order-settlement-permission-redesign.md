# 订单/结算 权限模块重整（方案 A）

> 状态：设计稿，待用户确认角色分配后实施
> 日期：2026-06-09
> 背景：现有「订单结算」权限组命名与实际功能错配，且缺客户/采购订单的清晰划分。

## 一、现状盘点（问题）

| 配置页显示 | module_id | 实际 gate | 问题 |
|---|---|---|---|
| 订单管理 | `order` | 采购订单(purchase_order_routes) | 名不副实：以为客户订单，实为采购订单 |
| 结算管理 | `settlement` | 批价单结算单分页 + inventory 结算单列表/库存结算 | 语义模糊 |
| 库存管理 | `inventory` | 库存(inventory) | 基本正确 |
| 批价单管理 | `pricing_order` | 批价单(pricing_order_routes) | 正确 |
| 结算单管理 | `settlement_order` | **0 处使用** | 死模块 |
| （未注册） | `sales_order` | 客户订单(sales_order_routes) | 未注册模块 + 无角色配置 → 谁都看不到 |

关键技术事实：
- 批价单详情两个分页：批价单分页 ← `pricing_order` view；结算单分页 ← `can_view_settlement_tab()` → `check_permission('settlement_view')` → `has_permission('settlement','view')`。
- inventory.py 的结算路由（`settlement_list`/`settlement_detail` 查看类 + `create_settlement`/`execute_settlement`/`settle_product` 动作类）当前都挂 `settlement`。

## 二、目标分类（方案 A：不改权限模型，两个模块归一组当"两个勾选"）

| 显示名 | module_id | 控制 | 动作 |
|---|---|---|---|
| **客户订单** | `sales_order` | 客户订单查看/编辑 | 🆕 注册模块 + 配角色（代码已用，无需改路由） |
| **采购订单** | `order` | 采购订单查看/编辑 | ✏️ 改名（订单管理→采购订单），key 不变 |
| **批价单** | `pricing_order` | 批价单分页 | ✏️ 改名（批价单管理→批价单），规则不变 |
| **结算单** | `settlement` | **看结算单(view) + 做结算动作(create/edit)** —— 批价单结算单 tab、结算单列表、库存结算/执行结算 | ✏️ 改名（结算管理→结算单）；与批价单同组并排显示 |
| **库存管理** | `inventory` | 库存（**不含**结算动作） | 维持现状 |

> 决策更正(2026-06-10)：结算动作仍由「结算单(settlement)」权限管(view=看/create=做结算)，**不**移到库存管理。原方案 A 的"库存管理具备结算动作(B)"**取消**，inventory.py 结算路由保持挂 `settlement`，无需改代码。
| ~~结算单管理~~ | ~~`settlement_order`~~ | — | 🗑️ 删除死模块 |

"两个分页勾选"= 配置页里把 `pricing_order`(批价单) 与 `settlement`(结算单) **归到同一分组并排展示**，视觉等同两个勾选；底层仍是两个模块，**不动 RolePermission 模型**。

## 三、改动清单（三层）

### A. 权限模块注册表（`permission_modules` 表 / 种子）
1. 改名：`order` → 显示「采购订单 / Purchase Order」
2. 改名：`pricing_order` → 显示「批价单 / Pricing Order」
3. 改名：`settlement` → 显示「结算单 / Settlement Order」
4. 新增：`sales_order` → 「客户订单 / Sales Order」，同组、排序在采购订单之前
5. 删除/停用：`settlement_order`（死模块）
6. 分组排序：客户订单 → 采购订单 → 批价单 → 结算单 → 库存管理

### B. 代码（路由装饰器）
1. `sales_order_routes.py`：已用 `sales_order`，**无需改**。
2. `purchase_order_routes.py`：已用 `order`，**无需改**。
3. `pricing_order_routes.py`：已用 `pricing_order`，**无需改**。
4. `inventory.py`：**无需改**（决策更正）。结算路由(查看 settlement view / 动作 settlement create)全部保持挂 `settlement` 模块——「结算单」权限统管"看 + 做结算",符合用户最终意图。
5. 侧边栏 `at_sidebar.html`：客户订单已 gate `sales_order`、采购订单已 gate `order`，**无需改**。

### C. 角色权限数据（`role_permissions`）—— 由用户在「权限配置页」自行操作，不脚本化
- 结构层（A+B）完成后，配置页会出现正确的 5 个模块（客户订单/采购订单/批价单/结算单/库存管理）。
- **各角色勾选哪些模块/动作，由用户在权限配置页里配**（谁是销售→客户订单，谁是采购→采购订单，谁能看结算单，谁能做库存结算）。
- 注意现存遗留：`order` 此前被 sales 等多角色持有 view（沿用旧"订单管理"宽授权）。改名为「采购订单」后这些授权仍在，**需用户在配置页把非采购角色的采购订单权限取消**；`sales_order`（客户订单）新模块默认无人持有，由用户按需勾选。

## 四、实施与上线策略
1. 本地（pma_local，生产快照）先全套改完 + 实测：菜单显隐、各角色进出权限、批价单两分页、库存结算动作。
2. 模块注册表变更：用种子脚本/迁移（幂等，存在则改、缺则插）。
3. 角色数据变更：脚本幂等 upsert role_permissions；**变更前备份生产库**。
4. 部署：合 main → push → Gitea 同步 → update.sh；部署后核对各角色实际可见性。
5. 风险：生产权限改动影响所有用户可见范围，需逐角色核对；保留回滚（备份 + 脚本可逆）。

## 五、分工
- 代码/结构层（A 模块注册表 + B 路由）：由开发完成，使配置页呈现正确的 5 个模块。
- 配置层（C 角色权限）：由用户在权限配置页自行勾选；遗留的 `order` 宽授权需用户清理。
