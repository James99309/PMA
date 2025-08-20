#!/usr/bin/env python3
"""
批价单审批系统V1到V2迁移脚本
将existing pricing_order_approval_records迁移到统一的approval_instance系统

使用方法：
python migrate_pricing_orders_to_v2.py
"""

import os
import sys
from datetime import datetime, timezone
from sqlalchemy import create_engine, text, and_
from sqlalchemy.orm import sessionmaker

# 添加项目路径到sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入应用模型
from app import create_app, db
from app.models.pricing_order import PricingOrder, PricingOrderApprovalRecord
from app.models.approval import ApprovalInstance, ApprovalRecord, ApprovalStep, ApprovalProcessTemplate, ApprovalStatus
from app.models.user import User

def migrate_pricing_orders_to_v2():
    """将V1批价单审批记录迁移到V2系统"""
    
    app = create_app()
    
    with app.app_context():
        print("🚀 开始批价单审批系统V1到V2迁移...")
        
        # 统计迁移前的数据
        v1_records_count = PricingOrderApprovalRecord.query.count()
        v2_instances_count = ApprovalInstance.query.filter_by(object_type='pricing_order').count()
        pricing_orders_with_v1 = db.session.query(PricingOrder.id).join(
            PricingOrderApprovalRecord
        ).distinct().count()
        
        print(f"📊 迁移前统计:")
        print(f"   V1审批记录: {v1_records_count}条")
        print(f"   V2审批实例: {v2_instances_count}个") 
        print(f"   使用V1的批价单: {pricing_orders_with_v1}个")
        
        if v1_records_count == 0:
            print("✅ 没有V1记录需要迁移")
            return
            
        # 获取批价单审批流程模板
        template = ApprovalProcessTemplate.query.filter_by(
            name='批价单审批',
            object_type='pricing_order'
        ).first()
        
        if not template:
            print("❌ 错误: 未找到批价单审批流程模板")
            print("   请确保V2审批模板已正确配置")
            return
            
        print(f"📝 使用审批模板: {template.name} (ID: {template.id})")
        
        # 查询所有有V1审批记录的批价单
        pricing_orders_query = db.session.query(PricingOrder).join(
            PricingOrderApprovalRecord
        ).distinct()
        
        migrated_count = 0
        error_count = 0
        
        for pricing_order in pricing_orders_query:
            try:
                print(f"\n🔄 迁移批价单: {pricing_order.order_number} (ID: {pricing_order.id})")
                
                # 检查是否已有V2实例
                existing_instance = ApprovalInstance.query.filter_by(
                    object_type='pricing_order',
                    object_id=pricing_order.id
                ).first()
                
                if existing_instance:
                    print(f"   ⚠️  已存在V2实例 (ID: {existing_instance.id})，跳过迁移")
                    continue
                
                # 获取该批价单的所有V1审批记录
                v1_records = PricingOrderApprovalRecord.query.filter_by(
                    pricing_order_id=pricing_order.id
                ).order_by(PricingOrderApprovalRecord.step_order, 
                          PricingOrderApprovalRecord.approved_at).all()
                
                if not v1_records:
                    print(f"   ⚠️  没有V1审批记录，跳过")
                    continue
                    
                print(f"   📋 找到 {len(v1_records)} 条V1审批记录")
                
                # 创建V2审批实例
                approval_instance = ApprovalInstance(
                    process_id=template.id,
                    object_type='pricing_order',
                    object_id=pricing_order.id,
                    created_by=pricing_order.created_by,
                    started_at=pricing_order.created_at
                )
                
                # 根据批价单状态设置实例状态
                if pricing_order.status == 'approved':
                    approval_instance.status = ApprovalStatus.APPROVED
                    approval_instance.ended_at = max(r.approved_at for r in v1_records if r.approved_at)
                elif pricing_order.status == 'rejected':
                    approval_instance.status = ApprovalStatus.REJECTED  
                    approval_instance.ended_at = max(r.approved_at for r in v1_records if r.approved_at)
                elif pricing_order.status == 'pending':
                    approval_instance.status = ApprovalStatus.PENDING
                    # 找到当前步骤
                    current_step_order = pricing_order.current_approval_step
                    template_step = ApprovalStep.query.filter_by(
                        process_id=template.id,
                        step_order=current_step_order
                    ).first()
                    if template_step:
                        approval_instance.current_step = template_step.id
                else:  # draft or other status
                    approval_instance.status = ApprovalStatus.PENDING
                
                db.session.add(approval_instance)
                db.session.flush()  # 获取实例ID
                
                print(f"   ✅ 创建V2审批实例 (ID: {approval_instance.id})")
                
                # 迁移V1审批记录到V2
                migrated_records = 0
                for v1_record in v1_records:
                    # 找到对应的模板步骤
                    template_step = ApprovalStep.query.filter_by(
                        process_id=template.id,
                        step_order=v1_record.step_order
                    ).first()
                    
                    if not template_step:
                        print(f"   ⚠️  未找到步骤 {v1_record.step_order} 的模板，跳过该记录")
                        continue
                    
                    # 创建V2审批记录
                    v2_record = ApprovalRecord(
                        instance_id=approval_instance.id,
                        step_id=template_step.id,
                        approver_id=v1_record.approver_id,
                        action='approve' if v1_record.approved_at else 'pending',
                        timestamp=v1_record.approved_at if v1_record.approved_at else pricing_order.created_at,
                        comment=v1_record.comment or ''  # V1系统有comment字段
                    )
                    
                    db.session.add(v2_record)
                    migrated_records += 1
                
                print(f"   📝 迁移了 {migrated_records} 条审批记录")
                
                db.session.commit()
                migrated_count += 1
                print(f"   ✅ 批价单 {pricing_order.order_number} 迁移完成")
                
            except Exception as e:
                db.session.rollback()
                error_count += 1
                print(f"   ❌ 迁移失败: {str(e)}")
                
        print(f"\n🎉 迁移完成!")
        print(f"   成功迁移: {migrated_count} 个批价单")
        print(f"   失败: {error_count} 个批价单")
        
        # 统计迁移后的数据
        v2_instances_count_after = ApprovalInstance.query.filter_by(object_type='pricing_order').count()
        print(f"   迁移后V2实例数量: {v2_instances_count_after}")
        
        if error_count == 0:
            print("✅ 所有批价单已成功迁移到V2系统!")
        else:
            print(f"⚠️  有 {error_count} 个批价单迁移失败，请检查日志")

def verify_migration():
    """验证迁移结果"""
    
    app = create_app()
    
    with app.app_context():
        print("\n🔍 验证迁移结果...")
        
        # 统计数据
        v1_pricing_orders = db.session.query(PricingOrder.id).join(
            PricingOrderApprovalRecord
        ).distinct().count()
        
        v2_pricing_orders = ApprovalInstance.query.filter_by(
            object_type='pricing_order'
        ).count()
        
        orphaned_v1_records = PricingOrderApprovalRecord.query.outerjoin(
            ApprovalInstance,
            and_(
                ApprovalInstance.object_type == 'pricing_order',
                ApprovalInstance.object_id == PricingOrderApprovalRecord.pricing_order_id
            )
        ).filter(ApprovalInstance.id.is_(None)).count()
        
        print(f"📊 验证结果:")
        print(f"   V1批价单数量: {v1_pricing_orders}")
        print(f"   V2批价单数量: {v2_pricing_orders}")
        print(f"   孤立的V1记录: {orphaned_v1_records}")
        
        if v1_pricing_orders == v2_pricing_orders and orphaned_v1_records == 0:
            print("✅ 迁移验证通过!")
        else:
            print("❌ 迁移可能不完整，请检查数据")

if __name__ == '__main__':
    print("批价单审批系统V1到V2迁移工具")
    print("=" * 50)
    
    try:
        migrate_pricing_orders_to_v2()
        verify_migration()
        
    except Exception as e:
        print(f"\n❌ 迁移过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    print("\n🚀 迁移工具执行完毕!")