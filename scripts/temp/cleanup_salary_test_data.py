#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
薪资测试数据清理脚本
清理由 create_salary_test_data.py 创建的所有测试数据

清理内容：
- 批价单: order_number LIKE 'TEST-SALARY-%'
- 报价单: quotation_number LIKE 'TEST-Q-SALARY-%'
- 项目: project_name LIKE '[测试]薪资验证项目%'
"""
import sys
import os

# 路径修正 - 支持从任何位置运行
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
from app.models.pricing_order import PricingOrder


def count_test_data(app):
    """统计测试数据数量"""
    with app.app_context():
        orders = PricingOrder.query.filter(
            PricingOrder.order_number.like('TEST-SALARY-%')
        ).count()

        quotations = Quotation.query.filter(
            Quotation.quotation_number.like('TEST-Q-SALARY-%')
        ).count()

        projects = Project.query.filter(
            Project.project_name.like('[测试]薪资验证项目%')
        ).count()

        return {
            'orders': orders,
            'quotations': quotations,
            'projects': projects
        }


def cleanup_test_data(app, dry_run=True):
    """清理测试数据

    Args:
        app: Flask 应用实例
        dry_run: True=仅显示将删除的内容，False=实际删除
    """
    with app.app_context():
        # 1. 删除批价单（必须先删除，因为有外键依赖）
        orders = PricingOrder.query.filter(
            PricingOrder.order_number.like('TEST-SALARY-%')
        ).all()

        print(f'\n批价单 ({len(orders)} 条):')
        for o in orders:
            print(f'  - {o.order_number}: {(o.pricing_total_amount or 0)/10000:.2f}万')

        if not dry_run and orders:
            for o in orders:
                db.session.delete(o)
            print(f'  ✅ 已删除 {len(orders)} 条批价单')

        # 2. 删除报价单
        quotations = Quotation.query.filter(
            Quotation.quotation_number.like('TEST-Q-SALARY-%')
        ).all()

        print(f'\n报价单 ({len(quotations)} 条):')
        for q in quotations:
            print(f'  - {q.quotation_number}')

        if not dry_run and quotations:
            for q in quotations:
                db.session.delete(q)
            print(f'  ✅ 已删除 {len(quotations)} 条报价单')

        # 3. 删除项目
        projects = Project.query.filter(
            Project.project_name.like('[测试]薪资验证项目%')
        ).all()

        print(f'\n项目 ({len(projects)} 条):')
        for p in projects:
            print(f'  - ID={p.id}: {p.project_name}')

        if not dry_run and projects:
            for p in projects:
                db.session.delete(p)
            print(f'  ✅ 已删除 {len(projects)} 条项目')

        # 提交事务
        if not dry_run:
            db.session.commit()
            print('\n✅ 所有测试数据已清理完成!')
        else:
            print('\n⚠️  这是预览模式，未实际删除数据')
            print('    使用 --confirm 参数执行实际删除')


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='清理薪资测试数据')
    parser.add_argument('--confirm', action='store_true',
                       help='确认删除（不带此参数仅预览）')
    args = parser.parse_args()

    print('=' * 60)
    print(' 薪资测试数据清理脚本')
    print('=' * 60)

    app = create_app()

    # 统计
    counts = count_test_data(app)
    total = sum(counts.values())

    if total == 0:
        print('\n✅ 没有找到测试数据，无需清理')
        return

    print(f'\n发现测试数据:')
    print(f'  - 批价单: {counts["orders"]} 条')
    print(f'  - 报价单: {counts["quotations"]} 条')
    print(f'  - 项目: {counts["projects"]} 条')
    print(f'  - 合计: {total} 条')

    # 执行清理
    cleanup_test_data(app, dry_run=not args.confirm)

    if not args.confirm:
        print('\n' + '=' * 60)
        print(' 执行命令进行实际删除:')
        print('=' * 60)
        print('python3 scripts/temp/cleanup_salary_test_data.py --confirm')


if __name__ == '__main__':
    main()
