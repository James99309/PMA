# 批价单 Excel 格式改版设计方案

**日期**: 2026-04-28  
**状态**: UI 已确认 ✅，待实现  
**Mockup**: `docs/plans/2026-04-28-pricing-order-excel-mockup.html`

---

## 背景

报价单已改为 Excel 格式编辑页（`tw_quotation_edit.html`），效果直观干净。  
批价单目前是嵌入在报价单详情页内的 Modal 组件（`tw_pricing_order_modal.html`，2840 行），  
需要改版为同风格的独立全屏页面，同时加入结算单视图。

---

## 设计目标

1. **独立全屏页面**，不再是 Modal
2. **风格与报价单编辑页完全一致**（q-grid 表格、gray body、paper box-shadow 等）
3. **顶部 Tab 切换**：批价单 ↔ 结算单
4. **审批流程**通过顶部 header 按钮打开右侧抽屉（不遮挡主表格）

---

## 页面结构

### 顶部 Header（sticky，h-14，与报价单完全一致）

```
← 批价单 · PO-2026-0042   [审批中]    [审批流程 >]  [显示列]  [+ 添加行 ▾]  [打印]  [取消]  [保存]
   深圳智慧城市对讲系统项目
```

- 左侧：返回箭头 + 标题 + 项目名 + 状态徽章
- 右侧：审批流程按钮（indigo）、显示列、添加行（蓝）、打印、取消、保存（emerald）

### Tab Bar（sticky，top: 56px）

```
[📋 批价单]  [🧾 结算单]
```

---

## 批价单 Tab

### 基本信息表格（q-grid）

| 项目 | 深圳智慧城市对讲系统项目 | 批价单号 | PO-2026-0042 | 关联报价 | Q-2026-0089 |
|------|---|---|---|---|---|
| 分销商 | （下拉） | 经销商 | （下拉） | 批价日期 | （日期） | 有效期 | （日期） |
| 货币 | （下拉）CNY | 备注 | （多行文本） |

### 产品明细表格（q-grid，与报价单一致）

列：拖拽 / S/N / 产品编码 / 品牌 / 型号规格 / 数量 / 市场价 / 折扣% / 批价 / 小计 / 删除

行类型（与报价单完全一致）：
- `tr.section-row` — 分类标题行（可编辑名称）
- `tr.product-row` — 主产品行
- `tr.config-row` — 配件行（缩进、蓝色编码）
- `tr.total-row` — 合计行

---

## 结算单 Tab

### 基本信息表格（q-grid）

| 结算公司 | （下拉） | 结算日期 | （日期） | 合同号 | （文本） |
|---|---|---|---|---|---|
| 付款条件 | （下拉）到到付款 | 备注 | （多行文本） |

提示横幅：`ⓘ 结算单基于批价单明细自动生成，仅需填写结算价格`

### 产品列表（共用批价单行数据，只增加"结算价"列）

### 底部利润 KPI 卡片

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  批价收入    │  │  结算成本    │  │  毛利润      │  │  毛利率      │
│  ¥ 95,388   │  │  ¥ 69,600   │  │  ¥ 25,788   │  │   27.0%     │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

---

## 审批流程抽屉

触发：点击 header 右侧"审批流程 >"按钮  
位置：`position: fixed; right: 0; width: 320px`  
效果：主内容区 `padding-right: 320px`，不遮挡表格

抽屉内容：
- 顶部：提交审批按钮（或当前状态）
- 竖向时间线：销售提交 → 销售经理审批（含同意/驳回按钮）→ 总经理审批 → 审批完成
- 底部：折扣权限信息（当前折扣范围、授权下限）

---

## 组件化架构

为了让报销单将来也能复用 Excel 编辑风格，计划抽取：

### `app/static/css/excel-paper-editor.css`
- `body` 背景色 `#cfd2d7`
- `.pricing-paper` / `.quotation-paper` 样式（box-shadow、width）
- 所有 `table.q-grid` 样式
- `td.editable`、`td.label`、`td.readonly`、`td.product-th` 等
- `tr.section-row`、`tr.config-row`、`tr.product-row`、`tr.total-row` 等
- 审批抽屉通用样式

### `app/static/js/excel-editor-base.js`
- Tab 切换逻辑
- 审批抽屉开关逻辑
- 显示列勾选联动
- 金额自动计算（批价 = 市场价 × 折扣% / 100，小计 = 批价 × 数量）

### 页面继承关系
```
excel-paper-editor.css / excel-editor-base.js
    ├── tw_quotation_edit.html   (报价单，已有，迁移样式到共享 CSS)
    ├── pricing_order/tw_edit.html  (批价单，新建)
    └── expense/tw_edit.html     (报销单，未来，纸质布局变体)
```

---

## 实现步骤（待执行）

- [ ] 1. 创建 `app/static/css/excel-paper-editor.css`，从 `tw_quotation_edit.html` 提取共享样式
- [ ] 2. 创建 `app/static/js/excel-editor-base.js`，提取 tab 切换 + 抽屉 + 列显示逻辑
- [ ] 3. 新建 `app/templates/pricing_order/tw_edit.html`（独立页面，复用 CSS/JS）
- [ ] 4. 在 `app/views/pricing_order.py` 添加独立编辑路由
- [ ] 5. 修改 `tw_quotation_detail.html` 中批价单按钮，从打开 Modal 改为跳转新页面
- [ ] 6. 旧 Modal 组件（`tw_pricing_order_modal.html`）在新页面稳定后归档

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `app/templates/quotation/tw_quotation_edit.html` | 报价单编辑页，样式来源参考 |
| `app/templates/quotation/tw_quotation_detail.html` | 报价单详情，含批价单 Modal 入口 |
| `app/templates/pricing_order/tw_pricing_order_modal.html` | 当前批价单 Modal（2840行），待替换 |
| `app/views/pricing_order.py` | 批价单视图，需新增独立编辑路由 |
| `docs/plans/2026-04-28-pricing-order-excel-mockup.html` | UI Mockup（可在浏览器直接打开预览） |
