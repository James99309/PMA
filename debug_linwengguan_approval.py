#!/usr/bin/env python3

from app import create_app, db
from app.models.pricing_order import PricingOrder, PricingOrderApprovalRecord
from app.models.user import User
from app.services.pricing_order_service import PricingOrderService

def debug_linwengguan_approval():
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
        
        # 查找林文冠用户
        linwengguan = User.query.filter_by(username='linwengguan').first()
        if not linwengguan:
            print('未找到linwengguan用户')
            return
        
        print(f'\n林文冠用户信息:')
        print(f'  ID: {linwengguan.id}')
        print(f'  用户名: {linwengguan.username}')
        print(f'  姓名: {linwengguan.real_name}')
        print(f'  角色: {linwengguan.role}')
        
        # 检查当前审批记录
        current_record = PricingOrderApprovalRecord.query.filter_by(
            pricing_order_id=po.id,
            step_order=po.current_approval_step
        ).first()
        
        if current_record:
            print(f'\n当前审批记录:')
            print(f'  步骤: {current_record.step_order}')
            print(f'  名称: {current_record.step_name}')
            print(f'  审批人ID: {current_record.approver_id}')
            print(f'  林文冠ID: {linwengguan.id}')
            print(f'  是否匹配: {current_record.approver_id == linwengguan.id}')
            print(f'  当前状态: {current_record.action or "待审批"}')
            
            # 如果已经审批过了，说明问题可能在前端
            if current_record.action:
                print(f'  ⚠️  该步骤已经审批过了！')
                print(f'  审批时间: {current_record.approved_at}')
                print(f'  审批意见: {current_record.comment}')
                
                # 检查是否触发了快速通过
                if current_record.is_fast_approval:
                    print(f'  🚀 触发了快速通过机制')
                    print(f'  快速通过原因: {current_record.fast_approval_reason}')
                
                print(f'\n批价单当前状态: {po.status}')
                if po.status == 'approved':
                    print(f'  ✅ 批价单已经审批通过，无需再次审批')
                    print(f'  审批完成时间: {po.approved_at}')
                    print(f'  审批人: {po.approved_by}')
        
        # 检查结算单折扣率（快速通过条件）
        print(f'\n快速通过检查:')
        print(f'  结算单折扣率: {po.settlement_discount_percentage}%')
        print(f'  渠道经理快速通过标准: {PricingOrderService.FAST_APPROVAL_RULES.get("渠道经理", "未定义")}%')
        
        if po.settlement_discount_percentage and PricingOrderService.FAST_APPROVAL_RULES.get("渠道经理"):
            is_fast = po.settlement_discount_percentage >= PricingOrderService.FAST_APPROVAL_RULES["渠道经理"]
            print(f'  是否满足快速通过: {is_fast}')

if __name__ == '__main__':
    debug_linwengguan_approval() 