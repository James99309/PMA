#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""删除「测试项目测试分支审批」项目及所有关联数据"""
import sys, os
import argparse
from datetime import datetime

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

def confirm_deletion(auto_confirm=False):
    """二次确认机制"""
    if auto_confirm:
        print("\n⚠️  自动确认模式：跳过交互式确认")
        return True

    print("\n" + "=" * 80)
    print("⚠️  危险操作警告")
    print("=" * 80)
    print("\n此操作将永久删除「测试分支审批项目」项目及其所有关联数据！")
    print("删除后无法恢复（除非从备份恢复）")
    print("\n请确认：")
    print("  1. ✅ 已执行数据库备份")
    print("  2. ✅ 已仔细核对待删除的数据范围")
    print("  3. ✅ 确认项目确实已完成使命")

    response = input("\n是否继续删除？请输入项目名称「测试分支审批项目」以确认: ")

    if response.strip() != "测试分支审批项目":
        print("\n❌ 确认失败，操作已取消")
        return False

    final_confirm = input("\n最后确认：输入 YES 继续删除，输入其他任何内容取消: ")

    if final_confirm.strip().upper() != "YES":
        print("\n❌ 操作已取消")
        return False

    return True

def delete_project_data(auto_confirm=False):
    """删除项目及所有关联数据（在事务中执行）"""
    with app.app_context():
        print("=" * 80)
        print("删除「测试项目测试分支审批」项目数据")
        print("=" * 80)
        print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 查找项目
        print("\n【步骤1】查找目标项目")
        project = Project.query.filter(
            Project.project_name.like('%测试分支审批项目%')
        ).first()

        if not project:
            print("❌ 未找到「测试分支审批项目」项目")
            return False

        print(f"✅ 找到项目: {project.project_name} (ID: {project.id})")
        project_id = project.id

        # 二次确认
        if not confirm_deletion(auto_confirm):
            return False

        print("\n" + "=" * 80)
        print("【步骤2】开始删除操作（事务模式）")
        print("=" * 80)

        deletion_log = []

        try:
            # 开始事务（使用嵌套事务以便测试时回滚）

            # 第1层：删除明细和记录（按外键依赖顺序）
            print("\n📝 第1层：删除明细和记录...")

            # 1.1 删除报价单明细
            quotations = Quotation.query.filter_by(project_id=project_id).all()
            quotation_ids = [q.id for q in quotations]

            if quotation_ids:
                deleted = QuotationDetail.query.filter(
                    QuotationDetail.quotation_id.in_(quotation_ids)
                ).delete(synchronize_session=False)
                deletion_log.append(f"报价单明细: {deleted} 条")
                print(f"  ✅ 删除报价单明细: {deleted} 条")

            # 1.2 获取批价单和结算单ID
            pricing_orders = PricingOrder.query.filter_by(project_id=project_id).all()
            pricing_order_ids = [po.id for po in pricing_orders]

            if pricing_order_ids:
                # 获取结算单
                settlement_orders = SettlementOrder.query.filter(
                    SettlementOrder.pricing_order_id.in_(pricing_order_ids)
                ).all()
                settlement_order_ids = [so.id for so in settlement_orders]

                # 1.3 先删除结算单明细（因为它引用批价单明细）
                if settlement_order_ids:
                    deleted = SettlementOrderDetail.query.filter(
                        SettlementOrderDetail.settlement_order_id.in_(settlement_order_ids)
                    ).delete(synchronize_session=False)
                    deletion_log.append(f"结算单明细: {deleted} 条")
                    print(f"  ✅ 删除结算单明细: {deleted} 条")

                # 1.4 再删除批价单明细
                deleted = PricingOrderDetail.query.filter(
                    PricingOrderDetail.pricing_order_id.in_(pricing_order_ids)
                ).delete(synchronize_session=False)
                deletion_log.append(f"批价单明细: {deleted} 条")
                print(f"  ✅ 删除批价单明细: {deleted} 条")

            # 1.5 删除审批记录
            approval_instances = ApprovalInstance.query.filter(
                ApprovalInstance.object_type == 'project',
                ApprovalInstance.object_id == project_id
            ).all()
            instance_ids = [ai.id for ai in approval_instances]

            if instance_ids:
                deleted = ApprovalRecord.query.filter(
                    ApprovalRecord.instance_id.in_(instance_ids)
                ).delete(synchronize_session=False)
                deletion_log.append(f"审批记录: {deleted} 条")
                print(f"  ✅ 删除审批记录: {deleted} 条")

            # 1.6 删除项目客户关联
            result = db.session.execute(
                text("DELETE FROM project_customer_associations WHERE project_id = :pid"),
                {'pid': project_id}
            )
            deleted = result.rowcount
            deletion_log.append(f"项目客户关联: {deleted} 条")
            print(f"  ✅ 删除项目客户关联: {deleted} 条")

            # 1.7 删除项目阶段历史
            result = db.session.execute(
                text("DELETE FROM project_stage_history WHERE project_id = :pid"),
                {'pid': project_id}
            )
            deleted = result.rowcount
            deletion_log.append(f"项目阶段历史: {deleted} 条")
            print(f"  ✅ 删除项目阶段历史: {deleted} 条")

            # 1.8 删除项目评分记录
            result = db.session.execute(
                text("DELETE FROM project_scoring_records WHERE project_id = :pid"),
                {'pid': project_id}
            )
            deleted = result.rowcount
            deletion_log.append(f"项目评分记录: {deleted} 条")
            print(f"  ✅ 删除项目评分记录: {deleted} 条")

            # 1.9 删除项目总分
            result = db.session.execute(
                text("DELETE FROM project_total_scores WHERE project_id = :pid"),
                {'pid': project_id}
            )
            deleted = result.rowcount
            deletion_log.append(f"项目总分记录: {deleted} 条")
            print(f"  ✅ 删除项目总分记录: {deleted} 条")

            # 第2层：删除主表（按外键依赖顺序）
            print("\n📊 第2层：删除主表...")

            # 2.1 先删除结算单（它引用批价单）
            if pricing_order_ids:
                deleted = SettlementOrder.query.filter(
                    SettlementOrder.pricing_order_id.in_(pricing_order_ids)
                ).delete(synchronize_session=False)
                deletion_log.append(f"结算单: {deleted} 条")
                print(f"  ✅ 删除结算单: {deleted} 条")

                # 2.2 再删除批价单（它引用报价单）
                deleted = PricingOrder.query.filter(
                    PricingOrder.id.in_(pricing_order_ids)
                ).delete(synchronize_session=False)
                deletion_log.append(f"批价单: {deleted} 条")
                print(f"  ✅ 删除批价单: {deleted} 条")

            # 2.3 删除报价单（现在没有依赖了）
            if quotation_ids:
                deleted = Quotation.query.filter(
                    Quotation.id.in_(quotation_ids)
                ).delete(synchronize_session=False)
                deletion_log.append(f"报价单: {deleted} 条")
                print(f"  ✅ 删除报价单: {deleted} 条")

            # 2.4 删除审批实例
            if instance_ids:
                deleted = ApprovalInstance.query.filter(
                    ApprovalInstance.id.in_(instance_ids)
                ).delete(synchronize_session=False)
                deletion_log.append(f"审批实例: {deleted} 条")
                print(f"  ✅ 删除审批实例: {deleted} 条")

            # 第3层：删除项目
            print("\n🗂️  第3层：删除项目...")
            db.session.delete(project)
            deletion_log.append(f"项目: 1 条")
            print(f"  ✅ 删除项目: {project.project_name}")

            # 第4层：清理变更日志
            print("\n📋 第4层：清理变更日志...")
            result = db.session.execute(
                text("DELETE FROM change_logs WHERE table_name = 'projects' AND record_id = :pid"),
                {'pid': project_id}
            )
            deleted = result.rowcount
            deletion_log.append(f"变更日志: {deleted} 条")
            print(f"  ✅ 删除变更日志: {deleted} 条")

            # 提交事务
            print("\n💾 提交事务...")
            db.session.commit()

            # 删除成功
            print("\n" + "=" * 80)
            print("✅ 删除成功！")
            print("=" * 80)
            print("\n删除统计:")
            for log_entry in deletion_log:
                print(f"  - {log_entry}")

            total_deleted = sum(int(entry.split(': ')[1].split(' ')[0]) for entry in deletion_log)
            print(f"\n总计删除: {total_deleted} 条记录")
            print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)

            return True

        except Exception as e:
            # 回滚事务
            db.session.rollback()
            print("\n" + "=" * 80)
            print("❌ 删除失败，已回滚所有操作")
            print("=" * 80)
            print(f"\n错误信息: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='删除「测试分支审批项目」及所有关联数据')
    parser.add_argument('--confirm', action='store_true',
                       help='自动确认删除（跳过交互式确认）')
    args = parser.parse_args()

    print("\n🚀 准备删除「测试分支审批项目」项目")
    print("=" * 80)

    if args.confirm:
        print("⚠️  使用自动确认模式")

    try:
        success = delete_project_data(auto_confirm=args.confirm)
        if success:
            print("\n✅ 任务完成")
            sys.exit(0)
        else:
            print("\n❌ 任务失败或已取消")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
