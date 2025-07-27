# SP8D云端数据库与本地PMA_local数据库差异分析报告

## 📊 分析概览

**分析时间**: 2025-07-27T09:34:33.045700
**分析类型**: 结构差异对比（只读分析，未修改任何数据库）

### 数据库基本信息
| 数据库 | 表数量 | 连接状态 |
|--------|--------|----------|
| 本地PMA_local | 58 | ✅ 正常 |
| SP8D云端 | 58 | ✅ 正常 |

### 差异统计
- **SP8D缺失表**: 0 个
- **SP8D独有表**: 0 个  
- **结构差异表**: 5 个

## 🔍 详细差异分析

### 1. 表级别差异

#### SP8D缺失的表 (0 个)
无缺失表

#### SP8D独有的表 (0 个)
无独有表

### 2. 表结构差异 (5 个表)


#### 表: `dictionaries`

**记录数对比**:
- 本地: 27 条
- SP8D: 25 条

**字段类型差异** (5 个):
- `website`: 本地(character varying) vs SP8D(character varying)
- `address`: 本地(character varying) vs SP8D(text)
- `email`: 本地(character varying) vs SP8D(character varying)
- `email_signature_filename`: 本地(character varying) vs SP8D(character varying)
- `logo_filename`: 本地(character varying) vs SP8D(character varying)


#### 表: `approval_step`

**记录数对比**:
- 本地: 12 条
- SP8D: 4 条

**SP8D缺失字段** (6 个):
- `branch_on_reject`
- `branch_on_approve`
- `condition_config`
- `condition_type`
- `is_conditional`
- `skip_conditions`


#### 表: `approval_process_template`

**记录数对比**:
- 本地: 7 条
- SP8D: 4 条

**SP8D缺失字段** (1 个):
- `visual_data`


#### 表: `purchase_orders`

**记录数对比**:
- 本地: 5 条
- SP8D: 0 条

**SP8D独有字段** (3 个):
- `approval_completed_at`
- `approval_submitted_at`
- `approval_status`


#### 表: `settlement_orders`

**记录数对比**:
- 本地: 28 条
- SP8D: 23 条

**SP8D缺失字段** (1 个):
- `settlement_status`


## 🚨 数据安全性评估

### 风险等级: 🟡 MEDIUM

### 数据丢失风险
- 🟡 **MEDIUM**: 表 purchase_orders 在SP8D有额外字段，同步可能导致这些字段的数据丢失
  影响字段: approval_completed_at, approval_submitted_at, approval_status

### 建议方案
⚠️ 可以谨慎进行同步，但需要特别注意
💾 同步前必须完整备份SP8D数据库
🔍 建议先在测试环境验证同步结果


## 📋 技术细节

### 约束差异分析


## ⚠️ 重要声明

1. **只读分析**: 本报告基于只读查询生成，未对任何数据库进行修改
2. **数据安全**: 云端数据库完全安全，未受任何影响
3. **建议谨慎**: 任何同步操作前请务必完整备份目标数据库
4. **专业指导**: 建议在数据库专家指导下执行同步操作

---
*报告生成时间: 2025-07-27 09:34:40*
*分析工具: SP8D数据库差异分析器 v1.0*
