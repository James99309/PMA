# 批价单 AT 化改造设计

- 日期：2026-06-27
- 状态：设计已确认（原型已验收：布局/元素/功能对齐）
- 原型：`scratchpad/pricing_order_at_prototype.html`（仅布局示意）

## 1. 目标

把批价单从现有的「自定义 Excel 表格编辑页」(`pricing_order/tw_edit.html`) **完全替换**为 **AT 风格的查看+编辑一体页**，观感与 AT 报价单详情页 (`quotation/at_view.html`) 一致：

- 顶部 Hero（单号 + 状态 pill + 操作区：查看/编辑切换、打印、审批流程、同意/驳回）
- 两个 tab：**批价单 / 结算单**
- 每个 tab 内三个选区，随 tab 切换：
  1. **基本信息选区**（批价 tab：项目/经销商/报价单/直签/工厂提货/批价日期；结算 tab：结算公司/结算单号/结算日期）
  2. **毛利 KPI 选区**（批价 tab：批价总额/总折扣率/市场价合计/行数；结算 tab：结算总额/结算折扣率/毛利/毛利率）
  3. **明细表**（AT 明细组件样式）
- 旧 `tw_edit.html` 下线。

## 2. 确认的能力裁剪（来自需求确认）

| 能力 | 决定 |
|---|---|
| 行内编辑明细（数量/市场价/折扣/批价/结算价/备注） | ✅ 保留 |
| 增删行 | ✅ 保留（仅批价单；结算明细结构继承批价单，不增删） |
| 拖拽排序 | ❌ 砍掉 |
| 双权限分管（can_edit_pricing / can_edit_settlement） | ✅ 保留，用「列可编辑配置」表达 |
| 基本信息 + 毛利 KPI 各自选区、随 tab 切换 | ✅ 保留 |
| 打印批价单/结算单 | ✅ 保留 |

## 3. 组件复用方案（核心决策 — 待最终拍板）

明细表要复用 AT 报价单那套明细组件的**视觉与机制**（陶土橙令牌、view/edit 切换、隐藏列、行内输入框样式），位于 `components/at_minitables.html`。

但批价单与报价单的**列集不同**（批价单：编码/品牌/市场价/折扣/批价；报价单：产品名/规格/单位/税率/分组），且批价单是**双实体**（批价/结算两套）。因此 `render_quotation_details_table` 不能原样套用。两条路：

- **方案 A（推荐）：在 `at_minitables.html` 内新增 `render_pricing_order_details_table` 宏**，复用同一套 CSS 类与 view/edit 机制，列集为批价单专用，接收 `editable_fields`（控制双权限可编辑列）+ `entity='pricing'|'settlement'` 参数。
  - 优点：完全不动 `render_quotation_details_table`，报价单零回归风险；仍是同一组件文件、同一视觉系统，符合「复用 AT 那套」。
  - 缺点：与报价宏有少量结构相似代码（可共享底层 cell/row 子宏降低重复）。
- **方案 B：把 `render_quotation_details_table` 抽象成通用 details 表核心**（列配置化），报价单与批价单各传列配置。
  - 优点：真正单一组件。
  - 缺点：要改报价单已上线的明细渲染，有回归风险。

> 倾向方案 A：既复用 AT 明细组件的视觉与交互，又不动已上线的报价单。最终请确认 A 还是 B。

## 4. 路由与模板

- 现 `GET /pricing_order/<id>/excel-edit` → `excel_edit_pricing_order()` 渲染 `tw_edit.html`。
- 改为渲染新模板 `pricing_order/at_edit.html`（AT 外壳 + 两 tab + 上述选区 + 新明细宏）。
- `at_list.html` 行点击、「待我审批」tab 跳转目标统一指向该页。
- 旧 `tw_edit.html` 归档到 `_archived/`（迁移规范）。

## 5. 数据流（复用现有后端，不新建并行接口）

沿用 tw_edit 已用的端点：
- 基本信息：`POST /pricing_order/<id>/update_basic_info`
- 备注：`POST /pricing_order/<id>/update_notes`
- 批价明细：`POST /pricing_order/<id>/save_pricing_details`
- 结算明细：`POST /pricing_order/<id>/update_settlement_detail`（行级）/ 结算折扣等现有端点
- 删除：`DELETE /pricing_order/<id>/delete`

前端：tab 内编辑态收集行数据 → 调对应端点 → 成功后局部刷新/reload。双权限由后端既有 `can_edit_pricing/can_edit_settlement` 继续把关（前端只读列仅为体验）。

## 6. 审批集成（含顺带修复）

- 复用 AT 审批组件（`at-approval-dropdown.js` / `tw_approval_flow`）。
- **顺带修复**先前发现的 bug：批价单审批通过后跳到了项目列表，应**返回上一页**（来源页）。在 AT 页审批成功回调里改为回退 referrer/来源，而非 `project.list_projects`。

## 7. 测试

- 本地（pma_local，5097）：批价/结算两 tab 渲染、tab 切换、view/edit 切换、行内编辑保存、增删行（批价）、双权限只读（结算）、打印、审批通过后返回来源页。
- 回归：报价单 AT 详情页明细表不受影响（若选方案 B 重点回归）。

## 8. 不在本次范围

- 拖拽排序（已砍）
- 报价单页面任何可见变化（方案 A 下应为零变化）

## 9. 待办决策

1. 组件方案 A / B（§3）
2. 是否同时把「审批后返回上一页」修复纳入本次（建议是）
