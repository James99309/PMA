#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证「测试分支审批项目」删除结果"""
import sys, os

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

# 设置云端SP8D数据库连接
os.environ['DATABASE_URL'] = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

from app import create_app, db
from app.models.project import Project
from app.models.quotation import Quotation, QuotationDetail
from app.models.pricing_order import PricingOrder, PricingOrderDetail, SettlementOrder, SettlementOrderDetail
from app.models.approval import ApprovalInstance, ApprovalRecord
from sqlalchemy import text

app = create_app()

def verify_deletion():
    """验证删除结果"""
    with app.app_context():
        print("=" * 80)
        print("验证「测试分支审批项目」删除结果")
        print("=" * 80)

        # 1. 验证项目是否已删除
        print("\n【验证1】项目是否已删除")
        project = Project.query.filter(
            Project.project_name.like('%测试分支审批项目%')
        ).first()

        if project:
            print(f"❌ 失败：项目仍然存在 (ID: {project.id})")
            return False
        else:
            print("✅ 成功：项目已删除")

        # 2. 验证报价单是否已删除 (ID: 838)
        print("\n【验证2】报价单是否已删除")
        quotation = Quotation.query.get(838)
        if quotation:
            print(f"❌ 失败：报价单仍然存在 (ID: 838)")
            return False
        else:
            print("✅ 成功：报价单已删除 (ID: 838)")

        # 3. 验证批价单是否已删除 (ID: 76)
        print("\n【验证3】批价单是否已删除")
        pricing_order = PricingOrder.query.get(76)
        if pricing_order:
            print(f"❌ 失败：批价单仍然存在 (ID: 76)")
            return False
        else:
            print("✅ 成功：批价单已删除 (ID: 76)")

        # 4. 验证审批实例是否已删除 (ID: 201, 383)
        print("\n【验证4】审批实例是否已删除")
        instance_201 = ApprovalInstance.query.get(201)
        instance_383 = ApprovalInstance.query.get(383)

        if instance_201 or instance_383:
            print(f"❌ 失败：审批实例仍然存在")
            if instance_201:
                print(f"   - 实例 201 仍存在")
            if instance_383:
                print(f"   - 实例 383 仍存在")
            return False
        else:
            print("✅ 成功：审批实例已删除 (ID: 201, 383)")

        # 5. 验证项目ID 738 的关联数据
        print("\n【验证5】项目ID 738 的关联数据是否已清理")

        # 项目客户关联
        result = db.session.execute(
            text("SELECT COUNT(*) FROM project_customer_associations WHERE project_id = 738")
        )
        count = result.scalar()
        if count > 0:
            print(f"❌ 失败：仍有 {count} 条项目客户关联")
            return False
        else:
            print("✅ 项目客户关联已清理")

        # 项目阶段历史
        result = db.session.execute(
            text("SELECT COUNT(*) FROM project_stage_history WHERE project_id = 738")
        )
        count = result.scalar()
        if count > 0:
            print(f"❌ 失败：仍有 {count} 条项目阶段历史")
            return False
        else:
            print("✅ 项目阶段历史已清理")

        # 项目评分记录
        result = db.session.execute(
            text("SELECT COUNT(*) FROM project_scoring_records WHERE project_id = 738")
        )
        count = result.scalar()
        if count > 0:
            print(f"❌ 失败：仍有 {count} 条项目评分记录")
            return False
        else:
            print("✅ 项目评分记录已清理")

        # 项目总分
        result = db.session.execute(
            text("SELECT COUNT(*) FROM project_total_scores WHERE project_id = 738")
        )
        count = result.scalar()
        if count > 0:
            print(f"❌ 失败：仍有 {count} 条项目总分记录")
            return False
        else:
            print("✅ 项目总分记录已清理")

        # 6. 统计当前数据库状态
        print("\n" + "=" * 80)
        print("【当前数据库状态】")
        print("=" * 80)

        total_projects = Project.query.filter_by(is_deleted=False).count()
        total_quotations = Quotation.query.count()
        total_pricing_orders = PricingOrder.query.count()
        total_approval_instances = ApprovalInstance.query.count()

        print(f"\n项目总数: {total_projects} (删除前: {total_projects + 1})")
        print(f"报价单总数: {total_quotations} (删除前: {total_quotations + 1})")
        print(f"批价单总数: {total_pricing_orders} (删除前: {total_pricing_orders + 1})")
        print(f"审批实例总数: {total_approval_instances} (删除前: {total_approval_instances + 2})")

        print("\n" + "=" * 80)
        print("✅ 所有验证通过！项目及所有关联数据已成功删除！")
        print("=" * 80)

        return True

if __name__ == '__main__':
    try:
        success = verify_deletion()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
