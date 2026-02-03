#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""添加客户活跃度指标到数据库

用法: python scripts/temp/add_customer_activity_metric.py
"""
import sys
import os

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from app import create_app, db
from app.models.performance_config import PerformanceMetricsDefinition

app = create_app()

with app.app_context():
    # 检查是否已存在
    existing = PerformanceMetricsDefinition.query.filter_by(
        metric_code='customer_activity_rate'
    ).first()

    if existing:
        print("✅ 客户活跃度指标已存在，无需添加")
    else:
        metric = PerformanceMetricsDefinition(
            metric_code='customer_activity_rate',
            metric_name='客户活跃度',
            metric_category='客户管理',
            data_type='percentage',
            default_unit='%',
            description='活跃和高度活跃客户占总客户的比例',
            is_system_metric=True,
            is_active=True,
            available_sources={
                'model': 'Company',
                'field': 'activity_status',
                'aggregate': 'custom',
                'formula': '(highly_active + active) / total * 100'
            }
        )
        db.session.add(metric)
        db.session.commit()
        print("✅ 成功添加客户活跃度指标")

    # 显示当前所有指标
    all_metrics = PerformanceMetricsDefinition.query.filter_by(is_active=True).all()
    print(f"\n当前共有 {len(all_metrics)} 个绩效指标:")
    for m in all_metrics:
        print(f"  - {m.metric_code}: {m.metric_name}")
