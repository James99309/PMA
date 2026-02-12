#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回填产品经理分类积分 - 扫描所有历史报价单，写入 pm_category ledger 条目"""
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
from app.helpers.product_points import sync_pm_category_points

app = create_app()

with app.app_context():
    quotations = Quotation.query.all()
    total = len(quotations)
    synced = 0
    errors = 0

    print(f"共 {total} 条报价单，开始回填 PM 分类积分...")

    for i, q in enumerate(quotations, 1):
        try:
            sync_pm_category_points(q)
            synced += 1
        except Exception as e:
            errors += 1
            print(f"  [ERROR] 报价单 {q.id}: {e}")

        if i % 100 == 0:
            db.session.commit()
            print(f"  进度: {i}/{total}")

    db.session.commit()
    print(f"\n完成: 成功 {synced}, 失败 {errors}, 总计 {total}")

    # 验证：按 PM 汇总显示
    from app.models.user_points_ledger import UserPointsLedger
    from app.models.user import User
    from sqlalchemy import func

    results = db.session.query(
        UserPointsLedger.user_id,
        UserPointsLedger.year,
        func.sum(UserPointsLedger.points).label('total')
    ).filter(
        UserPointsLedger.source_type == 'pm_category'
    ).group_by(
        UserPointsLedger.user_id, UserPointsLedger.year
    ).order_by(
        UserPointsLedger.year.desc(), func.sum(UserPointsLedger.points).desc()
    ).all()

    if results:
        print("\n=== PM 分类积分汇总 ===")
        for r in results:
            user = User.query.get(r.user_id)
            name = user.real_name or user.username if user else f'ID:{r.user_id}'
            print(f"  {name} ({r.year}): {r.total:,.0f}")
    else:
        print("\n无 PM 分类积分记录")
