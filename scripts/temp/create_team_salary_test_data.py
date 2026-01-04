#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
团队成员薪资测试数据创建脚本
为gxh的团队成员（李华伟、林文冠）创建2025年12个月的批价单数据

测试数据标记规则：
- 项目名称: [测试]薪资验证项目-{姓名}2025
- 报价单号: TEST-Q-SALARY-{ID}-001
- 批价单号: TEST-SALARY-{ID}-2025-MM

折扣率设计：
- 高批价: < 0.45 (如 0.38, 0.40, 0.42, 0.43)
- 普通: > 0.45 (如 0.46, 0.48, 0.50, 0.52, 0.55)
- 边界: = 0.45
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

TEST_YEAR = 2025

# 团队成员配置
TEAM_MEMBERS = [
    {
        'id': 15,
        'name': '李华伟',
        'monthly_data': {
            1:  {'amount': 75000,  'rate': 0.42},  # 7.5万, 高批价
            2:  {'amount': 75000,  'rate': 0.48},  # 7.5万, 普通
            3:  {'amount': 75000,  'rate': 0.40},  # 7.5万, 高批价
            4:  {'amount': 87500,  'rate': 0.50},  # 8.75万, 普通
            5:  {'amount': 87500,  'rate': 0.43},  # 8.75万, 高批价
            6:  {'amount': 87500,  'rate': 0.46},  # 8.75万, 普通
            7:  {'amount': 100000, 'rate': 0.38},  # 10万, 高批价
            8:  {'amount': 100000, 'rate': 0.52},  # 10万, 普通
            9:  {'amount': 100000, 'rate': 0.45},  # 10万, 边界
            10: {'amount': 112500, 'rate': 0.40},  # 11.25万, 高批价
            11: {'amount': 112500, 'rate': 0.55},  # 11.25万, 普通
            12: {'amount': 112500, 'rate': 0.42},  # 11.25万, 高批价
        }
    },
    {
        'id': 19,
        'name': '林文冠',
        'monthly_data': {
            1:  {'amount': 62500,  'rate': 0.48},  # 6.25万, 普通
            2:  {'amount': 62500,  'rate': 0.42},  # 6.25万, 高批价
            3:  {'amount': 62500,  'rate': 0.50},  # 6.25万, 普通
            4:  {'amount': 75000,  'rate': 0.38},  # 7.5万, 高批价
            5:  {'amount': 75000,  'rate': 0.45},  # 7.5万, 边界
            6:  {'amount': 75000,  'rate': 0.52},  # 7.5万, 普通
            7:  {'amount': 87500,  'rate': 0.40},  # 8.75万, 高批价
            8:  {'amount': 87500,  'rate': 0.48},  # 8.75万, 普通
            9:  {'amount': 87500,  'rate': 0.43},  # 8.75万, 高批价
            10: {'amount': 125000, 'rate': 0.55},  # 12.5万, 普通
            11: {'amount': 125000, 'rate': 0.42},  # 12.5万, 高批价
            12: {'amount': 125000, 'rate': 0.45},  # 12.5万, 边界
        }
    }
]


def create_test_project(app, user_id, user_name):
    """创建测试项目"""
    with app.app_context():
        project_name = f'[测试]薪资验证项目-{user_name}{TEST_YEAR}'

        # 检查是否已存在
        existing = Project.query.filter(
            Project.project_name == project_name
        ).first()

        if existing:
            print(f'  ✅ 已存在测试项目: ID={existing.id}')
            return existing.id

        project = Project(
            project_name=project_name,
            project_type='工程项目',
            current_stage='成交',
            status='approved',
            created_by=user_id,
            owner_id=user_id,
            report_time=date(TEST_YEAR, 1, 1)
        )
        db.session.add(project)
        db.session.commit()

        print(f'  ✅ 创建测试项目: ID={project.id}')
        return project.id


def create_test_quotation(app, user_id, project_id):
    """创建测试报价单"""
    with app.app_context():
        quotation_number = f'TEST-Q-SALARY-{user_id}-001'

        # 检查是否已存在
        existing = Quotation.query.filter_by(quotation_number=quotation_number).first()

        if existing:
            print(f'  ✅ 已存在测试报价单: ID={existing.id}')
            return existing.id

        # 获取一个客户公司ID用于关联
        customer = Company.query.first()
        customer_id = customer.id if customer else None

        quotation = Quotation(
            quotation_number=quotation_number,
            project_id=project_id,
            owner_id=user_id,
            customer_id=customer_id,
            created_at=datetime(TEST_YEAR, 1, 1, 10, 0, 0)
        )
        db.session.add(quotation)
        db.session.commit()

        print(f'  ✅ 创建测试报价单: ID={quotation.id}')
        return quotation.id


def create_test_pricing_orders(app, user_id, project_id, quotation_id, monthly_data):
    """创建12个月的测试批价单"""
    created_count = 0
    high_price_count = 0
    normal_count = 0

    with app.app_context():
        for month, data in monthly_data.items():
            order_number = f'TEST-SALARY-{user_id}-{TEST_YEAR}-{month:02d}'

            # 检查是否已存在
            existing = PricingOrder.query.filter_by(order_number=order_number).first()
            if existing:
                print(f'    跳过: {order_number} (已存在)')
                continue

            # 判断高批价/普通
            rate = data['rate']
            if rate < 0.45:
                price_type = '高批价'
                high_price_count += 1
            elif rate > 0.45:
                price_type = '普通'
                normal_count += 1
            else:
                price_type = '边界'

            # 创建批价单
            order = PricingOrder(
                order_number=order_number,
                project_id=project_id,
                quotation_id=quotation_id,
                created_by=user_id,
                status='approved',
                approved_at=datetime(TEST_YEAR, month, 15, 14, 0, 0),
                pricing_total_amount=data['amount'],
                pricing_total_discount_rate=rate,
                approval_flow_type='sales_opportunity',
                created_at=datetime(TEST_YEAR, month, 10, 10, 0, 0)
            )
            db.session.add(order)
            created_count += 1
            print(f'    创建: {order_number}, 金额={data["amount"]/10000:.2f}万, 折扣率={rate:.0%} ({price_type})')

        db.session.commit()

    return created_count, high_price_count, normal_count


def verify_member_data(app, user_id, user_name):
    """验证成员的数据"""
    with app.app_context():
        orders = PricingOrder.query.filter(
            PricingOrder.order_number.like(f'TEST-SALARY-{user_id}-{TEST_YEAR}-%'),
            PricingOrder.created_by == user_id,
            PricingOrder.status == 'approved'
        ).order_by(PricingOrder.approved_at).all()

        total_amount = 0
        high_price_amount = 0
        normal_amount = 0

        for o in orders:
            amount = o.pricing_total_amount / 10000
            total_amount += amount
            if o.pricing_total_discount_rate < 0.45:
                high_price_amount += amount
            elif o.pricing_total_discount_rate > 0.45:
                normal_amount += amount

        print(f'\n  {user_name} (ID: {user_id}) 数据统计:')
        print(f'    批价单数量: {len(orders)} 条')
        print(f'    年度合计: {total_amount:.2f}万')
        print(f'    高批价金额: {high_price_amount:.2f}万')
        print(f'    普通金额: {normal_amount:.2f}万')

        return len(orders), total_amount


def main():
    """主函数"""
    print('=' * 70)
    print(' 团队成员薪资测试数据创建脚本')
    print(' 目标: 为gxh的团队成员创建2025年批价单测试数据')
    print('=' * 70)

    app = create_app()

    total_orders = 0
    total_amount = 0

    for member in TEAM_MEMBERS:
        user_id = member['id']
        user_name = member['name']
        monthly_data = member['monthly_data']

        print(f'\n处理成员: {user_name} (ID: {user_id})')
        print('-' * 50)

        # 1. 创建测试项目
        print('  步骤1: 创建测试项目')
        project_id = create_test_project(app, user_id, user_name)

        # 2. 创建测试报价单
        print('  步骤2: 创建测试报价单')
        quotation_id = create_test_quotation(app, user_id, project_id)

        # 3. 创建12个月的批价单
        print('  步骤3: 创建12个月的批价单')
        created, high, normal = create_test_pricing_orders(
            app, user_id, project_id, quotation_id, monthly_data
        )
        print(f'  新创建: {created} 条 (高批价: {high}, 普通: {normal})')

        # 4. 验证数据
        orders, amount = verify_member_data(app, user_id, user_name)
        total_orders += orders
        total_amount += amount

    # 汇总
    print('\n' + '=' * 70)
    print(' 汇总统计')
    print('=' * 70)
    print(f'  总批价单数量: {total_orders} 条')
    print(f'  团队业绩合计: {total_amount:.2f}万')

    # 清理命令
    print('\n' + '=' * 70)
    print(' 清理命令 (测试完成后执行)')
    print('=' * 70)
    print('''
# 清理所有团队成员测试数据
python3 scripts/temp/cleanup_team_salary_test_data.py --confirm

# 或手动SQL:
DELETE FROM pricing_orders WHERE order_number LIKE 'TEST-SALARY-15-%' OR order_number LIKE 'TEST-SALARY-19-%';
DELETE FROM quotations WHERE quotation_number LIKE 'TEST-Q-SALARY-15-%' OR quotation_number LIKE 'TEST-Q-SALARY-19-%';
DELETE FROM projects WHERE project_name LIKE '[测试]薪资验证项目-李华伟%' OR project_name LIKE '[测试]薪资验证项目-林文冠%';
''')

    if total_orders == 24:  # 2个成员 × 12个月
        print('✅ 测试数据创建完成!')
        print('\n下一步:')
        print('  1. 访问 gxh 的薪资详情页，查看团队目标和团队完成率')
        print('  2. 访问 lihuawei/linwengguan 的薪资详情页，查看个人收益')
    else:
        print(f'⚠️ 数据不完整，只有 {total_orders}/24 条记录')


if __name__ == '__main__':
    main()
