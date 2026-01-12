# 采购订单(PO)与客户订单(SO)模块设计方案

## 一、业务需求概述

### 需求来源
- 参考 `EVERTAC_PO_Template_International.docx` 模板
- 建立完整的采购订单管理流程
- 与现有销售端模块（批价单、结算单）配合

### 核心功能
1. **采购订单管理** - 扩展现有 PurchaseOrder
2. **测试管理** - 工厂测试（必须）+ 现场FAT/到货测试（二选一）
3. **客户订单** - 从批价单转换，包含物流交付信息
4. **序列号追溯** - 从入库到出库的全生命周期追踪

---

## 二、系统架构

```
【采购端】                              【销售端】

PurchaseOrder(采购PO)                  Project(项目)
     ↓                                      ↓
生产进度跟踪                            Quotation(报价单)
     ↓                                      ↓
┌────────────────────┐                 PricingOrder(批价单)
│ 工厂测试（必须）    │                      ↓
│ + 现场FAT/到货测试  │                 SalesOrder(客户订单) ← 新增
│   （二选一）        │                      ↓
└────────────────────┘                 Shipment(发货出库)
     ↓                                      ↓
物流发货 → 验收入库                    客户签收
     ↓
ProductSerialNumber ←──────────────────→ 序列号出库
     ↓
═══════════════ Inventory(库存) ═══════════════
```

---

## 三、数据模型设计

### 3.1 扩展 PurchaseOrder（采购订单）

**文件**: `app/models/inventory.py`

新增字段：
```python
# PO模板字段
revision = Column(String(20))  # 版本号 Rev.01
incoterms = Column(String(20))  # 贸易术语 DDP/FOB
order_category = Column(String(20))  # 订单类别 channel/direct

# 供应商确认
supplier_confirmed = Column(Boolean, default=False)
supplier_confirmed_date = Column(DateTime)
supplier_confirmed_by = Column(String(100))

# 交货信息
required_date = Column(DateTime)  # 需求日期
confirmed_date = Column(DateTime)  # 确认日期
ship_to = Column(Text)  # 交货地点
shipping_method = Column(String(50))  # 运输方式
freight_terms = Column(String(20))  # 运费承担

# 测试配置
verification_test_type = Column(String(20))  # site_fat / incoming
factory_test_status = Column(String(20), default='pending')
verification_test_status = Column(String(20), default='pending')

# 项目关联（可选，支持需求驱动采购）
project_id = Column(Integer, ForeignKey('projects.id'))  # 可选
sales_order_id = Column(Integer, ForeignKey('sales_orders.id'))  # 可选

# 生产跟踪
production_status = Column(String(20), default='not_started')
production_progress = Column(Integer, default=0)

# 物流信息
carrier = Column(String(100))
tracking_number = Column(String(100))
ship_date = Column(DateTime)
arrival_date = Column(DateTime)

# 验收信息
acceptance_status = Column(String(20), default='pending')
acceptance_date = Column(DateTime)
acceptance_by_id = Column(Integer, ForeignKey('users.id'))
acceptance_documents = Column(Text)  # JSON
```

### 3.2 新增 ProductTest（产品测试记录）

**文件**: `app/models/product_test.py`（新建）

```python
class ProductTest(db.Model):
    __tablename__ = 'product_tests'

    id = Column(Integer, primary_key=True)
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'))
    purchase_detail_id = Column(Integer, ForeignKey('purchase_order_details.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    serial_number_id = Column(Integer, ForeignKey('product_serial_numbers.id'))

    # 测试分类
    test_category = Column(String(20))  # factory / verification
    test_type = Column(String(20))  # factory_self / site_fat / incoming

    # 测试内容
    test_items = Column(Text)  # JSON
    test_date = Column(DateTime)
    test_location = Column(String(200))

    # 测试人员
    tester_id = Column(Integer, ForeignKey('users.id'))
    supplier_tester = Column(String(100))

    # 结果
    result = Column(String(20))  # passed/failed/conditional
    issues = Column(Text)
    resolution = Column(Text)

    # 附件
    documents = Column(Text)  # JSON
    report_file = Column(String(500))

    notes = Column(Text)
    created_by_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

### 3.3 新增 SalesOrder（客户订单）

**文件**: `app/models/sales_order.py`（新建）

```python
class SalesOrder(db.Model):
    __tablename__ = 'sales_orders'

    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True)  # SO202501-001
    pricing_order_id = Column(Integer, ForeignKey('pricing_orders.id'))
    project_id = Column(Integer, ForeignKey('projects.id'))
    customer_id = Column(Integer, ForeignKey('companies.id'))

    # 交付信息
    delivery_date = Column(DateTime)
    delivery_address = Column(Text)
    delivery_contact = Column(String(100))
    delivery_phone = Column(String(50))
    delivery_email = Column(String(100))

    # 物流信息
    shipping_method = Column(String(50))
    freight_terms = Column(String(20))
    incoterms = Column(String(20))
    carrier = Column(String(100))
    tracking_number = Column(String(100))
    ship_date = Column(DateTime)
    arrival_date = Column(DateTime)
    actual_arrival_date = Column(DateTime)

    # 签收信息
    received_by = Column(String(100))
    received_date = Column(DateTime)
    received_documents = Column(Text)  # JSON

    # 金额
    total_amount = Column(Numeric(15, 2))
    total_quantity = Column(Integer)
    currency = Column(String(10), default='CNY')

    # 状态
    status = Column(String(20), default='draft')
    # draft/confirmed/preparing/shipped/delivered/completed/cancelled

    notes = Column(Text)
    created_by_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SalesOrderDetail(db.Model):
    __tablename__ = 'sales_order_details'

    id = Column(Integer, primary_key=True)
    sales_order_id = Column(Integer, ForeignKey('sales_orders.id'))
    pricing_detail_id = Column(Integer, ForeignKey('pricing_order_details.id'))
    product_id = Column(Integer, ForeignKey('products.id'))

    product_name = Column(String(200))
    product_model = Column(String(100))
    specification = Column(Text)
    quantity = Column(Integer)
    unit = Column(String(20))
    unit_price = Column(Numeric(15, 2))
    total_price = Column(Numeric(15, 2))

    shipped_quantity = Column(Integer, default=0)
    received_quantity = Column(Integer, default=0)
    status = Column(String(20), default='pending')

    notes = Column(Text)
```

### 3.4 新增 Shipment（发货记录）

**文件**: `app/models/shipment.py`（新建）

```python
class Shipment(db.Model):
    __tablename__ = 'shipments'

    id = Column(Integer, primary_key=True)
    shipment_number = Column(String(50), unique=True)  # SHP202501-001
    sales_order_id = Column(Integer, ForeignKey('sales_orders.id'))

    # 物流信息
    carrier = Column(String(100))
    tracking_number = Column(String(100))
    shipping_method = Column(String(50))
    ship_date = Column(DateTime)
    expected_arrival = Column(DateTime)
    freight_cost = Column(Numeric(15, 2))
    freight_payer = Column(String(20))

    # 地址
    ship_from = Column(Text)
    ship_to = Column(Text)
    contact_name = Column(String(100))
    contact_phone = Column(String(50))

    # 附件和状态
    documents = Column(Text)  # JSON
    status = Column(String(20), default='pending')

    notes = Column(Text)
    created_by_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ShipmentDetail(db.Model):
    __tablename__ = 'shipment_details'

    id = Column(Integer, primary_key=True)
    shipment_id = Column(Integer, ForeignKey('shipments.id'))
    sales_order_detail_id = Column(Integer, ForeignKey('sales_order_details.id'))
    product_id = Column(Integer, ForeignKey('products.id'))

    quantity = Column(Integer)
    unit = Column(String(20))
    serial_numbers = Column(Text)  # JSON [序列号列表]

    notes = Column(Text)
```

### 3.5 新增 ProductSerialNumber（产品序列号）

**文件**: `app/models/product_serial_number.py`（新建）

```python
class ProductSerialNumber(db.Model):
    __tablename__ = 'product_serial_numbers'

    id = Column(Integer, primary_key=True)
    serial_number = Column(String(100), unique=True)
    product_id = Column(Integer, ForeignKey('products.id'))

    # 采购来源
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'))
    purchase_detail_id = Column(Integer, ForeignKey('purchase_order_details.id'))
    batch_number = Column(String(100))

    # 入库信息
    warehouse_in_date = Column(DateTime)
    warehouse_location = Column(String(100))
    inventory_id = Column(Integer, ForeignKey('inventory.id'))

    # 出库信息
    sales_order_id = Column(Integer, ForeignKey('sales_orders.id'))
    shipment_id = Column(Integer, ForeignKey('shipments.id'))
    ship_out_date = Column(DateTime)
    destination = Column(String(200))

    # 状态
    status = Column(String(20), default='registered')
    # registered/in_stock/reserved/shipped/delivered

    # 测试记录
    test_passed = Column(Boolean)
    test_date = Column(DateTime)
    test_id = Column(Integer, ForeignKey('product_tests.id'))

    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

---

## 四、状态流转设计

### 4.1 PurchaseOrder 状态

```
draft → pending → approved → confirmed → producing → tested → shipped → stored → completed
  ↓                  ↓
cancelled         rejected
```

| 状态 | 说明 | 触发条件 |
|-----|------|---------|
| draft | 草稿 | 新建 |
| pending | 内部审批中 | 提交审批 |
| approved | 审批通过 | 审批完成 |
| confirmed | 供应商确认 | 供应商确认订单 |
| producing | 生产中 | 开始生产 |
| tested | 测试通过 | 工厂测试+验证测试都通过 |
| shipped | 已发货 | 供应商发货 |
| stored | 已入库 | 验收入库完成 |
| completed | 已完成 | 订单关闭 |

### 4.2 SalesOrder 状态

```
draft → confirmed → preparing → shipped → delivered → completed
  ↓
cancelled
```

| 状态 | 说明 | 触发条件 |
|-----|------|---------|
| draft | 草稿 | 从批价单转换 |
| confirmed | 已确认 | 确认订单 |
| preparing | 备货中 | 开始备货 |
| shipped | 已发货 | 创建发货单 |
| delivered | 已送达 | 客户签收 |
| completed | 已完成 | 订单关闭 |

### 4.3 ProductSerialNumber 状态

```
registered → in_stock → reserved → shipped → delivered
```

---

## 五、测试管理逻辑

### 5.1 测试类型

| 类型 | 说明 | 执行者 | 时机 |
|-----|------|--------|------|
| factory_self | 工厂测试 | 供应商 | 发货前（必须） |
| site_fat | 现场FAT | 我方人员 | 发货前（可选） |
| incoming | 到货测试 | 我方人员 | 入库时（可选） |

### 5.2 业务规则

1. **工厂测试（必须）**：供应商必须提供测试报告
2. **验证测试（二选一）**：创建PO时选择 site_fat 或 incoming
3. **发货条件**：
   - 工厂测试必须通过
   - 如选择 site_fat，现场FAT必须通过
4. **入库条件**：
   - 如选择 incoming，到货测试必须通过

---

## 六、用户确认事项

1. **PO关联方式**: 两种都支持（可关联项目/订单，也可独立采购）
2. **序列号录入**: 两种都支持（Excel批量导入 + 手动录入）

---

## 七、现有采购订单分析

**现有 PurchaseOrder 模型**：`app/models/inventory.py:111-172`

已有功能：
- 订单号、供应商、日期、状态、金额
- 明细表（产品、数量、单价、已收货数量）
- 基本的入库状态计算

需要扩展：
- PO模板字段（版本号、贸易术语等）
- 供应商确认机制
- 测试管理
- 生产进度跟踪
- 验收流程
- PO导出功能

**策略**: 扩展现有模型，保留已有数据

---

## 八、实施步骤

### Phase 1: 数据库迁移
1. 扩展 PurchaseOrder 模型（新增字段）
2. 创建 ProductTest 表
3. 创建 SalesOrder / SalesOrderDetail 表
4. 创建 Shipment / ShipmentDetail 表
5. 创建 ProductSerialNumber 表

### Phase 2: 采购端功能
1. PurchaseOrder 编辑页面增加新字段
2. 生产进度跟踪功能
3. 测试记录管理（工厂测试/现场FAT/到货测试）
4. 验收入库功能
5. PO单导出（按模板格式）

### Phase 3: 销售端功能
1. 从批价单创建客户订单
2. 客户订单管理页面
3. 发货出库功能
4. 物流跟踪
5. 客户签收确认

### Phase 4: 序列号追溯
1. 序列号录入
   - Excel批量导入（模板下载、数据校验）
   - 手动录入界面
2. 入库登记关联序列号
3. 出库关联序列号
4. 全生命周期查询

### Phase 5: 菜单与权限配置
1. 修改 `tw_nav_menu.html`
   - 拆分"订单结算"为"销售管理"+"采购仓储"两组
   - 添加新菜单项
2. 添加新权限模块到 `permissions` 表
   - sales_order, shipment, purchase_order, serial_number
3. 配置角色默认权限
4. 翻译更新 `messages.po`

---

## 九、与现有模块关系

| 现有模块 | 用途 | 新模块 | 关系 |
|---------|------|--------|------|
| PricingOrder | 销售定价 | SalesOrder | 转换关系 |
| SettlementOrder | 代理商结算 | - | 独立 |
| Inventory | 库存数量 | ProductSerialNumber | 关联入库 |
| PurchaseOrder | 采购订单 | 扩展 | 增加字段 |

**结论：不冲突，互补关系**

---

## 十、关键文件

### 需要修改
- `app/models/inventory.py` - 扩展 PurchaseOrder
- `app/templates/components/tw_nav_menu.html` - 菜单重构

### 需要新建
- `app/models/product_test.py`
- `app/models/sales_order.py`
- `app/models/shipment.py`
- `app/models/product_serial_number.py`
- `app/routes/sales_order_routes.py`
- `app/routes/shipment_routes.py`
- `app/routes/product_test_routes.py`
- `app/routes/product_sn_routes.py`
- `app/services/sales_order_service.py`
- `app/templates/sales_order/*.html`
- `app/templates/shipment/*.html`
- `app/templates/product_test/*.html`

### 迁移文件
- `migrations/versions/add_purchase_order_fields_*.py`
- `migrations/versions/create_product_test_*.py`
- `migrations/versions/create_sales_order_*.py`
- `migrations/versions/create_shipment_*.py`
- `migrations/versions/create_product_serial_number_*.py`

---

## 十一、前端页面设计

### 11.1 采购订单模块（PurchaseOrder）

#### 页面清单

| 页面 | 文件路径 | 类型 | 说明 |
|-----|---------|------|------|
| 采购订单列表 | `inventory/tw_purchase_order_list.html` | 页面 | 主列表页，筛选、统计 |
| 采购订单详情 | `inventory/tw_purchase_order_detail.html` | 页面 | 详情页，使用 tw_detail_layout |
| 创建采购订单 | - | 模态框 | 新建PO表单 |
| 编辑基本信息 | - | 模态框 | 编辑PO基本信息 |
| 供应商确认 | - | 模态框 | 记录供应商确认 |
| 生产进度更新 | - | 模态框 | 更新生产进度 |
| 添加订单明细 | - | 模态框 | 添加产品明细 |
| 导出PO单 | - | 模态框 | 按模板格式导出PDF |
| 上传测试报告 | - | 模态框 | 上传工厂测试/现场FAT/到货测试报告 |

#### 列表页设计 (`tw_purchase_order_list.html`)

```
┌────────────────────────────────────────────────────────────────┐
│ 采购订单管理                                    [+ 新建采购订单] │
├────────────────────────────────────────────────────────────────┤
│ 统计卡片 (tw_stat_cards_grid cols=5)                           │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                  │
│ │全部  │ │待确认│ │生产中│ │已发货│ │已入库│                  │
│ │ 150  │ │  12  │ │  28  │ │   8  │ │ 102  │                  │
│ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘                  │
├────────────────────────────────────────────────────────────────┤
│ 筛选栏 (tw_filter_bar)                                         │
│ [状态 ▼] [供应商 ▼] [测试状态 ▼] [日期范围] [🔍 搜索]         │
├────────────────────────────────────────────────────────────────┤
│ 数据表格 (tw_data_table)                                       │
│ ┌────────┬────────┬────────┬────────┬────────┬────────┬─────┐ │
│ │ PO单号 │ 供应商 │ 金额   │ 状态   │ 测试   │ 交期   │操作 │ │
│ ├────────┼────────┼────────┼────────┼────────┼────────┼─────┤ │
│ │CG-2501 │杭州长泽│¥91,554 │🟡生产中│✅工厂 │02-10  │ ⋮  │ │
│ │CG-2502 │深圳XX  │¥45,200 │🔵待确认│⏳待测 │02-15  │ ⋮  │ │
│ └────────┴────────┴────────┴────────┴────────┴────────┴─────┘ │
└────────────────────────────────────────────────────────────────┘
```

**使用组件**：
- `tw_layout` - 主布局
- `tw_fixed_header_page` - 固定头部
- `tw_stat_card` - 统计卡片（5个：全部/待确认/生产中/已发货/已入库）
- `tw_filter_bar` - 筛选栏
- `tw_data_table` - 数据表格
- `tw_btn` - 按钮

#### 详情页设计 (`tw_purchase_order_detail.html`)

```
┌────────────────────────────────────────────────────────────────────────┐
│ 面包屑: 采购管理 > 采购订单 > CG-2501-001                              │
│ [返回] [← →]                    [🟡生产中] [编辑] [删除] [导出PO]      │
├──────────────────────────────────────────────┬─────────────────────────┤
│ 左侧主内容 (col-span-2)                       │ 右侧边栏 (sticky)       │
│                                              │                         │
│ ┌──────────────────────────────────────────┐ │ ┌─────────────────────┐ │
│ │ 基本信息 (tw_info_card)                  │ │ │ 操作面板            │ │
│ │ 供应商: 杭州长泽科技                      │ │ │ ┌─────────────────┐ │ │
│ │ 订单日期: 2025-01-15                     │ │ │ │[📋 供应商确认]  │ │ │
│ │ 需求日期: 2025-02-10                     │ │ │ │[📦 更新进度]    │ │ │
│ │ 确认日期: 待确认                         │ │ │ │[🧪 上传测试报告]│ │ │
│ │ 贸易术语: DDP Shanghai                   │ │ │ │[🚚 确认发货]    │ │ │
│ │ 运输方式: 汽运                           │ │ │ │[✅ 验收入库]    │ │ │
│ └──────────────────────────────────────────┘ │ │ └─────────────────┘ │ │
│                                              │ └─────────────────────┘ │
│ ┌──────────────────────────────────────────┐ │                         │
│ │ 生产进度 (自定义卡片)         [更新进度] │ │ ┌─────────────────────┐ │
│ │ ╔════════════════════════╗              │ │ │ 测试状态            │ │
│ │ ║██████████░░░░░░░░░░░░░░║ 45%          │ │ │ ✅ 工厂测试: 通过   │ │
│ │ ╚════════════════════════╝              │ │ │ ⏳ 现场FAT: 待执行  │ │
│ │ 当前阶段: 生产中                         │ │ └─────────────────────┘ │
│ │ 预计完成: 2025-02-05                     │ │                         │
│ └──────────────────────────────────────────┘ │ ┌─────────────────────┐ │
│                                              │ │ 物流信息            │ │
│ ┌──────────────────────────────────────────┐ │ │ 承运商: -           │ │
│ │ 订单明细 (tw_table_card)      [添加产品] │ │ │ 运单号: -           │ │
│ │ ┌────┬────────┬──────┬────┬──────┬────┐  │ │ │ 发货日期: -         │ │
│ │ │行号│产品描述│型号  │数量│单价  │金额│  │ │ └─────────────────────┘ │
│ │ ├────┼────────┼──────┼────┼──────┼────┤  │ │                         │
│ │ │ 1  │智能光纤│RFT-..│ 17 │5,162 │87K │  │ │ ┌─────────────────────┐ │
│ │ │ 2  │系统合路│E-FHP│  2 │1,900 │3.8K│  │ │ │ 元数据              │ │
│ │ └────┴────────┴──────┴────┴──────┴────┘  │ │ │ 创建人: 张三        │ │
│ │ 合计: ¥91,554.00                         │ │ │ 创建时间: 01-15     │ │
│ └──────────────────────────────────────────┘ │ │ 更新时间: 01-18     │ │
│                                              │ └─────────────────────┘ │
├──────────────────────────────────────────────┴─────────────────────────┤
│ 全宽区域                                                               │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ 测试记录 (Tabs: 工厂测试 | 验证测试)                               │ │
│ │ ┌────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 工厂测试报告                                    [上传测试报告] │ │ │
│ │ │ 📄 测试报告_RFT-BDA310.pdf         2025-01-20   ✅ 已审核      │ │ │
│ │ │ 📄 出厂检验报告.pdf                 2025-01-20   ✅ 已审核      │ │ │
│ │ └────────────────────────────────────────────────────────────────┘ │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ 验收记录 (时间线)                                                  │ │
│ │ ○ 2025-01-15 创建采购订单                                         │ │
│ │ ○ 2025-01-16 供应商确认订单                                       │ │
│ │ ● 2025-01-20 工厂测试报告已上传                                   │ │
│ │ ◌ 待发货                                                          │ │
│ │ ◌ 待验收入库                                                      │ │
│ └────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

**使用组件**：
- `tw_detail_layout` - 详情页布局
- `tw_info_card` - 基本信息卡片
- `tw_card_shell` - 生产进度卡片（自定义内容）
- `tw_table_card` - 订单明细表格
- `tw_tabs` - 测试记录标签页
- `tw_file_preview` - 文件预览
- `tw_metadata_card_simple` - 元数据卡片
- 新组件: `tw_progress_bar` - 进度条
- 新组件: `tw_timeline` - 时间线

#### 模态框设计

**1. 创建采购订单模态框**
```
┌─────────────────────────────────────────────────────┐
│ 新建采购订单                                         │
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 基本信息                                        │ │
│ │ 供应商 *     [选择供应商 ▼]                     │ │
│ │ 订单类别     [渠道订单 ▼]                       │ │
│ │ 需求日期 *   [📅 2025-02-10]                   │ │
│ │ 贸易术语     [DDP ▼]                           │ │
│ │ 运输方式     [汽运 ▼]                          │ │
│ │ 运费承担     [○供应商 ●采购方]                  │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 测试要求                                        │ │
│ │ 验证测试方式  [○现场FAT ●到货测试]              │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 交货信息                                        │ │
│ │ 交货地点     [上海市普陀区...]                  │ │
│ │ 付款条件     [50%预付，发货后45天付清]          │ │
│ │ 备注         [                    ]             │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│                           [取消]  [创建采购订单]    │
└─────────────────────────────────────────────────────┘
```

**2. 生产进度更新模态框**
```
┌─────────────────────────────────────────────────────┐
│ 更新生产进度                                         │
│                                                     │
│ 当前阶段     [备料 ▼]                               │
│              ○ 备料                                 │
│              ○ 生产                                 │
│              ○ 测试                                 │
│              ○ 包装                                 │
│              ○ 待发货                               │
│                                                     │
│ 进度百分比   [══════════○══════] 45%                │
│                                                     │
│ 预计完成日期 [📅 2025-02-05]                        │
│                                                     │
│ 备注说明     [生产进展顺利，预计提前完成]            │
│                                                     │
│                              [取消]  [保存]         │
└─────────────────────────────────────────────────────┘
```

**3. 上传测试报告模态框**
```
┌─────────────────────────────────────────────────────┐
│ 上传测试报告                                         │
│                                                     │
│ 测试类型     ● 工厂测试报告                         │
│              ○ 现场FAT报告                          │
│              ○ 到货测试报告                         │
│                                                     │
│ 测试日期     [📅 2025-01-20]                        │
│                                                     │
│ 测试人员     [供应商测试工程师姓名]                  │
│                                                     │
│ 测试结果     [● 通过 ○ 不通过 ○ 有条件通过]         │
│                                                     │
│ 上传文件     ┌────────────────────────────────────┐ │
│              │  📎 点击或拖拽上传文件              │ │
│              │     支持 PDF, Word, 图片           │ │
│              └────────────────────────────────────┘ │
│              📄 测试报告.pdf ✕                      │
│                                                     │
│ 问题说明     [如有问题请填写]                        │
│                                                     │
│                              [取消]  [保存]         │
└─────────────────────────────────────────────────────┘
```

---

### 11.2 客户订单模块（SalesOrder）

#### 页面清单

| 页面 | 文件路径 | 类型 | 说明 |
|-----|---------|------|------|
| 客户订单列表 | `sales_order/tw_list.html` | 页面 | 主列表页 |
| 客户订单详情 | `sales_order/tw_detail.html` | 页面 | 详情页 |
| 从批价单创建 | - | 模态框 | 从批价单转换（含交付信息收集） |
| 编辑交付信息 | - | 模态框 | 编辑交付地址等 |
| 创建发货单 | - | 模态框 | 发货出库 |

#### 从批价单创建客户订单模态框

```
┌─────────────────────────────────────────────────────────────────┐
│ 创建客户订单                                    来源: PO-2501-001 │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 订单信息 (自动填充)                                         │ │
│ │ 批价单号: PO-2501-001                                       │ │
│ │ 客户: 上海XX公司                                            │ │
│ │ 项目: 上海XX通信项目                                        │ │
│ │ 订单金额: ¥91,554.00                                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 交付信息 *                                                  │ │
│ │ 期望交付日期 * [📅 2025-02-15]                              │ │
│ │ 交付地址 *     [上海市浦东新区XX路XX号]                     │ │
│ │               [从客户地址选择 ▼] 快捷填充                    │ │
│ │ 联系人 *       [李经理]                                     │ │
│ │ 联系电话 *     [138-xxxx-xxxx]                              │ │
│ │ 联系邮箱       [li@example.com]                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 物流方式                                                    │ │
│ │ 运输方式       [● 汽运 ○ 空运 ○ 快递 ○ 自提]               │ │
│ │ 贸易术语       [DDP ▼]                                      │ │
│ │ 运费承担       [● 卖方 ○ 买方]                              │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 订单明细 (从批价单复制，可编辑数量)                          │ │
│ │ ┌────────┬────────┬────────┬────────┬────────────────────┐ │ │
│ │ │ 产品   │ 型号   │ 批价数 │ 订购数 │ 单价               │ │ │
│ │ ├────────┼────────┼────────┼────────┼────────────────────┤ │ │
│ │ │智能光纤│RFT-310 │  20    │ [17]   │ ¥5,162.00          │ │ │
│ │ │系统合路│E-FHP   │   5    │ [ 2]   │ ¥1,900.00          │ │ │
│ │ └────────┴────────┴────────┴────────┴────────────────────┘ │ │
│ │ 订购总额: ¥91,554.00                                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ 备注           [                                        ]       │
│                                                                 │
│                         [取消]  [保存为草稿]  [创建并确认]      │
└─────────────────────────────────────────────────────────────────┘
```

**交互说明**：
- 从批价单点击"创建客户订单"触发
- 自动填充订单信息，用户补充交付信息
- "从客户地址选择"下拉可快速填充已保存的收货地址
- 订购数量可调整（不超过批价数量）
- "保存为草稿"创建draft状态，"创建并确认"直接confirmed

#### 详情页设计 (`sales_order/tw_detail.html`)

```
┌────────────────────────────────────────────────────────────────────────┐
│ 面包屑: 销售管理 > 客户订单 > SO-2501-001                              │
│ [返回] [← →]                    [🟡备货中] [编辑] [创建发货单]          │
├──────────────────────────────────────────────┬─────────────────────────┤
│ 左侧主内容                                    │ 右侧边栏               │
│                                              │                         │
│ ┌──────────────────────────────────────────┐ │ ┌─────────────────────┐ │
│ │ 订单信息 (tw_info_card)                  │ │ │ 物流跟踪            │ │
│ │ 客户: 上海XX公司                          │ │ │ ○ 待备货            │ │
│ │ 来源批价单: PO-2501-001                  │ │ │ ● 备货中            │ │
│ │ 关联项目: 上海XX通信项目                  │ │ │ ○ 已发货            │ │
│ │ 订单金额: ¥91,554.00                     │ │ │ ○ 运输中            │ │
│ │ 币种: CNY                                │ │ │ ○ 已签收            │ │
│ └──────────────────────────────────────────┘ │ └─────────────────────┘ │
│                                              │                         │
│ ┌──────────────────────────────────────────┐ │ ┌─────────────────────┐ │
│ │ 交付信息 (tw_info_card)       [编辑]     │ │ │ 发货记录            │ │
│ │ 交付日期: 2025-02-15                     │ │ │ 第1批: 10件 已签收  │ │
│ │ 交付地址: 上海市浦东新区...               │ │ │ 第2批: 9件 运输中   │ │
│ │ 联系人: 李经理                           │ │ └─────────────────────┘ │
│ │ 电话: 138-xxxx-xxxx                      │ │                         │
│ │ 运输方式: 汽运                           │ │ ┌─────────────────────┐ │
│ │ 贸易术语: DDP                            │ │ │ 元数据              │ │
│ └──────────────────────────────────────────┘ │ └─────────────────────┘ │
│                                              │                         │
│ ┌──────────────────────────────────────────┐ │                         │
│ │ 订单明细 (tw_table_card)                 │ │                         │
│ │ ┌────┬────────┬────┬────┬────┬────┬────┐ │ │                         │
│ │ │行号│产品    │数量│已发│已收│单价│金额│ │ │                         │
│ │ ├────┼────────┼────┼────┼────┼────┼────┤ │ │                         │
│ │ │ 1  │智能光纤│ 17 │ 10 │ 10 │5.1K│87K │ │ │                         │
│ │ │ 2  │系统合路│  2 │  2 │  0 │1.9K│3.8K│ │ │                         │
│ │ └────┴────────┴────┴────┴────┴────┴────┘ │ │                         │
│ └──────────────────────────────────────────┘ │                         │
└──────────────────────────────────────────────┴─────────────────────────┘
```

---

### 11.3 发货管理模块（Shipment）

#### 页面清单

| 页面 | 文件路径 | 类型 | 说明 |
|-----|---------|------|------|
| 发货记录列表 | `shipment/tw_list.html` | 页面 | 主列表页 |
| 发货记录详情 | `shipment/tw_detail.html` | 页面 | 详情页，含签收操作 |
| 创建发货单 | - | 模态框 | 在客户订单中创建 |
| 签收确认 | - | 模态框 | 客户签收操作 |

#### 列表页设计 (`shipment/tw_list.html`)

```
┌────────────────────────────────────────────────────────────────┐
│ 发货记录                                        [+ 创建发货单] │
├────────────────────────────────────────────────────────────────┤
│ 统计卡片 (tw_stat_cards_grid cols=5)                           │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                  │
│ │全部  │ │待发货│ │运输中│ │已送达│ │已签收│                  │
│ │ 120  │ │  15  │ │  28  │ │  12  │ │  65  │                  │
│ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘                  │
├────────────────────────────────────────────────────────────────┤
│ 筛选栏 (tw_filter_bar)                                         │
│ [状态 ▼] [客户订单 ▼] [承运商 ▼] [日期范围] [🔍 搜索运单号]   │
├────────────────────────────────────────────────────────────────┤
│ 数据表格 (tw_data_table)                                       │
│ ┌──────────┬────────┬──────┬────────┬────────┬────────┬─────┐ │
│ │ 发货单号 │ 客户   │ 承运商│ 运单号 │ 状态   │ 发货日 │ ⋮  │ │
│ ├──────────┼────────┼──────┼────────┼────────┼────────┼─────┤ │
│ │SHP-2501  │上海XX  │顺丰  │SF123.. │🟢已签收│01-25  │ ⋮  │ │
│ │SHP-2502  │北京YY  │德邦  │DB456.. │🔵运输中│01-26  │ ⋮  │ │
│ └──────────┴────────┴──────┴────────┴────────┴────────┴─────┘ │
└────────────────────────────────────────────────────────────────┘
```

#### 详情页设计 (`shipment/tw_detail.html`)

```
┌────────────────────────────────────────────────────────────────────────┐
│ 面包屑: 销售管理 > 发货出库 > SHP-2501-001                              │
│ [返回] [← →]                         [🔵运输中] [编辑] [确认签收]       │
├──────────────────────────────────────────────┬─────────────────────────┤
│ 左侧主内容 (col-span-2)                       │ 右侧边栏 (sticky)       │
│                                              │                         │
│ ┌──────────────────────────────────────────┐ │ ┌─────────────────────┐ │
│ │ 物流信息 (tw_info_card)                  │ │ │ 物流跟踪            │ │
│ │ 发货单号: SHP-2501-001                   │ │ │ ● 01-25 已发货      │ │
│ │ 客户订单: SO-2501-001                    │ │ │ │ 上海仓库发出      │ │
│ │ 客户: 上海XX公司                          │ │ │ ● 01-26 运输中      │ │
│ │ 承运商: 顺丰速运                         │ │ │ │ 已到达北京中转站   │ │
│ │ 运单号: SF1234567890                     │ │ │ ◌ 待送达            │ │
│ │ 发货日期: 2025-01-25                     │ │ │ ◌ 待签收            │ │
│ │ 预计到达: 2025-01-28                     │ │ └─────────────────────┘ │
│ │ 运费: ¥350.00 (卖方承担)                 │ │                         │
│ └──────────────────────────────────────────┘ │ ┌─────────────────────┐ │
│                                              │ │ 签收信息            │ │
│ ┌──────────────────────────────────────────┐ │ │ 状态: 待签收        │ │
│ │ 收货信息 (tw_info_card)                  │ │ │ [确认签收]          │ │
│ │ 收货地址: 上海市浦东新区XX路XX号          │ │ └─────────────────────┘ │
│ │ 联系人: 李经理                           │ │                         │
│ │ 联系电话: 138-xxxx-xxxx                  │ │ ┌─────────────────────┐ │
│ └──────────────────────────────────────────┘ │ │ 元数据              │ │
│                                              │ │ 创建人: 张三        │ │
│ ┌──────────────────────────────────────────┐ │ │ 创建时间: 01-25     │ │
│ │ 发货明细 (tw_table_card)                 │ │ └─────────────────────┘ │
│ │ ┌────┬────────┬────┬────────────────────┐│ │                         │
│ │ │行号│产品    │数量│序列号              ││ │                         │
│ │ ├────┼────────┼────┼────────────────────┤│ │                         │
│ │ │ 1  │智能光纤│ 10 │SN001,SN002...      ││ │                         │
│ │ │ 2  │系统合路│  2 │SN101,SN102         ││ │                         │
│ │ └────┴────────┴────┴────────────────────┘│ │                         │
│ └──────────────────────────────────────────┘ │                         │
├──────────────────────────────────────────────┴─────────────────────────┤
│ 全宽区域                                                               │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ 相关单据 (tw_file_upload compact模式)                              │ │
│ │ 📄 运单.pdf   📄 装箱单.pdf   📄 签收单.pdf                        │ │
│ └────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

#### 创建发货单模态框

```
┌─────────────────────────────────────────────────────────────────┐
│ 创建发货单                                                       │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 物流信息                                                    │ │
│ │ 承运商 *       [顺丰速运 ▼]                                 │ │
│ │ 运单号 *       [SF1234567890]                               │ │
│ │ 发货日期 *     [📅 2025-01-25]                              │ │
│ │ 预计到达       [📅 2025-01-28]                              │ │
│ │ 运费           [¥ 350.00]                                   │ │
│ │ 运费承担       [● 卖方 ○ 买方]                              │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 发货明细                                                    │ │
│ │ ┌────────────┬──────┬──────┬──────────────────────────────┐ │ │
│ │ │ 产品       │ 订购 │ 本次 │ 序列号                       │ │ │
│ │ ├────────────┼──────┼──────┼──────────────────────────────┤ │ │
│ │ │ 智能光纤   │  17  │ [10] │ [选择序列号...]              │ │ │
│ │ │ 系统合路   │   2  │ [ 2] │ [选择序列号...]              │ │ │
│ │ └────────────┴──────┴──────┴──────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 上传单据                                                    │ │
│ │ 📎 点击上传运单、装箱单等                                    │ │
│ │ 📄 运单.pdf ✕                                               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│                                    [取消]  [创建发货单]         │
└─────────────────────────────────────────────────────────────────┘
```

#### 签收确认模态框

```
┌─────────────────────────────────────────────────────────────────┐
│ 确认签收                                        使用 tw_confirm_modal │
│                                                                 │
│ ⚠️ 确认客户已签收此发货单？                                     │
│                                                                 │
│ 发货单号: SHP-2501-001                                          │
│ 客户: 上海XX公司                                                │
│ 产品数量: 12件                                                  │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 签收信息                                                    │ │
│ │ 签收人 *       [李经理]                                     │ │
│ │ 签收日期 *     [📅 2025-01-28]                              │ │
│ │ 签收备注       [                    ]                       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 上传签收凭证（可选）                                         │ │
│ │ 📎 点击上传签收单照片                                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│                              [取消]  [确认签收]                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 11.4 序列号管理模块（ProductSerialNumber）

#### 页面清单

| 页面 | 文件路径 | 类型 | 说明 |
|-----|---------|------|------|
| 序列号列表 | `product_sn/tw_list.html` | 页面 | 主列表页，筛选、统计、搜索 |
| 序列号详情 | `product_sn/tw_detail.html` | 页面 | 生命周期追溯详情 |
| 批量导入 | - | 模态框 | Excel批量导入 |
| 手动录入 | - | 模态框 | 单个序列号录入 |

#### 列表页设计 (`product_sn/tw_list.html`)

```
┌────────────────────────────────────────────────────────────────┐
│ 序列号管理                         [批量导入] [+ 手动录入]      │
├────────────────────────────────────────────────────────────────┤
│ 统计卡片 (tw_stat_cards_grid cols=5)                           │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                  │
│ │全部  │ │在库  │ │已预留│ │已出库│ │已交付│                  │
│ │ 500  │ │ 280  │ │  45  │ │ 120  │ │  55  │                  │
│ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘                  │
├────────────────────────────────────────────────────────────────┤
│ 筛选栏 (tw_filter_bar)                                         │
│ [状态 ▼] [产品 ▼] [采购订单 ▼] [客户订单 ▼] [🔍 搜索序列号]   │
├────────────────────────────────────────────────────────────────┤
│ 数据表格 (tw_data_table)                                       │
│ ┌────────────┬────────┬────────┬────────┬────────┬──────┬───┐ │
│ │ 序列号     │ 产品   │ 采购PO │ 状态   │ 客户订单│ 出库 │ ⋮│ │
│ ├────────────┼────────┼────────┼────────┼────────┼──────┼───┤ │
│ │SN20250001  │智能光纤│CG-2501 │🟢在库  │ -      │ -    │ ⋮│ │
│ │SN20250002  │智能光纤│CG-2501 │🔵已出库│SO-2501 │01-25 │ ⋮│ │
│ │SN20250003  │系统合路│CG-2502 │🟡预留  │SO-2502 │ -    │ ⋮│ │
│ └────────────┴────────┴────────┴────────┴────────┴──────┴───┘ │
│                                                                │
│ 分页: [< 1 2 3 ... 10 >]                                       │
└────────────────────────────────────────────────────────────────┘
```

#### 详情页设计 (`product_sn/tw_detail.html`)

```
┌────────────────────────────────────────────────────────────────────────┐
│ 面包屑: 采购仓储 > 序列号管理 > SN20250001                              │
│ [返回] [← →]                                    [🟢在库] [编辑] [打印] │
├──────────────────────────────────────────────┬─────────────────────────┤
│ 左侧主内容 (col-span-2)                       │ 右侧边栏 (sticky)       │
│                                              │                         │
│ ┌──────────────────────────────────────────┐ │ ┌─────────────────────┐ │
│ │ 基本信息 (tw_info_card)                  │ │ │ 当前状态            │ │
│ │ 序列号: SN20250001                        │ │ │ ┌─────────────────┐ │ │
│ │ 产品: 智能光纤 RFT-BDA310                 │ │ │ │  🟢 在库        │ │ │
│ │ 批次号: B2025-001                         │ │ │ │  仓位: A-01-03  │ │ │
│ │ 采购订单: CG-2501-001                     │ │ │ └─────────────────┘ │ │
│ │ 入库日期: 2025-01-20                      │ │ └─────────────────────┘ │
│ │ 仓库位置: A区-01排-03位                   │ │                         │
│ └──────────────────────────────────────────┘ │ ┌─────────────────────┐ │
│                                              │ │ 快速操作            │ │
│ ┌──────────────────────────────────────────┐ │ │ [预留到订单]        │ │
│ │ 生命周期追溯 (tw_timeline)               │ │ │ [调整仓位]          │ │
│ │                                          │ │ │ [标记异常]          │ │
│ │ ● 2025-01-25 已入库                      │ │ └─────────────────────┘ │
│ │ │ 采购订单 CG-2501-001                   │ │                         │
│ │ │ 操作人: 张三                           │ │ ┌─────────────────────┐ │
│ │ │                                        │ │ │ 测试信息            │ │
│ │ ● 2025-01-22 工厂测试通过                │ │ │ ✅ 工厂测试: 通过   │ │
│ │ │ 测试报告: 📄查看                       │ │ │ ✅ 到货测试: 通过   │ │
│ │ │                                        │ │ └─────────────────────┘ │
│ │ ● 2025-01-20 序列号登记                  │ │                         │
│ │ │ 来源: Excel批量导入                    │ │ ┌─────────────────────┐ │
│ │ │ 操作人: 李四                           │ │ │ 元数据              │ │
│ │ │                                        │ │ │ 创建时间: 01-20     │ │
│ │ ◌ 待出库                                 │ │ │ 更新时间: 01-25     │ │
│ │ ◌ 待交付                                 │ │ └─────────────────────┘ │
│ └──────────────────────────────────────────┘ │                         │
├──────────────────────────────────────────────┴─────────────────────────┤
│ 全宽区域                                                               │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ 关联记录 (Tabs: 采购信息 | 销售信息 | 测试记录 | 操作日志)         │ │
│ │ ┌────────────────────────────────────────────────────────────────┐ │ │
│ │ │ 采购信息                                                        │ │ │
│ │ │ 采购订单: CG-2501-001        供应商: 杭州长泽科技               │ │ │
│ │ │ 采购日期: 2025-01-15         入库日期: 2025-01-25               │ │ │
│ │ │ 采购价格: ¥5,162.00          测试状态: ✅ 全部通过              │ │ │
│ │ └────────────────────────────────────────────────────────────────┘ │ │
│ └────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

#### 手动录入模态框

```
┌─────────────────────────────────────────────────────────────────┐
│ 手动录入序列号                                                   │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 基本信息                                                    │ │
│ │ 序列号 *       [SN20250100]                                 │ │
│ │ 产品 *         [选择产品 ▼]                                 │ │
│ │ 批次号         [B2025-001]                                  │ │
│ │ 采购订单       [选择采购订单 ▼] (可选)                       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 入库信息                                                    │ │
│ │ 仓库位置       [A区-01排-03位]                              │ │
│ │ 入库日期       [📅 2025-01-25]                              │ │
│ │ 备注           [                    ]                       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│                              [取消]  [保存并继续] [保存]        │
└─────────────────────────────────────────────────────────────────┘
```

#### 批量导入模态框

```
┌─────────────────────────────────────────────────────────────────┐
│ 批量导入序列号                                                   │
│                                                                 │
│ 步骤 1: 下载模板                                                 │
│ [📥 下载Excel模板]                                              │
│                                                                 │
│ 步骤 2: 上传文件                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │  📎 点击或拖拽上传Excel文件                                  │ │
│ │     支持 .xlsx, .xls 格式                                   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ 步骤 3: 数据预览                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✅ 有效: 45条  ⚠️ 重复: 2条  ❌ 错误: 1条                    │ │
│ │ ┌──────────┬────────┬────────┬────────┐                     │ │
│ │ │ 序列号   │ 产品   │ 批次号 │ 状态   │                     │ │
│ │ ├──────────┼────────┼────────┼────────┤                     │ │
│ │ │SN2025... │智能光纤│B001    │ ✅     │                     │ │
│ │ │SN2025... │智能光纤│B001    │ ⚠️重复 │                     │ │
│ │ └──────────┴────────┴────────┴────────┘                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│                          [取消]  [确认导入 (45条)]              │
└─────────────────────────────────────────────────────────────────┘
```

#### 交互设计

| 操作 | 触发方式 | 行为 |
|-----|---------|------|
| 查看详情 | 点击序列号 | 跳转详情页 |
| 筛选状态 | 点击统计卡片 | 自动筛选对应状态 |
| 批量导入 | 点击按钮 | 弹出导入模态框 |
| 手动录入 | 点击按钮 | 弹出录入模态框 |
| 预留到订单 | 详情页按钮 | 弹出订单选择器 |
| 打印标签 | 详情页按钮 | 生成条码/二维码标签 |

---

### 11.5 测试管理模块（ProductTest）

#### 测试记录列表（嵌入采购订单详情页）

```
┌────────────────────────────────────────────────────────────────┐
│ 测试记录                                                        │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ [工厂测试] [现场FAT] [到货测试]                               ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                 │
│ 工厂测试 (必须)                                    [上传报告]   │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ ┌────────┬────────┬────────┬────────┬────────┬────────────┐ ││
│ │ │ 产品   │ 测试日期│ 测试人 │ 结果   │ 报告   │ 操作       │ ││
│ │ ├────────┼────────┼────────┼────────┼────────┼────────────┤ ││
│ │ │智能光纤│01-20   │王工    │✅通过  │📄查看  │ [审核]     │ ││
│ │ │系统合路│01-20   │王工    │✅通过  │📄查看  │ [审核]     │ ││
│ │ └────────┴────────┴────────┴────────┴────────┴────────────┘ ││
│ └──────────────────────────────────────────────────────────────┘│
│                                                                 │
│ 验证测试 (现场FAT / 到货测试 二选一)                             │
│ 当前选择: 现场FAT                                [执行测试]     │
│ ┌──────────────────────────────────────────────────────────────┐│
│ │ 暂无测试记录                                                  ││
│ └──────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────┘
```

---

## 十二、组件与JS工具依赖

### 12.1 需要新建的组件（精简后：2个）

| 组件名称 | 文件路径 | 功能 | 复用性 |
|---------|---------|------|--------|
| `tw_timeline` | `components/tw_timeline.html` | 时间线展示（竖向、只读） | 高（通用） |
| `tw_serial_number_selector` | `components/tw_serial_number_selector.html` | 序列号选择器 | 低（专用） |

### 12.2 可复用的现有组件

| 组件 | 路径 | 用途 |
|-----|------|------|
| `tw_editable_table` | `components/tw_editable_table.html` | 订单明细行内编辑 |
| `tw_confirm_modal` | `components/tw_confirm_modal.html` | 确认对话框（签收、删除等） |
| `tw_file_upload` | `components/tw_file_upload.html` | 文件上传（测试报告、单据） |
| `tw_info_card` | `components/tw_info_card.html` | 详情页信息卡片 |
| `tw_table_card` | `components/tw_table_card.html` | 表格卡片 |
| `tw_stat_card` | `components/tw_stat_card.html` | 统计卡片 |
| `tw_filter_bar` | `components/tw_filter_bar.html` | 列表页筛选栏 |
| `tw_data_table` | `components/tw_data_table.html` | 列表页数据表格 |
| `tw_detail_layout` | `components/tw_detail_layout.html` | 详情页布局 |
| `tw_tabs` | `components/tw_tabs.html` | 标签页切换 |
| `tw_approval_flow` | `components/tw_approval_flow.html` | 审批流程（可选） |

### 12.3 可复用的现有JS工具

| 工具 | 路径 | 用途 |
|-----|------|------|
| `keyword-selector.js` | `static/js/keyword-selector.js` | 搜索选择（客户、联系人、产品） |
| `export-info-modal.js` | `static/js/export-info-modal.js` | 导出PDF时收集额外信息 |
| `file-upload-component.js` | `static/js/file-upload-component.js` | 文件上传交互 |
| `approval_flow.js` | `static/js/approval_flow.js` | 审批流程交互 |

### 12.4 需要新建的JS工具

| 工具 | 文件 | 功能 | 使用场景 |
|-----|------|------|---------|
| `serial-number-selector.js` | `static/js/serial-number-selector.js` | 序列号多选 | 发货时选择出库序列号 |
| `excel-import.js` | `static/js/excel-import.js` | Excel导入预览 | 序列号批量导入 |
| `progress-slider.js` | `static/js/progress-slider.js` | 进度滑块交互 | 生产进度更新 |

### 12.5 复用方案说明

| 原计划组件 | 复用方案 | 说明 |
|-----------|---------|------|
| `tw_progress_bar` | 内联HTML | 复用 `tw_expense_budget_card.html` 进度条HTML模式 |
| `tw_status_flow` | 内联HTML | 参考 `macros/stage_tracker.html` 横向阶段组件 |
| `tw_file_upload_card` | 现有组件 | 使用 `tw_file_upload.html` compact模式 |
| 确认模态框 | 现有组件 | 使用 `tw_confirm_modal.html` |
| 可编辑表格 | 现有组件 | 使用 `tw_editable_table.html` |

### 12.6 新建组件详细设计

#### tw_timeline (时间线)

**用途**：序列号生命周期、发货物流跟踪、操作历史

```jinja2
{# 调用示例 #}
{% call tw_timeline() %}
    {{ tw_timeline_item(
        title='创建采购订单',
        time='2025-01-15 10:30',
        status='completed',  # completed/current/pending
        description='由张三创建'
    ) }}
    {{ tw_timeline_item(
        title='生产中',
        time=none,
        status='current',
        description='预计2025-02-05完成'
    ) }}
    {{ tw_timeline_item(
        title='待发货',
        status='pending'
    ) }}
{% endcall %}
```

#### tw_serial_number_selector (序列号选择器)

**用途**：发货时从库存中选择要出库的序列号

```jinja2
{# 调用示例 #}
{{ tw_serial_number_selector(
    container_id='snSelector',
    product_id=product.id,
    max_count=10,
    filter_status='in_stock',
    on_change='onSerialNumberChange'
) }}
```

**特性**：
- 按产品筛选可选序列号
- 支持搜索
- 多选模式
- 显示序列号状态
- 选择数量验证

### 12.7 Bootstrap兼容（已移除，全部使用Tailwind）

所有新页面统一使用Tailwind CSS，不再使用Bootstrap。

---

## 十三（旧）、组件详细设计

> 注：以下保留原有的组件设计示例代码，供开发参考

#### tw_progress_bar (进度条) - 内联使用

```jinja2
{# 调用示例 #}
{{ tw_progress_bar(
    value=45,
    max=100,
    label='生产进度',
    show_percentage=true,
    color='primary',  # primary/success/warning/danger
    size='md'  # sm/md/lg
) }}

{# 输出 #}
<div class="space-y-1">
    <div class="flex justify-between text-sm">
        <span class="text-slate-600 dark:text-slate-400">生产进度</span>
        <span class="text-slate-900 dark:text-white font-medium">45%</span>
    </div>
    <div class="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div class="h-full bg-primary rounded-full transition-all duration-300"
             style="width: 45%"></div>
    </div>
</div>
```

#### tw_timeline (时间线)

```jinja2
{# 调用示例 #}
{% call tw_timeline() %}
    {{ tw_timeline_item(
        title='创建采购订单',
        time='2025-01-15 10:30',
        status='completed',  # completed/current/pending
        description='由张三创建'
    ) }}
    {{ tw_timeline_item(
        title='供应商确认',
        time='2025-01-16 14:00',
        status='completed'
    ) }}
    {{ tw_timeline_item(
        title='生产中',
        time=none,
        status='current',
        description='预计2025-02-05完成'
    ) }}
    {{ tw_timeline_item(
        title='待发货',
        status='pending'
    ) }}
{% endcall %}

{# 输出 #}
<div class="space-y-0">
    <div class="flex gap-4">
        <div class="flex flex-col items-center">
            <div class="w-3 h-3 rounded-full bg-green-500"></div>
            <div class="w-0.5 h-full bg-green-500"></div>
        </div>
        <div class="pb-6">
            <p class="font-medium text-slate-900 dark:text-white">创建采购订单</p>
            <p class="text-sm text-slate-500">2025-01-15 10:30</p>
            <p class="text-sm text-slate-600">由张三创建</p>
        </div>
    </div>
    <!-- more items -->
</div>
```

---

### 12.3 组件复用汇总

#### 复用现有组件

| 组件 | 来源 | 使用场景 |
|-----|------|---------|
| `tw_layout` | 现有 | 所有页面主布局 |
| `tw_detail_layout` | 现有 | 采购订单详情、客户订单详情 |
| `tw_fixed_header_page` | 现有 | 列表页固定头部 |
| `tw_stat_card` | 现有 | 列表页统计卡片 |
| `tw_filter_bar` | 现有 | 列表页筛选栏 |
| `tw_data_table` | 现有 | 列表页数据表格 |
| `tw_info_card` | 现有 | 详情页信息展示 |
| `tw_card_shell` | 现有 | 自定义内容卡片 |
| `tw_table_card` | 现有 | 详情页表格卡片 |
| `tw_tabs` | 现有 | 测试记录标签页 |
| `tw_btn` | 现有 | 按钮 |
| `tw_form_fields` | 现有 | 表单字段 |
| `tw_modal_base` | 现有 | 模态框基础 |
| `tw_file_upload` | 现有 | 文件上传 |
| `tw_file_preview` | 现有 | 文件预览 |
| `tw_metadata_card_simple` | 现有 | 元数据卡片 |

#### 新建组件（精简后：2个）

| 组件 | 复用性 | 说明 |
|-----|--------|------|
| `tw_timeline` | **高** | 通用时间线，用于订单跟踪、操作历史等（竖向、只读） |
| `tw_serial_number_selector` | 低 | 序列号选择器，发货时关联序列号专用 |

#### 复用说明

| 原计划组件 | 复用方案 |
|-----------|---------|
| `tw_progress_bar` | **复用** `tw_expense_budget_card.html` 中的进度条HTML模式 |
| `tw_status_flow` | **复用** `macros/stage_tracker.html` 的横向阶段组件模式 |
| `tw_file_upload_card` | **复用** `tw_file_upload.html` 现有组件（支持compact模式） |

#### 新建JS工具函数

| 函数 | 文件 | 功能 |
|-----|------|------|
| `initProgressSlider()` | `progress-slider.js` | 进度滑块交互 |
| `initSerialNumberSelector()` | `serial-number-selector.js` | 序列号多选 |
| `initExcelImport()` | `excel-import.js` | Excel导入预览 |

---

## 十三、文件清单汇总

### 后端文件

| 文件路径 | 类型 | 说明 |
|---------|------|------|
| `app/models/inventory.py` | 修改 | 扩展 PurchaseOrder 模型 |
| `app/models/product_test.py` | 新建 | 产品测试模型 |
| `app/models/sales_order.py` | 新建 | 客户订单模型 |
| `app/models/shipment.py` | 新建 | 发货记录模型 |
| `app/models/product_serial_number.py` | 新建 | 产品序列号模型 |
| `app/routes/purchase_order_routes.py` | 新建 | 采购订单路由 |
| `app/routes/sales_order_routes.py` | 新建 | 客户订单路由 |
| `app/routes/shipment_routes.py` | 新建 | 发货管理路由 |
| `app/routes/product_sn_routes.py` | 新建 | 序列号管理路由 |
| `app/services/purchase_order_service.py` | 新建 | 采购订单服务 |
| `app/services/sales_order_service.py` | 新建 | 客户订单服务 |
| `app/services/shipment_service.py` | 新建 | 发货管理服务 |
| `app/services/product_sn_service.py` | 新建 | 序列号服务 |

### 前端页面文件

| 文件路径 | 类型 | 说明 |
|---------|------|------|
| `templates/inventory/tw_purchase_order_list.html` | 新建 | 采购订单列表 |
| `templates/inventory/tw_purchase_order_detail.html` | 新建 | 采购订单详情 |
| `templates/sales_order/tw_list.html` | 新建 | 客户订单列表 |
| `templates/sales_order/tw_detail.html` | 新建 | 客户订单详情 |
| `templates/shipment/tw_list.html` | 新建 | 发货记录列表 |
| `templates/shipment/tw_detail.html` | 新建 | 发货记录详情 |
| `templates/product_sn/tw_list.html` | 新建 | 序列号列表 |
| `templates/product_sn/tw_detail.html` | 新建 | 序列号详情（生命周期追溯） |

### 组件文件（精简后）

| 文件路径 | 类型 | 说明 |
|---------|------|------|
| `templates/components/tw_timeline.html` | 新建 | 时间线组件 |
| `templates/components/tw_serial_number_selector.html` | 新建 | 序列号选择器 |

### JS文件

| 文件路径 | 类型 | 说明 |
|---------|------|------|
| `static/js/progress-slider.js` | 新建 | 进度滑块 |
| `static/js/serial-number-selector.js` | 新建 | 序列号选择器 |
| `static/js/excel-import.js` | 新建 | Excel导入 |
| `static/js/purchase-order.js` | 新建 | 采购订单页面逻辑 |
| `static/js/sales-order.js` | 新建 | 客户订单页面逻辑 |

### 迁移文件

| 文件路径 | 说明 |
|---------|------|
| `migrations/versions/extend_purchase_order_*.py` | 扩展采购订单字段 |
| `migrations/versions/create_product_test_*.py` | 创建测试表 |
| `migrations/versions/create_sales_order_*.py` | 创建客户订单表 |
| `migrations/versions/create_shipment_*.py` | 创建发货表 |
| `migrations/versions/create_product_sn_*.py` | 创建序列号表 |

---

## 十四、菜单入口设计

### 14.1 菜单重构方案

**原菜单结构**：
```
订单结算
├── 订单管理 (order) - PricingOrder 批价单
├── 结算管理 (settlement) - SettlementOrder
└── 库存管理 (inventory)
```

**新菜单结构**（拆分为两组）：

```
销售管理 (sales)
├── 批价单管理 (pricing_order)     - 原"订单管理"，改名更清晰
├── 客户订单 (sales_order)          - 新增，从批价单转换
├── 发货出库 (shipment)             - 新增
├── ──分隔线──
└── 结算管理 (settlement)           - 保留

采购仓储 (procurement)
├── 采购订单 (purchase_order)       - 新增/强化
├── ──分隔线──
├── 库存管理 (inventory)            - 保留
└── 序列号管理 (serial_number)      - 新增
```

### 14.2 权限配置

| 菜单项 | 权限模块 | 权限操作 | 说明 |
|-------|---------|---------|------|
| 批价单管理 | `order` | `view` | 复用现有权限 |
| 客户订单 | `sales_order` | `view` | 新增权限模块 |
| 发货出库 | `shipment` | `view` | 新增权限模块 |
| 结算管理 | `settlement` | `view` | 复用现有权限 |
| 采购订单 | `purchase_order` | `view` | 新增权限模块 |
| 库存管理 | `inventory` | `view` | 复用现有权限 |
| 序列号管理 | `serial_number` | `view` | 新增权限模块 |

### 14.3 菜单代码修改

**文件**: `app/templates/components/tw_nav_menu.html`

**修改内容**：
1. 将"订单结算"组拆分为"销售管理"和"采购仓储"两组
2. 添加新的菜单项
3. 更新 active_page 判断逻辑
4. 添加权限检查

**销售管理组代码结构**：
```jinja2
<!-- 销售管理组 -->
{% if has_permission('order', 'view') or has_permission('sales_order', 'view') or has_permission('shipment', 'view') or has_permission('settlement', 'view') %}
<div x-data="{ open: {{ 'true' if active_page in ['pricing_order', 'sales_order', 'shipment', 'settlement'] else 'false' }} }">
    <button>销售管理</button>
    <div>
        <!-- 批价单管理 -->
        <!-- 客户订单 -->
        <!-- 发货出库 -->
        <!-- 分隔线 -->
        <!-- 结算管理 -->
    </div>
</div>
{% endif %}
```

**采购仓储组代码结构**：
```jinja2
<!-- 采购仓储组 -->
{% if has_permission('purchase_order', 'view') or has_permission('inventory', 'view') or has_permission('serial_number', 'view') %}
<div x-data="{ open: {{ 'true' if active_page in ['purchase_order', 'inventory', 'serial_number'] else 'false' }} }">
    <button>采购仓储</button>
    <div>
        <!-- 采购订单 -->
        <!-- 分隔线 -->
        <!-- 库存管理 -->
        <!-- 序列号管理 -->
    </div>
</div>
{% endif %}
```

### 14.4 图标选择

| 菜单项 | Material Symbol | 说明 |
|-------|----------------|------|
| 销售管理 (组) | `point_of_sale` | 销售点 |
| 批价单管理 | `request_quote` | 报价请求 |
| 客户订单 | `shopping_bag` | 购物袋 |
| 发货出库 | `local_shipping` | 本地配送 |
| 结算管理 | `payments` | 付款 |
| 采购仓储 (组) | `inventory` | 库存 |
| 采购订单 | `assignment` | 订单任务 |
| 库存管理 | `warehouse` | 仓库 |
| 序列号管理 | `qr_code_2` | 二维码/条码 |

### 14.5 路由配置

| 菜单项 | 路由 | Blueprint |
|-------|------|-----------|
| 批价单管理 | `inventory.order_list` | 保持现有 |
| 客户订单 | `sales_order.list` | 新建 |
| 发货出库 | `shipment.list` | 新建 |
| 结算管理 | `inventory.settlement_order_list` | 保持现有 |
| 采购订单 | `purchase_order.list` | 新建 |
| 库存管理 | `inventory.stock_list` | 保持现有 |
| 序列号管理 | `product_sn.list` | 新建 |

---

## 十五、完整验证测试方案

### 15.1 组件复用检查清单

#### 前端组件检查（实施前）

| 检查项 | 检查方法 | 预期结果 |
|-------|---------|---------|
| **列表页组件** | 检查是否使用 `tw_stat_card`, `tw_filter_bar`, `tw_data_table` | 不创建新的列表组件 |
| **详情页布局** | 检查是否使用 `tw_detail_layout` | 不手写三栏布局 |
| **信息卡片** | 检查是否使用 `tw_info_card` | 不手写卡片HTML |
| **表格卡片** | 检查是否使用 `tw_table_card` | 不手写表格容器 |
| **确认模态框** | 检查是否使用 `tw_confirm_modal` | 不手写确认对话框 |
| **文件上传** | 检查是否使用 `tw_file_upload` | 不创建新上传组件 |
| **可编辑表格** | 检查是否使用 `tw_editable_table` | 不手写行内编辑 |
| **标签页** | 检查是否使用 `tw_tabs` | 不手写Tab切换 |

#### JS工具检查（实施前）

| 检查项 | 现有工具 | 用途 |
|-------|---------|------|
| 搜索选择器 | `keyword-selector.js` | 客户/联系人/产品选择 |
| 导出信息收集 | `export-info-modal.js` | PDF导出前信息补充 |
| 文件上传交互 | `file-upload-component.js` | 文件上传处理 |
| 审批流程 | `approval_flow.js` | 审批流程展示 |

**检查命令**：
```bash
# 检查是否有重复的选择器实现
grep -r "class.*Selector" app/static/js/*.js
grep -r "搜索.*选择" app/templates/**/*.html

# 检查是否有重复的模态框实现
grep -r "modal.*confirm" app/templates/**/*.html
```

---

### 15.2 徽章复用检查清单

#### 已有徽章宏（必须复用）

| 徽章类型 | 宏名称 | 位置 |
|---------|-------|------|
| 订单状态 | `render_order_status_badge` | `macros/ui_helpers.html` |
| 入库状态 | `render_inventory_status_badge` | `macros/ui_helpers.html` |
| 结算状态 | `render_settlement_status_badge` | `macros/ui_helpers.html` |
| 审批状态 | `render_approval_badge` | `macros/ui_helpers.html` |
| 通用状态 | `render_tw_status_badge` | `macros/ui_helpers.html` |

#### 需要新增的徽章

| 徽章类型 | 需新增宏名 | 状态值 |
|---------|----------|-------|
| 采购订单状态 | `render_tw_purchase_order_status_badge` | draft/pending/approved/confirmed/producing/tested/shipped/stored/completed |
| 客户订单状态 | `render_tw_sales_order_status_badge` | draft/confirmed/preparing/shipped/delivered/completed |
| 发货状态 | `render_tw_shipment_status_badge` | pending/shipped/in_transit/delivered/received |
| 序列号状态 | `render_tw_serial_number_status_badge` | registered/in_stock/reserved/shipped/delivered |
| 测试结果 | `render_tw_test_result_badge` | passed/failed/conditional/pending |

**检查命令**：
```bash
# 检查徽章是否通过宏渲染而非硬编码
grep -r "badge.*bg-" app/templates/inventory/*.html
grep -r "badge.*bg-" app/templates/sales_order/*.html
grep -r "badge.*bg-" app/templates/shipment/*.html
grep -r "badge.*bg-" app/templates/product_sn/*.html

# 预期：应该看到 {{ render_tw_*_badge(...) }} 而非直接的HTML
```

---

### 15.3 翻译与映射检查清单

#### 翻译规则检查

| 检查项 | 规则 | 检查方法 |
|-------|------|---------|
| **页面标题** | 必须使用 `{{ _('...') }}` | 搜索 `<h1>`, `<h2>` 标签 |
| **按钮文本** | 必须使用 `{{ _('...') }}` | 搜索 `render_button`, `tw_btn` |
| **表格表头** | 必须使用 `{{ _('...') }}` | 搜索 `<th>` 标签 |
| **标签文本** | 必须使用 `{{ _('...') }}` | 搜索 `<label>` 标签 |
| **占位符** | 必须使用 `{{ _('...') }}` | 搜索 `placeholder=` |
| **提示信息** | 必须使用 `{{ _('...') }}` | 搜索 `alert`, `toast`, `message` |
| **状态文本** | 使用字典映射 | 检查 `dictionary_helpers.py` |

#### 字典映射检查（状态标签）

以下状态必须通过 `dictionaries` 表映射，不能硬编码翻译：

| 字典类型 | 键值 | 需添加到数据库 |
|---------|------|---------------|
| `purchase_order_status` | draft, pending, approved, confirmed, producing, tested, shipped, stored, completed | ✅ |
| `sales_order_status` | draft, confirmed, preparing, shipped, delivered, completed, cancelled | ✅ |
| `shipment_status` | pending, shipped, in_transit, delivered, received | ✅ |
| `serial_number_status` | registered, in_stock, reserved, shipped, delivered | ✅ |
| `test_result` | passed, failed, conditional, pending | ✅ |
| `test_type` | factory_self, site_fat, incoming | ✅ |
| `production_status` | not_started, preparing, producing, testing, packaging, ready | ✅ |

**检查命令**：
```bash
# 检查是否有漏翻译的硬编码中文
grep -r "草稿\|待确认\|生产中\|已发货" app/templates/**/*.html | grep -v "_("

# 检查是否有硬编码的英文（应该用中文msgid）
grep -rE "'[A-Z][a-z]+'" app/templates/**/*.html | grep -v "_("

# 提取新的翻译文本
pybabel extract -F babel.cfg -k _l -o messages.pot .
pybabel update -i messages.pot -d app/translations
```

#### 翻译文件更新清单

需要添加到 `app/translations/en/LC_MESSAGES/messages.po`：

```po
# 采购订单模块
msgid "采购订单管理"
msgstr "Purchase Order Management"

msgid "供应商确认"
msgstr "Supplier Confirmation"

msgid "生产进度"
msgstr "Production Progress"

msgid "测试报告"
msgstr "Test Report"

msgid "验收入库"
msgstr "Acceptance & Warehousing"

# 客户订单模块
msgid "客户订单"
msgstr "Sales Order"

msgid "交付信息"
msgstr "Delivery Information"

msgid "期望交付日期"
msgstr "Expected Delivery Date"

# 发货管理模块
msgid "发货出库"
msgstr "Shipment"

msgid "确认签收"
msgstr "Confirm Receipt"

msgid "物流跟踪"
msgstr "Logistics Tracking"

# 序列号管理模块
msgid "序列号管理"
msgstr "Serial Number Management"

msgid "批量导入"
msgstr "Batch Import"

msgid "生命周期追溯"
msgstr "Lifecycle Tracking"

# 菜单
msgid "销售管理"
msgstr "Sales Management"

msgid "采购仓储"
msgstr "Procurement & Warehouse"
```

---

### 15.4 UI/UX 一致性检查清单

#### 页面结构一致性

| 检查项 | 标准 | 检查方法 |
|-------|------|---------|
| **列表页头部** | 标题左侧 + 操作按钮右侧 | 目视检查 |
| **统计卡片** | 5列等宽，点击可筛选 | 功能测试 |
| **筛选栏** | 统一顺序：状态→关联→日期→搜索 | 目视检查 |
| **表格操作列** | 统一使用 `⋮` 下拉菜单 | 目视检查 |
| **详情页布局** | 左2右1三栏，右侧sticky | 滚动测试 |
| **模态框按钮** | 取消在左，确认在右 | 目视检查 |

#### 交互一致性

| 检查项 | 标准 | 检查方法 |
|-------|------|---------|
| **点击卡片筛选** | 点击统计卡片自动筛选对应状态 | 功能测试 |
| **链接跳转** | 订单号/序列号等可点击跳转详情 | 功能测试 |
| **表单验证** | 必填项标红，错误提示即时 | 功能测试 |
| **加载状态** | 按钮loading + 禁用 | 功能测试 |
| **成功提示** | 使用统一toast样式 | 目视检查 |
| **确认对话框** | 危险操作使用红色按钮 | 目视检查 |

#### 响应式检查

| 检查项 | 断点 | 检查方法 |
|-------|------|---------|
| **列表页** | 移动端隐藏非关键列 | 调整窗口宽度 |
| **详情页** | 移动端变为单列布局 | 调整窗口宽度 |
| **模态框** | 移动端全屏或接近全屏 | 调整窗口宽度 |

---

### 15.5 功能完整性检查清单

#### 采购订单模块

| 功能 | 前端页面 | 后端API | 状态 |
|-----|---------|---------|------|
| 列表展示 | `tw_purchase_order_list.html` | `GET /purchase_order/list` | ☐ |
| 创建订单 | 模态框 | `POST /purchase_order/create` | ☐ |
| 查看详情 | `tw_purchase_order_detail.html` | `GET /purchase_order/<id>` | ☐ |
| 编辑基本信息 | 模态框 | `PUT /purchase_order/<id>` | ☐ |
| 供应商确认 | 模态框 | `POST /purchase_order/<id>/confirm` | ☐ |
| 更新进度 | 模态框 | `POST /purchase_order/<id>/progress` | ☐ |
| 添加明细 | 模态框 | `POST /purchase_order/<id>/detail` | ☐ |
| 上传测试报告 | 模态框 | `POST /purchase_order/<id>/test` | ☐ |
| 确认发货 | 模态框 | `POST /purchase_order/<id>/ship` | ☐ |
| 验收入库 | 模态框 | `POST /purchase_order/<id>/receive` | ☐ |
| 导出PDF | 按钮 | `GET /purchase_order/<id>/export` | ☐ |
| 删除订单 | 确认框 | `DELETE /purchase_order/<id>` | ☐ |

#### 客户订单模块

| 功能 | 前端页面 | 后端API | 状态 |
|-----|---------|---------|------|
| 列表展示 | `tw_list.html` | `GET /sales_order/list` | ☐ |
| 从批价单创建 | 模态框 | `POST /sales_order/create_from_pricing` | ☐ |
| 查看详情 | `tw_detail.html` | `GET /sales_order/<id>` | ☐ |
| 编辑交付信息 | 模态框 | `PUT /sales_order/<id>/delivery` | ☐ |
| 创建发货单 | 模态框 | `POST /sales_order/<id>/shipment` | ☐ |
| 取消订单 | 确认框 | `POST /sales_order/<id>/cancel` | ☐ |

#### 发货管理模块

| 功能 | 前端页面 | 后端API | 状态 |
|-----|---------|---------|------|
| 列表展示 | `tw_list.html` | `GET /shipment/list` | ☐ |
| 查看详情 | `tw_detail.html` | `GET /shipment/<id>` | ☐ |
| 确认签收 | 模态框 | `POST /shipment/<id>/receive` | ☐ |
| 更新物流 | 模态框 | `PUT /shipment/<id>/tracking` | ☐ |
| 上传单据 | 组件 | `POST /shipment/<id>/documents` | ☐ |

#### 序列号管理模块

| 功能 | 前端页面 | 后端API | 状态 |
|-----|---------|---------|------|
| 列表展示 | `tw_list.html` | `GET /product_sn/list` | ☐ |
| 批量导入 | 模态框 | `POST /product_sn/import` | ☐ |
| 下载模板 | 按钮 | `GET /product_sn/template` | ☐ |
| 手动录入 | 模态框 | `POST /product_sn/create` | ☐ |
| 查看详情 | `tw_detail.html` | `GET /product_sn/<id>` | ☐ |
| 预留到订单 | 模态框 | `POST /product_sn/<id>/reserve` | ☐ |
| 调整仓位 | 模态框 | `PUT /product_sn/<id>/location` | ☐ |
| 打印标签 | 按钮 | `GET /product_sn/<id>/label` | ☐ |

---

### 15.6 流程完整性测试

#### 采购端流程测试

```
步骤1: 创建采购订单
├── 填写供应商、需求日期、贸易术语
├── 选择验证测试方式（现场FAT/到货测试）
├── 添加产品明细
└── 验证：订单状态=draft

步骤2: 提交审批（如启用）
├── 点击提交审批
└── 验证：订单状态=pending

步骤3: 审批通过
├── 审批人审批
└── 验证：订单状态=approved

步骤4: 供应商确认
├── 填写确认人、确认日期
└── 验证：订单状态=confirmed

步骤5: 更新生产进度
├── 选择阶段、填写进度百分比
└── 验证：订单状态=producing，进度显示正确

步骤6: 上传工厂测试报告
├── 选择测试类型=工厂测试
├── 上传测试报告文件
├── 选择测试结果=通过
└── 验证：factory_test_status=passed

步骤7: 现场FAT（如选择）
├── 选择测试类型=现场FAT
├── 上传测试报告
└── 验证：verification_test_status=passed

步骤8: 确认发货
├── 填写承运商、运单号
└── 验证：订单状态=shipped

步骤9: 验收入库
├── 填写验收数量
├── 录入/导入序列号
└── 验证：订单状态=stored，库存增加，序列号状态=in_stock

步骤10: 到货测试（如选择）
├── 选择测试类型=到货测试
├── 上传测试报告
└── 验证：verification_test_status=passed
```

#### 销售端流程测试

```
步骤1: 从批价单创建客户订单
├── 在批价单详情页点击"创建客户订单"
├── 填写交付信息
├── 调整订购数量（可选）
└── 验证：客户订单创建成功，状态=draft

步骤2: 确认订单
├── 点击确认
└── 验证：订单状态=confirmed

步骤3: 开始备货
├── 系统自动或手动触发
└── 验证：订单状态=preparing

步骤4: 创建发货单
├── 填写物流信息
├── 选择发货数量
├── 选择序列号
└── 验证：发货单创建，序列号状态=shipped

步骤5: 确认签收
├── 填写签收人、签收日期
├── 上传签收凭证（可选）
└── 验证：发货单状态=received，序列号状态=delivered

步骤6: 订单完成
├── 所有明细已签收
└── 验证：订单状态=completed
```

#### 序列号追溯测试

```
测试1: 正向追溯（从采购到销售）
├── 输入序列号 SN20250001
├── 验证显示：采购订单→入库日期→测试记录→客户订单→发货单→签收日期
└── 验证：时间线完整，状态正确

测试2: 反向追溯（从客户查序列号）
├── 打开客户订单详情
├── 展开发货记录
└── 验证：显示所有相关序列号列表

测试3: 批量查询
├── 筛选条件：状态=在库，产品=智能光纤
└── 验证：显示符合条件的序列号列表
```

---

### 15.7 数据库迁移验证

```bash
# 1. 生成迁移文件
flask db migrate -m "Add PO/SO module tables"

# 2. 检查迁移文件（人工审核SQL）
cat migrations/versions/*_add_po_so_module_tables.py

# 3. 应用迁移
flask db upgrade

# 4. 验证表结构
python3 -c "
from app import create_app, db
from sqlalchemy import inspect
app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    tables = ['purchase_orders', 'product_tests', 'sales_orders',
              'sales_order_details', 'shipments', 'shipment_details',
              'product_serial_numbers']
    for table in tables:
        if table in inspector.get_table_names():
            print(f'✅ {table} exists')
            cols = [c['name'] for c in inspector.get_columns(table)]
            print(f'   Columns: {len(cols)}')
        else:
            print(f'❌ {table} MISSING')
"

# 5. 验证字典数据
python3 -c "
from app import create_app, db
from app.models import Dictionary
app = create_app()
with app.app_context():
    dicts = ['purchase_order_status', 'sales_order_status',
             'shipment_status', 'serial_number_status', 'test_result']
    for d in dicts:
        count = Dictionary.query.filter_by(type=d).count()
        print(f'  {d}: {count} entries')
"
```

---

### 15.8 实施后回归测试

#### 自动化测试脚本（建议）

```python
# tests/test_po_so_module.py

def test_purchase_order_crud():
    """测试采购订单CRUD"""
    # 创建
    # 读取
    # 更新
    # 删除
    pass

def test_sales_order_from_pricing():
    """测试从批价单创建客户订单"""
    pass

def test_shipment_with_serial_numbers():
    """测试发货关联序列号"""
    pass

def test_serial_number_lifecycle():
    """测试序列号生命周期"""
    pass

def test_translation_coverage():
    """测试翻译覆盖率"""
    # 检查所有页面是否有未翻译的中文
    pass
```

#### 手动测试检查表

| # | 测试项 | 结果 | 备注 |
|---|-------|------|------|
| 1 | 所有列表页能正常加载 | ☐ | |
| 2 | 所有详情页能正常加载 | ☐ | |
| 3 | 所有模态框能正常打开/关闭 | ☐ | |
| 4 | 表单验证工作正常 | ☐ | |
| 5 | 状态徽章颜色正确 | ☐ | |
| 6 | 中英文切换显示正确 | ☐ | |
| 7 | 权限控制工作正常 | ☐ | |
| 8 | 菜单显示正确 | ☐ | |
| 9 | 采购流程可走通 | ☐ | |
| 10 | 销售流程可走通 | ☐ | |
| 11 | 序列号追溯正确 | ☐ | |
| 12 | 文件上传/下载正常 | ☐ | |
| 13 | 导出PDF正常 | ☐ | |
| 14 | 响应式布局正常 | ☐ | |
| 15 | 暗色模式显示正常 | ☐ | |

---

### 15.9 代码审查清单

#### 提交前检查

- [ ] 所有新页面使用 Tailwind 组件，无手写重复HTML
- [ ] 所有状态徽章通过宏渲染
- [ ] 所有可翻译文本使用 `_()` 包裹
- [ ] 所有状态标签使用字典映射
- [ ] 所有表单有验证
- [ ] 所有API有错误处理
- [ ] 所有删除操作有确认
- [ ] 所有敏感操作有权限检查
- [ ] 翻译文件已编译 (`pybabel compile`)
- [ ] 无console.log或print调试语句
- [ ] 无硬编码的测试数据

#### 代码规范检查

```bash
# Python代码检查
flake8 app/routes/purchase_order_routes.py
flake8 app/routes/sales_order_routes.py
flake8 app/services/*.py

# 检查未使用的导入
pylint --disable=all --enable=unused-import app/routes/*.py

# 检查HTML模板语法
# 使用浏览器开发者工具检查是否有Jinja2渲染错误
```
