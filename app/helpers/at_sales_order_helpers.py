# -*- coding: utf-8 -*-
"""
AT 客户订单详情页 · 数据聚合 helpers

把 ORM 对象转换成 at_* 组件期望的 dict shapes:
  - build_so_stages_data(order)   → 5 阶段(从客户视角)
  - build_so_items_data(order)    → 订单明细(含进度色)
  - build_so_shipments_data(order)→ 该 SO 的发货单列表
  - build_so_current_action(order, stages) → 当前阶段动作卡(只读)
"""
import json
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)


# ─── 5 阶段配置(从客户视角,不暴露 PO 内部审批/确认) ───────────
SO_STAGE_DEFS = [
    {'key': 'confirmed',  'label': '订单确认', 'icon': 'check'},
    {'key': 'production', 'label': '备料生产', 'icon': 'factory'},
    {'key': 'test',       'label': '测试完成', 'icon': 'flask'},
    {'key': 'shipping',   'label': '发货',     'icon': 'truck'},
    {'key': 'received',   'label': '验收入库', 'icon': 'archive'},
]


def _fmt_date(dt):
    if not dt:
        return None
    if isinstance(dt, str):
        return dt[:10]
    if hasattr(dt, 'strftime'):
        return dt.strftime('%Y-%m-%d')
    return str(dt)


def _safe_json_load(raw):
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        val = json.loads(raw)
        return val if isinstance(val, list) else []
    except (json.JSONDecodeError, TypeError, ValueError):
        return []


def _format_sn_range(sn_list):
    """SN 列表 → 紧凑展示"""
    if not sn_list:
        return ''
    if len(sn_list) == 1:
        return sn_list[0]
    import re
    parsed = []
    for s in sn_list:
        m = re.match(r'^(.*?)(\d+)$', str(s))
        if not m:
            parsed = None
            break
        parsed.append((m.group(1), int(m.group(2))))
    if parsed and len(set(p[0] for p in parsed)) == 1:
        nums = [p[1] for p in parsed]
        if all(nums[i] == nums[i-1] + 1 for i in range(1, len(nums))):
            return f"{len(sn_list)} 个 · {sn_list[0]} ~ {sn_list[-1]}"
    return f"{len(sn_list)} 个 · {sn_list[0]} 等"


# ─── 5 阶段:从客户视角看订单进度 ──────────────────────────
def build_so_stages_data(order):
    """构造 5 阶段数据 — 从关联 PO 聚合(取最慢的)+ 自身发货状态。

    判定规则:
      1. 订单确认  → SO.status != 'draft' 且 != 'cancelled'
      2. 备料生产  → 所有关联 PO 都 production_status ∈ {ready, completed, stored}
                    若无关联 PO,fallback 用 procured_quantity >= total
      3. 测试完成  → 所有关联 PO 的 factory_test_status == 'passed'
      4. 发货      → 已发数量 >= 总数量
      5. 验收入库  → 已签收数量 >= 总数量
    """
    from app.models.inventory import PurchaseOrder

    po_ids = {pod.order_id for sod in order.details for pod in (sod.purchase_details or [])}
    linked_pos = PurchaseOrder.query.filter(PurchaseOrder.id.in_(po_ids)).all() if po_ids else []

    total = order.total_quantity or 0
    cancelled = (order.status == 'cancelled')

    is_confirmed = (order.status not in ('draft', 'cancelled'))
    prod_done = (all(po.production_status in ('ready', 'completed', 'stored') for po in linked_pos)
                 if linked_pos else (total > 0 and order.procured_quantity >= total))
    test_done = bool(linked_pos) and all((po.factory_test_status or '') == 'passed' for po in linked_pos)
    shipped_done = total > 0 and order.shipped_quantity >= total
    recv_done = total > 0 and order.received_quantity >= total

    # 日期采样
    confirm_date = _fmt_date(order.created_at) if is_confirmed else None
    prod_dates = []
    for po in linked_pos:
        # 从 stage_history 找最近的 "preparing 完成 / producing 开始" 时刻
        if hasattr(po, 'stage_history') and po.stage_history:
            for h in po.stage_history:
                if h.from_stage in ('preparing', 'producing', 'testing') and h.created_at:
                    prod_dates.append(h.created_at)
    test_dates = [po.factory_test_signed_at for po in linked_pos if po.factory_test_signed_at]
    ship_dates = [s.ship_date for s in order.shipments if s.ship_date]
    recv_dates = [s.received_date for s in order.shipments if s.received_date]

    # 状态机:从前往后判断
    states = [is_confirmed, prod_done, test_done, shipped_done, recv_done]
    # 取消态:所有未完成的阶段都标为 pending,不显示 current
    current_set = False
    stages = []
    for idx, sdef in enumerate(SO_STAGE_DEFS):
        done = states[idx]
        if done:
            status = 'done'
        elif cancelled:
            status = 'future'  # 取消的订单后续阶段全 future
        elif not current_set:
            status = 'current'
            current_set = True
        else:
            status = 'future'

        # 节点日期
        if sdef['key'] == 'confirmed':
            date_str = confirm_date
        elif sdef['key'] == 'production' and prod_dates:
            date_str = _fmt_date(max(prod_dates))
        elif sdef['key'] == 'test' and test_dates:
            date_str = _fmt_date(max(test_dates))
        elif sdef['key'] == 'shipping' and ship_dates:
            date_str = _fmt_date(min(ship_dates))
        elif sdef['key'] == 'received' and recv_dates:
            date_str = _fmt_date(max(recv_dates))
        else:
            date_str = None

        stages.append({
            'key': sdef['key'],
            'label': sdef['label'],
            'icon': sdef['icon'],
            'status': status,
            'date': date_str,
            'attachments': [],
        })
    return stages


# ─── 订单明细(含每行进度色) ──────────────────────────
def build_so_items_data(order):
    """SO 明细 → at_item_table 期望的形态。"""
    items = []
    for d in order.details:
        items.append({
            'desc':  d.product_name,
            'spec':  d.specification or '',
            'model': d.product_model or '',
            'code':  (d.product_mn or (d.product.product_mn if getattr(d, 'product', None) and getattr(d.product, 'product_mn', None) else '')) or '',
            'qty':   d.quantity or 0,
            'unit':  d.unit or '',
            'price': float(d.unit_price or 0),
            # SO 特有:进度三列
            'procured': d.procured_quantity or 0,
            'shipped':  d.shipped_quantity or 0,
            'received': d.received_quantity or 0,
        })
    return items


# ─── 发货记录(只筛该 SO 的发货单) ────────────────────────
# 注:这是发货单自身的状态。SO 详情视角下,'pending'(已开单未发出)≠ SO 的"待发货"
# 整体阶段,所以专门用"已开单"区分,避免和 SO 整体阶段混淆。
SHIPMENT_STATUS_LABEL = {
    'pending':    '已开单',
    'shipped':    '已发出',
    'in_transit': '运输中',
    'delivered':  '已送达',
    'received':   '已签收',
    'exception':  '异常',
}
SHIPMENT_STATUS_TONE = {
    'pending':    'neutral',
    'shipped':    'info',
    'in_transit': 'info',
    'delivered':  'success',
    'received':   'success',
    'exception':  'danger',
}


def build_so_shipments_data(order):
    """该 SO 直接关联的所有发货单(shipment.sales_order_id == order.id)"""
    if not getattr(order, 'shipments', None):
        return []
    out = []
    for s in order.shipments:
        items = []
        for d in (s.details or []):
            sns = _safe_json_load(d.serial_numbers)
            items.append({
                'name': d.product_name,
                'model': d.product_model or '',
                'qty': d.quantity or 0,
                'sn_count': len(sns),
                'sn_range': _format_sn_range(sns),
            })

        docs   = _safe_json_load(getattr(s, 'documents', None))
        proofs = _safe_json_load(getattr(s, 'delivery_proof', None))

        def _attach(name, url, uploaded_at=None):
            if not url:
                return None
            ext = ''
            if isinstance(url, str):
                clean = url.split('?')[0].split('#')[0]
                if '.' in clean:
                    ext = clean.rsplit('.', 1)[-1].lower()
            return {
                'name': name or '附件',
                'url': url,
                'uploaded_at': _fmt_date(uploaded_at) if uploaded_at else None,
                'type': ext,
            }

        express_file = _attach(docs[0].get('name'), docs[0].get('url'), s.ship_date) if docs else None
        receipt_file = _attach(proofs[0].get('name'), proofs[0].get('url'), s.received_date) if proofs else None

        # 目标:SO 详情=客户视角,显示客户名+收货地址(不暴露上游 PO/供应商)
        cust_name = (order.customer.company_name if getattr(order, 'customer', None) else '')
        addr = getattr(order, 'delivery_address', None) or getattr(order, 'delivery_contact', None) or ''
        out.append({
            'id': s.id,
            'number': s.shipment_number,
            'target': cust_name or '客户',
            'target_sub': addr or None,
            'qty': s.total_quantity or 0,
            'status': s.status,
            'status_label': SHIPMENT_STATUS_LABEL.get(s.status, s.status),
            'status_tone':  SHIPMENT_STATUS_TONE.get(s.status, 'neutral'),
            'date':    _fmt_date(s.received_date or s.ship_date),
            'ship_date': _fmt_date(s.ship_date),
            'eta':     _fmt_date(s.expected_arrival),
            'carrier': s.carrier,
            'waybill': s.tracking_number,
            'express': express_file,
            'receipt': receipt_file,
            'notes': s.notes or '',
            'received_notes': s.received_notes or '',
            'ship_items': items,
        })
    return out


# ─── 当前阶段动作卡(只读,SO 没用户操作) ─────────────────────
def build_so_current_action(order, stages):
    """根据当前 stage 给只读提示卡(不显示按钮)。"""
    if order.status == 'cancelled':
        return {
            'phase': 'cancelled',
            'icon': 'cancel',
            'title_label': '订单状态',
            'title': '订单已取消',
            'desc': '该订单已被取消,后续阶段不再推进',
            'hint': '',
            'btn_label': '',
            'btn_onclick': '',
        }

    current = next((s for s in stages if s['status'] == 'current'), None)
    if not current:
        return None  # 全部 done → 不显示卡

    desc_map = {
        'confirmed':  ('等待确认',     '订单尚未确认,请点击右上角"确认订单"开始流程'),
        'production': ('备料生产中',   '关联的采购订单正在生产,请耐心等待'),
        'test':       ('等待测试完成', '生产已完成,正在出厂测试'),
        'shipping':   ('等待发货',     '已通过测试,等待安排发货'),
        'received':   ('等待签收',     '货物已发出,等待签收入库'),
    }
    title_lbl, desc = desc_map.get(current['key'], ('当前阶段', ''))
    return {
        'phase': 'execution',
        'icon': current.get('icon') or 'clock',
        'title_label': '当前阶段',
        'title': current['label'],
        'desc': title_lbl,
        'hint': desc,
        'btn_label': '',
        'btn_onclick': '',
    }
