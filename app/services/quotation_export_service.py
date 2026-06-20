# -*- coding: utf-8 -*-
"""报价单批量导出 — 产品统计电子表格(透视友好)。

数据整理在此,表格构建复用 product_stats_export.build_product_stats_xlsx。
"""
from flask_babel import gettext as _

from app.services.product_stats_export import build_product_stats_xlsx
from app.utils.dictionary_helpers import project_stage_label
from app.utils.status_meta import get_status_label


def build_batch_product_xlsx(quotations, lang='zh'):
    """构建报价产品统计 xlsx(BytesIO)。quotations:已鉴权过的报价单列表。"""
    rows = []
    for q in quotations:
        proj_name = q.project.project_name if q.project else ''
        stage_key = (q.project.current_stage if q.project else None) or q.project_stage
        stage = project_stage_label(stage_key, lang) if stage_key else ''
        status = get_status_label(q.confirmation_badge_status or 'none', 'quotation')
        for d in q.details:
            if getattr(d, 'row_type', 'product') == 'section':
                continue
            rows.append([
                d.product_mn or '', d.product_name or '', d.product_model or '',
                d.quantity or 0, float(d.unit_price or 0), float(d.total_price or 0),
                q.quotation_number, proj_name, stage, status,
            ])
    return build_product_stats_xlsx(rows, _('报价单编号'), _('报价单状态'), table_prefix='quot')
