#!/usr/bin/env python3

from app import create_app, db
from app.models.pricing_order import PricingOrder, PricingOrderApprovalRecord
from app.models.user import User

def debug_approval_permission():
    app = create_app()
    with app.app_context():
        # 查找PO202506-007批价单
        po = PricingOrder.query.filter_by(order_number='PO202506-007').first()
        if not po:
            print('未找到PO202506-007批价单')
            return
        
        print(f'批价单: {po.order_number}')
        print(f'状态: {po.status}')
        print(f'当前审批步骤: {po.current_approval_step}')
        
        # 获取当前审批记录
        current_record = PricingOrderApprovalRecord.query.filter_by(
            pricing_order_id=po.id,
            step_order=po.current_approval_step
        ).first()
        
        if current_record:
            print(f'\n当前审批步骤信息:')
            print(f'  步骤名称: {current_record.step_name}')
            print(f'  审批人ID: {current_record.approver_id}')
            print(f'  审批人用户名: {current_record.approver.username}')
            print(f'  审批人姓名: {current_record.approver.real_name or "未设置"}')
            print(f'  审批状态: {current_record.action or "待审批"}')
        
        # 列出所有用户，看看谁可能在尝试审批
        print(f'\n系统中的用户列表:')
        users = User.query.all()
        for user in users:
            print(f'  ID: {user.id}, 用户名: {user.username}, 姓名: {user.real_name or "未设置"}, 角色: {user.role}')
        
        # 检查是否有其他管理员用户
        print(f'\n管理员用户:')
        admin_users = User.query.filter_by(role='admin').all()
        for user in admin_users:
            print(f'  ID: {user.id}, 用户名: {user.username}, 姓名: {user.real_name or "未设置"}')
        
        # 检查渠道经理角色的用户
        print(f'\n渠道经理用户:')
        channel_managers = User.query.filter_by(role='channel_manager').all()
        for user in channel_managers:
            print(f'  ID: {user.id}, 用户名: {user.username}, 姓名: {user.real_name or "未设置"}')

if __name__ == '__main__':
    debug_approval_permission() 