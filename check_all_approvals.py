#!/usr/bin/env python3
"""
检查所有审批实例，特别是报价单相关的
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.quotation import Quotation
from app.models.approval import ApprovalInstance, ApprovalProcessTemplate

def check_all_approvals():
    """检查所有审批实例"""
    
    app = create_app()
    
    with app.app_context():
        print("=== 所有审批实例检查 ===\n")
        
        # 1. 检查所有审批实例
        all_instances = ApprovalInstance.query.all()
        print(f"总审批实例数: {len(all_instances)}")
        
        # 按对象类型分组
        by_type = {}
        for instance in all_instances:
            obj_type = instance.object_type
            if obj_type not in by_type:
                by_type[obj_type] = []
            by_type[obj_type].append(instance)
        
        for obj_type, instances in by_type.items():
            print(f"\n{obj_type} 类型审批实例 ({len(instances)}个):")
            for instance in instances:
                print(f"  - 实例ID: {instance.id}")
                print(f"    对象ID: {instance.object_id}")
                print(f"    状态: {instance.status}")
                print(f"    发起人: {instance.creator.username if instance.creator else '未知'}")
                print(f"    发起时间: {instance.started_at}")
                
                # 如果是报价单，显示报价单编号
                if obj_type == 'quotation':
                    quotation = Quotation.query.get(instance.object_id)
                    if quotation:
                        print(f"    报价单编号: {quotation.quotation_number}")
                    else:
                        print(f"    报价单编号: 报价单不存在")
        
        # 2. 检查QU202505-006报价单
        print(f"\n=== QU202505-006 报价单检查 ===")
        quotation = Quotation.query.filter_by(quotation_number='QU202505-006').first()
        if quotation:
            print(f"报价单ID: {quotation.id}")
            print(f"报价单状态: 存在")
            
            # 查找是否有历史审批实例（包括已删除的）
            quotation_instances = ApprovalInstance.query.filter_by(
                object_type='quotation',
                object_id=quotation.id
            ).all()
            
            if quotation_instances:
                print(f"找到 {len(quotation_instances)} 个相关审批实例:")
                for instance in quotation_instances:
                    print(f"  - 实例ID: {instance.id}")
                    print(f"    状态: {instance.status}")
                    print(f"    发起时间: {instance.started_at}")
                    print(f"    结束时间: {instance.ended_at or '进行中'}")
            else:
                print("未找到任何相关审批实例")
        else:
            print("报价单不存在")
        
        # 3. 检查审批模板
        print(f"\n=== 审批模板检查 ===")
        templates = ApprovalProcessTemplate.query.filter_by(object_type='quotation').all()
        print(f"报价单审批模板数: {len(templates)}")
        
        for template in templates:
            print(f"  - 模板ID: {template.id}")
            print(f"    模板名称: {template.name}")
            print(f"    是否启用: {template.is_active}")
            print(f"    创建时间: {template.created_at}")

if __name__ == "__main__":
    check_all_approvals() 