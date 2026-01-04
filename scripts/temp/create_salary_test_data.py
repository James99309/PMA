#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
薪资测试数据创建脚本
为郭小会创建2025年12个月的批价单数据，用于验证薪资计算系统

测试数据标记规则：
- 项目名称: [测试]薪资验证项目
- 报价单号: TEST-Q-SALARY-001
- 批价单号: TEST-SALARY-2025-MM
"""
import sys
import os
from datetime import datetime, date

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
from app.models.project import Project
from app.models.quotation import Quotation
from app.models.pricing_order import PricingOrder
from app.models.customer import Company

# 郭小会的用户ID
USER_ID = 13
TEST_YEAR = 2025

# 月度业绩数据（万元）
MONTHLY_DATA = {
    # Q1: 50% 完成率, 月目标 29.17万
    1: {'amount': 145800, 'rate': 0.90},   # 14.58万, 高批价
    2: {'amount': 145800, 'rate': 0.90},
    3: {'amount': 145800, 'rate': 0.90},
    # Q2: 60% 完成率
    4: {'amount': 175000, 'rate': 0.88},   # 17.5万
    5: {'amount': 175000, 'rate': 0.88},
    6: {'amount': 175000, 'rate': 0.88},
    # Q3: 70% 完成率
    7: {'amount': 204200, 'rate': 0.86},   # 20.42万
    8: {'amount': 204200, 'rate': 0.86},
    9: {'amount': 204200, 'rate': 0.86},
    # Q4: 100% 完成率
    10: {'amount': 291700, 'rate': 0.85},  # 29.17万
    11: {'amount': 291700, 'rate': 0.85},
    12: {'amount': 291700, 'rate': 0.85},
}


def create_test_project(app):
    """创建测试项目"""
    with app.app_context():
        # 检查是否已存在
        existing = Project.query.filter(
            Project.project_name.like('[测试]薪资验证项目%')
        ).first()

        if existing:
            print(f'✅ 已存在测试项目: ID={existing.id}')
            return existing.id

        # 查找一个客户公司用于关联
        company = Company.query.filter_by(company_type='customer').first()

        project = Project(
            project_name='[测试]薪资验证项目-郭小会2025',
            project_type='工程项目',
            current_stage='成交',
            status='approved',
            created_by=USER_ID,
            owner_id=USER_ID,
            report_time=date(2025, 1, 1)
        )
        db.session.add(project)
        db.session.commit()

        print(f'✅ 创建测试项目: ID={project.id}')
        return project.id


def create_test_quotation(app, project_id):
    """创建测试报价单"""
    with app.app_context():
        # 检查是否已存在
        existing = Quotation.query.filter(
            Quotation.quotation_number.like('TEST-Q-SALARY-%')
        ).first()

        if existing:
            print(f'✅ 已存在测试报价单: ID={existing.id}')
            return existing.id

        # 获取一个客户公司ID用于关联
        customer = Company.query.first()
        customer_id = customer.id if customer else None

        quotation = Quotation(
            quotation_number='TEST-Q-SALARY-001',
            project_id=project_id,
            owner_id=USER_ID,
            customer_id=customer_id,
            created_at=datetime(2025, 1, 1, 10, 0, 0)
        )
        db.session.add(quotation)
        db.session.commit()

        print(f'✅ 创建测试报价单: ID={quotation.id}')
        return quotation.id


def create_test_pricing_orders(app, project_id, quotation_id):
    """创建12个月的测试批价单"""
    created_count = 0

    with app.app_context():
        for month, data in MONTHLY_DATA.items():
            order_number = f'TEST-SALARY-{TEST_YEAR}-{month:02d}'

            # 检查是否已存在
            existing = PricingOrder.query.filter_by(order_number=order_number).first()
            if existing:
                print(f'  跳过: {order_number} (已存在)')
                continue

            # 创建批价单
            order = PricingOrder(
                order_number=order_number,
                project_id=project_id,
                quotation_id=quotation_id,
                created_by=USER_ID,
                status='approved',
                approved_at=datetime(TEST_YEAR, month, 15, 14, 0, 0),
                pricing_total_amount=data['amount'],
                pricing_total_discount_rate=data['rate'],
                approval_flow_type='sales_opportunity',
                created_at=datetime(TEST_YEAR, month, 10, 10, 0, 0)
            )
            db.session.add(order)
            created_count += 1
            print(f'  创建: {order_number}, 金额={data["amount"]/10000:.2f}万')

        db.session.commit()

    return created_count


def verify_data(app):
    """验证创建的数据"""
    with app.app_context():
        orders = PricingOrder.query.filter(
            PricingOrder.order_number.like(f'TEST-SALARY-{TEST_YEAR}-%'),
            PricingOrder.created_by == USER_ID,
            PricingOrder.status == 'approved'
        ).order_by(PricingOrder.approved_at).all()

        print(f'\n已创建的测试批价单: {len(orders)} 条')
        print('-' * 60)

        total_amount = 0
        for o in orders:
            month = o.approved_at.month
            amount = o.pricing_total_amount / 10000
            total_amount += amount
            print(f'{month:2d}月: {o.order_number}, {amount:>8.2f}万, 折扣率={o.pricing_total_discount_rate:.0%}')

        print('-' * 60)
        print(f'年度合计: {total_amount:.2f}万')
        print()

        return len(orders)


def main():
    """主函数"""
    print('=' * 60)
    print(' 薪资测试数据创建脚本')
    print(' 用户: 郭小会 (ID: 13)')
    print(' 年份: 2025')
    print('=' * 60)

    app = create_app()

    # 1. 创建测试项目
    print('\n步骤1: 创建测试项目')
    project_id = create_test_project(app)

    # 2. 创建测试报价单
    print('\n步骤2: 创建测试报价单')
    quotation_id = create_test_quotation(app, project_id)

    # 3. 创建12个月的批价单
    print('\n步骤3: 创建12个月的批价单')
    created_count = create_test_pricing_orders(app, project_id, quotation_id)
    print(f'\n新创建: {created_count} 条')

    # 4. 验证数据
    print('\n步骤4: 验证数据')
    total_orders = verify_data(app)

    # 5. 输出清理命令
    print('=' * 60)
    print(' 清理命令 (测试完成后执行)')
    print('=' * 60)
    print('''
python3 scripts/temp/cleanup_salary_test_data.py

或手动SQL:
DELETE FROM pricing_orders WHERE order_number LIKE 'TEST-SALARY-%';
DELETE FROM quotations WHERE quotation_number LIKE 'TEST-Q-SALARY-%';
DELETE FROM projects WHERE project_name LIKE '[测试]薪资验证项目%';
''')

    if total_orders == 12:
        print('✅ 测试数据创建完成!')
        print(f'\n下一步: 访问用户详情页 → 薪资明细 Tab (选择2025年)')
        print(f'   或调用API: GET /api/v1/user/13/salary?year=2025')
    else:
        print(f'⚠️ 数据不完整，只有 {total_orders}/12 条记录')


if __name__ == '__main__':
    main()
