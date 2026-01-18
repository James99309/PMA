# 旧规格系统 (ProductCodeField) 依赖清单

**文档更新**: 2026-01-17
**系统**: PMA 项目管理系统
**范围**: ProductCodeField (旧规格系统) 完整依赖映射
**用途**: 支持架构解耦、特性开关控制和未来系统移除

---

## 📋 快速概览

### 系统状态
- **当前状态**: 已架构隐藏，通过特性开关控制 (`LEGACY_SPEC_SYSTEM_ENABLED`)
- **依赖评估**: 低风险 - ProductCodeField 已完全本地化
- **数据完整性**: ✅ 所有表保留，支持历史数据查询
- **迁移准备**: ✅ 快照机制已实现，支持平滑过渡

---

## 🔍 ProductCodeField 相关API端点

### POST 创建操作
| 端点 | 功能 | 特性开关 | 状态 |
|-----|------|--------|------|
| `POST /product-code/api/fields` | 创建规格字段 (分类/子分类级) | ✅ LEGACY_SPEC_SYSTEM_ENABLED | [LegacySpecSystem] 已标记 |
| `POST /product-code/api/field-options` | 创建字段选项 | ✅ LEGACY_SPEC_SYSTEM_ENABLED | [LegacySpecSystem] 已标记 |

### GET 读取操作
| 端点 | 功能 | 特性开关 | 状态 |
|-----|------|--------|------|
| `GET /product-code/api/fields/:field_id` | 获取字段详情 | ✅ LEGACY_SPEC_SYSTEM_ENABLED | [LegacySpecSystem] 已标记 |
| `GET /product-code/api/fields/available-specs/:subcategory_id` | 获取可用规格列表 | ✅ LEGACY_SPEC_SYSTEM_ENABLED | 已标记 |
| `GET /product-code/api/category/:id/fields` | 获取分类级字段 | ✅ LEGACY_SPEC_SYSTEM_ENABLED | 已标记 |
| `GET /product-code/api/subcategory/:id/fields` | 获取子分类级字段 | ✅ LEGACY_SPEC_SYSTEM_ENABLED | 已标记 |
| `GET /product-code/api/field-options/:field_id` | 获取字段选项 | ✅ LEGACY_SPEC_SYSTEM_ENABLED | 已标记 |

### PUT 更新操作
| 端点 | 功能 | 特性开关 | 状态 |
|-----|------|--------|------|
| `PUT /product-code/api/fields/:field_id` | 更新规格字段 | ✅ LEGACY_SPEC_SYSTEM_ENABLED | [LegacySpecSystem] 已标记 |
| `PUT /product-code/api/field-options/:option_id` | 更新字段选项 | ✅ LEGACY_SPEC_SYSTEM_ENABLED | [LegacySpecSystem] 已标记 |

### DELETE 删除操作
| 端点 | 功能 | 特性开关 | 状态 |
|-----|------|--------|------|
| `DELETE /product-code/api/fields/:field_id` | 删除规格字段 | ✅ LEGACY_SPEC_SYSTEM_ENABLED | [LegacySpecSystem] 已标记 |
| `DELETE /product-code/api/field-options/:option_id` | 删除字段选项 | ✅ LEGACY_SPEC_SYSTEM_ENABLED | [LegacySpecSystem] 已标记 |

### 排序操作
| 端点 | 功能 | 特性开关 | 状态 |
|-----|------|--------|------|
| `POST /product-code/api/category/:id/update-fields-order` | 更新分类字段排序 | ✅ LEGACY_SPEC_SYSTEM_ENABLED | [LegacySpecSystem] 已标记 |
| `POST /product-code/api/subcategory/:id/update-fields-order` | 更新子分类字段排序 | ✅ LEGACY_SPEC_SYSTEM_ENABLED | [LegacySpecSystem] 已标记 |

---

## 💾 数据库表与模型

### ProductCodeField 相关表
```sql
-- 核心表
product_code_fields          -- 规格字段定义表
product_code_field_options   -- 规格选项表 (用于选择型规格)
product_code_field_values    -- 规格值表 (历史快照数据)
product_codes                -- 产品编码表 (关联products表)
```

### 保留策略
- ✅ **完全保留**: 所有ProductCodeField相关表保留用于历史数据查询
- ✅ **备份**: 定期备份确保数据安全
- ✅ **查询**: 所有查询可正常执行，无功能影响
- ✅ **完整性**: 外键约束保持完整

### 字段关系
```
ProductSubcategory (1) ─── (M) ProductCodeField
                              ├─ product_code_fields.subcategory_id
                              ├─ 快照: products.code_definition_snapshot
                              └─ 历史: ProductCodeFieldValue
```

---

## 🔗 本地数据库查询 (无需改动，始终可用)

### 1. 产品快照查询
**文件**: `app/routes/product.py`
**功能**: 获取产品快照规格数据
**查询方式**: 使用 `products.code_definition_snapshot` (JSON)

```python
product = Product.query.get(product_id)
specs = json.loads(product.code_definition_snapshot or '{}')
```

**特点**:
- ✅ 无API调用
- ✅ 本地查询，不受特性开关影响
- ✅ 快照在产品创建时生成，数据完整

### 2. 报价单规格使用
**文件**: `app/views/quotation.py`
**功能**: 创建报价单时读取产品规格
**查询方式**: 使用产品快照数据

```python
product = Product.query.get(product_id)
code_definition_snapshot = product.code_definition_snapshot
```

**特点**:
- ✅ 使用快照数据，无API调用
- ✅ 报价单创建完全不受特性开关影响
- ✅ 历史报价数据永远可用

### 3. 产品编码快照生成
**文件**: `app/services/product_helpers.py`
**功能**: 生成 `code_definition_snapshot`
**查询方式**: 直接查询 ProductCodeField 本地表

```python
# [LegacySpecSystem] 查询当前ProductCodeField定义
fields = ProductCodeField.query.filter_by(
    subcategory_id=product.subcategory_id
).all()
```

**特点**:
- ✅ 本地查询，不经过API
- ✅ 不受特性开关影响（内部函数）
- ✅ 生成的快照独立存在

### 4. 订单系统规格使用
**文件**: `app/routes/order.py`
**功能**: 订单审核、履行相关
**查询方式**: 使用报价单中的规格信息 (来自快照)

**特点**:
- ✅ 完全不涉及ProductCodeField API
- ✅ 使用历史快照数据
- ✅ 无任何外部依赖

---

## ⚠️ 系统状态与禁用影响分析

### 启用状态 (LEGACY_SPEC_SYSTEM_ENABLED=true)
```
用户界面 ✅                  后端系统 ✅
├─ 规格管理UI 显示           ├─ ProductCodeField API 可用
├─ 规格编辑按钮 启用          ├─ 特性开关 通过
├─ 编辑规格表单 显示          └─ 日志记录 [LegacySpecSystem]

本地查询 ✅
├─ Product.code_definition_snapshot 可用
├─ ProductCodeField 查询 可用
└─ 历史数据 完整
```

### 禁用状态 (LEGACY_SPEC_SYSTEM_ENABLED=false)
```
用户界面 ❌                  后端系统 ❌
├─ 规格管理UI 隐藏           ├─ ProductCodeField API 返回 503
├─ 规格编辑按钮 隐藏          ├─ 特性开关 阻止
├─ 编辑规格表单 隐藏          ├─ 错误响应:
└─ 提示: "规格系统已禁用"       │  {
                              │    "success": false,
本地查询 ✅ (不受影响)          │    "source": "legacy_spec_system",
├─ Product.code_definition_snapshot 仍可用  │    "error": "系统已禁用"
├─ ProductCodeField 查询 仍可用  │  }
└─ 历史数据 完整                  └─ HTTP 503 Service Unavailable
```

---

## 📊 已验证的非依赖系统

### ✅ 已确认无依赖
| 系统 | 检查点 | 结论 |
|-----|--------|------|
| OVS 外部系统 | sp8d_api_service.py 无ProductCodeField引用 | ✅ 完全独立 |
| 报价单系统 | 使用产品快照，无API调用 | ✅ 完全独立 |
| 订单系统 | 从报价单读取规格，无直接依赖 | ✅ 完全独立 |
| 发票系统 | 无规格相关操作 | ✅ 完全独立 |
| 库存系统 | 仅涉及数量，无规格依赖 | ✅ 完全独立 |

---

## 🎯 特性开关控制点

### 配置文件
**文件**: `config.py` (第221-223行)
```python
# 旧规格系统特性开关
LEGACY_SPEC_SYSTEM_ENABLED = os.getenv('LEGACY_SPEC_SYSTEM_ENABLED', 'true').lower() == 'true'
```

### 后端控制
**文件**: `app/utils/legacy_decorators.py`
```python
@feature_flag('LEGACY_SPEC_SYSTEM_ENABLED')  # 装饰器自动拦截
def api_endpoint():
    # 当LEGACY_SPEC_SYSTEM_ENABLED=false时返回503
    pass
```

### 前端控制
**文件**: `app/static/js/tw-category-manager.js`
```javascript
// 条件检查
if (!this.legacySpecSystemEnabled) {
    this.showToast('规格系统已禁用，请使用新规格模板系统', 'warning');
    return;
}
```

### 模板控制
**文件**: `app/templates/product_code/tw_category_management.html`
```html
{% if config.LEGACY_SPEC_SYSTEM_ENABLED %}
    <!-- 规格管理UI -->
{% else %}
    <div class="alert alert-info">规格管理已迁移至规格模板系统</div>
{% endif %}
```

---

## 📝 代码标记规范

### 标记位置
所有ProductCodeField相关代码使用统一标记:
```python
# [LegacySpecSystem] 此代码仅用于旧规格系统
```

### 日志规范
所有操作使用统一前缀:
```python
logger.info('[LegacySpecSystem] Operation description')
logger.error('[LegacySpecSystem] Error description', exc_info=True)
```

### API响应规范
所有错误响应包含来源标识:
```json
{
    "success": false,
    "source": "legacy_spec_system",
    "error": "错误信息"
}
```

---

## 🔄 迁移检查清单

### 前置条件 (启用新系统)
- [ ] 新规格模板系统 (SpecTemplate) 已充分验证
- [ ] 新系统功能覆盖所有使用场景
- [ ] 用户已培训使用新系统
- [ ] 新API接口已稳定运行

### 过渡阶段 (并行运行)
- [ ] 设置 `LEGACY_SPEC_SYSTEM_ENABLED=true` (保持启用)
- [ ] 监控旧系统使用日志 (3-6个月)
- [ ] 收集用户反馈
- [ ] 记录迁移问题

### 禁用阶段 (关闭旧系统)
- [ ] 设置 `LEGACY_SPEC_SYSTEM_ENABLED=false`
- [ ] 验证UI正确隐藏
- [ ] 验证API返回503
- [ ] 验证新系统接管
- [ ] 运行1-2周，无错误后继续

### 代码清理阶段 (删除旧系统)
- [ ] 删除 `app/utils/legacy_decorators.py`
- [ ] 删除 `app/routes/product_code.py` ProductCodeField部分 (保留分类管理)
- [ ] 移除所有 `@feature_flag` 装饰器
- [ ] 移除所有 `{% if LEGACY_SPEC_SYSTEM_ENABLED %}` 条件块
- [ ] 更新文档
- [ ] 完整测试验证

### 数据库清理阶段 (可选，谨慎操作)
- [ ] 确认 ProductCodeFieldValue 不再需要
- [ ] 确认历史快照可归档
- [ ] 备份所有表到冷存储
- [ ] 考虑表数据归档而非删除
- [ ] 定期存档历史数据

---

## 📈 风险评估

### 禁用旧系统风险: **极低 ⭐**

| 风险点 | 影响范围 | 缓解措施 | 风险等级 |
|--------|--------|--------|--------|
| 报价单系统 | 使用快照，无影响 | 快照已保存 | ✅ 无风险 |
| 订单系统 | 从报价读取，无影响 | 数据已保留 | ✅ 无风险 |
| 产品创建 | 使用本地查询 | 本地表保留 | ✅ 无风险 |
| 历史数据 | 完全保留 | 表未删除 | ✅ 无风险 |
| 外部系统 | 无依赖 | 已验证 | ✅ 无风险 |

### 删除旧系统代码风险: **低风险 ⭐⭐**

| 风险点 | 缓解措施 | 建议 |
|--------|--------|------|
| 隐藏变量 | 通过搜索找到所有引用 | 使用Grep工具 |
| 级联删除 | 保留相关表结构 | 保留数据库 |
| 配置变量 | 统一搜索所有配置引用 | 检查文件清单 |

---

## 🛠️ 故障排查指南

### 症状: API返回503
```python
# 检查配置
os.getenv('LEGACY_SPEC_SYSTEM_ENABLED')

# 预期值: 'false' (被禁用) 或 'true' (启用)
# 如果获得503，说明特性开关工作正常
```

### 症状: UI显示规格管理按钮但禁用
```javascript
// 检查浏览器控制台日志
console.log('[LegacySpec]')  // 应看到初始化日志

// 验证config对象
console.log(window.config.LEGACY_SPEC_SYSTEM_ENABLED)
```

### 症状: 报价单创建失败
```python
# 检查快照是否存在
product = Product.query.get(product_id)
print(product.code_definition_snapshot)

# 快照应包含完整的规格定义
```

### 症状: 历史数据丢失
```python
# 验证表是否存在
from sqlalchemy import inspect
inspector = inspect(db.engine)
print(inspector.get_table_names())
# 应包含: product_code_fields, product_code_field_options等
```

---

## 📞 联系与支持

### 文档维护
- **更新者**: PMA开发团队
- **最后更新**: 2026-01-17
- **下次审查**: 2026-06-17

### 相关文档
- [CLAUDE.md](./CLAUDE.md) - 项目核心规范
- [产品代码路由](./app/routes/product_code.py) - API实现
- [产品模型](./app/models/product.py) - 数据模型
- [规格服务](./app/services/product_helpers.py) - 快照生成

### 问题报告
请在GitHub Issues中报告相关问题，使用标签: `legacy-spec-system`

---

## ✅ 解耦验证清单

### 依赖验证
- [x] ProductCodeField API已通过特性开关控制
- [x] 前端UI已条件隐藏
- [x] JavaScript已条件初始化
- [x] 所有错误已标记来源
- [x] 日志已统一前缀
- [x] 本地查询验证无外部依赖
- [x] 快照机制验证独立完整

### 文档完整性
- [x] API端点清单完整
- [x] 数据库表关系明确
- [x] 本地查询场景覆盖
- [x] 非依赖系统已验证
- [x] 特性开关控制点清晰
- [x] 迁移检查清单完整
- [x] 风险评估已进行
- [x] 故障排查指南已提供

---

**文档完成**✅
**下一步**: 执行测试验证 (Step 6)
