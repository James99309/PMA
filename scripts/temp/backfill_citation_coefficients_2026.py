#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回填引用频次系数并重新计算2026年积分

流程:
1. 调用 batch_update_citation_coefficients() 计算所有产品系数
2. 删除 user_points_ledger 中 year=2026 的所有记录
3. 查出2026年有明细的报价单，按 id 升序处理
4. 对每张报价单重新调用 sync_quotation_points, sync_pm_category_points, sync_se_project_points
5. 输出变化统计

⚠️ 执行前必须备份数据库!
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

from datetime import datetime
from app import create_app, db
from app.models.quotation import Quotation
from app.models.user_points_ledger import UserPointsLedger
from app.helpers.product_points import (
    batch_update_citation_coefficients,
    sync_quotation_points,
    sync_pm_category_points,
    sync_se_project_points
)

app = create_app()

with app.app_context():
    print("=" * 60)
    print("引用频次系数回填脚本")
    print(f"时间: {datetime.now()}")
    print("=" * 60)

    # Step 1: 计算引用系数
    print("\n[1/4] 计算产品引用系数...")
    updated, total = batch_update_citation_coefficients()
    print(f"  ✓ 更新 {updated}/{total} 产品")

    # Step 2: 统计回填前积分
    year = 2026
    before_stats = db.session.query(
        db.func.count(UserPointsLedger.id),
        db.func.coalesce(db.func.sum(UserPointsLedger.points), 0)
    ).filter(UserPointsLedger.year == year).first()
    print(f"\n[2/4] 回填前 {year} 年积分统计:")
    print(f"  记录数: {before_stats[0]}, 总积分: {before_stats[1]:,.0f}")

    # Step 3: 删除2026年所有积分记录
    deleted = UserPointsLedger.query.filter(
        UserPointsLedger.year == year
    ).delete(synchronize_session=False)
    db.session.commit()
    print(f"\n[3/4] 已删除 {deleted} 条 {year} 年积分记录")

    # Step 4: 重新计算2026年所有报价单积分
    print(f"\n[4/4] 重新计算 {year} 年报价单积分...")
    year_start = datetime(year, 1, 1)
    year_end = datetime(year + 1, 1, 1)

    quotations = Quotation.query.filter(
        Quotation.created_at >= year_start,
        Quotation.created_at < year_end,
        Quotation.is_deleted == False
    ).order_by(Quotation.id.asc()).all()

    print(f"  找到 {len(quotations)} 张报价单")

    for i, q in enumerate(quotations):
        try:
            sync_quotation_points(q)
            sync_pm_category_points(q)
            sync_se_project_points(q)
            if (i + 1) % 50 == 0:
                db.session.commit()
                print(f"  ... 已处理 {i + 1}/{len(quotations)}")
        except Exception as e:
            print(f"  ⚠ 报价单 #{q.id} ({q.quotation_number}) 出错: {e}")

    db.session.commit()

    # 统计回填后积分
    after_stats = db.session.query(
        db.func.count(UserPointsLedger.id),
        db.func.coalesce(db.func.sum(UserPointsLedger.points), 0)
    ).filter(UserPointsLedger.year == year).first()

    print(f"\n{'=' * 60}")
    print(f"回填完成!")
    print(f"  回填前: {before_stats[0]} 条, 总积分 {before_stats[1]:,.0f}")
    print(f"  回填后: {after_stats[0]} 条, 总积分 {after_stats[1]:,.0f}")
    diff = int(after_stats[1]) - int(before_stats[1])
    sign = '+' if diff >= 0 else ''
    print(f"  变化: {sign}{diff:,.0f}")
    print(f"{'=' * 60}")
