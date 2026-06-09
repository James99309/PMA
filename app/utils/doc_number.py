# -*- coding: utf-8 -*-
"""
通用业务单号生成器
─────────────────────────────────────────────────────────────
统一格式: <PREFIX><YYYYMM>-<NNN>
  例: PO202506-001 / SO202506-001 / SHP202506-001

为什么不带 dash 在前缀和年月之间(`PO-2506-001`):
  - 历史 SO/SHP 已采用无 dash 风格,统一更省事
  - 6 位年月避免 2030 后 YY 跨世纪歧义

为什么序号 3 位:
  - 当月内 999 单 ≈ 业务上限;若某模块需更多位,传 seq_width 调整

并发安全提示:
  - 当前实现按 max(order_number)+1,极端并发下两个请求可能拿到同一序号 →
    依赖 model 的 UNIQUE 约束兜底(commit 时其中一个会 IntegrityError)
  - 调用方推荐捕获 IntegrityError 重试 1-2 次(后续可加 retry decorator)
"""
from datetime import datetime
from sqlalchemy.orm.attributes import InstrumentedAttribute


def generate_doc_number(prefix, model, number_field='order_number',
                        seq_width=3, when=None):
    """
    生成业务单号 <PREFIX><YYYYMM>-<NNN>

    Args:
        prefix:        前缀字符串,如 'PO' / 'SO' / 'SHP'
        model:         SQLAlchemy model 类,需有 number_field 属性
        number_field:  存单号的字段名(默认 'order_number')
        seq_width:     序号位数(默认 3 → '001')
        when:          指定时间(默认 now);供测试或回填使用

    Returns:
        str — 形如 'PO202506-001'

    Example:
        from app.models.inventory import PurchaseOrder
        num = generate_doc_number('PO', PurchaseOrder)         # PO202506-001
        num = generate_doc_number('SO', SalesOrder)            # SO202506-001
        num = generate_doc_number('SHP', Shipment, 'shipment_number')
    """
    if not prefix:
        raise ValueError('prefix 必须提供')

    column = getattr(model, number_field, None)
    if column is None or not isinstance(column, InstrumentedAttribute):
        raise ValueError(f'{model.__name__} 没有字段 {number_field!r}')

    today = when or datetime.now()
    base = f"{prefix}{today.strftime('%Y%m')}"   # e.g. 'PO202506'

    latest = (
        model.query
             .filter(column.like(f'{base}-%'))
             .order_by(column.desc())
             .first()
    )

    seq = 1
    if latest:
        try:
            seq = int(getattr(latest, number_field).rsplit('-', 1)[-1]) + 1
        except (ValueError, IndexError, AttributeError):
            seq = 1

    return f"{base}-{seq:0{seq_width}d}"
