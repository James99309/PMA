#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回填积分按明细年份分组

对所有报价单重新执行 sync_quotation_points + sync_pm_category_points，
使积分条目按 QuotationDetail.created_at.year 正确归年。

运行前确保已执行 Alembic 迁移 a7f3e1c9d024（唯一约束含 year）。
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
from app.models.quotation import Quotation
from app.helpers.product_points import sync_quotation_points, sync_pm_category_points


def main():
    app = create_app()
    with app.app_context():
        quotations = Quotation.query.order_by(Quotation.id).all()

        total = len(quotations)
        print(f"共 {total} 个报价单需要回填")

        for i, q in enumerate(quotations, 1):
            try:
                sync_quotation_points(q)
                sync_pm_category_points(q)
                if i % 50 == 0:
                    db.session.commit()
                    print(f"  已处理 {i}/{total}")
            except Exception as e:
                print(f"  报价单 #{q.id} ({q.quotation_number}) 出错: {e}")
                db.session.rollback()

        db.session.commit()
        print(f"回填完成，共处理 {total} 个报价单")


if __name__ == '__main__':
    main()
