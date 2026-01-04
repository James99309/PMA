# 编码快照系统文档

本项目包含两套独立的编码快照系统，用于记录产品编码的生成规则，便于历史追溯和规则变更管理。

---

## 系统对比总览

| 对比项 | 老系统（Product） | 新系统（SpecTemplate） |
|-------|------------------|----------------------|
| **用途** | 标准产品编码定义 | 规格模板MN编码规则 |
| **主数据表** | `products` | `product_configurations` |
| **快照字段** | `code_definition_snapshot` | `code_rule_snapshot` |
| **版本字段** | 快照内 `version: "1.0"` | 独立字段 `code_rule_version` |
| **触发时机** | 研发产品入库/手动创建 | 规格配置矩阵保存MN编码 |

---

## 老系统：Product/ProductCode

### 适用场景
- 研发产品入库到标准产品
- 手动创建/编辑标准产品
- 产品编码定义的历史追溯

### 数据表结构

```
products                    # 标准产品表
  └── code_definition_snapshot (JSON)  # 编码定义快照

product_codes               # 产品编码表
  └── generate_snapshot()   # 快照生成方法

product_specs               # 产品规格表
  └── field_name, field_value, field_code
```

### 快照函数

#### 1. ProductCode.generate_snapshot()

**位置**: `app/models/product_code.py:265`

**用法**:
```python
product_code = ProductCode.query.get(id)
snapshot = product_code.generate_snapshot()
```

**返回结构**:
```python
{
    "version": "1.0",
    "generated_at": "2025-12-24T10:30:00",
    "product_code_id": 123,
    "full_code": "BC4I2X4NN",
    "category": {
        "id": 1,
        "name": "对讲机",
        "code_letter": "R"
    },
    "subcategory": {
        "id": 2,
        "name": "手持对讲机",
        "code_letter": "B"
    },
    "region": {
        "id": 5,
        "name": "中国",
        "code": "C"
    },
    "code_parts": [
        {
            "position": 1,
            "field_name": "频段",
            "field_id": 10,
            "option_id": 101,
            "code": "3",
            "value": "400-470MHz",
            "description": "UHF频段"
        }
    ]
}
```

#### 2. generate_product_snapshot()

**位置**: `app/utils/product_helpers.py:180`

**用法**:
```python
from app.utils.product_helpers import generate_product_snapshot

# 研发产品入库时
snapshot = generate_product_snapshot(product, source="dev_product", dev_product=dev_product)

# 手动创建时
snapshot = generate_product_snapshot(product, source="manual_create")

# 手动编辑时
snapshot = generate_product_snapshot(product, source="manual_update")
```

**返回结构**:
```python
{
    "version": "1.0",
    "source": "dev_product",          # 来源标识
    "dev_product_id": 456,            # 研发产品ID（如适用）
    "generated_at": "2025-12-24T10:30:00",
    "full_code": "BC4I2X4NN",
    "category": {...},
    "subcategory": {...},
    "code_parts": [
        {
            "position": 1,
            "field_name": "频段",
            "field_code": "3",
            "code": "3",
            "value": "400-470MHz",
            "unit": "MHz",
            "use_in_code": true,
            "description": ""
        }
    ]
}
```

### 编码来源
- `ProductCodeField` - 编码字段定义
- `ProductCodeFieldOption` - 字段选项和编码映射

---

## 新系统：SpecTemplate/ProductConfiguration

### 适用场景
- 规格模板配置版本的MN编码生成
- 规格配置矩阵保存时自动生成快照
- MN编码规则变更追溯

### 数据表结构

```
spec_templates              # 规格模板表
  └── version               # 模板版本

spec_template_items         # 模板规格项
  └── use_in_code           # 是否参与编码
  └── code_length           # 编码长度（1或2位）
  └── options               # 值→编码映射 (JSON)

product_configurations      # 产品配置版本
  └── mn_code               # MN编码
  └── code_rule_version     # 规则版本号
  └── code_rule_snapshot    # 编码规则快照 (JSON)

product_config_values       # 配置规格值
  └── value                 # 具体规格值
```

### 快照函数

#### 1. generate_code_rule_snapshot()

**位置**: `app/views/spec_template.py:24`

**用法**:
```python
from app.views.spec_template import generate_code_rule_snapshot

snapshot = generate_code_rule_snapshot(config, mn_code, code_items_data)
```

**返回结构**:
```python
{
    "version": "V1.0",
    "generated_at": "2025-12-24T10:30:00",
    "template": {
        "id": 1,
        "model": "PD662",
        "version": "V1.0"
    },
    "category": {
        "id": 1,
        "code": "R"
    },
    "subcategory": {
        "id": 2,
        "code": "B"
    },
    "region": "CN",
    "code_items": [
        {
            "item_id": 10,
            "definition_name": "频段",
            "display_order": 1,
            "code_length": 1,
            "options": {"400-470": "3", "450-520": "4"},
            "value": "400-470",
            "code_char": "3"
        }
    ],
    "mn_code": "CNRB3XXXX..."
}
```

#### 2. generate_mn_code()

**位置**: `app/views/spec_template.py:60`

**用法**:
```python
from app.views.spec_template import generate_mn_code

# 生成编码并保存快照（默认）
mn_code = generate_mn_code(config)

# 仅生成编码，不保存快照
mn_code = generate_mn_code(config, save_snapshot=False)
```

**自动行为**:
- 当 `save_snapshot=True` 时，自动设置:
  - `config.code_rule_version = CODE_RULE_VERSION`
  - `config.code_rule_snapshot = {...}`

### 编码来源
- `SpecTemplateItem.options` - 值→编码映射（JSON）
- 编码动态分配：`allocate_next_code()` 和 `ensure_code_for_value()`

### 版本常量

**位置**: `app/models/spec_template.py:524`

```python
CODE_RULE_VERSION = "V1.0"
```

当编码规则发生重大变化时，更新此常量。

---

## 主要区别

### 1. 编码映射来源

| 系统 | 编码映射来源 | 说明 |
|-----|------------|------|
| 老系统 | `ProductCodeField` + `ProductCodeFieldOption` | 全局定义，按分类/子分类级别 |
| 新系统 | `SpecTemplateItem.options` | 模板级别，每个规格项独立维护 |

### 2. 版本号管理

| 系统 | 版本号位置 | 查询方式 |
|-----|----------|---------|
| 老系统 | 快照JSON内部 `version: "1.0"` | 需解析JSON |
| 新系统 | 独立字段 `code_rule_version` | 可直接查询过滤 |

### 3. 触发时机

| 系统 | 触发场景 |
|-----|---------|
| 老系统 | 研发产品入库、手动创建/编辑标准产品 |
| 新系统 | 规格配置矩阵保存MN编码时 |

---

## 快速查询示例

### 老系统：查找有快照的产品

```python
from app.models.product import Product

products_with_snapshot = Product.query.filter(
    Product.code_definition_snapshot.isnot(None)
).all()
```

### 新系统：查找特定版本的配置

```python
from app.models.spec_template import ProductConfiguration

# 查找 V1.0 版本的配置
configs_v1 = ProductConfiguration.query.filter(
    ProductConfiguration.code_rule_version == 'V1.0'
).all()

# 查找有快照的配置
configs_with_snapshot = ProductConfiguration.query.filter(
    ProductConfiguration.code_rule_snapshot.isnot(None)
).all()
```

---

## 相关文件索引

### 老系统文件
- `app/models/product.py` - Product 模型（含 `code_definition_snapshot` 字段）
- `app/models/product_code.py` - ProductCode 模型（含 `generate_snapshot()` 方法）
- `app/utils/product_helpers.py` - `generate_product_snapshot()` 函数

### 新系统文件
- `app/models/spec_template.py` - ProductConfiguration 模型（含快照字段和 `CODE_RULE_VERSION` 常量）
- `app/views/spec_template.py` - `generate_code_rule_snapshot()` 和 `generate_mn_code()` 函数

---

**文档版本**: 1.0
**创建日期**: 2025-12-24
**最后更新**: 2025-12-24
