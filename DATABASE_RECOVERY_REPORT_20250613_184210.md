# 数据库恢复报告

**恢复时间**: 2025-06-13 18:42:10
**备份文件**: ./cloud_backup_20250613_151838.sql
**安全备份**: pre_recovery_backup_20250613_184150.sql

## 📊 恢复概要

| 统计项 | 恢复前 | 恢复后 | 变化 |
|--------|--------|--------|------|
| 表数量 | 53 | 53 | +0 |
| 总记录数 | 2,688 | 10,545 | +7,857 |

## 🎯 关键业务表验证

| 表名 | 记录数 | ID范围 | 最新时间 | 状态 |
|------|--------|--------|----------|------|
| quotation_details | 4,040 | 1-8916 | 2025-06-13 09:32:48 | ✅ 成功 |
| quotations | 341 | 337-694 | 2025-06-13 09:32:48 | ✅ 成功 |
| projects | 470 | 1-624 | 2025-06-13 09:32:28 | ✅ 成功 |
| companies | 521 | 4-525 | 2025-06-13 09:49:05 | ✅ 成功 |
| contacts | 718 | 1-721 | 2025-06-13 04:50:40 | ✅ 成功 |
| products | 186 | 1-186 | 2025-04-15 00:23:07 | ✅ 成功 |
| users | 24 | 2-31 | 1748319839.6103299 | ✅ 成功 |

## 🔍 数据一致性对比

| 表名 | 备份文件 | 恢复后 | 差异 | 状态 |
|------|----------|--------|------|------|
| action_reply | 7 | 0 | -7 | ⚠️ 差异 |
| actions | 668 | 3 | -665 | ⚠️ 差异 |
| affiliations | 37 | 28 | -9 | ⚠️ 差异 |
| alembic_version | 1 | 1 | +0 | ✅ 匹配 |
| approval_instance | 49 | 49 | +0 | ✅ 匹配 |
| approval_process_template | 3 | 3 | +0 | ✅ 匹配 |
| approval_record | 35 | 35 | +0 | ✅ 匹配 |
| approval_step | 3 | 3 | +0 | ✅ 匹配 |
| change_logs | 145 | 8 | -137 | ⚠️ 差异 |
| companies | 519 | 521 | +2 | ⚠️ 差异 |
| contacts | 718 | 718 | +0 | ✅ 匹配 |
| dev_product_specs | 75 | 75 | +0 | ✅ 匹配 |
| dev_products | 5 | 5 | +0 | ✅ 匹配 |
| dictionaries | 25 | 23 | -2 | ⚠️ 差异 |
| event_registry | 4 | 4 | +0 | ✅ 匹配 |
| feature_changes | 0 | 0 | +0 | ✅ 匹配 |
| inventory | 0 | 0 | +0 | ✅ 匹配 |
| inventory_transactions | 0 | 0 | +0 | ✅ 匹配 |
| permissions | 19 | 19 | +0 | ✅ 匹配 |
| pricing_order_approval_records | 6 | 2 | -4 | ⚠️ 差异 |
| pricing_order_details | 22 | 25 | +3 | ⚠️ 差异 |
| pricing_orders | 2 | 3 | +1 | ⚠️ 差异 |
| product_categories | 8 | 8 | +0 | ✅ 匹配 |
| product_code_field_options | 45 | 45 | +0 | ✅ 匹配 |
| product_code_field_values | 0 | 0 | +0 | ✅ 匹配 |
| product_code_fields | 43 | 43 | +0 | ✅ 匹配 |
| product_codes | 0 | 0 | +0 | ✅ 匹配 |
| product_regions | 8 | 8 | +0 | ✅ 匹配 |
| product_subcategories | 60 | 60 | +0 | ✅ 匹配 |
| products | 186 | 186 | +0 | ✅ 匹配 |
| project_members | 0 | 0 | +0 | ✅ 匹配 |
| project_rating_records | 0 | 0 | +0 | ✅ 匹配 |
| project_scoring_config | 11 | 11 | +0 | ✅ 匹配 |
| project_scoring_records | 3,237 | 3,237 | +0 | ✅ 匹配 |
| project_stage_history | 359 | 8 | -351 | ⚠️ 差异 |
| project_total_scores | 375 | 375 | +0 | ✅ 匹配 |
| projects | 468 | 470 | +2 | ⚠️ 差异 |
| purchase_order_details | 0 | 0 | +0 | ✅ 匹配 |
| purchase_orders | 0 | 0 | +0 | ✅ 匹配 |
| quotation_details | 4,032 | 4,040 | +8 | ⚠️ 差异 |
| quotations | 338 | 341 | +3 | ⚠️ 差异 |
| role_permissions | 98 | 135 | +37 | ⚠️ 差异 |
| settlement_details | 0 | 0 | +0 | ✅ 匹配 |
| settlement_order_details | 22 | 6 | -16 | ⚠️ 差异 |
| settlement_orders | 2 | 3 | +1 | ⚠️ 差异 |
| settlements | 0 | 0 | +0 | ✅ 匹配 |
| solution_manager_email_settings | 1 | 1 | +0 | ✅ 匹配 |
| system_metrics | 0 | 0 | +0 | ✅ 匹配 |
| system_settings | 2 | 2 | +0 | ✅ 匹配 |
| upgrade_logs | 0 | 0 | +0 | ✅ 匹配 |
| user_event_subscriptions | 16 | 16 | +0 | ✅ 匹配 |
| users | 24 | 24 | +0 | ✅ 匹配 |
| version_records | 1 | 1 | +0 | ✅ 匹配 |

**匹配率**: 37/53 (69.8%)

## 📋 恢复日志

```
[18:41:50] ================================================================================
[18:41:50] 🚀 开始数据库恢复流程
[18:41:50] ================================================================================
[18:41:50] 🔒 创建恢复前安全备份...
[18:41:54] ✅ 安全备份创建成功: pre_recovery_backup_20250613_184150.sql (0.86 MB)
[18:41:54] 📊 获取恢复前数据统计...
[18:41:55] 📋 恢复前统计: 53 个表, 2,688 条记录
[18:41:55] 🔄 开始数据库恢复...
[18:41:55] 📁 恢复文件: ./cloud_backup_20250613_151838.sql
[18:41:55] 📊 文件大小: 2.47 MB
[18:41:55] ⏳ 正在执行恢复操作...
[18:42:07] ✅ 数据库恢复成功
[18:42:07] 📊 获取恢复后数据统计...
[18:42:08] 📋 恢复后统计: 53 个表, 10,545 条记录
[18:42:08] 🔍 验证关键业务数据...
[18:42:08]    ✅ quotation_details: 4,040 条记录 (ID: 1-8916)
[18:42:08]    ✅ quotations: 341 条记录 (ID: 337-694)
[18:42:08]    ✅ projects: 470 条记录 (ID: 1-624)
[18:42:08]    ✅ companies: 521 条记录 (ID: 4-525)
[18:42:08]    ✅ contacts: 718 条记录 (ID: 1-721)
[18:42:08]    ✅ products: 186 条记录 (ID: 1-186)
[18:42:09]    ✅ users: 24 条记录 (ID: 2-31)
[18:42:09] 📄 与备份文件进行数据对比...
[18:42:09] 📊 获取恢复后数据统计...
[18:42:10] 📋 恢复后统计: 53 个表, 10,545 条记录
[18:42:10] 📊 对比结果: 37/53 个表完全匹配
```

## 💡 建议

⚠️ **需要关注**: 部分表存在数据差异，建议进一步检查。

### 后续措施
1. 验证关键业务功能是否正常
2. 建立定期备份机制
3. 实施数据监控告警
4. 考虑平台迁移计划
