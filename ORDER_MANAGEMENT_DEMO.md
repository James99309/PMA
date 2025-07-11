# 库存管理系统 - 订单管理功能

## 功能概述

为库存管理系统创建了完整的订单管理功能，类似于批量添加库存的模板，支持通过产品类别和型号选择具体产品，并通过折扣率确定价格。

## 主要功能

### 1. 订单表结构

#### 订单主表 (purchase_orders)
- `order_number`: 订单编号（自动生成）
- `company_id`: 订单目标公司
- `order_type`: 订单类型（采购/销售）
- `order_date`: 订单日期
- `expected_date`: 预期到货时间
- `status`: 订单状态（草稿/已确认/已发货/已完成/已取消）
- `total_amount`: 订单总金额
- `total_quantity`: 订单总数量
- `payment_terms`: 付款条件
- `delivery_address`: 交付地址
- `description`: 订单说明
- `created_by_id`: 创建人
- `approved_by_id`: 审批人
- `created_at/updated_at`: 时间戳

#### 订单明细表 (purchase_order_details)
- `order_id`: 关联订单ID
- `product_id`: 产品ID
- `product_name`: 产品名称（冗余字段）
- `product_model`: 产品型号（冗余字段）
- `product_desc`: 产品描述
- `brand`: 品牌
- `quantity`: 数量
- `unit`: 单位
- `unit_price`: 单价
- `discount`: 折扣率（小数形式，如0.8表示80%）
- `total_price`: 小计金额
- `notes`: 备注

### 2. 页面功能

#### 订单列表页面 (`/inventory/orders`)
- 显示所有订单的列表
- 支持按订单号、公司名称搜索
- 支持按订单类型、公司、状态筛选
- 显示订单统计信息（各状态订单数量）
- 分页显示
- 操作按钮：查看详情、编辑（草稿状态）、导出PDF

#### 创建订单页面 (`/inventory/orders/create`)
- **订单基本信息**：
  - 订单目标公司选择（必填）
  - 订单类型（采购/销售）
  - 预期到货时间
  - 付款条件
  - 交付地址
  - 订单说明

- **产品明细表格**：
  - 产品类别选择（级联）
  - 产品名称选择（基于类别）
  - 产品型号选择（基于名称）
  - 品牌、单位（自动填充）
  - 数量输入
  - 单价输入
  - 折扣率输入（百分比）
  - 小计自动计算
  - 备注输入
  - 删除行功能

- **订单总计**：
  - 总数量统计
  - 总金额计算
  - 实时更新

#### 订单详情页面 (`/inventory/orders/<id>`)
- 显示订单完整信息
- 产品明细表格
- 订单总计信息
- 操作历史（如果有审批记录）

### 3. 核心特性

#### 产品选择流程
1. **选择产品类别** → 加载该类别下的所有产品名称
2. **选择产品名称** → 加载该产品的所有型号
3. **选择产品型号** → 自动填充品牌、单位、建议零售价

#### 价格计算逻辑
- **单价**：用户输入或使用建议零售价
- **折扣率**：用户输入百分比（如85表示85%）
- **小计** = 数量 × 单价 × (折扣率/100)
- **总计** = 所有产品小计之和

#### 数据验证
- 必须选择订单目标公司
- 至少添加一个有效产品
- 所有产品必须完整选择（类别→名称→型号）
- 数量必须大于0
- 价格和折扣率必须为有效数值

### 4. 技术实现

#### 前端技术
- **jQuery** 用于DOM操作和AJAX请求
- **Bootstrap** 用于响应式布局和样式
- **动态表格** 支持添加/删除产品行
- **级联选择器** 实现产品选择流程
- **实时计算** 自动更新小计和总计

#### 后端API
- `GET /product/api/products/categories` - 获取产品类别列表
- `GET /product/api/products/by-category` - 按类别获取产品
- `GET /product/api/products/by-name` - 按名称获取产品型号
- `POST /inventory/orders/create` - 创建订单

#### 数据处理
- 表单数据以数组形式提交（`product_id[]`, `quantity[]`等）
- 折扣率从百分比转换为小数存储
- 自动生成订单编号
- 事务处理确保数据一致性

### 5. 界面设计

#### 视觉风格
- **渐变色卡片**：订单信息使用蓝色渐变，总计使用黄色渐变
- **响应式布局**：适配桌面和移动设备
- **固定操作列**：表格右侧操作按钮始终可见
- **状态标识**：不同颜色表示订单状态和类型

#### 用户体验
- **智能提示**：产品选择时显示相关信息
- **实时反馈**：价格计算即时更新
- **操作确认**：删除行时有确认提示
- **加载状态**：提交时显示加载动画

### 6. 使用流程

1. **访问订单列表**：`http://localhost:10000/inventory/orders`
2. **点击创建订单**：进入订单创建页面
3. **填写基本信息**：选择目标公司，设置订单类型等
4. **添加产品明细**：
   - 点击"添加产品"按钮
   - 依次选择产品类别、名称、型号
   - 输入数量、调整单价和折扣率
   - 系统自动计算小计
5. **确认订单**：检查总计金额，点击"创建订单"
6. **查看结果**：系统显示成功消息并跳转到订单详情

### 7. 扩展功能

#### 已实现
- 订单状态管理
- 审批流程支持
- 操作历史记录
- 分页和搜索

#### 可扩展
- 订单编辑功能
- PDF导出
- 邮件通知
- 库存关联
- 财务集成

## 文件结构

```
app/
├── models/inventory.py          # 订单数据模型
├── routes/inventory.py          # 订单路由处理
├── templates/inventory/
│   ├── order_list.html         # 订单列表页面
│   ├── create_order.html       # 创建订单页面
│   └── order_detail.html       # 订单详情页面
└── utils/inventory_helpers.py   # 订单辅助函数
```

## 数据库表

订单相关表已自动创建：
- `purchase_orders` - 订单主表
- `purchase_order_details` - 订单明细表

## 总结

该订单管理功能提供了完整的订单创建、查看、管理流程，界面友好，功能完善，支持复杂的产品选择和价格计算逻辑，为库存管理系统提供了重要的业务支持。 