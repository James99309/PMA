#!/usr/bin/env python3

from app import create_app, db
from app.models.pricing_order import PricingOrder, PricingOrderApprovalRecord
from app.models.project import Project

def reset_po202506_007():
    app = create_app()
    with app.app_context():
        # 查找PO202506-007批价单
        po = PricingOrder.query.filter_by(order_number='PO202506-007').first()
        if not po:
            print('未找到PO202506-007批价单')
            return
        
        print(f'重置批价单: {po.order_number}')
        print(f'当前状态: {po.status}')
        
        # 重置批价单状态
        po.status = 'pending'
        po.current_approval_step = 1
        po.approved_by = None
        po.approved_at = None
        
        # 重置所有审批记录
        records = PricingOrderApprovalRecord.query.filter_by(pricing_order_id=po.id).all()
        for record in records:
            record.action = None
            record.comment = None
            record.approved_at = None
            record.is_fast_approval = False
            record.fast_approval_reason = None
        
        # 重置项目状态（如果需要）
        if po.project:
            project = po.project
            if project.current_stage == 'signed':
                project.current_stage = 'quoted'
                project.is_locked = False
                project.locked_reason = None
                print(f'项目 {project.project_name} 状态已重置为 quoted')
        
        # 重置报价单状态（如果需要）
        if po.quotation:
            quotation = po.quotation
            if quotation.approval_status == 'quoted_approved':
                quotation.approval_status = 'quoted'
                quotation.is_locked = False
                quotation.lock_reason = None
                print(f'报价单 {quotation.quotation_number} 状态已重置')
        
        # 重置结算单状态（如果需要）
        if hasattr(po, 'settlement_order') and po.settlement_order:
            settlement = po.settlement_order
            settlement.status = 'draft'
            settlement.approved_by = None
            settlement.approved_at = None
            print(f'结算单状态已重置')
        
        db.session.commit()
        print(f'✅ PO202506-007 已重置为待审批状态')
        
        # 显示重置后的状态
        print(f'\n重置后状态:')
        print(f'  批价单状态: {po.status}')
        print(f'  当前审批步骤: {po.current_approval_step}')
        print(f'  审批记录状态:')
        for record in records:
            print(f'    步骤{record.step_order}: {record.action or "待审批"}')

if __name__ == '__main__':
    reset_po202506_007() 