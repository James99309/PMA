# 通用组件修改日志

## ⚠️ 重要说明
此文件记录所有对通用组件的修改历史，任何对通用组件的修改都必须在此记录。

## 受保护的通用组件文件
- `app/templates/macros/ui_helpers.html` - 通用UI组件模板
- `app/static/js/data-list.js` - 通用数据列表组件
- `app/static/js/filter-search.js` - 通用筛选搜索组件
- `app/static/css/style.css` (通用组件相关样式) - 通用组件CSS样式

## 修改协议
每次修改必须包含以下信息：
1. **修改日期**
2. **修改人员**  
3. **修改原因**
4. **影响范围分析**
5. **测试验证情况**
6. **批准人员**

---

## 修改历史

### 2026-07-30 - 审批中心「关联业务」徽章补齐缺失类型
**修改人员**: Claude AI Assistant
**批准人员**: nijie（待确认）
**修改原因**: `render_tw_business_type_badge` 的 `type_config` 只登记了 6 种 object_type，
其余类型走 fallback，把英文 key 原样当中文标签显示（审批中心里 `dealer_apply` 直接显示成
"dealer_apply"，`project_hold` 显示成 "project_hold"）。

**具体修改**: `app/templates/macros/ui_helpers.html:9134` 的 `type_config` 字典**新增** 6 个键：
`dealer_apply` / `project_hold` / `project_win_lock` / `perf_settlement` / `salary_run` / `rd_product`。

**影响范围分析**:
- 纯新增字典项，**未改动任何既有键的 class/zh/en/icon**，已登记的 6 种类型渲染结果零变化
- 使用方：`app/templates/approval/tw_center_rows.html:80+`（审批中心列表「关联业务」列）
- 无 JS/CSS 变更，无 API 变更

**测试验证情况**: 本地 5097（pma_local）审批中心列表渲染验证；`dealer_apply` 行由
"dealer_apply" 变为「渠道身份」青色徽章，`project` / `expense` / `pricing_order` 等既有类型显示不变。

---

### 2025-07-26 - 蓝色边框问题修复
**修改人员**: Claude AI Assistant  
**批准人员**: nijie  
**修改原因**: 修复通用列表组件中出现不规则蓝色边框的问题  

**具体修改**:
1. **ui_helpers.html**: 移除 `table_config.enhanced_striping|default(true)` 中的 `|default(true)` 部分
2. **style.css**: 删除导致每第5行出现蓝色边框的CSS规则:
   - `.data-list-table.table-striped > tbody > tr:nth-of-type(10n+5) > td`
3. 添加通用组件保护声明到所有核心文件

**影响范围**: 所有使用通用列表组件的页面  
**测试验证**: 验证账户管理页面、企业列表页面等不再出现蓝色边框  
**风险评估**: 低风险，仅移除了造成视觉问题的样式规则  

---

### 2025-07-26 - 通用组件保护机制建立
**修改人员**: Claude AI Assistant  
**批准人员**: nijie  
**修改原因**: 防止对通用组件的随意修改造成大面积影响  

**具体修改**:
1. 在所有通用组件文件开头添加保护声明
2. 明确修改协议和流程
3. 创建修改日志文件

**影响范围**: 所有通用组件  
**测试验证**: 无功能性修改，仅添加文档说明  
**风险评估**: 无风险，仅为文档性修改  

---

**注意**: 后续任何对通用组件的修改都必须在此文件中记录！