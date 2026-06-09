# PMA 库存系统设计规范

## 仓库两种类型

| 类型 | 标识 | 归属 |
|---|---|---|
| **客户/经销商仓库** | `inventory.company_id IS NOT NULL` + `is_vendor_warehouse=false` | 指向 `companies` 表实例(distributor / dealer / integrator 等) |
| **厂商自营仓库**(系统级) | `inventory.company_id IS NULL` + `is_vendor_warehouse=true` | 系统级,**不在 `companies` 表**;显示名取自字典 |

## 厂商定义在哪里

**唯一权威**:`dictionaries` 表
```sql
SELECT id, value FROM dictionaries
WHERE type='company' AND is_vendor=true AND is_active=true;
-- 本地示例:id=27, value='和源通信(上海)股份有限公司'
```

- ❌ **不要**在 `companies` 表里建 vendor 公司
- ❌ **不要**用 `Company.query.filter_by(company_type='vendor')` 找厂商
- ✅ 后端写入库存:`update_inventory(target_type='vendor', company_id=None, ...)`
- ✅ 后端读取/UI 展示名:`get_vendor_warehouse_label()` (`app/utils/inventory_helpers.py`)
- ✅ 用户是不是厂商员工:`user.is_vendor_user()` (`app/models/user.py:514`)

## 唯一约束 (PG partial unique index)

```sql
-- 客户仓:同一公司同一产品唯一
CREATE UNIQUE INDEX uniq_inventory_customer_product
ON inventory (company_id, product_id) WHERE company_id IS NOT NULL;

-- 厂商仓:同产品全系统唯一
CREATE UNIQUE INDEX uniq_inventory_vendor_product
ON inventory (product_id) WHERE is_vendor_warehouse = true;
```

## update_inventory API

```python
from app.utils.inventory_helpers import update_inventory

# 客户仓库(默认)
update_inventory(
    company_id=customer_id, product_id=11, quantity_change=1,
    transaction_type='in', reference_type='shipment', reference_id=42,
    description='...', user_id=current_user.id
)

# 厂商自营仓(target_type='vendor', company_id 传 None)
update_inventory(
    company_id=None, target_type='vendor',
    product_id=11, quantity_change=1,
    transaction_type='in', reference_type='order', reference_id=po.id,
    description='采购订单 PO123 备货入库', user_id=current_user.id
)
```

## 库存页面 scope 路由

`/inventory/at_stock/<scope>` 路由参数 `scope`:

| scope | 含义 |
|---|---|
| (缺省) | 默认:用户的 linked_company_id;admin 无绑定 → 第一家有库存的客户公司 |
| `global` | 全局聚合视图(仅厂商管理员可见;含客户仓 + 厂商仓) |
| `vendor` | 厂商自营仓库视图(系统级) |
| 数字字符串 | 指定客户公司 ID |

## 已接入的业务流

| 业务 | 入仓时机 | target_type |
|---|---|---|
| 采购订单备货入库(`detail.sales_order_detail_id IS NULL`) | PO 全部签收 / 主动触发验收入库 | `'vendor'` |
| 客户订单签收入库(`shipment.sales_order_id`) | 发货单签收 | `'customer'` (sales_order.customer_id) |

## 新业务接入清单

> 假设某新业务也要写入库存。

1. **明确仓库归属**:
   - 入客户仓 → `target_type='customer'` + 传 `company_id`
   - 入厂商仓 → `target_type='vendor'` + `company_id=None`
2. **调 `update_inventory(...)`**(不要直接操作 Inventory ORM)
3. **如有 SN**:调 `link_serials_to_inventory(purchase_detail_id, inventory_id, user_id)` 把 SN 绑定到库存

## 改动历史

- **2026-05-31** 厂商系统级仓库改造:
  - 模型加 `is_vendor_warehouse` + `company_id` 改 nullable + partial unique index
  - `update_inventory` 加 `target_type` 参数
  - 6 处 `Company.query.filter_by(company_type='vendor')` 全部替换为新机制
  - 库存页面加 `scope='vendor'` 视图 + `_switchable_companies` 自动注入厂商条目
  - 数据回填:历史 SHP-002 的备货明细补入厂商仓 1 条
  - alembic: `inventory_vendor_warehouse_20260531`
