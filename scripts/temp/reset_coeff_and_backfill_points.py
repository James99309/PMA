#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性脚本：重置所有产品系数为1 + 回填三种角色积分

操作：
1. UPDATE products SET points_coefficient_override=1.0, points_coefficient_override_at=NULL
2. 对所有报价单执行 sync_quotation_points / sync_pm_category_points / sync_se_project_points

用法：
  本地: export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 scripts/temp/reset_coeff_and_backfill_points.py
  NAS:  docker exec -it pma-web python3 scripts/temp/reset_coeff_and_backfill_points.py
"""
import sys
import os


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
from sqlalchemy import text


def reset_coefficients(app):
    """Step 1: 重置所有产品系数为 1.0"""
    with app.app_context():
        result = db.session.execute(text(
            "UPDATE products SET points_coefficient_override = 1.0, "
            "points_coefficient_override_at = NULL"
        ))
        db.session.commit()
        print(f"✅ 已重置 {result.rowcount} 个产品的系数为 1.0")


def backfill_points(app):
    """Step 2: 回填三种角色积分"""
    from app.models.quotation import Quotation
    from app.helpers.product_points import (
        sync_quotation_points, sync_pm_category_points, sync_se_project_points
    )

    with app.app_context():
        quotations = Quotation.query.order_by(Quotation.id).all()
        total = len(quotations)
        print(f"共 {total} 个报价单需要回填")

        errors = 0
        for i, q in enumerate(quotations, 1):
            try:
                sync_quotation_points(q)
                sync_pm_category_points(q)
                sync_se_project_points(q)
                if i % 50 == 0:
                    db.session.commit()
                    print(f"  已处理 {i}/{total}")
            except Exception as e:
                errors += 1
                print(f"  ❌ 报价单 #{q.id} ({q.quotation_number}) 出错: {e}")
                db.session.rollback()

        db.session.commit()
        print(f"✅ 回填完成，共处理 {total} 个报价单，{errors} 个错误")


def verify_results(app):
    """Step 3: 验证结果"""
    with app.app_context():
        result = db.session.execute(text(
            "SELECT source_type, COUNT(*) as cnt, SUM(points) as total "
            "FROM user_points_ledger GROUP BY source_type ORDER BY source_type"
        ))
        rows = result.fetchall()
        print("\n📊 积分总览:")
        for r in rows:
            print(f"  {r.source_type}: {r.cnt} 条记录, 总积分 {r.total:,.0f}")

        # SE 明细
        se_result = db.session.execute(text(
            "SELECT u.real_name, upl.year, SUM(upl.points) as total_points, COUNT(*) as records "
            "FROM user_points_ledger upl "
            "JOIN users u ON u.id = upl.user_id "
            "WHERE upl.source_type = 'se_project' "
            "GROUP BY u.real_name, upl.year "
            "ORDER BY upl.year, u.real_name"
        ))
        se_rows = se_result.fetchall()
        if se_rows:
            print("\n📊 SE 积分明细:")
            for r in se_rows:
                print(f"  {r.real_name} | {r.year}年 | 积分: {r.total_points:,.0f} | 记录数: {r.records}")
        else:
            print("\n  暂无 SE 积分记录（可能无 solution_engineer 角色成员）")


def main():
    app = create_app()

    print("=" * 60)
    print("重置产品系数 + 回填三种角色积分")
    print("=" * 60)

    print("\n📌 Step 1: 重置产品系数为 1.0")
    reset_coefficients(app)

    print("\n📌 Step 2: 回填积分（销售 + PM + SE）")
    backfill_points(app)

    print("\n📌 Step 3: 验证结果")
    verify_results(app)

    print("\n✅ 全部完成")


if __name__ == '__main__':
    main()
