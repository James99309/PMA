# -*- coding: utf-8 -*-
"""
AT 序列号管理 · 数据聚合 helpers

  - build_sn_stages_data(sn)   → at_stage_strip 5 阶段
  - normalize_sn_timeline(raw) → at_timeline events
  - sn_status_meta(status)     → {tone, label}
"""

# ─── 状态徽章映射 ─────────────────────────────────────
SN_STATUS_META = {
    'registered': {'tone': 'neutral', 'label': '已登记'},
    'in_stock':   {'tone': 'success', 'label': '库存中'},
    'reserved':   {'tone': 'warn',    'label': '已预留'},
    'shipped':    {'tone': 'info',    'label': '已发货'},
    'delivered':  {'tone': 'success', 'label': '已交付'},
    'returned':   {'tone': 'warn',    'label': '已退回'},
    'defective':  {'tone': 'danger',  'label': '故障'},
}


def sn_status_meta(status):
    return SN_STATUS_META.get(status, {'tone': 'neutral', 'label': status or '未知'})


# ─── 5 阶段配置 ───────────────────────────────────────
SN_STAGE_DEFS = [
    {'key': 'registered', 'label': '已登记', 'icon': 'edit'},
    {'key': 'in_stock',   'label': '入库',   'icon': 'archive'},
    {'key': 'shipped',    'label': '出库',   'icon': 'truck'},
    {'key': 'delivered',  'label': '交付',   'icon': 'check'},
    {'key': 'warranty',   'label': '质保',   'icon': 'flask'},
]

# 状态 → 当前阶段 index 映射(正常生命周期)
_STATUS_TO_INDEX = {
    'registered': 0,
    'in_stock':   1,
    'reserved':   1,   # 预留也属于库存阶段
    'shipped':    2,
    'delivered':  3,
    # 异常态另处理(returned/defective)
}


def _fmt(dt):
    return dt.strftime('%Y-%m-%d') if dt else None


def build_sn_stages_data(sn):
    """
    把 SN 转换成 at_stage_strip 期望的 5 阶段列表:
      [{key, label, icon, status('done'|'current'|'future'), date, rejected?}]

    异常态规则:
      - defective(故障)→ 所有未来阶段标 rejected,可视化为红色阻断
      - returned(退回)→ 同上,但 tone 不同(实际由 status_map pill 处理)
    """
    is_defective = sn.status == 'defective'
    is_returned  = sn.status == 'returned'
    is_warranty_expired = (
        sn.warranty_end_date is not None
        and hasattr(sn.warranty_end_date, 'date')
    )  # 简化:有结束日期就算进入质保阶段

    current_idx = _STATUS_TO_INDEX.get(sn.status, 0)
    # delivered 且有 warranty_end → 推进到 warranty(index 4)
    if sn.status == 'delivered' and sn.warranty_end_date:
        current_idx = 4

    stages = []
    for i, sdef in enumerate(SN_STAGE_DEFS):
        # 取每阶段的日期(尽力而为)
        date = None
        if sdef['key'] == 'registered':
            date = _fmt(sn.created_at)
        elif sdef['key'] == 'in_stock':
            date = _fmt(sn.warehouse_in_date)
        elif sdef['key'] == 'shipped':
            date = _fmt(sn.ship_out_date)
        elif sdef['key'] == 'delivered':
            # 没有专门字段;近似为发货日期 + 客户存在
            date = _fmt(sn.ship_out_date) if sn.customer_id else None
        elif sdef['key'] == 'warranty':
            date = _fmt(sn.warranty_end_date)

        if i < current_idx:
            status = 'done'
        elif i == current_idx:
            status = 'current'
        else:
            status = 'future'

        # 异常态:current 之后(含 current)的标 rejected
        rejected = (is_defective or is_returned) and i >= current_idx

        stages.append({
            'key':      sdef['key'],
            'label':    sdef['label'],
            'icon':     sdef['icon'],
            'status':   status,
            'date':     date,
            'rejected': rejected,
        })

    return stages


# ─── 历史事件 → 时间线 events ─────────────────────────
_ACTION_ICON = {
    'register': 'edit',
    'stock_in': 'archive',
    'reserve':  'box',
    'ship':     'truck',
    'deliver':  'check',
    'return':   'back',
    'defect':   'close',
    'update':   'edit',
}

_ACTION_TONE = {
    'register': 'neutral',
    'stock_in': 'success',
    'reserve':  'warn',
    'ship':     'info',
    'deliver':  'success',
    'return':   'warn',
    'defect':   'danger',
    'update':   'accent',
}


def normalize_sn_timeline(raw_events):
    """
    ProductSNService.get_timeline 返回的 list[dict] → at_timeline 期望形态
    """
    out = []
    for ev in raw_events or []:
        action = ev.get('action', 'update')
        out.append({
            'icon':  _ACTION_ICON.get(action, 'check'),
            'tone':  _ACTION_TONE.get(action, 'neutral'),
            'title': ev.get('action_label') or action,
            'time':  ev.get('operated_at') or '',
            'desc':  ev.get('description') or '',
            'meta':  ev.get('location') or '',
            'by':    ev.get('operated_by') or '',
        })
    return out
