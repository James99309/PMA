#!/usr/bin/env python3
"""
检查xuhao用户的审批问题
分析为什么看不到需要他审批的记录

Created: 2025-06-27
Author: Assistant
Purpose: 诊断xuhao用户的审批问题
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from flask import Flask
from app import create_app, db
from app.models.user import User, Affiliation
from app.models.approval import ApprovalInstance, ApprovalStep, ApprovalStatus
from app.helpers.approval_helpers import get_user_pending_approvals, get_pending_approval_count
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_xuhao_user():
    """检查xuhao用户的基本信息"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # 查找xuhao用户
            xuhao = User.query.filter_by(username='xuhao').first()
            if not xuhao:
                print("❌ 未找到xuhao用户")
                return None
            
            print("=== xuhao用户基本信息 ===")
            print(f"用户ID: {xuhao.id}")
            print(f"用户名: {xuhao.username}")
            print(f"真实姓名: {xuhao.real_name}")
            print(f"角色: {xuhao.role}")
            print(f"部门: {xuhao.department}")
            print(f"公司: {xuhao.company_name}")
            print(f"是否激活: {xuhao.is_active}")
            
            return xuhao
            
        except Exception as e:
            logger.error(f"检查xuhao用户信息时发生错误: {str(e)}")
            return None

def check_pending_approvals_for_xuhao(xuhao):
    """检查xuhao的待审批记录"""
    
    try:
        print("\n=== xuhao待审批记录分析 ===")
        
        # 使用approval_helpers模块获取待审批
        pending_approvals = get_user_pending_approvals(xuhao)
        pending_count = get_pending_approval_count(xuhao)
        
        print(f"get_user_pending_approvals返回数量: {pending_approvals.count()}")
        print(f"get_pending_approval_count返回数量: {pending_count}")
        
        # 分析前5个待审批记录
        sample_approvals = pending_approvals.limit(5).all()
        print(f"\n前5个待审批记录详情:")
        
        for approval in sample_approvals:
            print(f"  审批ID: {approval.id} (APV-{approval.id:04d})")
            print(f"    对象类型: {approval.object_type}")
            print(f"    对象ID: {approval.object_id}")
            print(f"    状态: {approval.status}")
            print(f"    当前步骤: {approval.current_step}")
            print(f"    创建时间: {approval.created_at}")
            
            # 获取当前步骤信息
            current_step_info = approval.get_current_step_info()
            if current_step_info:
                if isinstance(current_step_info, dict):
                    print(f"    当前审批人ID(快照): {current_step_info.get('approver_user_id')}")
                else:
                    print(f"    当前审批人ID(模板): {current_step_info.approver_user_id}")
            print()
        
        return pending_count
        
    except Exception as e:
        logger.error(f"检查xuhao待审批记录时发生错误: {str(e)}")
        return 0

def check_all_pending_approvals_with_xuhao_as_approver():
    """检查所有应该由xuhao审批的记录"""
    
    try:
        print("\n=== 查找所有应该由xuhao审批的记录 ===")
        
        # 先找到xuhao的用户ID
        xuhao = User.query.filter_by(username='xuhao').first()
        if not xuhao:
            print("❌ 未找到xuhao用户")
            return
        
        xuhao_id = xuhao.id
        print(f"xuhao用户ID: {xuhao_id}")
        
        # 查找所有状态为pending的审批实例
        pending_instances = ApprovalInstance.query.filter_by(status=ApprovalStatus.PENDING).all()
        print(f"总共的待审批实例数量: {len(pending_instances)}")
        
        xuhao_should_approve = []
        
        for instance in pending_instances:
            current_step_info = instance.get_current_step_info()
            if current_step_info:
                current_approver_id = None
                
                if isinstance(current_step_info, dict):  # 快照数据
                    current_approver_id = current_step_info.get('approver_user_id')
                else:  # 模板步骤对象
                    current_approver_id = current_step_info.approver_user_id
                
                if current_approver_id == xuhao_id:
                    xuhao_should_approve.append(instance)
        
        print(f"应该由xuhao审批的实例数量: {len(xuhao_should_approve)}")
        
        if xuhao_should_approve:
            print("\n应该由xuhao审批的记录:")
            for instance in xuhao_should_approve[:10]:  # 显示前10个
                print(f"  审批ID: {instance.id} (APV-{instance.id:04d})")
                print(f"    对象类型: {instance.object_type}")
                print(f"    对象ID: {instance.object_id}")
                print(f"    状态: {instance.status}")
                print(f"    当前步骤: {instance.current_step}")
                print(f"    创建时间: {instance.created_at}")
                print()
        
        return len(xuhao_should_approve)
        
    except Exception as e:
        logger.error(f"查找所有应该由xuhao审批的记录时发生错误: {str(e)}")
        return 0

def check_xuhao_role_permissions():
    """检查xuhao角色的审批权限"""
    
    try:
        print("\n=== xuhao角色权限分析 ===")
        
        xuhao = User.query.filter_by(username='xuhao').first()
        if not xuhao:
            return
        
        user_role = xuhao.role.strip() if xuhao.role else ''
        print(f"xuhao角色 (去除空格): '{user_role}'")
        
        # 检查是否有特殊角色处理
        special_roles = ['admin', 'service', 'service_manager', 'channel_manager', 'sales_director', 'business_admin']
        
        if user_role in special_roles:
            print(f"✅ xuhao匹配特殊角色: {user_role}")
            print("根据角色可能有特殊的审批权限处理")
        else:
            print(f"❓ xuhao角色'{user_role}'可能没有特殊处理")
        
        # 检查归属关系
        affiliations = Affiliation.query.filter_by(viewer_id=xuhao.id).all()
        print(f"\nxuhao可以查看的用户数量(归属关系): {len(affiliations)}")
        
        for affiliation in affiliations:
            owner = User.query.get(affiliation.owner_id)
            if owner:
                print(f"  可查看用户: {owner.username} ({owner.real_name}) - 部门: {owner.department}")
        
    except Exception as e:
        logger.error(f"检查xuhao角色权限时发生错误: {str(e)}")

def check_approval_helper_logic_for_xuhao():
    """检查approval_helpers逻辑对xuhao的处理"""
    
    try:
        print("\n=== 测试approval_helpers逻辑 ===")
        
        xuhao = User.query.filter_by(username='xuhao').first()
        if not xuhao:
            return
        
        # 增加详细日志
        import logging
        logging.getLogger('app.helpers.approval_helpers').setLevel(logging.DEBUG)
        
        # 测试get_user_pending_approvals函数
        print("调用get_user_pending_approvals...")
        pending_approvals = get_user_pending_approvals(xuhao)
        actual_count = pending_approvals.count()
        
        print(f"实际返回的待审批数量: {actual_count}")
        
        # 测试get_pending_approval_count函数
        print("调用get_pending_approval_count...")
        count_result = get_pending_approval_count(xuhao)
        
        print(f"get_pending_approval_count返回: {count_result}")
        
        # 检查一致性
        if actual_count == count_result:
            print("✅ 两个函数结果一致")
        else:
            print(f"❌ 两个函数结果不一致: {actual_count} vs {count_result}")
        
    except Exception as e:
        logger.error(f"测试approval_helpers逻辑时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("=== xuhao用户审批问题诊断工具 ===")
    print()
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. 检查用户基本信息
            xuhao = check_xuhao_user()
            if not xuhao:
                print("❌ 无法获取xuhao用户信息，退出")
                return
            
            # 2. 检查待审批记录
            pending_count_helper = check_pending_approvals_for_xuhao(xuhao)
            
            # 3. 检查所有应该由xuhao审批的记录
            should_approve_count = check_all_pending_approvals_with_xuhao_as_approver()
            
            # 4. 检查角色权限
            check_xuhao_role_permissions()
            
            # 5. 测试approval_helpers逻辑
            check_approval_helper_logic_for_xuhao()
            
            # 6. 总结分析
            print("\n=== 诊断总结 ===")
            print(f"approval_helpers返回的待审批数量: {pending_count_helper}")
            print(f"实际应该审批的数量: {should_approve_count}")
            
            if pending_count_helper != should_approve_count:
                print("⚠️ 发现问题：approval_helpers返回的数量与实际应该审批的数量不匹配！")
                print("可能的原因：")
                print("1. approval_helpers中的权限过滤逻辑有问题")
                print("2. 模板快照处理逻辑有问题")
                print("3. 角色权限检查有问题")
            else:
                print("✅ approval_helpers逻辑看起来正常")
            
        except Exception as e:
            logger.error(f"诊断过程发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main() 