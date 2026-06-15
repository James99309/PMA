# -*- coding: utf-8 -*-
"""
状态徽章映射(label + tone)— PMA 各业务模块的状态值统一中文化 + 配色 tone。

设计原则:
- 按业务 scope 命名空间,避免不同模块同名状态语义冲突(approved 在采购订单 vs 报销 vs 报价 略不同)
- tone 对应 at_pill 的 tone(neutral/accent/success/warn/danger/info)
- 提供 fallback:scope 未匹配或 value 未匹配 → ('—', 'neutral')

使用:
    from app.utils.status_meta import get_status_meta
    label, tone = get_status_meta(obj.status, 'purchase_order')

模板:
    {% from 'components/at_base.html' import at_status_pill %}
    {{ at_status_pill(o.status, scope='purchase_order') }}
"""


# 审批通用(用于审批流卡片头部、approval_instance 状态)
APPROVAL_STATUS_META = {
    'draft':    ('草稿',     'neutral'),
    'pending':  ('审批中',   'warn'),
    'approved': ('已通过',   'success'),
    'rejected': ('已驳回',   'danger'),
    'recalled': ('已召回',   'neutral'),
}

# 采购订单(完整生命周期 12 个状态)
PURCHASE_ORDER_STATUS_META = {
    'draft':     ('草稿',   'neutral'),
    'pending':   ('审批中', 'warn'),
    'rejected':  ('已驳回', 'danger'),
    'approved':  ('已批准', 'success'),
    'confirmed': ('已确认', 'info'),
    'producing': ('生产中', 'accent'),
    'tested':    ('已测试', 'accent'),
    'shipped':   ('已发货', 'info'),
    'stored':    ('已入库', 'success'),
    'completed': ('已完成', 'success'),
    'cancelled': ('已取消', 'neutral'),
}

# 销售/客户订单(履约周期 7 状态)
SALES_ORDER_STATUS_META = {
    'draft':     ('草稿',   'neutral'),
    'confirmed': ('已确认', 'info'),
    'preparing': ('备货中', 'accent'),
    'shipped':   ('已发货', 'info'),
    'delivered': ('已送达', 'success'),
    'completed': ('已完成', 'success'),
    'cancelled': ('已取消', 'danger'),
}

# 报销
EXPENSE_STATUS_META = {
    'draft':             ('草稿',   'neutral'),
    'pending':           ('待审批', 'warn'),
    'approved':          ('已通过', 'success'),
    'awaiting_payment':  ('待付款', 'info'),
    'paid':              ('已支付', 'success'),
    'rejected':          ('已驳回', 'danger'),
}

# 报价(确认徽章)
QUOTATION_CONFIRMATION_META = {
    'none':      ('草稿', 'neutral'),
    'pending':   ('待确认', 'warn'),
    'confirmed': ('已确认', 'success'),
    'rejected':  ('已驳回', 'danger'),
}

# 批价单
PRICING_ORDER_STATUS_META = {
    'draft':    ('草稿',   'neutral'),
    'pending':  ('审批中', 'warn'),
    'approved': ('已批准', 'success'),
    'rejected': ('已驳回', 'danger'),
    'archived': ('已归档', 'neutral'),
}

# 项目阶段
PROJECT_STAGE_META = {
    'discover':   ('发现', 'neutral'),
    'embed':      ('植入', 'accent'),
    'pre_tender': ('标前', 'warn'),
    'quoted':     ('已报价', 'info'),
    'tendering':  ('标中', 'info'),
    'awarded':    ('中标', 'success'),
    'signed':     ('签约', 'success'),
    'lost':       ('失败', 'danger'),
    'paused':     ('暂停', 'neutral'),
}

# WorkItem(工作记录)状态
WORKITEM_STATUS_META = {
    'planned':     ('计划',   'neutral'),
    'in_progress': ('进行中', 'info'),
    'completed':   ('已完成', 'success'),
    'cancelled':   ('已取消', 'neutral'),
    'invalidated': ('已失效', 'neutral'),
}

# 报销支付状态(payment_status)
PAYMENT_STATUS_META = {
    'unpaid':   ('未支付', 'neutral'),
    'awaiting': ('待支付', 'warn'),
    'paid':     ('已支付', 'success'),
}

# 产品库
PRODUCT_STATUS_META = {
    'active':       ('在售',   'success'),
    'upcoming':     ('即将上架', 'info'),
    'discontinued': ('已停产', 'neutral'),
}

# 测试报告状态(采购订单 factory_test_status)
FACTORY_TEST_STATUS_META = {
    'passed':  ('已通过', 'success'),
    'pending': ('未上传', 'neutral'),
    'failed':  ('未通过', 'danger'),
}

# 报价单技术确认审批(标准 ApprovalInstance,与 SM confirmation_badge 区分)
QUOTATION_APPROVAL_STATUS_META = {
    'draft':    ('草稿',     'neutral'),
    'pending':  ('确认中',   'warn'),
    'approved': ('已确认',   'success'),
    'rejected': ('已驳回',   'danger'),
    'recalled': ('已召回',   'neutral'),
}

# 项目失败/搁置审核 chip(审核中态;target 决定颜色)
PROJECT_HOLD_STATUS_META = {
    'paused': ('搁置审核中', 'warn'),
    'lost':   ('失败审核中', 'danger'),
}

# ─── 注册表 ─────────────────────────────────────────────────
_REGISTRY = {
    'approval':            APPROVAL_STATUS_META,
    'project_hold':        PROJECT_HOLD_STATUS_META,
    'quotation_approval':  QUOTATION_APPROVAL_STATUS_META,
    'purchase_order':   PURCHASE_ORDER_STATUS_META,
    'sales_order':      SALES_ORDER_STATUS_META,
    'expense':          EXPENSE_STATUS_META,
    'quotation':        QUOTATION_CONFIRMATION_META,
    'pricing_order':    PRICING_ORDER_STATUS_META,
    'project':          PROJECT_STAGE_META,
    'product':          PRODUCT_STATUS_META,
    'payment':          PAYMENT_STATUS_META,
    'workitem':         WORKITEM_STATUS_META,
    'factory_test':     FACTORY_TEST_STATUS_META,
}


def get_status_meta(value, scope):
    """查指定 scope 下 status 值对应的 (label, tone)。
    未匹配返回 (value, 'neutral') — 让 UI 至少能显示原始值。
    """
    meta = _REGISTRY.get(scope, {}).get(value)
    if meta:
        return meta
    return (value or '—', 'neutral')


def get_status_label(value, scope):
    """只取 label(常用于纯文本场景:Excel 导出、邮件等)"""
    return get_status_meta(value, scope)[0]
