# 订单-采购-发货-库存 全链路重构计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 打通客户订单→采购订单→发货→库存的完整业务链路，支持需求池驱动采购、采购订单发起发货、发货自动关联客户订单、跨NAS需求同步。

**Architecture:** 以采购订单为发货创建入口，Shipment 同时关联 PurchaseOrder（来源）和 SalesOrder（需求方）。SalesOrderDetail 新增 procured_quantity 追踪采购进度，PurchaseOrderDetail 新增 sales_order_detail_id 实现明细级需求关联。CN/SG 通过 Tailscale 内网 API 同步采购需求。

**Tech Stack:** Flask + SQLAlchemy + PostgreSQL 17 + Alembic 迁移 + Tailwind CSS + Alpine.js

**范围排除:** 结算管理（代理商仓库与结算单的消结过程）不在本次范围内。

---

## 现有代码状态（审计结果）

### 模块完整度

| 模块 | 模型 | 路由 | 服务层 | 模板 | 状态 |
|------|------|------|--------|------|------|
| **客户订单** SalesOrder | ✅ 完整 (157行) | ✅ 8个端点 | ✅ 384行 | ✅ tw_list + tw_detail | 生产可用 |
| **采购订单** PurchaseOrder | ✅ 完整 (40+字段) | ✅ 40+端点 | ✅ helpers+service | ✅ tw_list + tw_detail | 生产可用 |
| **发货管理** Shipment | ✅ 完整 (152行) | ✅ 12个端点 | ✅ 473行 | ✅ tw_list + tw_detail | 生产可用 |
| **库存管理** Inventory | ✅ 基础模型 | ✅ 含在inventory.py | ✅ helpers | ⚠️ Bootstrap | 基础可用 |
| **跨NAS同步** cross_sync | ✅ 消息/产品同步 | ✅ 3个端点 | ✅ 244行 | N/A | 有现成模式 |

### 关键缺失字段

| 模型 | 缺失字段 | 用途 |
|------|----------|------|
| SalesOrderDetail | `procured_quantity` | 追踪该需求已被采购了多少 |
| PurchaseOrderDetail | `sales_order_detail_id` | 明细级关联到客户订单需求 |
| PurchaseOrderDetail | `dispatched_quantity` | 追踪该采购明细已发出多少 |
| Shipment | `purchase_order_id` | 记录发货来源是哪个采购单 |
| ShipmentDetail | `purchase_order_detail_id` | 明细级关联到采购订单明细 |

### 关键功能缺失

1. **需求池** — 供应链看不到哪些客户订单需求尚未采购
2. **采购订单发起发货** — tw_purchase_order_detail.html L676 是占位 toast
3. **发货与采购订单关联** — Shipment 仅关联 SalesOrder，无 PurchaseOrder
4. **跨NAS需求同步** — SG 客户订单需求无法进入 CN 采购需求池

---

## 业务流程全景

```
┌─────────────────────────────────────────────────────────────┐
│  订单中心（业务部门）                                         │
│                                                             │
│  客户订单 (SalesOrder)                                       │
│  ├─ 代理商下单：产品A×100, 产品B×50                           │
│  ├─ procured_quantity 追踪：已采购多少                        │
│  ├─ shipped_quantity 追踪：已发货多少（现有）                   │
│  └─ 发货管理列表查看物流进度（只读跟踪）                       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  采购仓储（供应链部门）                                       │
│                                                             │
│  需求池 ← CN本地SO需求 + SG远程SO需求(API同步)               │
│  ├─ 显示所有 remaining_to_procure > 0 的需求                 │
│  └─ 勾选 → 纳入采购订单                                     │
│                                                             │
│  采购订单 (PurchaseOrder)                                    │
│  ├─ 向供应商采购，明细关联SO需求（可选）                       │
│  ├─ 供应商确认 → 生产跟踪 → 测试 → 到货                     │
│  ├─ 到货后：创建发货单（选择发给哪个SO / 入仓库）              │
│  └─ dispatched_quantity 追踪：已发出多少                      │
│                                                             │
│  发货 (Shipment)                                            │
│  ├─ 从采购订单创建，自动关联客户订单                          │
│  ├─ purchase_order_id + sales_order_id 双向关联              │
│  └─ 多次发货：同一PO可分批发给不同SO或入仓库                   │
│                                                             │
│  库存管理 (Inventory)                                        │
│  ├─ 备货入库：PO到货且无SO关联 → 入公司仓库                   │
│  └─ 库存查看/调整（现有功能）                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Task 1: 数据库迁移 — 新增关联字段

**目标:** 为全链路打通添加必要的数据库字段

**Files:**
- Modify: `app/models/sales_order.py` (SalesOrderDetail 新增字段)
- Modify: `app/models/inventory.py` (PurchaseOrderDetail 新增字段)
- Modify: `app/models/shipment.py` (Shipment + ShipmentDetail 新增字段)
- Create: `migrations/versions/xxx_add_procurement_shipment_linkage.py`

### Step 1: 修改 SalesOrderDetail 模型

`app/models/sales_order.py` — SalesOrderDetail 类中 `shipped_quantity` 后面新增：

```python
procured_quantity = Column(Integer, default=0)  # 已纳入采购的数量
```

新增计算属性：

```python
@property
def remaining_to_procure(self):
    """剩余未采购数量"""
    return max(0, self.quantity - (self.procured_quantity or 0))
```

SalesOrder 类新增聚合属性：

```python
@property
def procured_quantity(self):
    """总已采购数量"""
    return sum(detail.procured_quantity or 0 for detail in self.details)
```

### Step 2: 修改 PurchaseOrderDetail 模型

`app/models/inventory.py` — PurchaseOrderDetail 类中 `received_quantity` 后面新增：

```python
sales_order_detail_id = Column(Integer, ForeignKey('sales_order_details.id'), nullable=True)  # 关联客户订单需求
dispatched_quantity = Column(Integer, default=0)  # 已分配发货的数量

# 关系
sales_order_detail = relationship('SalesOrderDetail', backref='purchase_details')
```

新增计算属性：

```python
@property
def remaining_to_dispatch(self):
    """剩余未发出数量（已到货但未分配发货）"""
    return max(0, (self.received_quantity or 0) - (self.dispatched_quantity or 0))

@property
def source_label(self):
    """需求来源标签"""
    if self.sales_order_detail_id and self.sales_order_detail:
        so = self.sales_order_detail.order
        return f"{so.order_number} {so.customer.company_name if so.customer else ''}"
    return "备货"
```

### Step 3: 修改 Shipment 模型

`app/models/shipment.py` — Shipment 类中 `sales_order_id` 后面新增：

```python
purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=True)  # 来源采购单

# 关系 — 在现有 sales_order relationship 后面新增
purchase_order = relationship('PurchaseOrder', backref='shipments')
```

ShipmentDetail 类中 `sales_order_detail_id` 后面新增：

```python
purchase_order_detail_id = Column(Integer, ForeignKey('purchase_order_details.id'), nullable=True)

# 关系
purchase_order_detail = relationship('PurchaseOrderDetail', backref='shipment_details')
```

### Step 4: 生成并执行迁移

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db migrate -m "add procurement shipment linkage fields"
```

检查迁移文件，确认只包含以下变更：
- `sales_order_details` 表新增 `procured_quantity` 列
- `purchase_order_details` 表新增 `sales_order_detail_id`, `dispatched_quantity` 列
- `shipments` 表新增 `purchase_order_id` 列
- `shipment_details` 表新增 `purchase_order_detail_id` 列

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db upgrade
```

### Step 5: Commit

```bash
git add app/models/sales_order.py app/models/inventory.py app/models/shipment.py migrations/versions/
git commit -m "feat: add procurement-shipment linkage fields for order-to-delivery chain"
```

---

## Task 2: 需求池 API — 供应链查看待采购需求

**目标:** 供应链在创建采购订单时，能看到所有未采购完的客户订单需求

**Files:**
- Modify: `app/routes/purchase_order_routes.py` (新增需求池端点)

### Step 1: 新增需求池 API 端点

`app/routes/purchase_order_routes.py` — 在现有路由后新增：

```python
@purchase_order_bp.route('/api/procurement-demands', methods=['GET'])
@login_required
@permission_required('order', 'view')
def api_procurement_demands():
    """获取待采购需求池（本地SO）"""
    try:
        search = request.args.get('search', '').strip()

        # 查询所有 remaining_to_procure > 0 的客户订单明细
        query = db.session.query(SalesOrderDetail).join(
            SalesOrder, SalesOrderDetail.sales_order_id == SalesOrder.id
        ).filter(
            SalesOrder.status.in_(['confirmed', 'preparing']),
            SalesOrderDetail.quantity > SalesOrderDetail.procured_quantity
        )

        if search:
            query = query.filter(db.or_(
                SalesOrderDetail.product_name.ilike(f'%{search}%'),
                SalesOrder.order_number.ilike(f'%{search}%')
            ))

        details = query.order_by(SalesOrder.created_at.desc()).all()

        demands = []
        for d in details:
            demands.append({
                'sales_order_detail_id': d.id,
                'sales_order_id': d.sales_order_id,
                'order_number': d.order.order_number if d.order else '',
                'customer_name': d.order.customer.company_name if d.order and d.order.customer else '',
                'product_id': d.product_id,
                'product_name': d.product_name,
                'product_model': d.product_model,
                'quantity': d.quantity,
                'procured_quantity': d.procured_quantity or 0,
                'remaining_to_procure': d.remaining_to_procure,
                'source': 'CN'
            })

        return jsonify({'success': True, 'demands': demands})
    except Exception as e:
        logger.error(f"获取需求池失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})
```

### Step 2: 补充 import

在 `purchase_order_routes.py` 顶部 import 区域新增：

```python
from app.models.sales_order import SalesOrder, SalesOrderDetail
```

### Step 3: Commit

```bash
git add app/routes/purchase_order_routes.py
git commit -m "feat: add procurement demands pool API for supply chain"
```

---

## Task 3: 采购订单创建时关联客户需求

**目标:** 创建PO明细时可选择关联客户订单需求，自动更新 procured_quantity

**Files:**
- Modify: `app/routes/purchase_order_routes.py` (修改创建/更新逻辑)
- Modify: `app/helpers/purchase_order_helpers.py` (明细处理增加关联)

### Step 1: 修改明细处理函数

`app/helpers/purchase_order_helpers.py` — `process_order_detail_item()` 函数中，保存明细后新增关联逻辑：

```python
# 在明细保存后，更新关联的客户订单需求的 procured_quantity
if detail.sales_order_detail_id:
    so_detail = SalesOrderDetail.query.get(detail.sales_order_detail_id)
    if so_detail:
        # 重新计算该SO明细被所有PO关联的总采购量
        total_procured = db.session.query(
            db.func.coalesce(db.func.sum(PurchaseOrderDetail.quantity), 0)
        ).filter(
            PurchaseOrderDetail.sales_order_detail_id == so_detail.id
        ).scalar()
        so_detail.procured_quantity = total_procured
```

### Step 2: 修改创建API接受 sales_order_detail_id

`app/routes/purchase_order_routes.py` — `api_create()` 中处理明细时，传递 `sales_order_detail_id`：

明细数据结构新增可选字段：
```python
# 在处理 details 循环中
detail.sales_order_detail_id = item.get('sales_order_detail_id')  # 可选关联
```

### Step 3: Commit

```bash
git add app/routes/purchase_order_routes.py app/helpers/purchase_order_helpers.py
git commit -m "feat: link PO details to SO demands and track procured_quantity"
```

---

## Task 4: 采购订单详情页 — 发货创建入口

**目标:** 替换采购订单详情页的占位 toast，实现从采购订单创建发货单的完整流程

**Files:**
- Modify: `app/templates/inventory/tw_purchase_order_detail.html` (发货模态框)
- Modify: `app/routes/shipment_routes.py` (修改创建API支持 purchase_order_id)
- Modify: `app/services/shipment_service.py` (支持从PO创建发货)

### Step 1: 修改 ShipmentService.create_shipment 支持 PO 来源

`app/services/shipment_service.py` — 修改 `create_shipment` 方法签名和逻辑：

```python
@staticmethod
def create_shipment(shipment_data, details, current_user_id,
                    sales_order_id=None, purchase_order_id=None):
    """
    创建发货单
    - 从客户订单发起：传 sales_order_id（现有逻辑保留）
    - 从采购订单发起：传 purchase_order_id，details 中包含目标 sales_order_id
    """
```

从 PO 创建时的核心逻辑：
- Shipment.purchase_order_id = purchase_order_id
- Shipment.sales_order_id = details 中指定的 sales_order_id（可选）
- 更新 PurchaseOrderDetail.dispatched_quantity
- 如果有关联 SO，同步更新 SalesOrderDetail.shipped_quantity

### Step 2: 新增从PO创建发货的API端点

`app/routes/shipment_routes.py` — 新增端点：

```python
@shipment_bp.route('/api/create-from-po', methods=['POST'])
@login_required
@permission_required('shipment', 'create')
def api_create_from_po():
    """从采购订单创建发货单"""
    data = request.get_json()
    purchase_order_id = data.get('purchase_order_id')
    destination_type = data.get('destination_type')  # 'sales_order' 或 'warehouse'
    sales_order_id = data.get('sales_order_id')  # destination_type='sales_order' 时必填
    # ... 创建逻辑
```

### Step 3: 采购订单详情页发货模态框

`app/templates/inventory/tw_purchase_order_detail.html` — 替换 L676 的占位 toast：

实现模态框包含：
1. **发货目的选择**：发给客户订单（下拉选 SO）/ 入公司仓库
2. **可发货明细列表**：显示 PO 中 remaining_to_dispatch > 0 的明细
3. **每条明细可填写本次发货数量**
4. **物流信息**：承运商、运单号、预计到达日期
5. 提交后调用 `/shipment/api/create-from-po`

### Step 4: 新增获取PO可发货明细API

`app/routes/shipment_routes.py` — 新增：

```python
@shipment_bp.route('/api/po/<int:po_id>/dispatchable-details', methods=['GET'])
@login_required
@permission_required('shipment', 'view')
def api_get_dispatchable_details(po_id):
    """获取采购订单中可分配发货的明细"""
    order = PurchaseOrder.query.get_or_404(po_id)
    details = []
    for d in order.details:
        remaining = d.remaining_to_dispatch
        if remaining > 0:
            item = {
                'id': d.id,
                'product_name': d.product_name,
                'product_model': d.product_model,
                'quantity': d.quantity,
                'received_quantity': d.received_quantity or 0,
                'dispatched_quantity': d.dispatched_quantity or 0,
                'remaining_to_dispatch': remaining,
                'source_label': d.source_label,
                'sales_order_detail_id': d.sales_order_detail_id
            }
            details.append(item)
    return jsonify({'success': True, 'details': details, 'order_number': order.order_number})
```

### Step 5: Commit

```bash
git add app/services/shipment_service.py app/routes/shipment_routes.py app/templates/inventory/tw_purchase_order_detail.html
git commit -m "feat: create shipments from purchase orders with SO/warehouse destination"
```

---

## Task 5: 客户订单详情页 — 显示采购进度

**目标:** 客户订单详情页展示每条明细的采购进度，业务部门可查看需求被采购了多少

**Files:**
- Modify: `app/templates/sales_order/tw_detail.html` (新增采购进度列)
- Modify: `app/routes/sales_order_routes.py` (API返回 procured_quantity)

### Step 1: 详情页明细表格新增"已采购"列

`app/templates/sales_order/tw_detail.html` — 明细表格 headers（约L132-139）新增"已采购"列，在"已发货"前面：

```html
<th>{{ _('已采购') }}</th>
```

明细行中（约L149前）新增：
```html
<td class="...">
    <span class="{% if detail.procured_quantity >= detail.quantity %}text-green-600{% else %}text-amber-600{% endif %}">
        {{ detail.procured_quantity or 0 }}
    </span>
    <span class="text-slate-400">/ {{ detail.quantity }}</span>
</td>
```

### Step 2: 侧边栏进度新增"采购进度"

`app/templates/sales_order/tw_detail.html` — 在发货进度（约L189）前面新增采购进度条：

```html
<!-- 采购进度 -->
<div class="flex justify-between text-sm mb-1">
    <span>{{ _('已采购') }}</span>
    <span class="font-medium">{{ order.procured_quantity }} / {{ order.total_quantity }}</span>
</div>
{% set proc_percent = (order.procured_quantity / order.total_quantity * 100) if order.total_quantity > 0 else 0 %}
<div class="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2 mb-3">
    <div class="bg-amber-500 h-2 rounded-full" style="width: {{ proc_percent|round(1) }}%"></div>
</div>
```

### Step 3: API 返回新增字段

`app/routes/sales_order_routes.py` — `api_get_order()` 中明细返回新增：

```python
'procured_quantity': d.procured_quantity or 0,
'remaining_to_procure': d.remaining_to_procure,
```

### Step 4: Commit

```bash
git add app/templates/sales_order/tw_detail.html app/routes/sales_order_routes.py
git commit -m "feat: show procurement progress on sales order detail page"
```

---

## Task 6: 采购订单创建页 — 需求池选择器

**目标:** 创建采购订单时，可从需求池勾选客户需求，自动填入PO明细

**Files:**
- Modify: `app/templates/inventory/tw_purchase_order_detail.html` (编辑模态框增加需求选择)
- 可能需要修改: `app/templates/components/tw_purchase_order_form_modal.html`

### Step 1: 新增需求池选择面板

在PO编辑/创建模态框中，明细区域上方新增"从客户需求导入"按钮：

```html
<button @click="showDemandPool = true" type="button"
    class="text-sm text-primary hover:text-primary-dark">
    <span class="material-symbols-outlined text-base align-middle">add_shopping_cart</span>
    {{ _('从客户需求导入') }}
</button>
```

点击后弹出面板：
- 调用 `/purchase-order/api/procurement-demands` 获取需求列表
- 显示：客户订单号、客户名、产品名、型号、待采购数量
- 支持搜索过滤
- 勾选后点"导入"→ 自动填入PO明细，带上 `sales_order_detail_id`

### Step 2: Commit

```bash
git add app/templates/inventory/ app/templates/components/
git commit -m "feat: add demand pool selector to purchase order creation form"
```

---

## Task 7: 跨NAS需求同步 — SG需求进入CN需求池

**目标:** CN采购需求池能看到SG的客户订单需求

**Files:**
- Modify (SG): `app/api/v1/cross_sync.py` (新增需求导出端点)
- Modify (CN): `app/routes/purchase_order_routes.py` (需求池聚合SG数据)
- Modify: `app/services/cross_sync_service.py` (新增需求同步方法)

### Step 1: SG 端新增需求导出 API

`app/api/v1/cross_sync.py` — 新增（部署到SG NAS）：

```python
@cross_sync_bp.route('/procurement-demands', methods=['GET'])
@require_api_key_or_jwt
def get_procurement_demands():
    """供CN采购需求池拉取本地待采购需求"""
    details = db.session.query(SalesOrderDetail).join(
        SalesOrder
    ).filter(
        SalesOrder.status.in_(['confirmed', 'preparing']),
        SalesOrderDetail.quantity > SalesOrderDetail.procured_quantity
    ).all()

    demands = [{
        'sales_order_detail_id': d.id,
        'order_number': d.order.order_number,
        'customer_name': d.order.customer.company_name if d.order.customer else '',
        'product_name': d.product_name,
        'product_model': d.product_model,
        'quantity': d.quantity,
        'procured_quantity': d.procured_quantity or 0,
        'remaining_to_procure': d.remaining_to_procure,
        'source': 'SG'
    } for d in details]

    return jsonify({'success': True, 'demands': demands})
```

### Step 2: CN 端需求池聚合

`app/routes/purchase_order_routes.py` — 修改 `api_procurement_demands()`：

```python
# 在返回本地需求后，尝试拉取SG需求
sg_demands = []
if cross_sync_service.is_cross_sync_enabled():
    try:
        sg_demands = cross_sync_service.fetch_peer_procurement_demands()
    except Exception as e:
        logger.warning(f"拉取SG需求失败（不影响本地）: {e}")

all_demands = demands + sg_demands
return jsonify({'success': True, 'demands': all_demands})
```

### Step 3: cross_sync_service 新增拉取方法

`app/services/cross_sync_service.py` — 新增：

```python
@staticmethod
def fetch_peer_procurement_demands():
    """从对端NAS拉取待采购需求"""
    peer_url = os.environ.get('CROSS_SYNC_PEER_URL')
    api_key = os.environ.get('CROSS_SYNC_API_KEY')

    resp = requests.get(
        f'{peer_url}/cross-sync/procurement-demands',
        headers={'X-API-Key': api_key},
        timeout=10
    )
    if resp.status_code == 200:
        data = resp.json()
        return data.get('demands', [])
    return []
```

### Step 4: Commit

```bash
git add app/api/v1/cross_sync.py app/routes/purchase_order_routes.py app/services/cross_sync_service.py
git commit -m "feat: cross-NAS procurement demand sync via Tailscale API"
```

---

## Task 8: 发货管理列表 — 支持按PO筛选

**目标:** 发货管理列表页同时展示 PO 来源和 SO 目标，支持双向筛选

**Files:**
- Modify: `app/routes/shipment_routes.py` (列表查询支持 PO 筛选)
- Modify: `app/templates/shipment/tw_list.html` (新增 PO 来源列)

### Step 1: 列表查询新增 PO 筛选

`app/routes/shipment_routes.py` — `list_view()` 新增筛选参数：

```python
purchase_order_id = request.args.get('purchase_order_id', '', type=int)
if purchase_order_id:
    query = query.filter(Shipment.purchase_order_id == purchase_order_id)
```

### Step 2: 列表模板新增来源列

`app/templates/shipment/tw_list.html` — 表格新增"采购订单"列：

```html
<td>
    {% if shipment.purchase_order %}
        <a href="{{ url_for('purchase_order.detail_view', order_id=shipment.purchase_order_id) }}"
           class="text-primary hover:underline">
            {{ shipment.purchase_order.order_number }}
        </a>
    {% else %}
        <span class="text-slate-400">-</span>
    {% endif %}
</td>
```

### Step 3: Commit

```bash
git add app/routes/shipment_routes.py app/templates/shipment/tw_list.html
git commit -m "feat: show purchase order source in shipment list with filtering"
```

---

## Task 9: 库存管理 — 备货入库 + 代理商签收入库

**目标:**
- 备货型PO到货验收后自动入公司仓库
- 代理商签收发货后自动增加代理商仓库库存（含基准库存管理）

**Files:**
- Modify: `app/routes/purchase_order_routes.py` (`api_accept_delivery` 增加备货入库逻辑)
- Modify: `app/services/shipment_service.py` (`confirm_receipt` 增加代理商入库逻辑)
- Reference: `app/utils/inventory_helpers.py` (现有入库工具)

### Step 1: 备货型PO验收入库

`app/routes/purchase_order_routes.py` — `api_accept_delivery()` (L779) 新增：

```python
# 验收通过后，检查是否为备货型（无关联SO的明细自动入库）
for detail in order.details:
    if not detail.sales_order_detail_id and detail.received_quantity > 0:
        # 备货明细 → 入公司仓库
        from app.utils.inventory_helpers import update_inventory
        update_inventory(
            company_id=order.company_id,
            product_id=detail.product_id,
            quantity_change=detail.received_quantity,
            transaction_type='in',
            reference_type='order',
            reference_id=order.id,
            description=f'采购订单 {order.order_number} 备货入库',
            user_id=current_user.id
        )
```

### Step 2: 代理商签收后自动入代理商库存

`app/services/shipment_service.py` — `confirm_receipt()` 方法中，签收完成后新增：

```python
# 签收完成后，更新代理商仓库库存
if shipment.sales_order and shipment.sales_order.customer_id:
    customer_company_id = shipment.sales_order.customer_id
    for detail in shipment.details:
        if detail.received_quantity and detail.received_quantity > 0:
            from app.utils.inventory_helpers import update_inventory
            update_inventory(
                company_id=customer_company_id,  # 代理商公司
                product_id=detail.product_id,
                quantity_change=detail.received_quantity,
                transaction_type='in',
                reference_type='shipment',
                reference_id=shipment.id,
                description=f'发货单 {shipment.shipment_number} 签收入库',
                user_id=current_user_id
            )
```

这样代理商的 Inventory 记录会自动更新 quantity，配合现有的 min_stock（基准库存）字段，
当 quantity < min_stock 时业务部门可以看到代理商需要补货。

### Step 3: Commit

```bash
git add app/routes/purchase_order_routes.py app/services/shipment_service.py
git commit -m "feat: auto stock-in for warehouse PO items and distributor receipt"
```

---

## 实施优先级和依赖关系

```
Task 1 (数据库迁移) ──────────────────┐
    ↓                                  │
Task 2 (需求池API)                     │ 所有后续任务依赖 Task 1
    ↓                                  │
Task 3 (PO创建关联SO需求) ←────────────┘
    ↓
Task 5 (SO详情显示采购进度)    ← 可与 Task 4 并行
    ↓
Task 4 (PO详情页发货入口)      ← 核心功能
    ↓
Task 6 (PO创建页需求池选择器)  ← 依赖 Task 2
    ↓
Task 7 (跨NAS需求同步)        ← 依赖 Task 2, 可后期
    ↓
Task 8 (发货列表PO筛选)       ← 依赖 Task 4
    ↓
Task 9 (备货自动入库)          ← 依赖 Task 4
```

**建议分批部署:**
- **第一批 (核心链路):** Task 1 → 2 → 3 → 4 → 5
- **第二批 (体验优化):** Task 6 → 8 → 9
- **第三批 (跨NAS):** Task 7

---

## 部署注意事项

1. **数据库迁移顺序:** 先 CN NAS 再 SG NAS（Task 1 的迁移两边都要跑）
2. **Task 7 的 SG 端代码:** 需要部署到 SG NAS，其余 Task 主要在 CN
3. **现有数据兼容:** 所有新字段 nullable 或有默认值，不影响现有记录
4. **现有发货功能保留:** 从 SO 创建发货的原有流程不删除，与从 PO 创建并存
