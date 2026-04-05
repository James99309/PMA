#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""刷新所有项目的 quotation_customer / quotation_currency 缓存字段

字段语义（2026-04-05 最终确定）：
- quotation_customer: **最新一张报价单的原金额**（不做汇率换算）
- quotation_currency: **最新一张报价单的原货币**

跨项目统计的汇率换算由 MultiCurrencyAggregationService.sum_converted 在读取端
动态完成，不依赖此缓存字段做跨货币求和。

用法：
    python3 scripts/temp/refresh_project_quotation_customer.py --dry-run  # 预览
    python3 scripts/temp/refresh_project_quotation_customer.py            # 执行
"""
import sys
import os
import argparse


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
from app.models.project import Project
from app.models.quotation import Quotation
from config import Config


def refresh_all_projects(dry_run=False):
    app = create_app()
    with app.app_context():
        print(f"模式: {'DRY RUN (不写入)' if dry_run else '执行'}")
        print(f"字段语义: quotation_customer = 最新报价单原金额, quotation_currency = 原货币")
        print("=" * 60)

        projects = Project.query.all()
        print(f"共 {len(projects)} 个项目\n")

        unchanged = 0
        updated = 0
        errors = 0

        for project in projects:
            try:
                # 查最新一张报价单
                latest = Quotation.query.filter(
                    Quotation.project_id == project.id
                ).order_by(Quotation.created_at.desc()).first()

                if latest is None:
                    # 无报价单 → 金额为 0, 货币取系统默认
                    new_amount = 0.0
                    new_currency = Config.DEFAULT_CURRENCY
                else:
                    new_amount = float(latest.amount or 0)
                    new_currency = (latest.currency or Config.DEFAULT_CURRENCY).upper()

                old_amount = float(project.quotation_customer or 0)
                old_currency = project.quotation_currency or Config.DEFAULT_CURRENCY

                if abs(new_amount - old_amount) < 0.01 and new_currency == old_currency:
                    unchanged += 1
                    continue

                print(f"  [{project.id}] {project.project_name[:30]}")
                print(f"      旧: {old_amount:,.2f} {old_currency}")
                print(f"      新: {new_amount:,.2f} {new_currency}")

                if not dry_run:
                    project.quotation_customer = new_amount
                    project.quotation_currency = new_currency
                updated += 1

            except Exception as e:
                print(f"  ❌ 项目 {project.id} 失败: {e}")
                errors += 1

        if not dry_run:
            db.session.commit()

        print()
        print("=" * 60)
        print(f"无变化: {unchanged}")
        print(f"已{'预览' if dry_run else '更新'}: {updated}")
        print(f"失败: {errors}")
        if dry_run:
            print("\n运行 `python3 scripts/temp/refresh_project_quotation_customer.py` 实际执行")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='预览不写入')
    args = parser.parse_args()
    refresh_all_projects(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
