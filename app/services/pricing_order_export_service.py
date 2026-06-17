# -*- coding: utf-8 -*-
"""批价单批量导出 — 产品统计电子表格(透视友好)。

支持两种维度:
  pricing    — 批价单明细(pricing_details)
  settlement — 结算单明细(settlement_details)

表格构建复用 product_stats_export.build_product_stats_xlsx。
"""
from flask_babel import gettext as _

from app.services.product_stats_export import build_product_stats_xlsx
from app.utils.dictionary_helpers import project_stage_label
from app.utils.status_meta import get_status_label


def build_batch_pricing_xlsx(orders, mode='pricing', lang='zh'):
    """构建批价/结算产品统计 xlsx(BytesIO)。

    orders:已鉴权过的批价单列表。
    mode: 'pricing' 取批价明细;'settlement' 取结算明细。
    """
    settlement = (mode == 'settlement')
    rows = []
    for o in orders:
        proj_name = o.project.project_name if o.project else ''
        stage_key = o.project.current_stage if o.project else None
        stage = project_stage_label(stage_key, lang) if stage_key else ''
        status = get_status_label(o.status or 'draft', 'pricing_order')
        details = o.settlement_details if settlement else o.pricing_details
        for d in details:
            rows.append([
                d.product_mn or '', d.product_name or '', d.product_model or '',
                d.quantity or 0, float(d.unit_price or 0), float(d.total_price or 0),
                o.order_number, proj_name, stage, status,
            ])

    doc_no = _('批价单编号')
    return build_product_stats_xlsx(rows, doc_no, _('批价单状态'), table_prefix='po')
