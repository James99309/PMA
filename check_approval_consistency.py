#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审批中心数据一致性检查工具
检查审批列表中是否存在已删除业务对象的孤立审批实例
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.approval import ApprovalInstance, ApprovalStatus
from app.models.project import Project
from app.models.quotation import Quotation
from app.models.customer import Company
from sqlalchemy import text

app = create_app()

def check_orphaned_approvals():
    """检查孤立的审批实例"""
    print("🔍 检查审批中心数据一致性...")
    
    with app.app_context():
        orphaned_instances = []
        
        # 检查项目审批实例
        print("\n1. 检查项目审批实例:")
        project_approvals = ApprovalInstance.query.filter_by(object_type='project').all()
        print(f"   找到 {len(project_approvals)} 个项目审批实例")
        
        for approval in project_approvals:
            project = Project.query.get(approval.object_id)
            if not project:
                orphaned_instances.append({
                    'type': 'project',
                    'approval_id': approval.id,
                    'approval_code': f"APV-{approval.id:04d}",
                    'object_id': approval.object_id,
                    'status': approval.status.value if hasattr(approval.status, 'value') else str(approval.status),
                    'creator': approval.creator.username if approval.creator else 'Unknown',
                    'started_at': approval.started_at.strftime('%Y-%m-%d %H:%M') if approval.started_at else 'Unknown'
                })
                print(f"   ❌ 孤立审批: APV-{approval.id:04d} -> 项目ID {approval.object_id} (不存在)")
        
        # 检查报价单审批实例
        print("\n2. 检查报价单审批实例:")
        quotation_approvals = ApprovalInstance.query.filter_by(object_type='quotation').all()
        print(f"   找到 {len(quotation_approvals)} 个报价单审批实例")
        
        for approval in quotation_approvals:
            quotation = Quotation.query.get(approval.object_id)
            if not quotation:
                orphaned_instances.append({
                    'type': 'quotation',
                    'approval_id': approval.id,
                    'approval_code': f"APV-{approval.id:04d}",
                    'object_id': approval.object_id,
                    'status': approval.status.value if hasattr(approval.status, 'value') else str(approval.status),
                    'creator': approval.creator.username if approval.creator else 'Unknown',
                    'started_at': approval.started_at.strftime('%Y-%m-%d %H:%M') if approval.started_at else 'Unknown'
                })
                print(f"   ❌ 孤立审批: APV-{approval.id:04d} -> 报价单ID {approval.object_id} (不存在)")
        
        # 检查客户审批实例
        print("\n3. 检查客户审批实例:")
        customer_approvals = ApprovalInstance.query.filter_by(object_type='customer').all()
        print(f"   找到 {len(customer_approvals)} 个客户审批实例")
        
        for approval in customer_approvals:
            customer = Company.query.get(approval.object_id)
            if not customer:
                orphaned_instances.append({
                    'type': 'customer',
                    'approval_id': approval.id,
                    'approval_code': f"APV-{approval.id:04d}",
                    'object_id': approval.object_id,
                    'status': approval.status.value if hasattr(approval.status, 'value') else str(approval.status),
                    'creator': approval.creator.username if approval.creator else 'Unknown',
                    'started_at': approval.started_at.strftime('%Y-%m-%d %H:%M') if approval.started_at else 'Unknown'
                })
                print(f"   ❌ 孤立审批: APV-{approval.id:04d} -> 客户ID {approval.object_id} (不存在)")
        
        # 汇总结果
        print(f"\n📊 检查结果汇总:")
        print(f"   总共发现 {len(orphaned_instances)} 个孤立的审批实例")
        
        if orphaned_instances:
            print("\n📋 孤立审批实例详情:")
            print("编号\t\t业务类型\t业务ID\t状态\t\t发起人\t\t创建时间")
            print("-" * 80)
            for instance in orphaned_instances:
                print(f"{instance['approval_code']}\t{instance['type']}\t\t{instance['object_id']}\t{instance['status']}\t\t{instance['creator']}\t{instance['started_at']}")
        else:
            print("   ✅ 没有发现孤立的审批实例，数据一致性良好！")
        
        return orphaned_instances

def get_approval_center_stats():
    """获取审批中心统计信息"""
    print("\n📈 审批中心统计信息:")
    
    with app.app_context():
        # 各类型审批统计
        project_count = ApprovalInstance.query.filter_by(object_type='project').count()
        quotation_count = ApprovalInstance.query.filter_by(object_type='quotation').count()
        customer_count = ApprovalInstance.query.filter_by(object_type='customer').count()
        
        print(f"   项目审批实例: {project_count}")
        print(f"   报价单审批实例: {quotation_count}")
        print(f"   客户审批实例: {customer_count}")
        print(f"   总计: {project_count + quotation_count + customer_count}")
        
        # 状态统计
        pending_count = ApprovalInstance.query.filter_by(status=ApprovalStatus.PENDING).count()
        approved_count = ApprovalInstance.query.filter_by(status=ApprovalStatus.APPROVED).count()
        rejected_count = ApprovalInstance.query.filter_by(status=ApprovalStatus.REJECTED).count()
        
        print(f"\n   审批中: {pending_count}")
        print(f"   已通过: {approved_count}")
        print(f"   已拒绝: {rejected_count}")

def clean_orphaned_approvals(orphaned_instances, auto_confirm=False):
    """清理孤立的审批实例"""
    if not orphaned_instances:
        print("\n✅ 没有需要清理的孤立审批实例")
        return
    
    print(f"\n🧹 发现 {len(orphaned_instances)} 个孤立的审批实例需要清理")
    
    if not auto_confirm:
        confirm = input("是否要删除这些孤立的审批实例？(y/N): ").strip().lower()
        if confirm != 'y':
            print("取消清理操作")
            return
    
    with app.app_context():
        try:
            deleted_count = 0
            for instance in orphaned_instances:
                approval = ApprovalInstance.query.get(instance['approval_id'])
                if approval:
                    db.session.delete(approval)
                    deleted_count += 1
                    print(f"   ✅ 删除孤立审批实例: {instance['approval_code']}")
            
            db.session.commit()
            print(f"\n🎉 成功清理 {deleted_count} 个孤立的审批实例！")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 清理失败: {str(e)}")

def check_specific_approval(approval_code):
    """检查特定审批实例"""
    if not approval_code.startswith('APV-'):
        print("请输入正确的审批编号格式 (如: APV-0066)")
        return
    
    try:
        approval_id = int(approval_code.split('-')[1])
    except (IndexError, ValueError):
        print("审批编号格式错误")
        return
    
    print(f"🔍 检查审批实例: {approval_code}")
    
    with app.app_context():
        approval = ApprovalInstance.query.get(approval_id)
        if not approval:
            print(f"   ❌ 审批实例 {approval_code} 不存在")
            return
        
        print(f"   审批ID: {approval.id}")
        print(f"   业务类型: {approval.object_type}")
        print(f"   业务对象ID: {approval.object_id}")
        print(f"   状态: {approval.status}")
        print(f"   发起人: {approval.creator.username if approval.creator else 'Unknown'}")
        print(f"   发起时间: {approval.started_at}")
        
        # 检查对应的业务对象是否存在
        business_object = None
        if approval.object_type == 'project':
            business_object = Project.query.get(approval.object_id)
            object_name = business_object.project_name if business_object else None
        elif approval.object_type == 'quotation':
            business_object = Quotation.query.get(approval.object_id)
            object_name = business_object.quotation_number if business_object else None
        elif approval.object_type == 'customer':
            business_object = Company.query.get(approval.object_id)
            object_name = business_object.company_name if business_object else None
        else:
            object_name = None
        
        if business_object:
            print(f"   ✅ 关联业务对象存在: {object_name}")
        else:
            print(f"   ❌ 关联业务对象不存在！这是一个孤立的审批实例")
            
            # 询问是否删除
            confirm = input(f"是否要删除这个孤立的审批实例 {approval_code}？(y/N): ").strip().lower()
            if confirm == 'y':
                try:
                    db.session.delete(approval)
                    db.session.commit()
                    print(f"   ✅ 已删除孤立审批实例 {approval_code}")
                except Exception as e:
                    db.session.rollback()
                    print(f"   ❌ 删除失败: {str(e)}")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--check':
            # 仅检查，不清理
            orphaned = check_orphaned_approvals()
            get_approval_center_stats()
        elif sys.argv[1] == '--clean':
            # 检查并清理
            orphaned = check_orphaned_approvals()
            get_approval_center_stats()
            clean_orphaned_approvals(orphaned)
        elif sys.argv[1] == '--auto-clean':
            # 自动清理
            orphaned = check_orphaned_approvals()
            clean_orphaned_approvals(orphaned, auto_confirm=True)
        elif sys.argv[1].startswith('APV-'):
            # 检查特定审批实例
            check_specific_approval(sys.argv[1])
        else:
            print("用法:")
            print("  python check_approval_consistency.py --check        # 仅检查")
            print("  python check_approval_consistency.py --clean        # 检查并清理")
            print("  python check_approval_consistency.py --auto-clean   # 自动清理")
            print("  python check_approval_consistency.py APV-0066       # 检查特定审批")
    else:
        # 默认只检查
        orphaned = check_orphaned_approvals()
        get_approval_center_stats()

if __name__ == "__main__":
    main() 