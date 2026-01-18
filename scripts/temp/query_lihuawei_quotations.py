#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询sp8d（PMA）数据库中李华伟的批价单
条件：2025年创建、审批通过、项目名称无"测试"
"""
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

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
from app.models.user import User
from app.models.quotation import Quotation, QuotationApprovalStatus
from app.models.project import Project
from sqlalchemy import and_, or_, extract, text

def query_lihuawei_quotations():
    """查询李华伟的所有符合条件的批价单"""

    app = create_app()
    with app.app_context():
        # 1. 先找到李华伟这个用户
        lihuawei = User.query.filter(User.username == 'lihuawei').first()
        if not lihuawei:
            print("❌ 未找到用户'lihuawei'")
            return []

        print(f"✓ 找到用户：{lihuawei.real_name or lihuawei.username} (ID: {lihuawei.id})")

        # 2. 查询该用户所有的批价单
        quotations = Quotation.query.filter(
            Quotation.owner_id == lihuawei.id
        ).all()

        print(f"\n✓ 用户'李华伟'共有 {len(quotations)} 个批价单")

        # 3. 过滤条件应用
        filtered_quotations = []

        for q in quotations:
            # 检查创建时间是否在2025年
            if q.created_at is None:
                continue

            # 转换为本地时区
            if q.created_at.tzinfo is None:
                created_time = q.created_at
            else:
                created_time = q.created_at.astimezone(ZoneInfo('Asia/Shanghai'))

            if created_time.year != 2025:
                continue

            # 检查审批状态是否为通过状态（以_approved结尾）
            if not q.approval_status or not q.approval_status.endswith('_approved'):
                continue

            # 获取关联的项目
            if not q.project:
                continue

            # 检查项目名称是否包含"测试"
            if '测试' in q.project.project_name:
                continue

            # 准备数据副本以支持Session分离后的访问
            q_dict = {
                'id': q.id,
                'quotation_number': q.quotation_number,
                'project_name': q.project.project_name,
                'amount': q.amount,
                'project_stage': q.project_stage,
                'project_type': q.project_type,
                'approval_status': q.approval_status,
                'created_at': q.created_at,
                'updated_at': q.updated_at,
                'details': [(d.id, getattr(d, 'product_name', 'N/A')) for d in q.details]
            }

            # 通过所有过滤条件
            filtered_quotations.append(q_dict)

        print(f"\n✓ 过滤后符合条件的批价单: {len(filtered_quotations)} 个")
        print("  条件: 2025年创建 + 审批通过 + 项目名称无'测试'")

        return filtered_quotations


def display_quotations(quotations):
    """显示批价单详细信息"""

    if not quotations:
        print("\n❌ 没有符合条件的批价单")
        return

    print("\n" + "=" * 150)
    print("李华伟的批价单明细（2025年创建、审批通过、项目名称无'测试'）")
    print("=" * 150)

    # 表头
    headers = [
        "序号",
        "批价单号",
        "项目名称",
        "金额(元)",
        "项目阶段",
        "项目类型",
        "审批状态",
        "创建时间",
        "更新时间"
    ]

    print(f"\n{'序号':<4} {'批价单号':<12} {'项目名称':<35} {'金额':<15} {'项目阶段':<12} {'项目类型':<12} {'审批状态':<20} {'创建时间':<12} {'更新时间':<12}")
    print("-" * 150)

    total_amount = 0

    for idx, q in enumerate(quotations, 1):
        # 格式化时间
        created_at = q['created_at'].strftime('%Y-%m-%d') if q['created_at'] else 'N/A'
        updated_at = q['updated_at'].strftime('%Y-%m-%d') if q['updated_at'] else 'N/A'

        # 金额
        amount = q['amount'] if q['amount'] else 0
        total_amount += amount

        # 获取状态标签（中文）
        approval_label = get_approval_status_label(q['approval_status'])

        project_name = q['project_name'] if q['project_name'] else 'N/A'
        project_stage = q['project_stage'] if q['project_stage'] else 'N/A'
        project_type = q['project_type'] if q['project_type'] else 'N/A'

        # 截断长项目名
        if len(project_name) > 35:
            project_name = project_name[:32] + '...'

        print(f"{idx:<4} {q['quotation_number']:<12} {project_name:<35} ¥{amount:>13,.2f} {project_stage:<12} {project_type:<12} {approval_label:<20} {created_at:<12} {updated_at:<12}")

    print("-" * 150)
    print(f"{'合计':<52} {'¥':>1}{total_amount:>13,.2f}")
    print("=" * 150)

    return total_amount


def display_detailed_list(quotations):
    """显示详细列表"""

    print("\n\n" + "=" * 100)
    print("详细列表")
    print("=" * 100)

    for idx, q in enumerate(quotations, 1):
        print(f"\n[{idx}] 批价单号: {q['quotation_number']}")
        print(f"    项目名称: {q['project_name']}")
        print(f"    金额: ¥{q['amount']:,.2f}" if q['amount'] else "    金额: N/A")
        print(f"    项目阶段: {q['project_stage']}")
        print(f"    项目类型: {q['project_type']}")
        print(f"    审批状态: {get_approval_status_label(q['approval_status'])}")
        print(f"    创建时间: {q['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    更新时间: {q['updated_at'].strftime('%Y-%m-%d %H:%M:%S')}")

        # 显示批价单明细
        if q['details']:
            print(f"    明细数量: {len(q['details'])} 条")
            for detail_idx, (detail_id, product_name) in enumerate(q['details'], 1):
                print(f"      [{detail_idx}] {product_name}")


def get_approval_status_label(status):
    """获取审批状态的中文标签"""
    status_map = {
        'pending': '待审核',
        'discover_approved': '发现阶段审核通过',
        'embed_approved': '植入阶段审核通过',
        'pre_tender_approved': '招标前审核通过',
        'tendering_approved': '招标中审核通过',
        'awarded_approved': '中标审核通过',
        'quoted_approved': '批价审核通过',
        'signed_approved': '签约审核通过',
        'rejected': '审核被驳回'
    }
    return status_map.get(status, status)


def main():
    print("=" * 100)
    print("查询sp8d(PMA)数据库中李华伟的批价单")
    print("=" * 100)

    # 查询
    quotations = query_lihuawei_quotations()

    # 显示摘要表格
    total_amount = display_quotations(quotations)

    # 显示详细列表
    if quotations:
        display_detailed_list(quotations)

    print(f"\n\n✓ 查询完成")
    print(f"  符合条件的批价单数: {len(quotations)}")
    if total_amount:
        print(f"  总金额: ¥{total_amount:,.2f}")


if __name__ == '__main__':
    main()
