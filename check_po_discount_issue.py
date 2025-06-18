#!/usr/bin/env python3
"""
检查PO202506-020批价单的折扣权限问题
"""

from app import create_app
from app.models.pricing_order import PricingOrder
from app.models.user import User
from app.helpers.approval_helpers import check_step_discount_violations, get_approval_step_discount_status

def check_po_discount_issue():
    app = create_app()
    with app.app_context():
        # 查找批价单
        po = PricingOrder.query.filter_by(order_number='PO202506-020').first()
        if not po:
            print("❌ 未找到 PO202506-020 批价单")
            return
        
        print(f"=== PO202506-020 批价单信息 ===")
        print(f"订单号: {po.order_number}")
        print(f"状态: {po.status}")
        print(f"创建者ID: {po.created_by}")
        print(f"项目ID: {po.project_id}")
        
        # 获取创建者信息
        creator = User.query.get(po.created_by) if po.created_by else None
        if creator:
            print(f"创建者: {creator.username} ({creator.role})")
            
        print(f"\n=== 折扣率信息 ===")
        print(f"批价总折扣率: {po.pricing_total_discount_rate}")
        print(f"批价折扣百分比: {po.pricing_discount_percentage}%")
        print(f"结算总折扣率: {po.settlement_total_discount_rate}")
        print(f"结算折扣百分比: {po.settlement_discount_percentage}%")
        
        print(f"\n=== 明细折扣率 ===")
        if po.pricing_details:
            print(f"批价明细数量: {len(po.pricing_details)}")
            for i, detail in enumerate(po.pricing_details[:5]):  # 显示前5个明细
                discount_pct = round(detail.discount_rate * 100, 2)
                print(f"  批价明细{i+1}: 折扣率{detail.discount_rate} ({discount_pct}%)")
        
        if po.settlement_details:
            print(f"结算明细数量: {len(po.settlement_details)}")
            for i, detail in enumerate(po.settlement_details[:5]):  # 显示前5个明细
                discount_pct = round(detail.discount_rate * 100, 2)
                print(f"  结算明细{i+1}: 折扣率{detail.discount_rate} ({discount_pct}%)")
        
        if not po.pricing_details and not po.settlement_details:
            print("无明细数据")
        
        # 检查权限违规
        print(f"\n=== 权限检查 ===")
        if creator:
            try:
                print(f"创建者角色: {creator.role}")
                
                # 使用服务检查用户权限
                from app.services.discount_permission_service import DiscountPermissionService
                user_limits = DiscountPermissionService.get_user_discount_limits(creator)
                print(f"用户权限限制: {user_limits}")
                
                # 检查创建者的权限违规（第0步 - 流程发起）
                violation_result = check_step_discount_violations(po, 0, creator.id)
                print(f"\n发起步骤权限检查结果:")
                print(f"  是否有违规: {violation_result['has_violation']}")
                print(f"  违规详情: {violation_result['violations']}")
                
                if violation_result['has_violation']:
                    print(f"❌ 发现权限违规:")
                    for violation in violation_result['violations']:
                        if violation['type'] == 'pricing_detail':
                            print(f"  - 批价明细 {violation['product_name']}: 折扣{violation['discount_rate']*100:.2f}% < 权限下限{violation['limit']}%")
                        elif violation['type'] == 'pricing_total':
                            print(f"  - 批价总折扣率: {violation['discount_rate']:.2f}% < 权限下限{violation['limit']}%")
                        elif violation['type'] == 'settlement_detail':
                            print(f"  - 结算明细 {violation['product_name']}: 折扣{violation['discount_rate']*100:.2f}% < 权限下限{violation['limit']}%")
                        elif violation['type'] == 'settlement_total':
                            print(f"  - 结算总折扣率: {violation['discount_rate']:.2f}% < 权限下限{violation['limit']}%")
                else:
                    print(f"✅ 创建者权限检查通过，无违规")
                    
            except Exception as e:
                print(f"❌ 权限检查出错: {e}")
                import traceback
                traceback.print_exc()
        
        # 检查所有审批步骤的权限状态
        print(f"\n=== 所有审批步骤权限状态 ===")
        try:
            step_statuses = get_approval_step_discount_status(po)
            print(f"获取到的步骤状态: {step_statuses}")
            
            for step_order, status in step_statuses.items():
                if step_order == 0:
                    print(f"流程发起步骤: {status['user_name']} ({status['user_role']})")
                else:
                    print(f"审批步骤{step_order}: {status['user_name']} ({status['user_role']})")
                
                if status['has_violation']:
                    print(f"  ❌ 存在权限违规")
                    for violation in status['violations']:
                        print(f"    - {violation}")
                else:
                    print(f"  ✅ 权限正常")
        except Exception as e:
            print(f"❌ 审批步骤权限检查出错: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    check_po_discount_issue() 