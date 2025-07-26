# SP8D云端数据库与本地PMA_local数据库差异分析报告

## 📊 分析概览

**分析时间**: 2025-07-26T13:47:46.973795
**分析类型**: 结构差异对比（只读分析，未修改任何数据库）

### 数据库基本信息
| 数据库 | 表数量 | 连接状态 |
|--------|--------|----------|
| 本地PMA_local | 58 | ✅ 正常 |
| SP8D云端 | 56 | ✅ 正常 |

### 差异统计
- **SP8D缺失表**: 2 个
- **SP8D独有表**: 0 个  
- **结构差异表**: 3 个

## 🔍 详细差异分析

### 1. 表级别差异

#### SP8D缺失的表 (2 个)
- `company_assets` (14 字段, 1 条记录)
- `temp_products` (16 字段, 33 条记录)

#### SP8D独有的表 (0 个)
无独有表

### 2. 表结构差异 (3 个表)


#### 表: `dictionaries`

**记录数对比**:
- 本地: 27 条
- SP8D: 25 条

**SP8D缺失字段** (14 个):
- `email_signature_filename`
- `logo_type`
- `phone`
- `address`
- `email_signature_type`
- `logo_size`
- `fax`
- `website`
- `email_signature_size`
- `email_signature_content`
- `logo_content`
- `postal_code`
- `email`
- `logo_filename`


#### 表: `settlement_orders`

**记录数对比**:
- 本地: 28 条
- SP8D: 23 条

**SP8D缺失字段** (1 个):
- `settlement_status`


#### 表: `purchase_orders`

**记录数对比**:
- 本地: 5 条
- SP8D: 0 条

**SP8D独有字段** (3 个):
- `approval_status`
- `approval_completed_at`
- `approval_submitted_at`


## 🚨 数据安全性评估

### 风险等级: 🟡 MEDIUM

### 数据丢失风险
- 🟡 **MEDIUM**: 表 purchase_orders 在SP8D有额外字段，同步可能导致这些字段的数据丢失
  影响字段: approval_status, approval_completed_at, approval_submitted_at

### 建议方案
⚠️ 可以谨慎进行同步，但需要特别注意
💾 同步前必须完整备份SP8D数据库
🔍 建议先在测试环境验证同步结果


## 📋 技术细节

### 约束差异分析
**SP8D缺失主键的表**: company_assets, temp_products
**SP8D缺失外键的表**: company_assets, temp_products


## ⚠️ 重要声明

1. **只读分析**: 本报告基于只读查询生成，未对任何数据库进行修改
2. **数据安全**: 云端数据库完全安全，未受任何影响
3. **建议谨慎**: 任何同步操作前请务必完整备份目标数据库
4. **专业指导**: 建议在数据库专家指导下执行同步操作

---
*报告生成时间: 2025-07-26 13:47:53*
*分析工具: SP8D数据库差异分析器 v1.0*
