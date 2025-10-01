#!/usr/bin/env python3

from app import create_app, db
from app.models.pricing_order import PricingOrder, PricingOrderApprovalRecord
from app.models.user import User

def check_pricing_order():
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
        print(f'创建人ID: {po.created_by}')
        
        # 查看审批记录
        records = PricingOrderApprovalRecord.query.filter_by(
            pricing_order_id=po.id
        ).order_by(PricingOrderApprovalRecord.step_order).all()
        
        print(f'\n审批记录 ({len(records)}条):')
        for record in records:
            approver = User.query.get(record.approver_id)
            print(f'  步骤{record.step_order}: {record.step_name}')
            print(f'    审批人: {approver.username if approver else "未知"} (ID: {record.approver_id})')
            print(f'    状态: {record.action or "待审批"}')
            print(f'    审批时间: {record.approved_at or "未审批"}')
            print(f'    意见: {record.comment or "无"}')
            print()
        
        # 检查当前用户是否有审批权限
        if po.status == 'pending' and po.current_approval_step:
            current_record = PricingOrderApprovalRecord.query.filter_by(
                pricing_order_id=po.id,
                step_order=po.current_approval_step
            ).first()
            
            if current_record:
                print(f'当前待审批步骤: {current_record.step_name}')
                print(f'当前审批人: {current_record.approver.username} (ID: {current_record.approver_id})')
                print(f'是否已审批: {"是" if current_record.action else "否"}')

if __name__ == '__main__':
    check_pricing_order() 