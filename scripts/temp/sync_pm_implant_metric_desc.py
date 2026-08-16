#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 pm_implant_amount 的指标说明同步为真实口径(按分管分类,非 product.owner_id)。

背景:initialize_default_metrics() 只在缺行时插入,已存在的行不会被更新,
     而绩效指标页读的是数据库里的 description —— 不跑这个脚本,界面上仍是旧文案。
只改说明性字段(description / available_sources),不碰任何计算逻辑。
注:表里没有 description_en 列,英文说明在定义清单里是装饰性的、入库时被丢弃。

用法:
  DATABASE_URL=... python3 scripts/temp/sync_pm_implant_metric_desc.py          # 预览
  DATABASE_URL=... python3 scripts/temp/sync_pm_implant_metric_desc.py --apply  # 执行
"""
import sys, os

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

APPLY = '--apply' in sys.argv

NEW = {
    'description': '分管产品分类下产品的报价单植入小计（仅厂商产品自动置数）',
    'available_sources': {
        'model': 'QuotationDetail',
        'field': 'implant_subtotal',
        'aggregate': 'sum',
        'filter': {'product.category_id': '{managed_category_ids}'},
        'date_field': 'quotation.created_at',
    },
}

from app import create_app, db  # noqa: E402
app = create_app()

with app.app_context():
    from app.models.performance_config import PerformanceMetricsDefinition
    print("目标库:", db.engine.url)
    m = PerformanceMetricsDefinition.query.filter_by(metric_code='pm_implant_amount').first()
    if not m:
        print("未找到 pm_implant_amount 定义行,无需处理")
        sys.exit(0)

    print("\n--- 当前 ---")
    print(" description   :", m.description)
    print(" sources       :", m.available_sources)
    print("\n--- 将改为 ---")
    for k, v in NEW.items():
        print(f" {k:<14}:", v)

    if not APPLY:
        print("\n(预览模式,未写库。加 --apply 执行)")
        sys.exit(0)

    m.description = NEW['description']
    m.available_sources = NEW['available_sources']
    db.session.commit()
    print("\n✅ 已更新")
