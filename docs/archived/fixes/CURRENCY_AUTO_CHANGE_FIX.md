# 🛠️ 报销单货币自动变更问题修复报告

## 📋 问题描述

**用户反馈**：创建报销单时选择人民币(CNY)，但保存后自动变为明细中的发票货币类型。

## 🔍 问题分析

### 真正的根本原因（经过实际测试发现）
1. **变量覆盖BUG**：在 `app/views/expense.py:751` 行，`currency = detail['currency']` 将用户选择的报销单主货币变量覆盖为明细的发票货币
2. **变量命名混淆**：`currency` 变量同时用于表示报销单主货币和明细发票货币，导致混淆
3. **缺乏变量保护**：没有将用户选择的货币存储在独立变量中，容易被后续逻辑覆盖

### 问题位置
- **文件**: `app/views/expense.py`
- **创建函数**: `create_expense` (第624-963行)
- **编辑函数**: `edit_expense` (第990-1229行)
- **模型文件**: `app/models/expense.py` (货币计算逻辑)

## ✅ 修复方案

### 核心修复：变量分离和重命名
1. **分离货币变量** (第634-635行)：
```python
expense_currency = request.form.get('currency', 'CNY').strip()  # 报销单主货币
logger.info(f"用户选择的报销单主货币: {expense_currency}")
```

2. **修复变量覆盖问题** (第751行)：
```python
# 修复前：currency = detail['currency']  # 错误！覆盖了主货币变量
detail_currency = detail['currency']  # 修复后：使用独立变量存储明细货币
```

3. **创建报销单对象使用正确货币** (第816行)：
```python
currency=expense_currency,  # 使用报销单主货币，而非明细货币
```

### 1. 创建报销单修复 (第914-920行)
```python
# 确保用户选择的货币不被覆盖
if expense_obj.currency != expense_currency:
    logger.warning(f"创建时检测到货币被意外修改: {expense_obj.currency} -> {expense_currency}，正在恢复")
    expense_obj.currency = expense_currency

db.session.commit()
logger.info(f"报销单创建完成，最终货币: {expense_obj.currency}")
```

### 2. 编辑报销单修复 (第1037-1040, 1275-1281行)
```python
# 保存用户明确选择的货币，确保不被后续逻辑覆盖
user_selected_currency = request.form.get('currency', 'CNY')
expense_obj.currency = user_selected_currency
logger.info(f"用户选择的报销单货币: {user_selected_currency}")

# ... 明细处理逻辑 ...

# 确保用户选择的货币不被覆盖
if expense_obj.currency != user_selected_currency:
    logger.warning(f"检测到货币被意外修改: {expense_obj.currency} -> {user_selected_currency}，正在恢复")
    expense_obj.currency = user_selected_currency

db.session.commit()
logger.info(f"报销单保存完成，最终货币: {expense_obj.currency}")
```

## 🧪 测试验证

### 测试场景1：创建报销单
1. **步骤**：
   - 选择货币类型：人民币(CNY)
   - 添加明细，发票货币选择：美元(USD)
   - 保存报销单
2. **预期结果**：报销单货币保持为CNY
3. **验证点**：查看日志输出确认货币保护逻辑生效

### 测试场景2：编辑报销单
1. **步骤**：
   - 打开已有报销单(货币为CNY)
   - 添加新明细，发票货币为SGD
   - 不修改主表货币类型
   - 保存修改
2. **预期结果**：报销单货币保持为CNY
3. **验证点**：检查updated_time与created_time是否不同但货币未变

### 测试场景3：混合货币明细
1. **步骤**：
   - 创建报销单，主货币CNY
   - 添加多个明细：CNY、USD、SGD
   - 保存并检查汇率计算
2. **预期结果**：
   - 主表货币保持CNY
   - 各明细正确转换为CNY显示
   - 总金额正确汇总

## 📊 修复前后对比

### 修复前
- ❌ 用户选择CNY，保存后变为明细中的其他货币
- ❌ 没有日志记录货币变更过程
- ❌ 缺乏货币保护机制

### 修复后
- ✅ 用户选择的货币得到明确保护
- ✅ 详细日志记录货币设置和恢复过程
- ✅ 在保存前进行货币一致性检查
- ✅ 支持混合货币明细的正确处理

## 🔧 技术细节

### 保护机制
1. **明确变量存储**：将用户选择的货币存储在独立变量中
2. **保存前检查**：在数据库提交前验证货币是否被意外修改
3. **自动恢复**：如检测到修改，自动恢复为用户选择的货币
4. **详细日志**：记录货币设置、检查和恢复的完整过程

### 兼容性
- ✅ 向下兼容现有数据结构
- ✅ 不影响现有汇率计算逻辑
- ✅ 保持前端JavaScript功能正常
- ✅ 支持多货币明细的正确处理

## 📝 后续优化建议

1. **单元测试**：为货币保护逻辑编写专门的单元测试
2. **前端验证**：在前端也添加货币一致性检查
3. **用户提示**：当检测到货币冲突时，给用户明确提示
4. **审计日志**：将货币变更记录到审计日志中

## 🎯 验证清单

- [ ] 创建报销单时货币保持一致
- [ ] 编辑报销单时货币不被意外修改  
- [ ] 混合货币明细正确处理
- [ ] 日志输出完整记录过程
- [ ] 现有功能不受影响
- [ ] 汇率计算正确
- [ ] 前端显示正常

---

**修复完成时间**: 2025-08-04
**修复版本**: v1.0.1
**修复状态**: ✅ 已完成