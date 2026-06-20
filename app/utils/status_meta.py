# -*- coding: utf-8 -*-
"""
状态徽章映射(label + tone)— PMA 各业务模块的状态值统一中文化 + 配色 tone。

设计原则:
- 按业务 scope 命名空间,避免不同模块同名状态语义冲突(approved 在采购订单 vs 报销 vs 报价 略不同)
- tone 对应 at_pill 的 tone(neutral/accent/success/warn/danger/info)
- 提供 fallback:scope 未匹配或 value 未匹配 → (_l('—'), 'neutral')

使用:
    from app.utils.status_meta import get_status_meta
    label, tone = get_status_meta(obj.status, 'purchase_order')

模板:
    {% from 'components/at_base.html' import at_status_pill %}
    {{ at_status_pill(o.status, scope='purchase_order') }}
"""

from flask_babel import lazy_gettext as _l


# 审批通用(用于审批流卡片头部、approval_instance 状态)
APPROVAL_STATUS_META = {
    'draft':    (_l('草稿'), 'neutral'),
    'pending':  (_l('审批中'), 'warn'),
    'approved': (_l('已通过'), 'success'),
    'rejected': (_l('已驳回'), 'danger'),
    'recalled': (_l('已召回'), 'neutral'),
}

# 采购订单(完整生命周期 12 个状态)
PURCHASE_ORDER_STATUS_META = {
    'draft':     (_l('草稿'), 'neutral'),
    'pending':   (_l('审批中'), 'warn'),
    'rejected':  (_l('已驳回'), 'danger'),
    'approved':  (_l('已批准'), 'success'),
    'confirmed': (_l('已确认'), 'info'),
    'producing': (_l('生产中'), 'accent'),
    'tested':    (_l('已测试'), 'accent'),
    'shipped':   (_l('已发货'), 'info'),
    'stored':    (_l('已入库'), 'success'),
    'completed': (_l('已完成'), 'success'),
    'cancelled': (_l('已取消'), 'neutral'),
}

# 销售/客户订单(履约周期 7 状态)
SALES_ORDER_STATUS_META = {
    'draft':     (_l('草稿'), 'neutral'),
    'confirmed': (_l('已确认'), 'info'),
    'preparing': (_l('备货中'), 'accent'),
    'shipped':   (_l('已发货'), 'info'),
    'delivered': (_l('已送达'), 'success'),
    'completed': (_l('已完成'), 'success'),
    'cancelled': (_l('已取消'), 'danger'),
}

# 报销
EXPENSE_STATUS_META = {
    'draft':             (_l('草稿'), 'neutral'),
    'pending':           (_l('待审批'), 'warn'),
    'approved':          (_l('已通过'), 'success'),
    'awaiting_payment':  (_l('待付款'), 'info'),
    'paid':              (_l('已支付'), 'success'),
    'rejected':          (_l('已驳回'), 'danger'),
}

# 报价(确认徽章)
QUOTATION_CONFIRMATION_META = {
    'none':      (_l('草稿'), 'neutral'),
    'pending':   (_l('待确认'), 'warn'),
    'confirmed': (_l('已确认'), 'success'),
    'rejected':  (_l('已驳回'), 'danger'),
    'reconfirm': (_l('需再次确认'), 'warn'),
}

# 批价单
PRICING_ORDER_STATUS_META = {
    'draft':    (_l('草稿'), 'neutral'),
    'pending':  (_l('审批中'), 'warn'),
    'approved': (_l('已批准'), 'success'),
    'rejected': (_l('已驳回'), 'danger'),
    'archived': (_l('已归档'), 'neutral'),
}

# 项目阶段
PROJECT_STAGE_META = {
    'discover':   (_l('发现'), 'neutral'),
    'embed':      (_l('植入'), 'accent'),
    'pre_tender': (_l('标前'), 'warn'),
    'quoted':     (_l('批价'), 'info'),
    'tendering':  (_l('标中'), 'info'),
    'awarded':    (_l('中标'), 'success'),
    'signed':     (_l('签约'), 'success'),
    'lost':       (_l('失败'), 'danger'),
    'paused':     (_l('暂停'), 'neutral'),
}

# WorkItem(工作记录)状态
WORKITEM_STATUS_META = {
    'planned':     (_l('计划'), 'neutral'),
    'in_progress': (_l('进行中'), 'info'),
    'completed':   (_l('已完成'), 'success'),
    'cancelled':   (_l('已取消'), 'neutral'),
    'invalidated': (_l('已失效'), 'neutral'),
}

# 报销支付状态(payment_status)
PAYMENT_STATUS_META = {
    'unpaid':   (_l('未支付'), 'neutral'),
    'awaiting': (_l('待支付'), 'warn'),
    'paid':     (_l('已支付'), 'success'),
}

# 产品库
PRODUCT_STATUS_META = {
    'active':       (_l('在售'), 'success'),
    'upcoming':     (_l('即将上架'), 'info'),
    'discontinued': (_l('已停产'), 'neutral'),
}

# 测试报告状态(采购订单 factory_test_status)
FACTORY_TEST_STATUS_META = {
    'passed':  (_l('已通过'), 'success'),
    'pending': (_l('未上传'), 'neutral'),
    'failed':  (_l('未通过'), 'danger'),
}

# 报价单技术确认审批(标准 ApprovalInstance,与 SM confirmation_badge 区分)
QUOTATION_APPROVAL_STATUS_META = {
    'draft':     (_l('草稿'), 'neutral'),
    'pending':   (_l('待确认'), 'warn'),
    'approved':  (_l('已确认'), 'success'),
    'rejected':  (_l('已驳回'), 'danger'),
    'recalled':  (_l('已召回'), 'neutral'),
    'reconfirm': (_l('需再次确认'), 'warn'),
}

# 任务状态(Task.status / effective_status)
TASK_STATUS_META = {
    'pending':     (_l('待办'), 'warn'),
    'in_progress': (_l('进行中'), 'info'),
    'completed':   (_l('已完成'), 'success'),
    'paused':      (_l('已暂停'), 'neutral'),
    'cancelled':   (_l('已取消'), 'neutral'),
}

# 任务复核状态(Task.review_status)
TASK_REVIEW_STATUS_META = {
    'pending_review': (_l('待复核'), 'warn'),
    'approved':       (_l('复核通过'), 'success'),
    'rejected':       (_l('复核驳回'), 'danger'),
}

# 项目失败/搁置审核 chip(审核中态;target 决定颜色)
PROJECT_HOLD_STATUS_META = {
    'paused': (_l('搁置审核中'), 'warn'),
    'lost':   (_l('失败审核中'), 'danger'),
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
    'task':             TASK_STATUS_META,
    'task_review':      TASK_REVIEW_STATUS_META,
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
    return str(get_status_meta(value, scope)[0])
