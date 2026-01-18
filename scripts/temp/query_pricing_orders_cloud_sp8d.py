#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询云端SP8D系统中的批价单数据
针对四个销售人员：lihuawei, gxh, fanjing, yangjj
2025年创建、审批通过、项目名称无"测试"
"""
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

project_root = get_project_root()
sys.path.insert(0, project_root)

# 加载云端SP8D配置
env_file = os.path.join(project_root, '.env.sp8d.local')
if os.path.exists(env_file):
    load_dotenv(env_file, override=True)
    print(f"✅ 已加载SP8D配置: {env_file}")
    print(f"   DATABASE_URL: {os.environ.get('DATABASE_URL', 'NOT SET')[:60]}...")
else:
    print(f"❌ 找不到SP8D配置文件: {env_file}")
    sys.exit(1)

from app import create_app, db
from app.models.user import User
from app.models.pricing_order import PricingOrder, SettlementOrder
from app.models.project import Project
from sqlalchemy import and_, or_

def query_sales_manager_pricing_orders():
    """查询四个销售人员的批价单及详细对比数据"""

    app = create_app()
    with app.app_context():
        print("\n" + "="*150)
        print("云端SP8D系统 - 四个销售人员的批价单数据对比")
        print("="*150)

        # 目标销售人员
        target_sales_people = ['lihuawei', 'gxh', 'fanjing', 'yangjj']

        all_results = {}

        for username in target_sales_people:
            print(f"\n\n{'='*150}")
            print(f"查询销售人员: {username}")
            print(f"{'='*150}")

            # 1. 找到用户
            user = User.query.filter(User.username == username).first()
            if not user:
                print(f"❌ 未找到用户: {username}")
                all_results[username] = {
                    'found': False,
                    'user_id': None,
                    'pricing_orders': []
                }
                continue

            print(f"✓ 找到用户: {user.real_name or user.username} (ID: {user.id})")

            # 2. 查询该用户作为项目销售经理的所有批价单
            pricing_orders = PricingOrder.query.join(
                Project, PricingOrder.project_id == Project.id
            ).filter(
                Project.vendor_sales_manager_id == user.id
            ).all()

            print(f"\n✓ 该销售经理共有 {len(pricing_orders)} 个批价单")

            # 3. 过滤条件应用
            filtered_pos = []

            for po in pricing_orders:
                # 检查创建时间是否在2025年
                if po.created_at is None:
                    continue

                # 转换为本地时区
                if po.created_at.tzinfo is None:
                    created_time = po.created_at
                else:
                    created_time = po.created_at.astimezone(ZoneInfo('Asia/Shanghai'))

                if created_time.year != 2025:
                    continue

                # 检查审批状态是否为批准状态
                if po.status != 'approved':
                    continue

                # 获取关联的项目
                if not po.project:
                    continue

                # 检查项目名称是否包含"测试"
                if '测试' in po.project.project_name:
                    continue

                # 计算零售价总和
                retail_total = 0.0
                for detail in po.pricing_details:
                    if detail.market_price and detail.quantity:
                        retail_total += (detail.market_price * detail.quantity)

                # 获取批价折扣和结算折扣
                pricing_discount_rate = po.pricing_total_discount_rate or 1.0
                settlement_discount_rate = po.settlement_total_discount_rate or 1.0

                # 准备数据
                po_dict = {
                    'id': po.id,
                    'po_number': po.order_number,
                    'project_name': po.project.project_name,
                    'retail_price_total': retail_total,
                    'pricing_discount_rate': pricing_discount_rate * 100,  # 转换为百分比
                    'pricing_amount': po.pricing_total_amount or 0.0,
                    'settlement_discount_rate': settlement_discount_rate * 100,  # 转换为百分比
                    'settlement_amount': po.settlement_total_amount or 0.0,
                    'project_type': po.project.project_type,
                    'current_stage': po.project.current_stage,
                    'status': po.status,
                    'created_at': po.created_at,
                }

                filtered_pos.append(po_dict)

            print(f"✓ 过滤后符合条件的批价单: {len(filtered_pos)} 个")
            print(f"  条件: 2025年创建 + 审批通过 + 项目名称无'测试'")

            all_results[username] = {
                'found': True,
                'user_id': user.id,
                'real_name': user.real_name or user.username,
                'pricing_orders': filtered_pos
            }

        return all_results


def display_comparison_table(all_results):
    """显示所有四个销售人员的对比汇总表"""

    print("\n\n" + "="*150)
    print("汇总对比表 - 四个销售人员的批价单数据")
    print("="*150)

    print(f"\n{'销售人员':<15} {'批价单数':<8} {'零售价总和':<18} {'批价折扣':<12} {'批价单金额':<18} {'结算折扣':<12} {'结算单金额':<18}")
    print("-"*150)

    for username in ['lihuawei', 'gxh', 'fanjing', 'yangjj']:
        result = all_results[username]
        if not result['found']:
            print(f"{username:<15} {'N/A':<8} {'用户不存在':<18}")
            continue

        pos = result['pricing_orders']
        if not pos:
            print(f"{username:<15} {0:<8} {0:<18} {'N/A':<12} {0:<18} {'N/A':<12} {0:<18}")
            continue

        # 计算总数
        po_count = len(pos)
        total_retail = sum(p['retail_price_total'] for p in pos)
        total_pricing = sum(p['pricing_amount'] for p in pos)
        total_settlement = sum(p['settlement_amount'] for p in pos)

        # 平均折扣率
        avg_pricing_discount = sum(p['pricing_discount_rate'] for p in pos) / len(pos) if pos else 0
        avg_settlement_discount = sum(p['settlement_discount_rate'] for p in pos) / len(pos) if pos else 0

        print(f"{username:<15} {po_count:<8} ¥{total_retail:>16,.0f} {avg_pricing_discount:>10.1f}% ¥{total_pricing:>16,.0f} {avg_settlement_discount:>10.1f}% ¥{total_settlement:>16,.0f}")

    print("="*150)


def display_detailed_list(all_results):
    """显示详细列表"""

    print("\n\n" + "="*150)
    print("详细明细列表")
    print("="*150)

    for username in ['lihuawei', 'gxh', 'fanjing', 'yangjj']:
        result = all_results[username]
        if not result['found']:
            print(f"\n❌ 用户 {username} 不存在")
            continue

        pos = result['pricing_orders']
        if not pos:
            print(f"\n{username} ({result['real_name']}): 没有符合条件的批价单")
            continue

        print(f"\n\n{'-'*150}")
        print(f"{username} ({result['real_name']}) - 共 {len(pos)} 个批价单")
        print(f"{'-'*150}")

        for idx, po in enumerate(pos, 1):
            print(f"\n[{idx}] 批价单号: {po['po_number']}")
            print(f"    项目名称: {po['project_name']}")
            print(f"    创建时间: {po['created_at'].strftime('%Y-%m-%d %H:%M:%S') if po['created_at'] else 'N/A'}")
            print(f"    状态: {po['status']}")
            print(f"    ---")
            print(f"    零售价总和:   ¥{po['retail_price_total']:>15,.2f}")
            print(f"    批价折扣率:   {po['pricing_discount_rate']:>15.1f}%")
            print(f"    批价单金额:   ¥{po['pricing_amount']:>15,.2f}")
            print(f"    ---")
            print(f"    结算折扣率:   {po['settlement_discount_rate']:>15.1f}%")
            print(f"    结算单金额:   ¥{po['settlement_amount']:>15,.2f}")


def main():
    print("="*150)
    print("查询云端SP8D系统 - 批价单数据对比分析")
    print("="*150)

    # 查询数据
    all_results = query_sales_manager_pricing_orders()

    # 显示汇总表
    display_comparison_table(all_results)

    # 显示详细列表
    display_detailed_list(all_results)

    print(f"\n\n✓ 查询完成")


if __name__ == '__main__':
    main()
