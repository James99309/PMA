#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回填积分流水表 - 将所有历史报价单的积分写入 user_points_ledger

注意: 历史报价单的积分使用当前衰减系数计算，无法还原当时的精确值。
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

from app import create_app, db
from app.models.quotation import Quotation
from app.helpers.product_points import sync_quotation_points

app = create_app()

with app.app_context():
    quotations = Quotation.query.all()
    total = len(quotations)
    synced = 0
    errors = 0

    print(f"共 {total} 条报价单，开始回填...")

    for i, q in enumerate(quotations, 1):
        try:
            sync_quotation_points(q)
            synced += 1
        except Exception as e:
            errors += 1
            print(f"  [ERROR] 报价单 {q.id}: {e}")

        if i % 100 == 0:
            db.session.commit()
            print(f"  进度: {i}/{total}")

    db.session.commit()
    print(f"\n完成: 成功 {synced}, 失败 {errors}, 总计 {total}")
