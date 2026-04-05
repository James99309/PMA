#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""刷新所有项目的 quotation_customer 缓存字段

背景：
多货币聚合统计改造（2026-04-05）后，Project.quotation_customer 字段语义从
"最新一张报价单的原 amount（可能是任意货币）"改为
"最新一张报价单的金额，已换算到 Config.DEFAULT_CURRENCY"。

Quotation 的 after_insert/after_update/after_delete 事件监听器会自动维护这个字段，
但对于 **历史数据**（旧报价单没有触发新事件监听器），需要手动一次性刷新。

用法：
    python3 scripts/temp/refresh_project_quotation_customer.py --dry-run  # 预览
    python3 scripts/temp/refresh_project_quotation_customer.py            # 执行

部署到生产后执行：
    cd /volume1/docker/pma && python3 scripts/temp/refresh_project_quotation_customer.py
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
from app.services.exchange_rate_service import exchange_rate_service
from config import Config


def refresh_all_projects(dry_run=False):
    app = create_app()
    with app.app_context():
        target_currency = Config.DEFAULT_CURRENCY
        print(f"系统默认货币: {target_currency}")
        print(f"模式: {'DRY RUN (不写入)' if dry_run else '执行'}")
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
                    # 无报价单 → 金额为 0
                    new_amount = 0.0
                    new_currency = target_currency
                    src_currency = None
                    src_amount = None
                else:
                    src_amount = float(latest.amount or 0)
                    src_currency = (latest.currency or target_currency).upper()
                    if src_amount == 0 or src_currency == target_currency:
                        new_amount = src_amount
                    else:
                        new_amount = float(exchange_rate_service.convert_amount(
                            src_amount, src_currency, target_currency
                        ))
                    new_currency = target_currency

                old_amount = float(project.quotation_customer or 0)
                old_currency = project.quotation_currency or 'CNY'

                if abs(new_amount - old_amount) < 0.01 and new_currency == old_currency:
                    unchanged += 1
                    continue

                if src_currency and src_currency != target_currency:
                    print(f"  [{project.id}] {project.project_name[:30]}")
                    print(f"      源: {src_amount:,.2f} {src_currency} → 换算: {new_amount:,.2f} {target_currency}")
                    print(f"      (缓存旧值: {old_amount:,.2f} {old_currency})")
                else:
                    print(f"  [{project.id}] {project.project_name[:30]}: {old_amount:,.2f} → {new_amount:,.2f} {target_currency}")

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
